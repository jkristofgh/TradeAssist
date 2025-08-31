"""
Advanced data aggregation service for TradeAssist historical data.

Provides efficient OHLCV aggregation, gap detection, and real-time calculations
for higher timeframes from base stored data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import structlog
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from src.backend.database.connection import get_db_session
from src.backend.models.historical_data import MarketDataBar
from src.backend.services.cache_service import CacheService

logger = structlog.get_logger()


class AggregationMethod(Enum):
    """Aggregation methods for different data types."""
    OHLCV = "ohlcv"  # Standard OHLC with Volume
    VWAP = "vwap"    # Volume Weighted Average Price
    CUSTOM = "custom"  # Custom aggregation function


@dataclass
class AggregationResult:
    """Result of data aggregation operation."""
    
    symbol: str
    source_frequency: str
    target_frequency: str
    aggregation_method: AggregationMethod
    bars: List[Dict[str, Any]]
    stats: Dict[str, Any]
    execution_time_ms: float
    cache_hit: bool = False


@dataclass
class GapInfo:
    """Information about data gaps in time series."""
    
    symbol: str
    frequency: str
    gap_start: datetime
    gap_end: datetime
    expected_bars: int
    actual_bars: int
    gap_duration_minutes: int
    

class DataAggregationService:
    """
    Advanced data aggregation service for historical market data.
    
    Features:
    - Efficient OHLCV aggregation from base timeframes
    - Volume-weighted average price (VWAP) calculations
    - Gap detection and filling capabilities  
    - Real-time aggregation with caching
    - Support for custom aggregation periods
    - Performance optimization for large datasets
    """
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.is_running = False
        
        # Frequency hierarchy for aggregation validation
        self.frequency_hierarchy = {
            '1m': 1, '5m': 5, '10m': 10, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480,
            '12h': 720, '1d': 1440, '2d': 2880, '1w': 10080, '1M': 43200
        }
        
        # Performance metrics
        self._aggregations_performed = 0
        self._cache_hits = 0
        self._total_bars_processed = 0
        
    async def start(self) -> None:
        """Start the data aggregation service."""
        if self.is_running:
            logger.warning("Data aggregation service already running")
            return
        
        logger.info("Starting data aggregation service")
        self.is_running = True
        
        # Validate frequency hierarchy
        await self._validate_frequency_hierarchy()
        
        logger.info("Data aggregation service started successfully")
        
    async def stop(self) -> None:
        """Stop the data aggregation service."""
        if not self.is_running:
            return
        
        logger.info("Stopping data aggregation service")
        self.is_running = False
        
        logger.info("Data aggregation service stopped")
    
    async def aggregate_data(
        self,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        start_date: datetime,
        end_date: datetime,
        method: AggregationMethod = AggregationMethod.OHLCV,
        use_cache: bool = True
    ) -> AggregationResult:
        """
        Aggregate historical data from source to target frequency.
        
        Args:
            symbol: Trading symbol
            source_frequency: Source data frequency (e.g., '1m')
            target_frequency: Target aggregation frequency (e.g., '1h')
            start_date: Start date for aggregation
            end_date: End date for aggregation
            method: Aggregation method to use
            use_cache: Whether to use cached results
            
        Returns:
            AggregationResult with aggregated bars and metadata
            
        Raises:
            ValueError: If aggregation parameters are invalid
            RuntimeError: If aggregation fails
        """
        start_time = datetime.now()
        
        # Validate parameters
        await self._validate_aggregation_params(
            symbol, source_frequency, target_frequency, start_date, end_date
        )
        
        # Check cache first
        cache_key = self._build_aggregation_cache_key(
            symbol, source_frequency, target_frequency, start_date, end_date, method
        )
        
        cached_result = None
        if use_cache:
            cached_result = await self.cache_service.get_query_results(cache_key)
            if cached_result:
                self._cache_hits += 1
                cached_result["cache_hit"] = True
                cached_result["execution_time_ms"] = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                
                logger.debug(f"Returning cached aggregation result for {symbol}")
                return AggregationResult(**cached_result)
        
        try:
            # Fetch source data
            source_bars = await self._fetch_source_bars(
                symbol, source_frequency, start_date, end_date
            )
            
            if not source_bars:
                logger.warning(f"No source bars found for {symbol} {source_frequency}")
                return AggregationResult(
                    symbol=symbol,
                    source_frequency=source_frequency,
                    target_frequency=target_frequency,
                    aggregation_method=method,
                    bars=[],
                    stats={
                        "source_bars": 0,
                        "target_bars": 0,
                        "gaps_detected": 0
                    },
                    execution_time_ms=0
                )
            
            # Perform aggregation
            aggregated_bars = await self._perform_aggregation(
                source_bars, target_frequency, method
            )
            
            # Detect gaps
            gaps = await self._detect_gaps(
                symbol, source_frequency, source_bars, start_date, end_date
            )
            
            # Calculate statistics
            stats = {
                "source_bars": len(source_bars),
                "target_bars": len(aggregated_bars),
                "gaps_detected": len(gaps),
                "compression_ratio": (
                    len(aggregated_bars) / len(source_bars) 
                    if source_bars else 0
                ),
                "data_completeness": (
                    (len(source_bars) / self._calculate_expected_bars(
                        start_date, end_date, source_frequency
                    )) * 100 if source_bars else 0
                )
            }
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = AggregationResult(
                symbol=symbol,
                source_frequency=source_frequency,
                target_frequency=target_frequency,
                aggregation_method=method,
                bars=aggregated_bars,
                stats=stats,
                execution_time_ms=execution_time_ms
            )
            
            # Cache the result
            if use_cache and aggregated_bars:
                await self.cache_service.set_query_results(
                    cache_key,
                    result.__dict__
                )
            
            self._aggregations_performed += 1
            self._total_bars_processed += len(source_bars)
            
            logger.info(
                f"Aggregated {len(source_bars)} {source_frequency} bars to "
                f"{len(aggregated_bars)} {target_frequency} bars for {symbol} "
                f"in {execution_time_ms:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Aggregation failed for {symbol}: {e}")
            raise RuntimeError(f"Aggregation failed: {e}") from e
    
    async def calculate_vwap(
        self,
        symbol: str,
        frequency: str,
        start_date: datetime,
        end_date: datetime,
        period_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Calculate Volume Weighted Average Price (VWAP) for given period.
        
        Args:
            symbol: Trading symbol
            frequency: Data frequency
            start_date: Start date
            end_date: End date
            period_minutes: VWAP calculation period in minutes
            
        Returns:
            List of VWAP data points
        """
        try:
            # Fetch base data
            bars = await self._fetch_source_bars(symbol, frequency, start_date, end_date)
            
            if not bars:
                return []
            
            vwap_bars = []
            current_period_bars = []
            period_start = bars[0]["timestamp"]
            
            for bar in bars:
                bar_time = bar["timestamp"]
                
                # Check if we need to start a new VWAP period
                if (bar_time - period_start).total_seconds() >= period_minutes * 60:
                    if current_period_bars:
                        vwap_value = self._calculate_period_vwap(current_period_bars)
                        vwap_bars.append({
                            "timestamp": period_start,
                            "symbol": symbol,
                            "vwap": vwap_value,
                            "volume": sum(b.get("volume", 0) for b in current_period_bars),
                            "bars_count": len(current_period_bars)
                        })
                    
                    current_period_bars = [bar]
                    period_start = bar_time
                else:
                    current_period_bars.append(bar)
            
            # Handle final period
            if current_period_bars:
                vwap_value = self._calculate_period_vwap(current_period_bars)
                vwap_bars.append({
                    "timestamp": period_start,
                    "symbol": symbol,
                    "vwap": vwap_value,
                    "volume": sum(b.get("volume", 0) for b in current_period_bars),
                    "bars_count": len(current_period_bars)
                })
            
            logger.info(f"Calculated {len(vwap_bars)} VWAP periods for {symbol}")
            return vwap_bars
            
        except Exception as e:
            logger.error(f"VWAP calculation failed for {symbol}: {e}")
            raise
    
    async def detect_gaps(
        self,
        symbol: str,
        frequency: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[GapInfo]:
        """
        Detect gaps in historical data time series.
        
        Args:
            symbol: Trading symbol
            frequency: Data frequency
            start_date: Start date for gap detection
            end_date: End date for gap detection
            
        Returns:
            List of detected gaps
        """
        try:
            bars = await self._fetch_source_bars(symbol, frequency, start_date, end_date)
            return await self._detect_gaps(symbol, frequency, bars, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Gap detection failed for {symbol}: {e}")
            raise
    
    async def fill_gaps(
        self,
        symbol: str,
        frequency: str,
        gaps: List[GapInfo],
        method: str = "forward_fill"
    ) -> int:
        """
        Fill detected gaps in historical data.
        
        Args:
            symbol: Trading symbol
            frequency: Data frequency
            gaps: List of gaps to fill
            method: Gap filling method ('forward_fill', 'interpolate', 'zero')
            
        Returns:
            Number of bars added to fill gaps
        """
        filled_count = 0
        
        try:
            async with get_db_session() as session:
                for gap in gaps:
                    if method == "forward_fill":
                        filled_count += await self._forward_fill_gap(
                            session, symbol, frequency, gap
                        )
                    elif method == "interpolate":
                        filled_count += await self._interpolate_gap(
                            session, symbol, frequency, gap
                        )
                    elif method == "zero":
                        filled_count += await self._zero_fill_gap(
                            session, symbol, frequency, gap
                        )
                
                await session.commit()
            
            logger.info(f"Filled {filled_count} bars for {len(gaps)} gaps in {symbol}")
            return filled_count
            
        except Exception as e:
            logger.error(f"Gap filling failed for {symbol}: {e}")
            raise
    
    async def get_aggregation_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the aggregation service."""
        return {
            "aggregations_performed": self._aggregations_performed,
            "cache_hits": self._cache_hits,
            "total_bars_processed": self._total_bars_processed,
            "cache_hit_rate": (
                (self._cache_hits / self._aggregations_performed * 100)
                if self._aggregations_performed > 0 else 0
            ),
            "is_running": self.is_running
        }
    
    # Private helper methods
    
    async def _validate_aggregation_params(
        self,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """Validate aggregation parameters."""
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        if source_frequency not in self.frequency_hierarchy:
            raise ValueError(f"Unsupported source frequency: {source_frequency}")
        
        if target_frequency not in self.frequency_hierarchy:
            raise ValueError(f"Unsupported target frequency: {target_frequency}")
        
        source_minutes = self.frequency_hierarchy[source_frequency]
        target_minutes = self.frequency_hierarchy[target_frequency]
        
        if target_minutes <= source_minutes:
            raise ValueError(
                f"Target frequency ({target_frequency}) must be higher than "
                f"source frequency ({source_frequency})"
            )
        
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
    
    async def _validate_frequency_hierarchy(self) -> None:
        """Validate frequency hierarchy configuration."""
        # Ensure frequencies are properly ordered
        frequencies = list(self.frequency_hierarchy.keys())
        minutes = list(self.frequency_hierarchy.values())
        
        if minutes != sorted(minutes):
            logger.error("Frequency hierarchy is not properly ordered")
            raise RuntimeError("Invalid frequency hierarchy configuration")
        
        logger.debug(f"Validated frequency hierarchy: {frequencies}")
    
    def _build_aggregation_cache_key(
        self,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        start_date: datetime,
        end_date: datetime,
        method: AggregationMethod
    ) -> str:
        """Build cache key for aggregation result."""
        return (
            f"aggregation:{symbol}:{source_frequency}:{target_frequency}:"
            f"{start_date.isoformat()}:{end_date.isoformat()}:{method.value}"
        )
    
    async def _fetch_source_bars(
        self,
        symbol: str,
        frequency: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch source bars from database."""
        try:
            async with get_db_session() as session:
                query = select(MarketDataBar).where(
                    and_(
                        MarketDataBar.symbol == symbol,
                        MarketDataBar.frequency == frequency,
                        MarketDataBar.timestamp >= start_date,
                        MarketDataBar.timestamp <= end_date
                    )
                ).order_by(MarketDataBar.timestamp)
                
                result = await session.execute(query)
                bars = result.scalars().all()
                
                return [
                    {
                        "timestamp": bar.timestamp,
                        "open_price": bar.open_price,
                        "high_price": bar.high_price,
                        "low_price": bar.low_price,
                        "close_price": bar.close_price,
                        "volume": bar.volume or 0,
                        "symbol": bar.symbol
                    }
                    for bar in bars
                ]
                
        except Exception as e:
            logger.error(f"Failed to fetch source bars for {symbol}: {e}")
            raise
    
    async def _perform_aggregation(
        self,
        source_bars: List[Dict[str, Any]],
        target_frequency: str,
        method: AggregationMethod
    ) -> List[Dict[str, Any]]:
        """Perform the actual aggregation of source bars."""
        if not source_bars:
            return []
        
        target_minutes = self.frequency_hierarchy[target_frequency]
        aggregated_bars = []
        current_group = []
        current_period_start = None
        
        for bar in source_bars:
            bar_time = bar["timestamp"]
            
            # Calculate period start for this bar
            if target_frequency == "1d":
                period_start = bar_time.replace(hour=0, minute=0, second=0, microsecond=0)
            elif target_frequency == "1w":
                days_since_monday = bar_time.weekday()
                period_start = (bar_time - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                # For intraday frequencies, align to period boundaries
                minutes_since_midnight = bar_time.hour * 60 + bar_time.minute
                period_offset = (minutes_since_midnight // target_minutes) * target_minutes
                period_start = bar_time.replace(
                    hour=period_offset // 60,
                    minute=period_offset % 60,
                    second=0,
                    microsecond=0
                )
            
            # Start new group if period changed
            if current_period_start != period_start:
                if current_group:
                    aggregated_bar = await self._aggregate_bar_group(
                        current_group, method
                    )
                    aggregated_bar["timestamp"] = current_period_start
                    aggregated_bars.append(aggregated_bar)
                
                current_group = [bar]
                current_period_start = period_start
            else:
                current_group.append(bar)
        
        # Handle final group
        if current_group:
            aggregated_bar = await self._aggregate_bar_group(current_group, method)
            aggregated_bar["timestamp"] = current_period_start
            aggregated_bars.append(aggregated_bar)
        
        return aggregated_bars
    
    async def _aggregate_bar_group(
        self,
        bars: List[Dict[str, Any]],
        method: AggregationMethod
    ) -> Dict[str, Any]:
        """Aggregate a group of bars using the specified method."""
        if not bars:
            return {}
        
        if method == AggregationMethod.OHLCV:
            return {
                "symbol": bars[0]["symbol"],
                "open_price": bars[0]["open_price"],
                "high_price": max(bar["high_price"] for bar in bars),
                "low_price": min(bar["low_price"] for bar in bars),
                "close_price": bars[-1]["close_price"],
                "volume": sum(bar["volume"] for bar in bars)
            }
        
        elif method == AggregationMethod.VWAP:
            total_volume = sum(bar["volume"] for bar in bars if bar["volume"])
            if total_volume == 0:
                avg_price = sum(
                    (bar["high_price"] + bar["low_price"] + bar["close_price"]) / 3
                    for bar in bars
                ) / len(bars)
            else:
                weighted_sum = sum(
                    ((bar["high_price"] + bar["low_price"] + bar["close_price"]) / 3) * bar["volume"]
                    for bar in bars if bar["volume"]
                )
                avg_price = weighted_sum / total_volume
            
            return {
                "symbol": bars[0]["symbol"],
                "vwap": avg_price,
                "volume": total_volume,
                "bars_count": len(bars)
            }
        
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")
    
    def _calculate_period_vwap(self, bars: List[Dict[str, Any]]) -> float:
        """Calculate VWAP for a period of bars."""
        total_volume = sum(bar.get("volume", 0) for bar in bars)
        
        if total_volume == 0:
            # Use simple average if no volume data
            return sum(
                (bar["high_price"] + bar["low_price"] + bar["close_price"]) / 3
                for bar in bars
            ) / len(bars)
        
        # Volume-weighted average
        weighted_sum = sum(
            ((bar["high_price"] + bar["low_price"] + bar["close_price"]) / 3) * bar.get("volume", 0)
            for bar in bars
        )
        
        return weighted_sum / total_volume
    
    async def _detect_gaps(
        self,
        symbol: str,
        frequency: str,
        bars: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> List[GapInfo]:
        """Detect gaps in the time series data."""
        if not bars:
            return []
        
        gaps = []
        frequency_minutes = self.frequency_hierarchy[frequency]
        expected_interval = timedelta(minutes=frequency_minutes)
        
        for i in range(len(bars) - 1):
            current_time = bars[i]["timestamp"]
            next_time = bars[i + 1]["timestamp"]
            
            expected_next_time = current_time + expected_interval
            
            # Check for gap (allowing some tolerance for market hours)
            if next_time > expected_next_time + timedelta(minutes=5):
                gap_duration = (next_time - expected_next_time).total_seconds() / 60
                expected_bars = int(gap_duration / frequency_minutes)
                
                if expected_bars > 0:
                    gaps.append(GapInfo(
                        symbol=symbol,
                        frequency=frequency,
                        gap_start=expected_next_time,
                        gap_end=next_time,
                        expected_bars=expected_bars,
                        actual_bars=0,
                        gap_duration_minutes=int(gap_duration)
                    ))
        
        return gaps
    
    def _calculate_expected_bars(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: str
    ) -> int:
        """Calculate expected number of bars for a date range and frequency."""
        total_minutes = (end_date - start_date).total_seconds() / 60
        frequency_minutes = self.frequency_hierarchy[frequency]
        
        # Rough estimate - doesn't account for market hours/holidays
        return int(total_minutes / frequency_minutes)
    
    async def _forward_fill_gap(
        self,
        session,
        symbol: str,
        frequency: str,
        gap: GapInfo
    ) -> int:
        """Fill gap using forward fill method."""
        # Implementation placeholder - would create bars with previous close values
        return 0
    
    async def _interpolate_gap(
        self,
        session,
        symbol: str,
        frequency: str,
        gap: GapInfo
    ) -> int:
        """Fill gap using interpolation method."""
        # Implementation placeholder - would interpolate between adjacent bars
        return 0
    
    async def _zero_fill_gap(
        self,
        session,
        symbol: str,
        frequency: str,
        gap: GapInfo
    ) -> int:
        """Fill gap with zero-volume bars."""
        # Implementation placeholder - would create bars with zero volume
        return 0