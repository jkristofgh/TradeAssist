"""
Unit tests for the base strategy interface.

Testing framework for strategy pattern infrastructure including:
- Test base interface compliance
- Test result format standardization
- Test parameter validation patterns
- Test error handling consistency
- Test performance monitoring integration
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import MagicMock
from abc import ABC

from src.backend.services.analytics.strategies.base import IndicatorStrategy


class MockIndicatorStrategy(IndicatorStrategy):
    """Mock strategy implementation for testing."""
    
    async def calculate(self, market_data: pd.DataFrame, instrument_id: int, **params):
        # Simple mock calculation
        return MagicMock(
            indicator_type="TEST",
            timestamp=datetime.utcnow(),
            instrument_id=instrument_id,
            values={'test_value': 42.0},
            metadata=params
        )
    
    def get_default_parameters(self):
        return {'period': 14, 'threshold': 50.0}
    
    def validate_parameters(self, params):
        period = params.get('period', 14)
        return isinstance(period, int) and 1 <= period <= 100


class TestIndicatorStrategy:
    """
    Testing framework for strategy pattern infrastructure.
    
    Requirements:
    - Test base interface compliance
    - Test result format standardization
    - Test parameter validation patterns
    - Test error handling consistency
    - Test performance monitoring integration
    """

    def test_abstract_base_class(self):
        """Test that IndicatorStrategy is properly defined as abstract."""
        assert issubclass(IndicatorStrategy, ABC)
        
        # Test that we can't instantiate the abstract class
        with pytest.raises(TypeError):
            IndicatorStrategy()

    def test_abstract_methods_defined(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = IndicatorStrategy.__abstractmethods__
        expected_methods = {'calculate', 'get_default_parameters', 'validate_parameters'}
        assert abstract_methods == expected_methods

    def test_concrete_implementation_compliance(self):
        """Test that concrete implementations can be instantiated."""
        # Should be able to instantiate concrete implementation
        strategy = MockIndicatorStrategy()
        assert isinstance(strategy, IndicatorStrategy)

    @pytest.mark.asyncio
    async def test_calculate_method_signature(self):
        """Test calculate method has correct signature and behavior."""
        strategy = MockIndicatorStrategy()
        
        # Create sample market data
        market_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        })
        
        result = await strategy.calculate(market_data, instrument_id=1, period=20)
        
        assert result.instrument_id == 1
        assert result.values['test_value'] == 42.0
        assert result.metadata['period'] == 20

    def test_get_default_parameters(self):
        """Test get_default_parameters returns proper dictionary."""
        strategy = MockIndicatorStrategy()
        defaults = strategy.get_default_parameters()
        
        assert isinstance(defaults, dict)
        assert 'period' in defaults
        assert defaults['period'] == 14
        assert defaults['threshold'] == 50.0

    def test_validate_parameters(self):
        """Test parameter validation logic."""
        strategy = MockIndicatorStrategy()
        
        # Test valid parameters
        assert strategy.validate_parameters({'period': 14}) == True
        assert strategy.validate_parameters({'period': 50}) == True
        
        # Test invalid parameters
        assert strategy.validate_parameters({'period': 0}) == False
        assert strategy.validate_parameters({'period': 101}) == False
        assert strategy.validate_parameters({'period': 'invalid'}) == False

    def test_get_supported_timeframes_default(self):
        """Test default supported timeframes."""
        strategy = MockIndicatorStrategy()
        timeframes = strategy.get_supported_timeframes()
        
        expected_timeframes = ["1min", "5min", "15min", "30min", "1hour", "1day"]
        assert timeframes == expected_timeframes

    def test_get_minimum_data_points_default(self):
        """Test default minimum data points requirement."""
        strategy = MockIndicatorStrategy()
        min_points = strategy.get_minimum_data_points()
        
        assert min_points == 20
        assert isinstance(min_points, int)

    def test_validate_market_data_success(self):
        """Test successful market data validation."""
        strategy = MockIndicatorStrategy()
        
        # Create valid market data
        market_data = pd.DataFrame({
            'open': [100] * 25,
            'high': [105] * 25,
            'low': [95] * 25,
            'close': [103] * 25,
            'volume': [1000] * 25
        })
        
        # Should not raise exception
        strategy._validate_market_data(market_data)

    def test_validate_market_data_missing_columns(self):
        """Test market data validation with missing columns."""
        strategy = MockIndicatorStrategy()
        
        # Create market data missing required columns
        market_data = pd.DataFrame({
            'open': [100] * 25,
            'high': [105] * 25,
            # Missing 'low', 'close', 'volume'
        })
        
        with pytest.raises(ValueError, match="Market data missing required columns"):
            strategy._validate_market_data(market_data)

    def test_validate_market_data_insufficient_data(self):
        """Test market data validation with insufficient data points."""
        strategy = MockIndicatorStrategy()
        
        # Create market data with too few data points
        market_data = pd.DataFrame({
            'open': [100] * 5,
            'high': [105] * 5,
            'low': [95] * 5,
            'close': [103] * 5,
            'volume': [1000] * 5
        })
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            strategy._validate_market_data(market_data)

    def test_validate_market_data_nan_values(self):
        """Test market data validation with NaN values."""
        strategy = MockIndicatorStrategy()
        
        # Create market data with NaN values
        market_data = pd.DataFrame({
            'open': [100] * 25,
            'high': [105] * 25,
            'low': [95] * 25,
            'close': [103, None] + [103] * 23,  # NaN in close column
            'volume': [1000] * 25
        })
        
        with pytest.raises(ValueError, match="Market data contains NaN values"):
            strategy._validate_market_data(market_data)

    def test_calculate_timestamp(self):
        """Test timestamp calculation utility."""
        strategy = MockIndicatorStrategy()
        timestamp1 = strategy._calculate_timestamp()
        timestamp2 = strategy._calculate_timestamp()
        
        assert isinstance(timestamp1, datetime)
        assert isinstance(timestamp2, datetime)
        # Timestamps should be very close (within a second)
        assert abs((timestamp2 - timestamp1).total_seconds()) < 1.0

    def test_safe_iloc_success(self):
        """Test safe iloc with valid data."""
        strategy = MockIndicatorStrategy()
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Test getting last value
        result = strategy._safe_iloc(series, -1, default=0.0)
        assert result == 5.0
        
        # Test getting first value
        result = strategy._safe_iloc(series, 0, default=0.0)
        assert result == 1.0

    def test_safe_iloc_empty_series(self):
        """Test safe iloc with empty series."""
        strategy = MockIndicatorStrategy()
        series = pd.Series([])
        
        result = strategy._safe_iloc(series, -1, default=42.0)
        assert result == 42.0

    def test_safe_iloc_invalid_index(self):
        """Test safe iloc with invalid index."""
        strategy = MockIndicatorStrategy()
        series = pd.Series([1.0, 2.0, 3.0])
        
        # Test index out of bounds
        result = strategy._safe_iloc(series, 10, default=99.0)
        assert result == 99.0

    def test_safe_iloc_invalid_data_type(self):
        """Test safe iloc with invalid data types."""
        strategy = MockIndicatorStrategy()
        series = pd.Series(['a', 'b', 'c'])  # Non-numeric data
        
        result = strategy._safe_iloc(series, -1, default=0.0)
        assert result == 0.0


class CustomTestStrategy(IndicatorStrategy):
    """Custom strategy for testing inheritance and customization."""
    
    def __init__(self):
        self.custom_attribute = "test_value"
    
    async def calculate(self, market_data: pd.DataFrame, instrument_id: int, **params):
        return MagicMock(custom_result=True)
    
    def get_default_parameters(self):
        return {'custom_param': 42}
    
    def validate_parameters(self, params):
        return 'custom_param' in params
    
    def get_supported_timeframes(self):
        return ["1day", "1week", "1month"]  # Override default
    
    def get_minimum_data_points(self):
        return 50  # Override default


class TestStrategyCustomization:
    """Test strategy customization and inheritance."""
    
    def test_custom_strategy_inheritance(self):
        """Test that custom strategies can inherit and override methods."""
        strategy = CustomTestStrategy()
        
        assert isinstance(strategy, IndicatorStrategy)
        assert strategy.custom_attribute == "test_value"

    def test_custom_timeframes(self):
        """Test custom supported timeframes override."""
        strategy = CustomTestStrategy()
        timeframes = strategy.get_supported_timeframes()
        
        assert timeframes == ["1day", "1week", "1month"]

    def test_custom_minimum_data_points(self):
        """Test custom minimum data points override."""
        strategy = CustomTestStrategy()
        min_points = strategy.get_minimum_data_points()
        
        assert min_points == 50

    def test_custom_parameters(self):
        """Test custom parameter handling."""
        strategy = CustomTestStrategy()
        
        defaults = strategy.get_default_parameters()
        assert defaults == {'custom_param': 42}
        
        assert strategy.validate_parameters({'custom_param': 100}) == True
        assert strategy.validate_parameters({'other_param': 100}) == False

    @pytest.mark.asyncio
    async def test_custom_calculate(self):
        """Test custom calculate method."""
        strategy = CustomTestStrategy()
        
        market_data = pd.DataFrame({
            'open': [100] * 25,
            'high': [105] * 25,
            'low': [95] * 25,
            'close': [103] * 25,
            'volume': [1000] * 25
        })
        
        result = await strategy.calculate(market_data, instrument_id=1)
        assert result.custom_result == True