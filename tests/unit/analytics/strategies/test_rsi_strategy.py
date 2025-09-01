"""
Unit tests for RSI Strategy implementation.

Tests validate calculation accuracy, parameter validation, and error handling
to ensure backward compatibility with the original AnalyticsEngine implementation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backend.services.analytics.strategies.rsi_strategy import RSIStrategy
from src.backend.services.analytics_engine import TechnicalIndicator


class TestRSIStrategy:
    """Test suite for RSI Strategy implementation."""
    
    @pytest.fixture
    def rsi_strategy(self):
        """Create RSI strategy instance for testing."""
        return RSIStrategy()
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        # Generate realistic price data with some volatility
        np.random.seed(42)  # For reproducible tests
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        
        # Start with base price and add random walk
        base_price = 100.0
        price_changes = np.random.randn(50) * 2
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] + change
            prices.append(max(new_price, 10))  # Keep prices reasonable
        
        return pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': np.random.randint(10000, 100000, 50)
        })
    
    @pytest.mark.asyncio
    async def test_rsi_calculation_accuracy(self, rsi_strategy, sample_market_data):
        """Test RSI calculation produces expected results."""
        result = await rsi_strategy.calculate(
            market_data=sample_market_data,
            instrument_id=1,
            period=14
        )
        
        # Validate result structure
        assert result is not None
        assert result.indicator_type == TechnicalIndicator.RSI
        assert result.instrument_id == 1
        assert isinstance(result.timestamp, datetime)
        
        # Validate RSI values
        assert 'rsi' in result.values
        assert 'overbought' in result.values
        assert 'oversold' in result.values
        
        # RSI should be between 0 and 100
        rsi_value = result.values['rsi']
        assert 0 <= rsi_value <= 100
        
        # Standard thresholds
        assert result.values['overbought'] == 70.0
        assert result.values['oversold'] == 30.0
        
        # Metadata validation
        assert result.metadata['period'] == 14
    
    def test_parameter_validation(self, rsi_strategy):
        """Test parameter validation logic."""
        # Valid parameters
        assert rsi_strategy.validate_parameters({'period': 14}) == True
        assert rsi_strategy.validate_parameters({'period': 5}) == True
        assert rsi_strategy.validate_parameters({'period': 50}) == True
        
        # Invalid parameters
        assert rsi_strategy.validate_parameters({'period': 1}) == False  # Too small
        assert rsi_strategy.validate_parameters({'period': 101}) == False  # Too large
        assert rsi_strategy.validate_parameters({'period': 'invalid'}) == False  # Wrong type
        assert rsi_strategy.validate_parameters({'period': 14.5}) == False  # Float instead of int
    
    def test_default_parameters(self, rsi_strategy):
        """Test default parameter values."""
        defaults = rsi_strategy.get_default_parameters()
        assert defaults == {'period': 14}
    
    @pytest.mark.asyncio
    async def test_rsi_with_custom_period(self, rsi_strategy, sample_market_data):
        """Test RSI calculation with different periods."""
        # Test with period 10
        result = await rsi_strategy.calculate(
            market_data=sample_market_data,
            instrument_id=1,
            period=10
        )
        
        assert result.metadata['period'] == 10
        assert 0 <= result.values['rsi'] <= 100
    
    @pytest.mark.asyncio
    async def test_insufficient_data_error(self, rsi_strategy):
        """Test behavior with insufficient data."""
        # Create minimal dataset
        small_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'open': [100, 101, 102, 101, 100],
            'high': [102, 103, 104, 103, 102],
            'low': [98, 99, 100, 99, 98],
            'close': [100, 101, 102, 101, 100],
            'volume': [10000] * 5
        })
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            await rsi_strategy.calculate(
                market_data=small_data,
                instrument_id=1,
                period=14
            )
    
    @pytest.mark.asyncio
    async def test_missing_columns_error(self, rsi_strategy):
        """Test behavior with missing required columns."""
        invalid_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=20, freq='D'),
            'close': [100] * 20
            # Missing open, high, low, volume columns
        })
        
        with pytest.raises(ValueError, match="Market data missing required columns"):
            await rsi_strategy.calculate(
                market_data=invalid_data,
                instrument_id=1,
                period=14
            )
    
    def test_minimum_data_points(self, rsi_strategy):
        """Test minimum data points calculation."""
        assert rsi_strategy.get_minimum_data_points() == 15  # period + 1
    
    @pytest.mark.asyncio
    async def test_edge_case_constant_prices(self, rsi_strategy):
        """Test RSI with constant prices (should result in RSI = 50)."""
        # Create data with constant prices (no price movement)
        constant_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=30, freq='D'),
            'open': [100] * 30,
            'high': [100] * 30,
            'low': [100] * 30,
            'close': [100] * 30,
            'volume': [10000] * 30
        })
        
        result = await rsi_strategy.calculate(
            market_data=constant_data,
            instrument_id=1,
            period=14
        )
        
        # With constant prices, RSI should be around 50 (neutral)
        # Due to NaN handling in calculation, it should default to 50
        assert result.values['rsi'] == 50.0
    
    @pytest.mark.asyncio
    async def test_calculation_time_performance(self, rsi_strategy, sample_market_data):
        """Test calculation performance meets requirements."""
        import time
        
        start_time = time.time()
        result = await rsi_strategy.calculate(
            market_data=sample_market_data,
            instrument_id=1,
            period=14
        )
        calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # RSI calculation should be very fast (<50ms for 50 data points)
        assert calculation_time < 50.0
        assert result is not None
    
    def test_rsi_calculation_manual_verification(self, rsi_strategy):
        """Test RSI calculation against manually calculated values."""
        # Use simple dataset with known RSI values
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=20, freq='D'),
            'open': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                    108, 110, 112, 111, 113, 115, 114, 116, 118, 117],
            'high': [101, 103, 102, 104, 106, 105, 107, 109, 108, 110,
                    109, 111, 113, 112, 114, 116, 115, 117, 119, 118],
            'low': [99, 101, 100, 102, 104, 103, 105, 107, 106, 108,
                   107, 109, 111, 110, 112, 114, 113, 115, 117, 116],
            'close': [101, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                     108, 110, 112, 111, 113, 115, 114, 116, 118, 117],
            'volume': [10000] * 20
        })
        
        # Calculate RSI manually using the same formula as the strategy
        prices = test_data['close']
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        expected_rsi = 100 - (100 / (1 + rs))
        expected_value = expected_rsi.iloc[-1] if not expected_rsi.empty else 50.0
        
        # Test our strategy
        result = rsi_strategy._calculate_rsi(test_data['close'], 14)
        calculated_value = result.iloc[-1] if not result.empty else 50.0
        
        # Values should match (within floating point precision)
        assert abs(calculated_value - expected_value) < 1e-10