"""
Alert Engine Service.

High-performance alert rule evaluation engine with sub-500ms latency target
supporting multiple rule types and real-time alert generation.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

import structlog
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database.connection import get_db_session
from ..database.decorators import with_db_session, handle_db_errors
from ..models.instruments import Instrument
from ..models.market_data import MarketData
from ..models.alert_rules import AlertRule, RuleType, RuleCondition
from ..models.alert_logs import AlertLog, AlertStatus, DeliveryStatus
from ..websocket.realtime import get_websocket_manager

logger = structlog.get_logger()


class AlertContext:
    """Context data for alert evaluation and firing."""
    
    def __init__(
        self,
        rule: AlertRule,
        current_price: float,
        trigger_value: float,
        evaluation_time_ms: int,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        self.rule = rule
        self.current_price = current_price
        self.trigger_value = trigger_value
        self.evaluation_time_ms = evaluation_time_ms
        self.additional_data = additional_data or {}
        self.timestamp = datetime.utcnow()


class RuleEvaluator:
    """
    Rule evaluation logic for different alert rule types.
    
    Optimized for sub-500ms evaluation performance with caching
    and efficient data access patterns.
    """
    
    def __init__(self):
        # Cache for historical data queries
        self._price_history_cache: Dict[Tuple[int, int], List[float]] = {}
        self._cache_max_age = 60  # 1 minute cache TTL
        self._last_cache_cleanup = time.time()
    
    async def evaluate_threshold_rule(
        self,
        rule: AlertRule,
        current_price: float,
        session
    ) -> Optional[AlertContext]:
        """
        Evaluate static threshold rule.
        
        Args:
            rule: Alert rule to evaluate.
            current_price: Current market price.
            session: Database session.
        
        Returns:
            Optional[AlertContext]: Alert context if rule triggered, None otherwise.
        """
        start_time = time.time()
        threshold = float(rule.threshold)
        triggered = False
        
        if rule.condition == RuleCondition.ABOVE and current_price > threshold:
            triggered = True
        elif rule.condition == RuleCondition.BELOW and current_price < threshold:
            triggered = True
        elif rule.condition == RuleCondition.EQUALS and abs(current_price - threshold) < 0.01:
            triggered = True
        
        if triggered:
            evaluation_time_ms = int((time.time() - start_time) * 1000)
            return AlertContext(
                rule=rule,
                current_price=current_price,
                trigger_value=current_price,
                evaluation_time_ms=evaluation_time_ms,
                additional_data={"threshold": threshold}
            )
        
        return None
    
    async def evaluate_rate_of_change_rule(
        self,
        rule: AlertRule,
        current_price: float,
        session
    ) -> Optional[AlertContext]:
        """
        Evaluate rate-of-change rule.
        
        Args:
            rule: Alert rule to evaluate.
            current_price: Current market price.
            session: Database session.
        
        Returns:
            Optional[AlertContext]: Alert context if rule triggered, None otherwise.
        """
        start_time = time.time()
        
        if not rule.time_window_seconds:
            return None
        
        # Get historical price for comparison
        time_ago = datetime.utcnow() - timedelta(seconds=rule.time_window_seconds)
        
        historical_result = await session.execute(
            select(MarketData.price)
            .where(
                MarketData.instrument_id == rule.instrument_id,
                MarketData.timestamp >= time_ago
            )
            .order_by(MarketData.timestamp)
            .limit(1)
        )
        
        historical_price = historical_result.scalar()
        if not historical_price:
            return None
        
        historical_price = float(historical_price)
        
        # Calculate percentage change
        pct_change = ((current_price - historical_price) / historical_price) * 100
        threshold_pct = float(rule.threshold)  # Threshold is percentage
        
        triggered = False
        if rule.condition == RuleCondition.PERCENT_CHANGE_UP and pct_change >= threshold_pct:
            triggered = True
        elif rule.condition == RuleCondition.PERCENT_CHANGE_DOWN and pct_change <= -threshold_pct:
            triggered = True
        
        if triggered:
            evaluation_time_ms = int((time.time() - start_time) * 1000)
            return AlertContext(
                rule=rule,
                current_price=current_price,
                trigger_value=pct_change,
                evaluation_time_ms=evaluation_time_ms,
                additional_data={
                    "historical_price": historical_price,
                    "percent_change": pct_change,
                    "time_window_seconds": rule.time_window_seconds
                }
            )
        
        return None
    
    async def evaluate_volume_spike_rule(
        self,
        rule: AlertRule,
        current_volume: Optional[int],
        session
    ) -> Optional[AlertContext]:
        """
        Evaluate volume spike rule.
        
        Args:
            rule: Alert rule to evaluate.
            current_volume: Current trade volume.
            session: Database session.
        
        Returns:
            Optional[AlertContext]: Alert context if rule triggered, None otherwise.
        """
        if not current_volume:
            return None
        
        start_time = time.time()
        threshold_volume = float(rule.threshold)
        
        triggered = False
        if rule.condition == RuleCondition.VOLUME_ABOVE and current_volume > threshold_volume:
            triggered = True
        
        if triggered:
            evaluation_time_ms = int((time.time() - start_time) * 1000)
            return AlertContext(
                rule=rule,
                current_price=0.0,  # Not applicable for volume rules
                trigger_value=float(current_volume),
                evaluation_time_ms=evaluation_time_ms,
                additional_data={"volume_threshold": threshold_volume}
            )
        
        return None


class AlertEngine:
    """
    Real-time alert rule evaluation engine.
    
    Evaluates alert rules against incoming market data with sub-500ms latency
    target and manages alert firing, suppression, and delivery tracking.
    """
    
    def __init__(self):
        self.evaluator = RuleEvaluator()
        self.websocket_manager = get_websocket_manager()
        self.notification_service = None  # Will be set by dependency injection
        
        # Engine state
        self.is_running = False
        self.evaluation_queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
        
        # Performance metrics
        self.evaluations_performed = 0
        self.alerts_fired = 0
        self.total_evaluation_time_ms = 0
        self.max_evaluation_time_ms = 0
        
        # Rule cache for performance
        self._active_rules_cache: Dict[int, List[AlertRule]] = {}
        self._cache_last_updated = datetime.min
        self._cache_ttl = 60  # 60 seconds cache TTL
    
    async def start(self) -> None:
        """
        Start the alert engine.
        
        Initializes rule caching and starts background evaluation loop.
        """
        if self.is_running:
            logger.warning("Alert engine already running")
            return
        
        logger.info("Starting alert engine")
        
        # Load active rules cache
        await self._refresh_rules_cache()
        
        # Start background evaluation loop
        self.is_running = True
        asyncio.create_task(self._evaluation_loop())
        
        logger.info("Alert engine started successfully")
    
    async def stop(self) -> None:
        """
        Stop the alert engine.
        
        Gracefully shuts down evaluation loop and processes remaining queue.
        """
        if not self.is_running:
            return
        
        logger.info("Stopping alert engine")
        self.is_running = False
        
        # Process remaining evaluations in queue
        await self._flush_evaluation_queue()
        
        logger.info("Alert engine stopped")
    
    async def queue_evaluation(self, instrument_id: int, market_data: MarketData) -> None:
        """
        Queue market data for alert rule evaluation.
        
        Args:
            instrument_id: Instrument ID for evaluation.
            market_data: Latest market data.
        """
        try:
            evaluation_data = {
                "instrument_id": instrument_id,
                "market_data": market_data,
                "queued_at": datetime.utcnow()
            }
            
            self.evaluation_queue.put_nowait(evaluation_data)
            
        except asyncio.QueueFull:
            logger.warning("Alert evaluation queue full, dropping evaluation")
    
    async def _evaluation_loop(self) -> None:
        """
        Background loop for processing alert rule evaluations.
        
        Processes queued evaluations with batch processing and performance
        optimization to meet sub-500ms latency targets.
        """
        batch_size = 50  # Process up to 50 evaluations per batch
        batch_timeout = 0.1  # 100ms batch timeout for low latency
        
        while self.is_running:
            batch_evaluations = []
            batch_start = asyncio.get_event_loop().time()
            
            try:
                # Collect batch evaluations
                while (
                    len(batch_evaluations) < batch_size and
                    (asyncio.get_event_loop().time() - batch_start) < batch_timeout
                ):
                    try:
                        evaluation = await asyncio.wait_for(
                            self.evaluation_queue.get(),
                            timeout=0.05  # 50ms timeout
                        )
                        batch_evaluations.append(evaluation)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if we have evaluations
                if batch_evaluations:
                    await self._process_evaluation_batch(batch_evaluations)
                
                # Refresh rules cache periodically
                if self._should_refresh_cache():
                    await self._refresh_rules_cache()
                    
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(0.1)  # Brief pause on error
    
    @with_db_session
    @handle_db_errors("Evaluation batch processing")
    async def _process_evaluation_batch(self, session, batch_evaluations: List[Dict]) -> None:
        """
        Process a batch of alert rule evaluations.
        
        Args:
            session: Database session.
            batch_evaluations: List of evaluation data.
        """
        alerts_to_fire = []
        
        for eval_data in batch_evaluations:
            instrument_id = eval_data["instrument_id"]
            market_data = eval_data["market_data"]
            
            # Get active rules for this instrument
            rules = self._active_rules_cache.get(instrument_id, [])
            
            # Evaluate each rule
            for rule in rules:
                # Check cooldown period
                if rule.is_in_cooldown():
                    continue
                
                # Evaluate rule based on type
                alert_context = await self._evaluate_rule(rule, market_data, session)
                
                if alert_context:
                    alerts_to_fire.append(alert_context)
        
        # Fire all triggered alerts
        for alert_context in alerts_to_fire:
            await self._fire_alert(alert_context, session)
    
    async def _evaluate_rule(
        self,
        rule: AlertRule,
        market_data: MarketData,
        session
    ) -> Optional[AlertContext]:
        """
        Evaluate a single alert rule against market data.
        
        Args:
            rule: Alert rule to evaluate.
            market_data: Current market data.
            session: Database session.
        
        Returns:
            Optional[AlertContext]: Alert context if triggered, None otherwise.
        """
        current_price = float(market_data.price) if market_data.price else 0.0
        current_volume = market_data.volume
        
        # Route to appropriate evaluator based on rule type
        if rule.rule_type == RuleType.THRESHOLD:
            return await self.evaluator.evaluate_threshold_rule(rule, current_price, session)
        
        elif rule.rule_type == RuleType.RATE_OF_CHANGE:
            return await self.evaluator.evaluate_rate_of_change_rule(rule, current_price, session)
        
        elif rule.rule_type == RuleType.VOLUME_SPIKE:
            return await self.evaluator.evaluate_volume_spike_rule(rule, current_volume, session)
        
        # TODO: Implement crossover and multi-condition rules
        elif rule.rule_type == RuleType.CROSSOVER:
            logger.debug(f"Crossover rules not yet implemented for rule {rule.id}")
            return None
        
        elif rule.rule_type == RuleType.MULTI_CONDITION:
            logger.debug(f"Multi-condition rules not yet implemented for rule {rule.id}")
            return None
        
        return None
    
    @handle_db_errors("Alert firing")
    async def _fire_alert(self, alert_context: AlertContext, session) -> None:
        """
        Fire an alert and log the event.
        
        Args:
            alert_context: Context data for the alert.
            session: Database session.
        """
        rule = alert_context.rule
    
        # Create alert log entry
        alert_log = AlertLog(
            timestamp=alert_context.timestamp,
            rule_id=rule.id,
            instrument_id=rule.instrument_id,
            trigger_value=alert_context.trigger_value,
            threshold_value=float(rule.threshold),
            fired_status=AlertStatus.FIRED,
            delivery_status=DeliveryStatus.PENDING,
            evaluation_time_ms=alert_context.evaluation_time_ms,
            rule_condition=rule.condition.value,
            alert_message=self._generate_alert_message(alert_context),
        )
    
        session.add(alert_log)
    
        # Update rule last triggered time
        rule.last_triggered = alert_context.timestamp
    
        # Update performance metrics
        self.alerts_fired += 1
        self.total_evaluation_time_ms += alert_context.evaluation_time_ms
        self.max_evaluation_time_ms = max(
            self.max_evaluation_time_ms,
            alert_context.evaluation_time_ms
        )
    
        # Broadcast alert via WebSocket
        await self.websocket_manager.broadcast_alert_fired(
            rule_id=rule.id,
            instrument_id=rule.instrument_id,
            symbol=rule.instrument.symbol,  # Assuming instrument is loaded
            trigger_value=alert_context.trigger_value,
            threshold_value=float(rule.threshold),
            condition=rule.condition.value,
            timestamp=alert_context.timestamp,
            evaluation_time_ms=alert_context.evaluation_time_ms
        )
    
        logger.info(
            f"Alert fired for rule {rule.id}: {rule.instrument.symbol} "
            f"{rule.condition.value} {rule.threshold} (actual: {alert_context.trigger_value})",
            rule_id=rule.id,
            instrument_symbol=rule.instrument.symbol,
            evaluation_time_ms=alert_context.evaluation_time_ms
        )
    
    def _generate_alert_message(self, alert_context: AlertContext) -> str:
        """
        Generate human-readable alert message.
        
        Args:
            alert_context: Alert context data.
        
        Returns:
            str: Formatted alert message.
        """
        rule = alert_context.rule
        
        if rule.name:
            base_msg = f"Alert: {rule.name}"
        else:
            base_msg = f"Alert: {rule.instrument.symbol} {rule.rule_type.value}"
        
        if rule.rule_type == RuleType.THRESHOLD:
            return (
                f"{base_msg} - Price {alert_context.current_price} "
                f"{rule.condition.value} threshold {rule.threshold}"
            )
        elif rule.rule_type == RuleType.RATE_OF_CHANGE:
            pct_change = alert_context.additional_data.get("percent_change", 0)
            return (
                f"{base_msg} - {pct_change:.2f}% change "
                f"in {rule.time_window_seconds}s (threshold: {rule.threshold}%)"
            )
        elif rule.rule_type == RuleType.VOLUME_SPIKE:
            return (
                f"{base_msg} - Volume {alert_context.trigger_value} "
                f"above threshold {rule.threshold}"
            )
        
        return f"{base_msg} - Triggered at {alert_context.timestamp}"
    
    @with_db_session
    @handle_db_errors("Rules cache refresh")
    async def _refresh_rules_cache(self, session) -> None:
        """
        Refresh the active rules cache for performance optimization.
        """
        # Get all active rules grouped by instrument
        result = await session.execute(
            select(AlertRule)
            .where(AlertRule.active == True)
            .options(selectinload(AlertRule.instrument))
            .order_by(AlertRule.instrument_id, AlertRule.created_at)
        )
        
        rules = result.scalars().all()
        
        # Group rules by instrument ID
        rules_by_instrument = {}
        for rule in rules:
            if rule.instrument_id not in rules_by_instrument:
                rules_by_instrument[rule.instrument_id] = []
            rules_by_instrument[rule.instrument_id].append(rule)
        
        self._active_rules_cache = rules_by_instrument
        self._cache_last_updated = datetime.utcnow()
        
        total_rules = sum(len(rules) for rules in rules_by_instrument.values())
        logger.debug(
            f"Refreshed rules cache: {total_rules} active rules for "
            f"{len(rules_by_instrument)} instruments"
        )
    
    def _should_refresh_cache(self) -> bool:
        """
        Check if rules cache should be refreshed.
        
        Returns:
            bool: True if cache needs refresh.
        """
        cache_age = (datetime.utcnow() - self._cache_last_updated).total_seconds()
        return cache_age > self._cache_ttl
    
    async def _flush_evaluation_queue(self) -> None:
        """Process all remaining evaluations in queue during shutdown."""
        if self.evaluation_queue.empty():
            return
        
        logger.info("Flushing remaining evaluations from queue")
        remaining_evaluations = []
        
        while not self.evaluation_queue.empty():
            try:
                evaluation = self.evaluation_queue.get_nowait()
                remaining_evaluations.append(evaluation)
            except asyncio.QueueEmpty:
                break
        
        if remaining_evaluations:
            await self._process_evaluation_batch(remaining_evaluations)
            logger.info(f"Flushed {len(remaining_evaluations)} remaining evaluations")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get alert engine performance statistics.
        
        Returns:
            Dict: Performance metrics and statistics.
        """
        avg_evaluation_time = (
            self.total_evaluation_time_ms / max(self.evaluations_performed, 1)
        )
        
        return {
            "running": self.is_running,
            "evaluations_performed": self.evaluations_performed,
            "alerts_fired": self.alerts_fired,
            "avg_evaluation_time_ms": round(avg_evaluation_time, 2),
            "max_evaluation_time_ms": self.max_evaluation_time_ms,
            "queue_size": self.evaluation_queue.qsize(),
            "active_rules_cached": sum(len(rules) for rules in self._active_rules_cache.values()),
            "cache_last_updated": self._cache_last_updated.isoformat(),
        }