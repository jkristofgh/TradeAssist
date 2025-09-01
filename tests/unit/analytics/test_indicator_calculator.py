"""
Unit tests for IndicatorCalculator strategy context.

Tests the strategy context that manages indicator calculations,
strategy registration, performance monitoring, and caching.
"""

import pytest
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.services.analytics.indicator_calculator import IndicatorCalculator
from src.backend.services.analytics.strategies.base import IndicatorStrategy
from src.backend.services.analytics_engine import IndicatorResult, TechnicalIndicator


class MockStrategy(IndicatorStrategy):
    """Mock strategy for testing."""
    
    def __init__(self, calculation_time_ms=10):
        self.calculation_time_ms = calculation_time_ms
    
    async def calculate(self, market_data: pd.DataFrame, instrument_id: int, **params):
        # Simulate calculation time
        await asyncio.sleep(self.calculation_time_ms / 1000)
        
        return IndicatorResult(
            indicator_type=TechnicalIndicator.RSI,
            timestamp=datetime.utcnow(),
            instrument_id=instrument_id,
            values={'rsi': 65.5, 'overbought': 70.0, 'oversold': 30.0},
            metadata={'period': params.get('period', 14)}
        )
    
    def get_default_parameters(self):
        return {'period': 14}
    
    def validate_parameters(self, params):
        period = params.get('period', 14)
        return isinstance(period, int) and 1 <= period <= 100


class FailingStrategy(IndicatorStrategy):
    """Strategy that always fails for testing error handling."""
    
    async def calculate(self, market_data: pd.DataFrame, instrument_id: int, **params):
        raise ValueError("Mock calculation failure")
    
    def get_default_parameters(self):
        return {'period': 14}
    
    def validate_parameters(self, params):
        return True


class TestIndicatorCalculator:
    """Test the IndicatorCalculator strategy context."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance for testing."""
        return IndicatorCalculator()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        return pd.DataFrame({
            'open': [100, 102, 101, 103, 105],
            'high': [105, 107, 106, 108, 110],
            'low': [95, 97, 96, 98, 100],
            'close': [103, 105, 104, 106, 108],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
    
    def test_calculator_initialization(self, calculator):
        """Test calculator initializes with correct state."""
        assert isinstance(calculator.strategies, dict)
        assert isinstance(calculator._performance_stats, dict)
        assert isinstance(calculator._calculation_cache, dict)
        assert calculator._cache_ttl_seconds == 300
        
        # Should have performance stats for all indicator types
        for indicator in TechnicalIndicator:
            assert indicator.value in calculator._performance_stats

    def test_register_strategy(self, calculator):
        """Test strategy registration."""
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        assert TechnicalIndicator.RSI in calculator.strategies
        assert calculator.strategies[TechnicalIndicator.RSI] == mock_strategy

    def test_get_supported_indicators(self, calculator):
        """Test getting supported indicators list."""
        # Initially empty
        assert calculator.get_supported_indicators() == []
        
        # After registering strategies
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        calculator.register_strategy(TechnicalIndicator.MACD, mock_strategy)
        
        supported = calculator.get_supported_indicators()
        assert TechnicalIndicator.RSI in supported
        assert TechnicalIndicator.MACD in supported
        assert len(supported) == 2

    @pytest.mark.asyncio
    async def test_calculate_indicator_success(self, calculator, sample_market_data):
        """Test successful indicator calculation."""
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=14
        )
        
        assert result is not None
        assert result.indicator_type == TechnicalIndicator.RSI
        assert result.instrument_id == 1
        assert result.values['rsi'] == 65.5
        assert result.metadata['period'] == 14
        assert 'calculation_time_ms' in result.metadata

    @pytest.mark.asyncio
    async def test_calculate_indicator_no_strategy(self, calculator, sample_market_data):
        """Test calculation when no strategy is registered."""
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_indicator_invalid_parameters(self, calculator, sample_market_data):
        """Test calculation with invalid parameters."""
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        # Invalid period (outside valid range)
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=200  # Invalid
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_indicator_strategy_failure(self, calculator, sample_market_data):
        """Test calculation when strategy throws exception."""
        failing_strategy = FailingStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, failing_strategy)
        
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_parameter_merging(self, calculator, sample_market_data):
        """Test that default parameters are merged with provided parameters."""
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        # Don't provide period, should use default
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1
        )
        
        assert result.metadata['period'] == 14  # Default value
        
        # Provide period, should override default
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=20
        )
        
        assert result.metadata['period'] == 20  # Provided value

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, calculator, sample_market_data):
        """Test performance statistics collection."""
        mock_strategy = MockStrategy(calculation_time_ms=50)  # Simulate 50ms calculation
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        # Perform calculation
        await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1
        )
        
        stats = calculator.get_performance_stats()
        rsi_stats = stats['rsi']  # Uses enum value, not name
        
        assert rsi_stats['count'] == 1
        assert rsi_stats['avg_time_ms'] >= 40  # Should be around 50ms
        assert rsi_stats['min_time_ms'] >= 40
        assert rsi_stats['max_time_ms'] >= 40
        assert rsi_stats['last_calculation_ms'] is not None

    @pytest.mark.asyncio
    async def test_caching_functionality(self, calculator, sample_market_data):
        """Test calculation result caching."""
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        # First calculation - should call strategy
        result1 = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=14
        )
        
        # Second calculation with same parameters - should use cache
        result2 = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=14
        )
        
        # Results should be identical (same cached object)
        assert result1 is result2
        assert len(calculator._calculation_cache) == 1

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, calculator, sample_market_data):
        """Test cache key generation for different scenarios."""
        mock_strategy = MockStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        # Same parameters should generate same cache key and hit cache
        await calculator.calculate_indicator(TechnicalIndicator.RSI, sample_market_data, 1, period=14)
        cache_size_1 = len(calculator._calculation_cache)
        
        await calculator.calculate_indicator(TechnicalIndicator.RSI, sample_market_data, 1, period=14)
        cache_size_2 = len(calculator._calculation_cache)
        
        assert cache_size_1 == cache_size_2 == 1  # Same cache entry used
        
        # Different parameters should generate different cache key
        await calculator.calculate_indicator(TechnicalIndicator.RSI, sample_market_data, 1, period=20)
        cache_size_3 = len(calculator._calculation_cache)
        
        assert cache_size_3 == 2  # New cache entry created

    def test_cache_expiration(self, calculator):
        """Test cache entry expiration."""
        # Mock expired cache entry
        cache_key = "test_key"
        mock_result = MagicMock()
        calculator._calculation_cache[cache_key] = mock_result
        calculator._cache_timestamps[cache_key] = datetime.utcnow() - timedelta(seconds=400)  # Expired
        
        # Should return None for expired entry
        result = calculator._get_cached_result(cache_key)
        assert result is None
        
        # Expired entry should be removed
        assert cache_key not in calculator._calculation_cache
        assert cache_key not in calculator._cache_timestamps

    def test_cache_size_limit(self, calculator):
        """Test cache size limiting functionality."""
        # Fill cache beyond limit
        for i in range(1100):  # Beyond the 1000 limit
            cache_key = f"test_key_{i}"
            mock_result = MagicMock()
            calculator._calculation_cache[cache_key] = mock_result
            calculator._cache_timestamps[cache_key] = datetime.utcnow()
        
        # Trigger cache cleanup by adding one more entry
        calculator._cache_result("new_key", MagicMock())
        
        # Cache should be reduced to manageable size
        assert len(calculator._calculation_cache) <= 1000

    def test_clear_cache(self, calculator):
        """Test cache clearing functionality."""
        # Add some cache entries
        calculator._calculation_cache["key1"] = MagicMock()
        calculator._calculation_cache["key2"] = MagicMock()
        calculator._cache_timestamps["key1"] = datetime.utcnow()
        calculator._cache_timestamps["key2"] = datetime.utcnow()
        
        count = calculator.clear_cache()
        
        assert count == 2
        assert len(calculator._calculation_cache) == 0
        assert len(calculator._cache_timestamps) == 0

    def test_get_performance_stats_empty(self, calculator):
        """Test performance stats when no calculations have been performed."""
        stats = calculator.get_performance_stats()
        
        # Should have entries for all indicators, but with zero counts
        for indicator in TechnicalIndicator:
            assert indicator.value in stats
            assert stats[indicator.value]['count'] == 0
            assert stats[indicator.value]['avg_time_ms'] == 0
        
        assert 'cache' in stats
        assert stats['cache']['entries'] == 0

    def test_performance_stats_limit(self, calculator):
        """Test that performance stats are limited to prevent memory growth."""
        # Simulate many calculations
        for i in range(150):  # More than the 100 limit
            calculator._record_performance('RSI', float(i))
        
        # Should be limited to 100 entries
        assert len(calculator._performance_stats['RSI']) == 100

    @pytest.mark.asyncio
    async def test_concurrent_calculations(self, calculator, sample_market_data):
        """Test concurrent calculation handling."""
        mock_strategy = MockStrategy(calculation_time_ms=20)
        calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
        
        # Run multiple concurrent calculations
        tasks = []
        for i in range(5):
            task = calculator.calculate_indicator(
                TechnicalIndicator.RSI,
                sample_market_data,
                instrument_id=i,  # Different instruments to avoid cache hits
                period=14
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All calculations should succeed
        for result in results:
            assert result is not None
            assert result.indicator_type == TechnicalIndicator.RSI
        
        # Should have 5 different cache entries
        assert len(calculator._calculation_cache) == 5

    def test_build_cache_key_consistency(self, calculator, sample_market_data):
        """Test cache key generation consistency."""
        # Same inputs should generate same cache key
        key1 = calculator._build_cache_key(TechnicalIndicator.RSI, 1, sample_market_data, {'period': 14})
        key2 = calculator._build_cache_key(TechnicalIndicator.RSI, 1, sample_market_data, {'period': 14})
        
        assert key1 == key2
        
        # Different inputs should generate different cache keys
        key3 = calculator._build_cache_key(TechnicalIndicator.RSI, 2, sample_market_data, {'period': 14})
        key4 = calculator._build_cache_key(TechnicalIndicator.RSI, 1, sample_market_data, {'period': 20})
        
        assert key1 != key3
        assert key1 != key4

    @pytest.mark.asyncio
    async def test_logging_integration(self, calculator, sample_market_data):
        """Test logging integration for various scenarios."""
        with patch('src.backend.services.analytics.indicator_calculator.logger') as mock_logger:
            # Test successful calculation logging
            mock_strategy = MockStrategy()
            calculator.register_strategy(TechnicalIndicator.RSI, mock_strategy)
            
            await calculator.calculate_indicator(TechnicalIndicator.RSI, sample_market_data, 1)
            
            # Should log successful calculation
            mock_logger.debug.assert_called()
            
            # Test no strategy logging
            await calculator.calculate_indicator(TechnicalIndicator.MACD, sample_market_data, 1)
            
            # Should log error about missing strategy
            mock_logger.error.assert_called()