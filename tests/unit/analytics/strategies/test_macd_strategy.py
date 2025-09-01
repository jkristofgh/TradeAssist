"""
Unit tests for MACD Strategy implementation.

Tests validate calculation accuracy, parameter validation, and error handling
to ensure backward compatibility with the original AnalyticsEngine implementation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backend.services.analytics.strategies.macd_strategy import MACDStrategy
from src.backend.services.analytics_engine import TechnicalIndicator


class TestMACDStrategy:
    """Test suite for MACD Strategy implementation."""
    
    @pytest.fixture
    def macd_strategy(self):
        """Create MACD strategy instance for testing."""
        return MACDStrategy()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        # Generate trending price data suitable for MACD
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=60, freq='D')
        
        # Create trending price with some volatility
        base_price = 100.0
        trend = np.linspace(0, 20, 60)  # Upward trend
        noise = np.random.randn(60) * 2
        prices = base_price + trend + noise
        
        return pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': np.random.randint(10000, 100000, 60)
        })
    
    @pytest.mark.asyncio
    async def test_macd_calculation_accuracy(self, macd_strategy, sample_market_data):
        """Test MACD calculation produces expected results."""
        result = await macd_strategy.calculate(
            market_data=sample_market_data,
            instrument_id=1,
            fast_period=12,
            slow_period=26,
            signal_period=9
        )
        
        # Validate result structure
        assert result is not None
        assert result.indicator_type == TechnicalIndicator.MACD
        assert result.instrument_id == 1
        assert isinstance(result.timestamp, datetime)
        
        # Validate MACD values
        assert 'macd' in result.values
        assert 'signal' in result.values
        assert 'histogram' in result.values
        
        # All values should be floats
        assert isinstance(result.values['macd'], float)
        assert isinstance(result.values['signal'], float)
        assert isinstance(result.values['histogram'], float)
        
        # Histogram should equal macd - signal
        expected_histogram = result.values['macd'] - result.values['signal']
        assert abs(result.values['histogram'] - expected_histogram) < 1e-10
        
        # Metadata validation
        assert result.metadata['fast'] == 12
        assert result.metadata['slow'] == 26
        assert result.metadata['signal'] == 9
    
    def test_parameter_validation(self, macd_strategy):
        """Test parameter validation logic."""
        # Valid parameters
        assert macd_strategy.validate_parameters({
            'fast_period': 12, 'slow_period': 26, 'signal_period': 9
        }) == True
        
        assert macd_strategy.validate_parameters({
            'fast_period': 5, 'slow_period': 20, 'signal_period': 5
        }) == True
        
        # Invalid parameters - fast >= slow
        assert macd_strategy.validate_parameters({
            'fast_period': 26, 'slow_period': 12, 'signal_period': 9
        }) == False
        
        assert macd_strategy.validate_parameters({
            'fast_period': 20, 'slow_period': 20, 'signal_period': 9
        }) == False
        
        # Invalid parameter ranges
        assert macd_strategy.validate_parameters({
            'fast_period': 0, 'slow_period': 26, 'signal_period': 9
        }) == False
        
        assert macd_strategy.validate_parameters({
            'fast_period': 12, 'slow_period': 200, 'signal_period': 9
        }) == False
        
        # Invalid types
        assert macd_strategy.validate_parameters({
            'fast_period': '12', 'slow_period': 26, 'signal_period': 9
        }) == False
    
    def test_default_parameters(self, macd_strategy):
        """Test default parameter values."""
        defaults = macd_strategy.get_default_parameters()
        expected = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }
        assert defaults == expected
    
    @pytest.mark.asyncio
    async def test_macd_with_custom_parameters(self, macd_strategy, sample_market_data):
        """Test MACD calculation with different parameters."""
        result = await macd_strategy.calculate(
            market_data=sample_market_data,
            instrument_id=1,
            fast_period=8,
            slow_period=21,
            signal_period=5
        )
        
        assert result.metadata['fast'] == 8
        assert result.metadata['slow'] == 21
        assert result.metadata['signal'] == 5
    
    @pytest.mark.asyncio
    async def test_insufficient_data_error(self, macd_strategy):
        """Test behavior with insufficient data."""
        # Create minimal dataset (less than slow_period + signal_period + buffer)
        small_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=20, freq='D'),
            'open': list(range(100, 120)),
            'high': list(range(102, 122)),
            'low': list(range(98, 118)),
            'close': list(range(100, 120)),
            'volume': [10000] * 20
        })
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            await macd_strategy.calculate(
                market_data=small_data,
                instrument_id=1,
                fast_period=12,
                slow_period=26,
                signal_period=9
            )
    
    def test_minimum_data_points(self, macd_strategy):
        """Test minimum data points calculation."""
        assert macd_strategy.get_minimum_data_points() == 45  # Conservative estimate
    
    @pytest.mark.asyncio
    async def test_calculation_time_performance(self, macd_strategy, sample_market_data):
        """Test calculation performance meets requirements."""
        import time
        
        start_time = time.time()
        result = await macd_strategy.calculate(
            market_data=sample_market_data,
            instrument_id=1
        )
        calculation_time = (time.time() - start_time) * 1000
        
        # MACD calculation should be fast (<100ms for 60 data points)
        assert calculation_time < 100.0
        assert result is not None
    
    def test_macd_calculation_manual_verification(self, macd_strategy):
        """Test MACD calculation against manually calculated values."""
        # Use simple trending data
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=40, freq='D'),
            'open': list(range(100, 140)),
            'high': [p + 2 for p in range(100, 140)],
            'low': [p - 2 for p in range(100, 140)],
            'close': list(range(100, 140)),
            'volume': [10000] * 40
        })
        
        # Calculate MACD manually using the same formula
        prices = test_data['close']
        ema_fast = prices.ewm(span=12).mean()
        ema_slow = prices.ewm(span=26).mean()
        expected_macd = ema_fast - ema_slow
        expected_signal = expected_macd.ewm(span=9).mean()
        expected_histogram = expected_macd - expected_signal
        
        # Get expected latest values
        expected_macd_value = expected_macd.iloc[-1]
        expected_signal_value = expected_signal.iloc[-1]
        expected_histogram_value = expected_histogram.iloc[-1]
        
        # Test our strategy calculation
        macd_line, signal_line, histogram = macd_strategy._calculate_macd(
            test_data['close'], 12, 26, 9
        )
        
        calculated_macd = macd_line.iloc[-1]
        calculated_signal = signal_line.iloc[-1]
        calculated_histogram = histogram.iloc[-1]
        
        # Values should match (within floating point precision)
        assert abs(calculated_macd - expected_macd_value) < 1e-10
        assert abs(calculated_signal - expected_signal_value) < 1e-10
        assert abs(calculated_histogram - expected_histogram_value) < 1e-10
    
    @pytest.mark.asyncio
    async def test_macd_with_flat_prices(self, macd_strategy):
        """Test MACD with constant prices."""
        # Create data with flat prices
        flat_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=50, freq='D'),
            'open': [100] * 50,
            'high': [100] * 50,
            'low': [100] * 50,
            'close': [100] * 50,
            'volume': [10000] * 50
        })
        
        result = await macd_strategy.calculate(
            market_data=flat_data,
            instrument_id=1
        )
        
        # With flat prices, all MACD components should be near 0
        assert abs(result.values['macd']) < 1e-10
        assert abs(result.values['signal']) < 1e-10
        assert abs(result.values['histogram']) < 1e-10