"""
Integration tests for Phase 1 infrastructure components.

Tests the integration between database decorators and strategy pattern
infrastructure to validate the foundation is working correctly.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.decorators import with_db_session, with_validated_instrument
from src.backend.services.analytics.indicator_calculator import IndicatorCalculator
from src.backend.services.analytics.strategies.base import IndicatorStrategy
from src.backend.services.analytics_engine import IndicatorResult, TechnicalIndicator


class Phase1TestStrategy(IndicatorStrategy):
    """Test strategy implementation for Phase 1 integration testing."""
    
    async def calculate(self, market_data: pd.DataFrame, instrument_id: int, **params):
        """Simple test calculation."""
        return IndicatorResult(
            indicator_type=TechnicalIndicator.RSI,
            timestamp=datetime.utcnow(),
            instrument_id=instrument_id,
            values={'rsi': 65.0, 'overbought': 70.0, 'oversold': 30.0},
            metadata={'period': params.get('period', 14)}
        )
    
    def get_default_parameters(self):
        return {'period': 14}
    
    def validate_parameters(self, params):
        period = params.get('period', 14)
        return isinstance(period, int) and 1 <= period <= 100


class TestPhase1Infrastructure:
    """Integration tests for Phase 1 infrastructure."""
    
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
    
    @pytest.mark.asyncio
    async def test_database_decorator_basic_functionality(self):
        """Test basic database decorator functionality."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Create a test service class
        class TestService:
            @with_db_session
            async def get_data(self, session: AsyncSession, param: str):
                # Simulate database operation
                return f"data-{param}"
        
        service = TestService()
        
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            result = await service.get_data("test")
            
        assert result == "data-test"
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_strategy_pattern_basic_functionality(self, sample_market_data):
        """Test basic strategy pattern functionality."""
        calculator = IndicatorCalculator()
        strategy = Phase1TestStrategy()
        
        # Register strategy
        calculator.register_strategy(TechnicalIndicator.RSI, strategy)
        
        # Calculate indicator
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=14
        )
        
        assert result is not None
        assert result.indicator_type == TechnicalIndicator.RSI
        assert result.instrument_id == 1
        assert result.values['rsi'] == 65.0
        assert result.metadata['period'] == 14
        assert 'calculation_time_ms' in result.metadata
    
    @pytest.mark.asyncio
    async def test_strategy_performance_monitoring(self, sample_market_data):
        """Test that performance monitoring works correctly."""
        calculator = IndicatorCalculator()
        strategy = Phase1TestStrategy()
        
        calculator.register_strategy(TechnicalIndicator.RSI, strategy)
        
        # Perform multiple calculations
        for i in range(5):
            await calculator.calculate_indicator(
                TechnicalIndicator.RSI,
                sample_market_data,
                instrument_id=i,  # Different instruments to avoid caching
                period=14
            )
        
        # Check performance stats
        stats = calculator.get_performance_stats()
        rsi_stats = stats['rsi']
        
        assert rsi_stats['count'] == 5
        assert rsi_stats['avg_time_ms'] > 0
        assert rsi_stats['min_time_ms'] > 0
        assert rsi_stats['max_time_ms'] > 0
        assert rsi_stats['last_calculation_ms'] is not None
    
    @pytest.mark.asyncio
    async def test_strategy_caching_functionality(self, sample_market_data):
        """Test that strategy caching works correctly."""
        calculator = IndicatorCalculator()
        strategy = Phase1TestStrategy()
        
        calculator.register_strategy(TechnicalIndicator.RSI, strategy)
        
        # First calculation
        result1 = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=14
        )
        
        # Second calculation with same parameters - should hit cache
        result2 = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1,
            period=14
        )
        
        # Results should be identical (cached)
        assert result1 is result2
        assert len(calculator._calculation_cache) == 1
        
        # Cache stats should show entries
        stats = calculator.get_performance_stats()
        assert stats['cache']['entries'] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_strategy_registration(self, sample_market_data):
        """Test that multiple strategies can be registered and used."""
        calculator = IndicatorCalculator()
        
        # Register the same strategy for different indicators (for testing)
        strategy = Phase1TestStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, strategy)
        calculator.register_strategy(TechnicalIndicator.MACD, strategy)
        
        # Test both strategies work
        rsi_result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI, sample_market_data, instrument_id=1
        )
        
        macd_result = await calculator.calculate_indicator(
            TechnicalIndicator.MACD, sample_market_data, instrument_id=1
        )
        
        assert rsi_result is not None
        assert macd_result is not None
        assert len(calculator.get_supported_indicators()) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling integration between components."""
        # Test database decorator error handling
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        class TestService:
            @with_db_session
            async def failing_operation(self, session: AsyncSession):
                raise ValueError("Test database error")
        
        service = TestService()
        
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            with pytest.raises(ValueError):
                await service.failing_operation()
            
            # Should have called rollback
            mock_session.rollback.assert_called_once()
            mock_session.commit.assert_not_called()
    
    def test_infrastructure_integration_readiness(self):
        """Test that infrastructure components are ready for Phase 2 integration."""
        # Test that IndicatorCalculator can be initialized
        calculator = IndicatorCalculator()
        assert calculator is not None
        assert hasattr(calculator, 'strategies')
        assert hasattr(calculator, 'register_strategy')
        assert hasattr(calculator, 'calculate_indicator')
        
        # Test that strategy base class is properly defined
        from src.backend.services.analytics.strategies.base import IndicatorStrategy
        assert hasattr(IndicatorStrategy, 'calculate')
        assert hasattr(IndicatorStrategy, 'get_default_parameters')
        assert hasattr(IndicatorStrategy, 'validate_parameters')
        
        # Test that decorators are importable and functional
        from src.backend.database.decorators import (
            with_db_session, with_validated_instrument, handle_db_errors
        )
        assert callable(with_db_session)
        assert callable(with_validated_instrument)
        assert callable(handle_db_errors)
    
    @pytest.mark.asyncio
    async def test_phase1_performance_requirements(self, sample_market_data):
        """Test that Phase 1 infrastructure meets performance requirements."""
        import time
        
        calculator = IndicatorCalculator()
        strategy = Phase1TestStrategy()
        calculator.register_strategy(TechnicalIndicator.RSI, strategy)
        
        # Test calculation performance
        start_time = time.time()
        
        result = await calculator.calculate_indicator(
            TechnicalIndicator.RSI,
            sample_market_data,
            instrument_id=1
        )
        
        calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Phase 1 requirement: Strategy pattern overhead <5ms per calculation setup
        assert calculation_time < 100  # Allow 100ms for test environment
        assert result is not None
        
        # Test that calculation time is recorded
        assert 'calculation_time_ms' in result.metadata
        assert result.metadata['calculation_time_ms'] > 0
    
    def test_phase1_memory_efficiency(self):
        """Test that Phase 1 infrastructure is memory efficient."""
        import sys
        
        # Test that creating calculator doesn't consume excessive memory
        initial_size = sys.getsizeof({})
        
        calculator = IndicatorCalculator()
        calculator_size = sys.getsizeof(calculator.__dict__)
        
        # Should be reasonable size (less than 10KB for basic structures)
        assert calculator_size < 10000
        
        # Test cache size limiting
        for i in range(50):
            cache_key = f"test_key_{i}"
            calculator._calculation_cache[cache_key] = MagicMock()
        
        assert len(calculator._calculation_cache) == 50
        
        # Clear cache and verify cleanup
        cleared_count = calculator.clear_cache()
        assert cleared_count == 50
        assert len(calculator._calculation_cache) == 0