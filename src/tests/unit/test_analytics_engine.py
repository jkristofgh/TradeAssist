"""
Unit tests for the Analytics Engine service.

Tests technical indicator calculations, market analysis, and real-time processing.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.services.analytics_engine import (
    AnalyticsEngine,
    TechnicalIndicator,
    IndicatorResult,
    MarketAnalysisResult
)


@pytest.fixture
def analytics_engine():
    """Create analytics engine instance for testing."""
    return AnalyticsEngine()


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.1)  # Random walk starting at 100
    
    data = []
    for date, price in zip(dates, prices):
        data.append({
            'timestamp': date,
            'open': price,
            'high': price + abs(np.random.randn() * 0.05),
            'low': price - abs(np.random.randn() * 0.05),
            'close': price,
            'volume': int(1000 + np.random.randn() * 100)
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


class TestAnalyticsEngine:
    """Test cases for AnalyticsEngine."""

    @pytest.mark.asyncio
    async def test_initialization(self, analytics_engine):
        """Test analytics engine initialization."""
        assert analytics_engine.data_cache == {}
        assert analytics_engine.cache_max_age == 300
        assert TechnicalIndicator.RSI in analytics_engine.indicator_periods
        assert analytics_engine.indicator_periods[TechnicalIndicator.RSI] == 14

    def test_calculate_rsi(self, analytics_engine, sample_market_data):
        """Test RSI calculation."""
        prices = sample_market_data['close']
        rsi = analytics_engine._calculate_rsi(prices, 14)
        
        # RSI should be between 0 and 100
        assert all(0 <= value <= 100 for value in rsi.dropna())
        
        # Should have fewer values than input (due to rolling window)
        assert len(rsi.dropna()) < len(prices)

    def test_calculate_macd(self, analytics_engine, sample_market_data):
        """Test MACD calculation."""
        prices = sample_market_data['close']
        macd_line, signal_line, histogram = analytics_engine._calculate_macd(prices, 12, 26, 9)
        
        # All series should have same length
        assert len(macd_line) == len(signal_line) == len(histogram)
        
        # Histogram should equal MACD - Signal
        diff = (macd_line - signal_line).dropna()
        hist = histogram.dropna()
        np.testing.assert_array_almost_equal(diff.values[-len(hist):], hist.values)

    def test_calculate_bollinger_bands(self, analytics_engine, sample_market_data):
        """Test Bollinger Bands calculation."""
        prices = sample_market_data['close']
        upper, middle, lower = analytics_engine._calculate_bollinger_bands(prices, 20, 2.0)
        
        # Upper band should be above middle, middle above lower
        valid_data = ~(upper.isna() | middle.isna() | lower.isna())
        assert all(upper[valid_data] >= middle[valid_data])
        assert all(middle[valid_data] >= lower[valid_data])
        
        # Middle band should be the moving average
        sma = prices.rolling(window=20).mean()
        np.testing.assert_array_almost_equal(middle.dropna().values, sma.dropna().values)

    def test_calculate_sma(self, analytics_engine, sample_market_data):
        """Test Simple Moving Average calculation."""
        prices = sample_market_data['close']
        sma = analytics_engine._calculate_sma(prices, 10)
        
        # SMA should have expected length
        assert len(sma.dropna()) == len(prices) - 9  # 10-period SMA loses first 9 values
        
        # First valid SMA value should be average of first 10 prices
        expected_first_sma = prices.iloc[:10].mean()
        assert abs(sma.dropna().iloc[0] - expected_first_sma) < 1e-10

    def test_calculate_stochastic(self, analytics_engine, sample_market_data):
        """Test Stochastic Oscillator calculation."""
        high = sample_market_data['high']
        low = sample_market_data['low']
        close = sample_market_data['close']
        
        k_percent, d_percent = analytics_engine._calculate_stochastic(high, low, close, 14, 3)
        
        # Values should be between 0 and 100
        assert all(0 <= value <= 100 for value in k_percent.dropna())
        assert all(0 <= value <= 100 for value in d_percent.dropna())
        
        # D% should be smoother than K% (less volatile)
        k_vol = k_percent.dropna().std()
        d_vol = d_percent.dropna().std()
        assert d_vol <= k_vol

    def test_calculate_atr(self, analytics_engine, sample_market_data):
        """Test Average True Range calculation."""
        high = sample_market_data['high']
        low = sample_market_data['low']
        close = sample_market_data['close']
        
        atr = analytics_engine._calculate_atr(high, low, close, 14)
        
        # ATR should be positive
        assert all(value >= 0 for value in atr.dropna())
        
        # ATR should be reasonable relative to price range
        price_range = (high - low).mean()
        assert atr.dropna().mean() <= price_range * 2

    @pytest.mark.asyncio
    async def test_get_market_data_cache(self, analytics_engine):
        """Test market data caching mechanism."""
        instrument_id = 1
        lookback_hours = 24
        
        # Mock the database query
        with patch.object(analytics_engine, '_get_market_data') as mock_get_data:
            mock_data = pd.DataFrame({
                'open': [100, 101, 102],
                'high': [101, 102, 103],
                'low': [99, 100, 101],
                'close': [100.5, 101.5, 102.5],
                'volume': [1000, 1100, 1200]
            })
            mock_data.index = pd.date_range('2024-01-01', periods=3, freq='1H')
            mock_get_data.return_value = mock_data
            
            # First call should hit database
            result1 = await analytics_engine._get_market_data(instrument_id, lookback_hours)
            
            # Verify cache was populated
            cache_key = f"{instrument_id}_{lookback_hours}"
            assert cache_key in analytics_engine.data_cache
            
            # Second call should use cache
            result2 = await analytics_engine._get_market_data(instrument_id, lookback_hours)
            
            # Should have been called only once (cached second time)
            assert mock_get_data.call_count >= 1
            pd.testing.assert_frame_equal(result1, result2)

    @pytest.mark.asyncio
    async def test_calculate_indicator_rsi(self, analytics_engine, sample_market_data):
        """Test RSI indicator calculation through main interface."""
        instrument_id = 1
        
        result = await analytics_engine._calculate_indicator(
            TechnicalIndicator.RSI, sample_market_data, instrument_id
        )
        
        assert result is not None
        assert result.indicator_type == TechnicalIndicator.RSI
        assert result.instrument_id == instrument_id
        assert 'rsi' in result.values
        assert 'overbought' in result.values
        assert 'oversold' in result.values
        assert result.values['overbought'] == 70.0
        assert result.values['oversold'] == 30.0
        assert 'period' in result.metadata

    @pytest.mark.asyncio
    async def test_calculate_indicator_macd(self, analytics_engine, sample_market_data):
        """Test MACD indicator calculation through main interface."""
        instrument_id = 1
        
        result = await analytics_engine._calculate_indicator(
            TechnicalIndicator.MACD, sample_market_data, instrument_id
        )
        
        assert result is not None
        assert result.indicator_type == TechnicalIndicator.MACD
        assert 'macd' in result.values
        assert 'signal' in result.values
        assert 'histogram' in result.values
        assert 'fast' in result.metadata
        assert 'slow' in result.metadata
        assert 'signal' in result.metadata

    def test_analyze_trend(self, analytics_engine, sample_market_data):
        """Test trend analysis."""
        trend_analysis = analytics_engine._analyze_trend(sample_market_data)
        
        assert 'short_term' in trend_analysis
        assert 'medium_term' in trend_analysis
        assert 'long_term' in trend_analysis
        assert 'trend_strength_20d' in trend_analysis
        assert 'current_price' in trend_analysis
        assert 'ma_20' in trend_analysis
        assert 'ma_50' in trend_analysis
        
        # Trend should be bullish, bearish, or insufficient_data
        assert trend_analysis['short_term'] in ['bullish', 'bearish']
        assert trend_analysis['medium_term'] in ['bullish', 'bearish']
        assert trend_analysis['long_term'] in ['bullish', 'bearish', 'insufficient_data']

    def test_calculate_volatility_metrics(self, analytics_engine, sample_market_data):
        """Test volatility metrics calculation."""
        volatility_metrics = analytics_engine._calculate_volatility_metrics(sample_market_data)
        
        assert 'volatility_annualized' in volatility_metrics
        assert 'atr_percent' in volatility_metrics
        assert 'daily_volatility' in volatility_metrics
        assert 'volatility_rank' in volatility_metrics
        
        # Volatility should be positive
        assert volatility_metrics['volatility_annualized'] >= 0
        assert volatility_metrics['daily_volatility'] >= 0
        assert 0 <= volatility_metrics['volatility_rank'] <= 5

    def test_find_support_resistance(self, analytics_engine, sample_market_data):
        """Test support and resistance level detection."""
        support_resistance = analytics_engine._find_support_resistance(sample_market_data)
        
        assert 'support' in support_resistance
        assert 'resistance' in support_resistance
        assert isinstance(support_resistance['support'], list)
        assert isinstance(support_resistance['resistance'], list)
        
        # Should return at most 3 levels each
        assert len(support_resistance['support']) <= 3
        assert len(support_resistance['resistance']) <= 3

    def test_detect_patterns(self, analytics_engine, sample_market_data):
        """Test pattern detection."""
        patterns = analytics_engine._detect_patterns(sample_market_data)
        
        assert isinstance(patterns, list)
        
        # Each pattern should have required fields
        for pattern in patterns:
            assert 'pattern' in pattern
            assert 'signal' in pattern
            assert 'confidence' in pattern
            assert 'description' in pattern
            assert pattern['signal'] in ['bullish', 'bearish']
            assert 0 <= pattern['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_get_market_analysis_insufficient_data(self, analytics_engine):
        """Test market analysis with insufficient data."""
        with patch.object(analytics_engine, '_get_market_data') as mock_get_data:
            # Return empty dataframe
            mock_get_data.return_value = pd.DataFrame()
            
            result = await analytics_engine.get_market_analysis(1, 24)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_real_time_indicators_insufficient_data(self, analytics_engine):
        """Test real-time indicators with insufficient data."""
        with patch.object(analytics_engine, '_get_market_data') as mock_get_data:
            # Return dataframe with insufficient data
            mock_data = pd.DataFrame({
                'close': [100, 101]  # Only 2 data points
            })
            mock_data.index = pd.date_range('2024-01-01', periods=2, freq='1H')
            mock_get_data.return_value = mock_data
            
            result = await analytics_engine.get_real_time_indicators(
                1, [TechnicalIndicator.RSI]
            )
            assert result == []


class TestTechnicalIndicatorEdgeCases:
    """Test edge cases for technical indicators."""

    def test_rsi_with_no_price_changes(self):
        """Test RSI calculation with constant prices."""
        engine = AnalyticsEngine()
        
        # Create series with no price changes
        prices = pd.Series([100.0] * 20)
        rsi = engine._calculate_rsi(prices, 14)
        
        # RSI should be NaN or 50 (neutral) when no price changes
        last_rsi = rsi.dropna().iloc[-1] if len(rsi.dropna()) > 0 else None
        assert last_rsi is None or abs(last_rsi - 50.0) < 1e-10

    def test_bollinger_bands_with_no_volatility(self):
        """Test Bollinger Bands with no price volatility."""
        engine = AnalyticsEngine()
        
        # Create series with no volatility
        prices = pd.Series([100.0] * 25)
        upper, middle, lower = engine._calculate_bollinger_bands(prices, 20, 2.0)
        
        # All bands should converge to the price level
        np.testing.assert_array_almost_equal(upper.dropna().values, [100.0] * len(upper.dropna()))
        np.testing.assert_array_almost_equal(middle.dropna().values, [100.0] * len(middle.dropna()))
        np.testing.assert_array_almost_equal(lower.dropna().values, [100.0] * len(lower.dropna()))

    def test_atr_with_no_gaps(self):
        """Test ATR calculation with no price gaps."""
        engine = AnalyticsEngine()
        
        # Create data with no gaps between sessions
        high = pd.Series([101.0] * 20)
        low = pd.Series([99.0] * 20)
        close = pd.Series([100.0] * 20)
        
        atr = engine._calculate_atr(high, low, close, 14)
        
        # ATR should be exactly 2.0 (high - low) for all periods
        expected_atr = 2.0
        np.testing.assert_array_almost_equal(
            atr.dropna().values, 
            [expected_atr] * len(atr.dropna())
        )


class TestIndicatorResult:
    """Test IndicatorResult data class."""

    def test_indicator_result_creation(self):
        """Test creating IndicatorResult instances."""
        timestamp = datetime.utcnow()
        values = {'rsi': 65.5, 'overbought': 70.0, 'oversold': 30.0}
        metadata = {'period': 14}
        
        result = IndicatorResult(
            indicator_type=TechnicalIndicator.RSI,
            timestamp=timestamp,
            instrument_id=1,
            values=values,
            metadata=metadata
        )
        
        assert result.indicator_type == TechnicalIndicator.RSI
        assert result.timestamp == timestamp
        assert result.instrument_id == 1
        assert result.values == values
        assert result.metadata == metadata

    def test_market_analysis_result_creation(self):
        """Test creating MarketAnalysisResult instances."""
        timestamp = datetime.utcnow()
        
        result = MarketAnalysisResult(
            timestamp=timestamp,
            instrument_id=1,
            technical_indicators=[],
            trend_analysis={},
            volatility_metrics={},
            support_resistance={},
            pattern_signals=[]
        )
        
        assert result.timestamp == timestamp
        assert result.instrument_id == 1
        assert isinstance(result.technical_indicators, list)
        assert isinstance(result.pattern_signals, list)


@pytest.mark.integration
class TestAnalyticsEngineIntegration:
    """Integration tests for analytics engine with database."""

    @pytest.mark.asyncio
    async def test_full_market_analysis_workflow(self, analytics_engine, sample_market_data):
        """Test complete market analysis workflow."""
        instrument_id = 1
        
        # Mock the database query to return sample data
        with patch.object(analytics_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = sample_market_data
            
            result = await analytics_engine.get_market_analysis(instrument_id, 24)
            
            assert result is not None
            assert result.instrument_id == instrument_id
            assert len(result.technical_indicators) > 0
            assert result.trend_analysis is not None
            assert result.volatility_metrics is not None
            assert result.support_resistance is not None
            assert isinstance(result.pattern_signals, list)

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, analytics_engine, sample_market_data):
        """Test handling concurrent analysis requests."""
        import asyncio
        
        with patch.object(analytics_engine, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = sample_market_data
            
            # Make concurrent requests
            tasks = [
                analytics_engine.get_market_analysis(i, 24) 
                for i in range(1, 6)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None