"""
Real-time WebSocket endpoints.

Provides WebSocket connections for real-time market data streaming,
alert notifications, and system status updates with <100ms delivery targets.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Set, Optional, Any, List

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..config import settings
from .message_types import (
    WebSocketMessage as TypedWebSocketMessage, OutgoingMessage,
    MarketDataMessage, MarketDataUpdate, AlertMessage, AlertNotification,
    AnalyticsMessage, AnalyticsUpdate, TechnicalIndicatorMessage, TechnicalIndicatorUpdate,
    ConnectionMessage, ConnectionStatus, ErrorMessage, ErrorDetails
)
from .message_handler import MessageHandler

logger = structlog.get_logger()
router = APIRouter()


class WebSocketMessage(BaseModel):
    """Legacy base model for WebSocket messages - kept for backward compatibility."""
    type: str
    timestamp: datetime
    data: Dict[str, Any]


class ConnectionManager:
    """
    Enhanced WebSocket connection manager with typed message support.
    
    Manages active WebSocket connections for real-time broadcasting
    of market data, alerts, and system status updates with comprehensive
    message validation and performance optimization.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # client_id -> websocket
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> subscription types
        self.connection_count = 0
        self.max_connections = settings.MAX_WEBSOCKET_CONNECTIONS
        self.message_handler = MessageHandler()
        self.performance_metrics = {
            "messages_sent": 0,
            "broadcast_times": [],
            "average_broadcast_time": 0.0
        }
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> tuple[bool, str]:
        """
        Accept new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to accept.
        
        Returns:
            bool: True if connection accepted, False if at capacity.
        """
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"WebSocket connection rejected: at capacity ({self.max_connections})")
            return False, ""
        
        # Generate client ID if not provided
        if not client_id:
            client_id = f"client_{self.connection_count + 1}_{int(time.time())}"
        
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        self.connection_count += 1
        
        logger.info(f"WebSocket connection accepted for {client_id}. Active connections: {len(self.active_connections)}")
        
        # Send typed welcome message
        welcome_message = ConnectionMessage(
            data=ConnectionStatus(
                client_id=client_id,
                connected_at=datetime.utcnow(),
                subscriptions=[],
                last_heartbeat=datetime.utcnow(),
                connection_quality="good"
            )
        )
        
        # Convert ConnectionMessage to dict for JSON serialization
        welcome_dict = {
            "type": "connection",
            "data": {
                "client_id": client_id,
                "connected_at": datetime.utcnow().isoformat(),
                "subscriptions": [],
                "last_heartbeat": datetime.utcnow().isoformat(),
                "connection_quality": "good"
            }
        }
        
        await self.send_personal_message(websocket, welcome_dict)
        
        return True, client_id
    
    def disconnect(self, client_id: str) -> None:
        """
        Remove WebSocket connection by client ID.
        
        Args:
            client_id: Client identifier to disconnect.
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")
    
    def disconnect_websocket(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection by websocket instance (backward compatibility).
        
        Args:
            websocket: WebSocket connection to remove.
        """
        client_id = None
        for cid, ws in self.active_connections.items():
            if ws == websocket:
                client_id = cid
                break
        if client_id:
            self.disconnect(client_id)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        """
        Send message to specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection.
            message: Message to send.
        """
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect_websocket(websocket)
    
    async def broadcast(self, message: dict) -> None:
        """
        Broadcast message to all active connections.
        
        Args:
            message: Message to broadcast.
        """
        if not self.active_connections:
            return
        
        # Create JSON message once for efficiency
        json_message = json.dumps(message, default=str)
        
        # Send to all connections, remove failed ones
        disconnected_connections = set()
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to connection: {e}")
                disconnected_connections.add(connection)
        
        # Remove failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        if disconnected_connections:
            logger.info(f"Removed {len(disconnected_connections)} failed connections")
    
    async def broadcast_tick_update(
        self, 
        instrument_id: int, 
        symbol: str, 
        price: float, 
        volume: int, 
        timestamp: datetime,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        change_percent: Optional[float] = None
    ) -> None:
        """
        Broadcast typed market tick update.
        
        Args:
            instrument_id: Instrument ID.
            symbol: Instrument symbol.
            price: Current price.
            volume: Trade volume.
            timestamp: Tick timestamp.
            bid: Bid price (optional).
            ask: Ask price (optional).
            change_percent: Price change percentage (optional).
        """
        message = MarketDataMessage(
            data=MarketDataUpdate(
                instrument_id=instrument_id,
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=timestamp,
                bid=bid,
                ask=ask,
                change_percent=change_percent
            )
        )
        await self.broadcast_message(message, "market_data")
    
    async def broadcast_alert_fired(
        self,
        alert_id: int,
        rule_id: int,
        instrument_id: int,
        symbol: str,
        rule_name: str,
        trigger_value: float,
        threshold_value: float,
        condition: str,
        timestamp: datetime,
        evaluation_time_ms: Optional[int] = None,
        severity: str = "medium",
        message_text: str = "Alert condition triggered"
    ) -> None:
        """
        Broadcast typed alert firing notification.
        
        Args:
            alert_id: Alert ID.
            rule_id: Rule ID that fired.
            instrument_id: Instrument ID.
            symbol: Instrument symbol.
            rule_name: Name of the rule.
            trigger_value: Value that triggered the alert.
            threshold_value: Threshold from the rule.
            condition: Rule condition.
            timestamp: Alert timestamp.
            evaluation_time_ms: Rule evaluation time.
            severity: Alert severity level.
            message_text: Alert message text.
        """
        message = AlertMessage(
            data=AlertNotification(
                alert_id=alert_id,
                rule_id=rule_id,
                instrument_id=instrument_id,
                symbol=symbol,
                rule_name=rule_name,
                condition=condition,
                target_value=threshold_value,
                current_value=trigger_value,
                severity=severity,
                message=message_text,
                evaluation_time_ms=evaluation_time_ms,
                rule_condition=condition
            )
        )
        await self.broadcast_message(message, "alerts")
    
    async def broadcast_health_status(self, status: dict) -> None:
        """
        Broadcast system health status (legacy method).
        
        Args:
            status: Health status data.
        """
        message = {
            "type": "health_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": status
        }
        await self.broadcast(message)
        
    async def broadcast_analytics_update(
        self,
        instrument_id: int,
        symbol: str,
        analysis_type: str,
        results: Dict[str, Any],
        confidence_score: Optional[float] = None
    ) -> None:
        """
        Broadcast typed analytics update.
        
        Args:
            instrument_id: Instrument ID.
            symbol: Instrument symbol.
            analysis_type: Type of analysis.
            results: Analysis results.
            confidence_score: Analysis confidence score.
        """
        message = AnalyticsMessage(
            data=AnalyticsUpdate(
                instrument_id=instrument_id,
                symbol=symbol,
                analysis_type=analysis_type,
                results=results,
                calculation_time=datetime.utcnow(),
                confidence_score=confidence_score
            )
        )
        await self.broadcast_message(message, f"analytics_{instrument_id}")
    
    async def broadcast_technical_indicators(
        self,
        instrument_id: int,
        symbol: str,
        indicators: Dict[str, Any],
        timeframe: str = "1min"
    ) -> None:
        """
        Broadcast typed technical indicator update.
        
        Args:
            instrument_id: Instrument ID.
            symbol: Instrument symbol.
            indicators: Technical indicators data.
            timeframe: Analysis timeframe.
        """
        message = TechnicalIndicatorMessage(
            data=TechnicalIndicatorUpdate(
                instrument_id=instrument_id,
                symbol=symbol,
                indicators=indicators,
                calculated_at=datetime.utcnow(),
                timeframe=timeframe
            )
        )
        await self.broadcast_message(message, f"technical_indicators_{instrument_id}")
    
    async def broadcast_rule_triggered(self, rule_id: int, match_details: dict, evaluation_time: int) -> None:
        """
        Broadcast rule trigger notification.
        
        Args:
            rule_id: Rule ID that triggered.
            match_details: Rule match details.
            evaluation_time: Evaluation time in milliseconds.
        """
        message = {
            "type": "rule_triggered",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "rule_id": rule_id,
                "match_details": match_details,
                "evaluation_time": evaluation_time
            }
        }
        await self.broadcast(message)

    # Phase 3: Historical Data WebSocket Integration
    
    async def broadcast_historical_data_progress(
        self,
        query_id: str,
        symbol: str,
        progress_percent: float,
        current_step: str,
        estimated_completion: Optional[datetime] = None
    ) -> None:
        """Broadcast progress updates for historical data queries."""
        
        message = WebSocketMessage(
            type="historical_data_progress",
            timestamp=datetime.now(),
            data={
                "query_id": query_id,
                "symbol": symbol,
                "progress_percent": progress_percent,
                "current_step": current_step,
                "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
                "status": "in_progress"
            }
        )
        
        await self.broadcast(message)
        
        logger.debug(f"Historical data progress broadcasted: {symbol} {progress_percent}%")
    
    async def broadcast_historical_data_complete(
        self,
        query_id: str,
        symbol: str,
        bars_retrieved: int,
        execution_time_ms: float,
        cache_hit: bool = False
    ) -> None:
        """Broadcast completion of historical data query."""
        
        message = WebSocketMessage(
            type="historical_data_complete",
            timestamp=datetime.now(),
            data={
                "query_id": query_id,
                "symbol": symbol,
                "bars_retrieved": bars_retrieved,
                "execution_time_ms": execution_time_ms,
                "cache_hit": cache_hit,
                "status": "complete"
            }
        )
        
        await self.broadcast(message)
        
        logger.info(f"Historical data query completed: {symbol} - {bars_retrieved} bars")
    
    async def broadcast_historical_data_error(
        self,
        query_id: str,
        symbol: str,
        error_message: str,
        error_type: str = "general"
    ) -> None:
        """Broadcast historical data query error."""
        
        message = WebSocketMessage(
            type="historical_data_error",
            timestamp=datetime.now(),
            data={
                "query_id": query_id,
                "symbol": symbol,
                "error_message": error_message,
                "error_type": error_type,
                "status": "error"
            }
        )
        
        await self.broadcast(message)
        
        logger.error(f"Historical data query error broadcasted: {symbol} - {error_message}")
    
    async def broadcast_aggregation_progress(
        self,
        aggregation_id: str,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        progress_percent: float
    ) -> None:
        """Broadcast progress updates for data aggregation operations."""
        
        message = WebSocketMessage(
            type="aggregation_progress",
            timestamp=datetime.now(),
            data={
                "aggregation_id": aggregation_id,
                "symbol": symbol,
                "source_frequency": source_frequency,
                "target_frequency": target_frequency,
                "progress_percent": progress_percent,
                "status": "aggregating"
            }
        )
        
        await self.broadcast(message)
        
        logger.debug(f"Aggregation progress: {symbol} {source_frequency}→{target_frequency} {progress_percent}%")
    
    async def broadcast_aggregation_complete(
        self,
        aggregation_id: str,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        source_bars: int,
        target_bars: int,
        execution_time_ms: float
    ) -> None:
        """Broadcast completion of data aggregation."""
        
        message = WebSocketMessage(
            type="aggregation_complete",
            timestamp=datetime.now(),
            data={
                "aggregation_id": aggregation_id,
                "symbol": symbol,
                "source_frequency": source_frequency,
                "target_frequency": target_frequency,
                "source_bars": source_bars,
                "target_bars": target_bars,
                "compression_ratio": round(target_bars / source_bars if source_bars > 0 else 0, 2),
                "execution_time_ms": execution_time_ms,
                "status": "complete"
            }
        )
        
        await self.broadcast(message)
        
        logger.info(f"Aggregation completed: {symbol} {source_bars}→{target_bars} bars in {execution_time_ms}ms")
    
    async def broadcast_cache_performance_update(
        self,
        cache_hit_rate: float,
        total_requests: int,
        redis_available: bool
    ) -> None:
        """Broadcast cache performance metrics for monitoring."""
        
        message = WebSocketMessage(
            type="cache_performance",
            timestamp=datetime.now(),
            data={
                "cache_hit_rate": cache_hit_rate,
                "total_requests": total_requests,
                "redis_available": redis_available,
                "status": "healthy" if cache_hit_rate > 50 else "degraded"
            }
        )
        
        await self.broadcast(message)
        
        logger.debug(f"Cache performance update: {cache_hit_rate}% hit rate")

    
    async def broadcast_database_performance(self, performance_data: Dict[str, Any]) -> None:
        """
        Broadcast real-time database performance metrics to all connected clients.
        
        Args:
            performance_data: Database performance metrics including connection pool,
                            INSERT rates, query performance, and partition health.
        """
        message = {
            "type": "database_performance",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "connection_pool": performance_data.get("connection_pool", {}),
                "performance_metrics": performance_data.get("performance_metrics", {}),
                "partition_health": performance_data.get("partition_health", {}),
                "alerts": performance_data.get("alerts", []),
                "overall_status": performance_data.get("status", "unknown")
            }
        }
        
        await self.broadcast(message)
        logger.debug("Broadcasted database performance update", 
                    active_connections=self.connection_count,
                    status=performance_data.get("status"))
    
    async def broadcast_performance_alert(self, alert_type: str, message: str, 
                                        severity: str = "warning") -> None:
        """
        Broadcast performance-related alerts to connected clients.
        
        Args:
            alert_type: Type of performance alert (connection_pool, slow_query, etc.)
            message: Alert message description
            severity: Alert severity level (info, warning, critical)
        """
        alert_message = {
            "type": "performance_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "source": "database_performance"
            }
        }
        
        await self.broadcast(alert_message)
        logger.info(f"Broadcasted performance alert: {alert_type}", 
                   message=message, severity=severity)
    
    async def broadcast_partition_status_update(self, partition_data: Dict[str, Any]) -> None:
        """
        Broadcast partition status updates to connected clients.
        
        Args:
            partition_data: Partition status information including health,
                          storage utilization, and maintenance status.
        """
        message = {
            "type": "partition_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "service_status": partition_data.get("service_status", "unknown"),
                "partitions": partition_data.get("partitions", {}),
                "health_summary": partition_data.get("health_summary", {}),
                "config": partition_data.get("config", {}),
                "recent_activity": partition_data.get("recent_activity", [])
            }
        }
        
        await self.broadcast(message)
        logger.debug("Broadcasted partition status update", 
                    total_partitions=partition_data.get("health_summary", {}).get("total_partitions", 0))
    
    async def broadcast_performance_benchmark_results(self, benchmark_data: Dict[str, Any]) -> None:
        """
        Broadcast performance benchmark test results to connected clients.
        
        Args:
            benchmark_data: Performance benchmark results including INSERT rates,
                          calculation speedup, and capacity validation.
        """
        message = {
            "type": "performance_benchmark",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "insert_performance": benchmark_data.get("insert_performance", {}),
                "calculation_performance": benchmark_data.get("calculation_performance", {}),
                "capacity_test": benchmark_data.get("capacity_test", {}),
                "baseline_comparison": benchmark_data.get("baseline_comparison", {}),
                "test_status": benchmark_data.get("test_status", "unknown")
            }
        }
        
        await self.broadcast(message)
        logger.info("Broadcasted performance benchmark results", 
                   test_status=benchmark_data.get("test_status"))
    
    async def send_historical_data_stream(
        self,
        client_id: str,
        query_id: str,
        symbol: str,
        bars_data: List[Dict[str, Any]],
        chunk_size: int = 100
    ) -> None:
        """Stream historical data in chunks to a specific WebSocket connection."""
        
        try:
            total_bars = len(bars_data)
            chunks_sent = 0
            
            # Send data in chunks to prevent overwhelming the connection
            for i in range(0, total_bars, chunk_size):
                chunk = bars_data[i:i + chunk_size]
                chunk_number = chunks_sent + 1
                total_chunks = (total_bars + chunk_size - 1) // chunk_size
                
                # Use legacy WebSocketMessage for historical data chunks
                message = WebSocketMessage(
                    type="historical_data_chunk",
                    timestamp=datetime.now(),
                    data={
                        "query_id": query_id,
                        "symbol": symbol,
                        "chunk_number": chunk_number,
                        "total_chunks": total_chunks,
                        "bars": chunk,
                        "is_final_chunk": chunk_number == total_chunks
                    }
                )
                
                # Convert to dict for legacy send method
                message_dict = {
                    "type": message.type,
                    "timestamp": message.timestamp.isoformat(),
                    "data": message.data
                }
                
                if client_id in self.active_connections:
                    websocket = self.active_connections[client_id]
                    await websocket.send_text(json.dumps(message_dict, default=str))
                
                chunks_sent += 1
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            logger.info(f"Streamed {total_bars} bars in {chunks_sent} chunks for {symbol}")
            
        except Exception as e:
            logger.error(f"Error streaming historical data for {symbol}: {e}")
            await self.broadcast_historical_data_error(
                query_id, symbol, f"Streaming error: {str(e)}", "streaming_error"
            )


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    Enhanced WebSocket endpoint for real-time data and alert streaming.
    
    Provides real-time streaming of market data, alerts, and system status
    with <50ms delivery target for connected clients using typed message system.
    
    Args:
        websocket: WebSocket connection.
    """
    # Attempt to accept connection with client ID
    connection_accepted, client_id = await manager.connect(websocket)
    
    if not connection_accepted:
        await websocket.close(code=1000, reason="Server at capacity")
        return
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping, subscription requests, etc.)
                data = await websocket.receive_text()
                
                # Parse client message
                try:
                    client_message = json.loads(data)
                    await manager.handle_client_message(websocket, client_id, client_message)
                except json.JSONDecodeError:
                    error_msg = await manager.message_handler.create_error_message(
                        "INVALID_JSON",
                        "Invalid JSON format",
                        None,
                        "error"
                    )
                    await manager.send_personal_message(websocket, error_msg)
                
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                error_msg = await manager.message_handler.create_error_message(
                    "INTERNAL_ERROR",
                    "Internal server error",
                    None,
                    "critical"
                )
                await manager.send_personal_message(websocket, error_msg)
                break
    
    finally:
        manager.disconnect(client_id)


# Legacy handle_client_message function removed - now handled by ConnectionManager.handle_client_message


# Export manager for use by other services
def get_websocket_manager() -> ConnectionManager:
    """
    Get the enhanced global WebSocket connection manager.
    
    Returns:
        ConnectionManager: Enhanced global connection manager instance with typed message support.
    """
    return manager


# Performance monitoring endpoint for connection manager
def get_websocket_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive WebSocket performance metrics.
    
    Returns:
        Dictionary containing connection and message processing metrics.
    """
    return manager.get_performance_metrics()