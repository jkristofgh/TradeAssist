"""
Strategy context for technical indicator calculations.

This module implements the strategy pattern context that manages and executes
technical indicator calculations using registered strategy implementations.
"""

import structlog
from typing import Dict, Any, Optional, List
import pandas as pd
import time
from datetime import datetime

from .strategies.base import IndicatorStrategy
from ..analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class IndicatorCalculator:
    """
    Strategy context for technical indicator calculations.
    
    Requirements:
    - Strategy registration and management
    - Performance monitoring and caching
    - Error handling and fallback strategies
    - Integration with existing AnalyticsEngine
    - Support for custom strategy registration
    """
    
    def __init__(self):
        self.strategies: Dict[TechnicalIndicator, IndicatorStrategy] = {}
        self._performance_stats: Dict[str, List[float]] = {}
        self._calculation_cache: Dict[str, IndicatorResult] = {}
        self._cache_ttl_seconds = 300  # 5 minutes
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Initialize performance stats for all indicator types
        for indicator in TechnicalIndicator:
            self._performance_stats[indicator.value] = []
    
    async def calculate_indicator(self, indicator_type: TechnicalIndicator,
                                 market_data: pd.DataFrame,
                                 instrument_id: int,
                                 **params) -> Optional[IndicatorResult]:
        """
        Calculate indicator using appropriate strategy.
        
        Args:
            indicator_type: Type of technical indicator to calculate
            market_data: Historical market data with OHLCV columns
            instrument_id: ID of the instrument being analyzed
            **params: Strategy-specific parameters
            
        Returns:
            IndicatorResult or None if calculation fails
        """
        # Check cache first
        cache_key = self._build_cache_key(indicator_type, instrument_id, market_data, params)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for {indicator_type.value}", instrument_id=instrument_id)
            return cached_result
        
        # Get strategy for indicator type
        strategy = self.strategies.get(indicator_type)
        if not strategy:
            logger.error(
                f"No strategy registered for {indicator_type.value}",
                indicator_type=indicator_type.value,
                available_strategies=list(self.strategies.keys())
            )
            return None
        
        # Merge with default parameters
        default_params = strategy.get_default_parameters()
        merged_params = {**default_params, **params}
        
        # Validate parameters
        if not strategy.validate_parameters(merged_params):
            logger.error(
                f"Invalid parameters for {indicator_type.value}",
                indicator_type=indicator_type.value,
                parameters=merged_params
            )
            return None
        
        try:
            # Measure calculation time
            start_time = time.time()
            
            # Calculate indicator using strategy
            result = await strategy.calculate(market_data, instrument_id, **merged_params)
            
            # Record performance metrics
            calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            self._record_performance(indicator_type.value, calculation_time)
            
            # Add calculation time to result metadata
            if result and result.metadata:
                result.metadata['calculation_time_ms'] = calculation_time
            
            # Cache successful result
            if result:
                self._cache_result(cache_key, result)
                logger.debug(
                    f"Calculated {indicator_type.value} successfully",
                    instrument_id=instrument_id,
                    calculation_time_ms=calculation_time
                )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error calculating {indicator_type.value}",
                indicator_type=indicator_type.value,
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    def register_strategy(self, indicator_type: TechnicalIndicator,
                         strategy: IndicatorStrategy) -> None:
        """
        Register strategy for indicator type.
        
        Args:
            indicator_type: Technical indicator type
            strategy: Strategy implementation for the indicator
        """
        self.strategies[indicator_type] = strategy
        logger.info(
            f"Registered strategy for {indicator_type.value}",
            indicator_type=indicator_type.value,
            strategy_class=strategy.__class__.__name__
        )
    
    def get_supported_indicators(self) -> List[TechnicalIndicator]:
        """
        Return list of supported indicators.
        
        Returns:
            List of TechnicalIndicator types that have registered strategies
        """
        return list(self.strategies.keys())
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Return calculation performance statistics.
        
        Returns:
            Dictionary containing performance metrics for each indicator type
        """
        stats = {}
        for indicator_name, times in self._performance_stats.items():
            if times:
                stats[indicator_name] = {
                    'count': len(times),
                    'avg_time_ms': sum(times) / len(times),
                    'min_time_ms': min(times),
                    'max_time_ms': max(times),
                    'last_calculation_ms': times[-1] if times else None
                }
            else:
                stats[indicator_name] = {
                    'count': 0,
                    'avg_time_ms': 0,
                    'min_time_ms': 0,
                    'max_time_ms': 0,
                    'last_calculation_ms': None
                }
        
        # Add cache statistics
        stats['cache'] = {
            'entries': len(self._calculation_cache),
            'hit_ratio': self._calculate_cache_hit_ratio()
        }
        
        return stats
    
    def clear_cache(self) -> int:
        """
        Clear all cached calculations.
        
        Returns:
            Number of cache entries cleared
        """
        count = len(self._calculation_cache)
        self._calculation_cache.clear()
        self._cache_timestamps.clear()
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def _build_cache_key(self, indicator_type: TechnicalIndicator, 
                        instrument_id: int, 
                        market_data: pd.DataFrame,
                        params: Dict[str, Any]) -> str:
        """
        Build cache key for calculation result.
        
        Args:
            indicator_type: Technical indicator type
            instrument_id: Instrument ID
            market_data: Market data (used for data hash)
            params: Calculation parameters
            
        Returns:
            String cache key
        """
        # Create a hash of the last few data points to detect data changes
        if len(market_data) >= 5:
            data_hash = hash(tuple(market_data['close'].tail(5).values))
        else:
            data_hash = hash(tuple(market_data['close'].values))
        
        # Sort params for consistent key generation
        params_str = str(sorted(params.items()))
        
        return f"{indicator_type.value}_{instrument_id}_{data_hash}_{hash(params_str)}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[IndicatorResult]:
        """
        Get cached result if still valid.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached IndicatorResult or None if expired/missing
        """
        if cache_key not in self._calculation_cache:
            return None
        
        # Check if cache entry has expired
        timestamp = self._cache_timestamps.get(cache_key)
        if timestamp:
            age_seconds = (datetime.utcnow() - timestamp).total_seconds()
            if age_seconds > self._cache_ttl_seconds:
                # Remove expired entry
                del self._calculation_cache[cache_key]
                del self._cache_timestamps[cache_key]
                return None
        
        return self._calculation_cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: IndicatorResult) -> None:
        """
        Cache calculation result.
        
        Args:
            cache_key: Cache key
            result: Calculation result to cache
        """
        self._calculation_cache[cache_key] = result
        self._cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size to prevent memory bloat
        max_cache_entries = 1000
        if len(self._calculation_cache) > max_cache_entries:
            # Remove oldest entries
            sorted_entries = sorted(
                self._cache_timestamps.items(),
                key=lambda x: x[1]
            )
            entries_to_remove = len(sorted_entries) - max_cache_entries + 100  # Remove extra for buffer
            
            for cache_key_to_remove, _ in sorted_entries[:entries_to_remove]:
                if cache_key_to_remove in self._calculation_cache:
                    del self._calculation_cache[cache_key_to_remove]
                if cache_key_to_remove in self._cache_timestamps:
                    del self._cache_timestamps[cache_key_to_remove]
    
    def _record_performance(self, indicator_name: str, calculation_time_ms: float) -> None:
        """
        Record performance metrics for an indicator calculation.
        
        Args:
            indicator_name: Name of the indicator
            calculation_time_ms: Calculation time in milliseconds
        """
        if indicator_name not in self._performance_stats:
            self._performance_stats[indicator_name] = []
        
        # Keep only last 100 measurements to prevent memory growth
        times = self._performance_stats[indicator_name]
        times.append(calculation_time_ms)
        if len(times) > 100:
            times.pop(0)
    
    def _calculate_cache_hit_ratio(self) -> float:
        """
        Calculate cache hit ratio based on performance stats.
        
        Returns:
            Cache hit ratio as a percentage (0-100)
        """
        # This is a simplified implementation
        # In a real implementation, you'd track cache hits vs misses
        total_calculations = sum(
            len(times) for times in self._performance_stats.values()
        )
        cache_entries = len(self._calculation_cache)
        
        if total_calculations == 0:
            return 0.0
        
        # Rough estimation - could be improved with actual hit/miss tracking
        estimated_hit_ratio = min(100.0, (cache_entries / max(total_calculations, 1)) * 100)
        return round(estimated_hit_ratio, 2)