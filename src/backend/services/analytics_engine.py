"""
Advanced Market Analytics Engine

Provides technical indicators, market analysis, and real-time calculations
for the TradeAssist platform Phase 4 implementation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from ..database.connection import get_db_session
from ..models.market_data import MarketData
from ..models.instruments import Instrument
from ..models.alert_rules import AlertRule
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class TechnicalIndicator(Enum):
    """Technical indicator types."""
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    MOVING_AVERAGE = "moving_average"
    STOCHASTIC = "stochastic"
    WILLIAMS_R = "williams_r"
    ATR = "atr"
    ADX = "adx"


@dataclass
class IndicatorResult:
    """Result from technical indicator calculation."""
    indicator_type: TechnicalIndicator
    timestamp: datetime
    instrument_id: int
    values: Dict[str, float]
    metadata: Dict[str, Any]


@dataclass
class MarketAnalysisResult:
    """Comprehensive market analysis result."""
    timestamp: datetime
    instrument_id: int
    technical_indicators: List[IndicatorResult]
    trend_analysis: Dict[str, Any]
    volatility_metrics: Dict[str, float]
    support_resistance: Dict[str, List[float]]
    pattern_signals: List[Dict[str, Any]]


class AnalyticsEngine:
    """
    Advanced market analytics engine for technical analysis.
    
    Provides real-time calculation of technical indicators, trend analysis,
    volatility metrics, and pattern recognition for trading decisions.
    """
    
    def __init__(self):
        self.data_cache: Dict[int, pd.DataFrame] = {}
        self.cache_max_age = 300  # 5 minutes cache
        self.indicator_periods = {
            TechnicalIndicator.RSI: 14,
            TechnicalIndicator.MACD: (12, 26, 9),
            TechnicalIndicator.BOLLINGER_BANDS: (20, 2),
            TechnicalIndicator.MOVING_AVERAGE: [5, 10, 20, 50, 200],
            TechnicalIndicator.STOCHASTIC: (14, 3),
            TechnicalIndicator.ATR: 14,
            TechnicalIndicator.ADX: 14
        }
        
    async def get_market_analysis(
        self,
        instrument_id: int,
        lookback_hours: int = 24
    ) -> Optional[MarketAnalysisResult]:
        """
        Get comprehensive market analysis for an instrument.
        
        Args:
            instrument_id: ID of instrument to analyze.
            lookback_hours: Hours of historical data to include.
            
        Returns:
            MarketAnalysisResult: Complete analysis or None if insufficient data.
        """
        try:
            # Get historical market data
            market_data = await self._get_market_data(instrument_id, lookback_hours)
            if market_data.empty:
                logger.warning(f"No market data available for instrument {instrument_id}")
                return None
                
            if len(market_data) < 50:  # Minimum data points for analysis
                logger.warning(f"Insufficient data points ({len(market_data)}) for analysis")
                return None
            
            # Calculate technical indicators
            technical_indicators = []
            for indicator_type in TechnicalIndicator:
                try:
                    result = await self._calculate_indicator(
                        indicator_type,
                        market_data,
                        instrument_id
                    )
                    if result:
                        technical_indicators.append(result)
                except Exception as e:
                    logger.error(f"Error calculating {indicator_type.value}: {e}")
            
            # Perform trend analysis
            trend_analysis = self._analyze_trend(market_data)
            
            # Calculate volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(market_data)
            
            # Find support and resistance levels
            support_resistance = self._find_support_resistance(market_data)
            
            # Detect chart patterns
            pattern_signals = self._detect_patterns(market_data)
            
            return MarketAnalysisResult(
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                technical_indicators=technical_indicators,
                trend_analysis=trend_analysis,
                volatility_metrics=volatility_metrics,
                support_resistance=support_resistance,
                pattern_signals=pattern_signals
            )
            
        except Exception as e:
            logger.error(f"Error performing market analysis for instrument {instrument_id}: {e}")
            return None
    
    async def get_real_time_indicators(
        self,
        instrument_id: int,
        indicators: List[TechnicalIndicator]
    ) -> List[IndicatorResult]:
        """
        Get real-time technical indicators for an instrument.
        
        Args:
            instrument_id: ID of instrument.
            indicators: List of indicators to calculate.
            
        Returns:
            List[IndicatorResult]: Calculated indicators.
        """
        try:
            # Get recent market data (last 4 hours for real-time calculations)
            market_data = await self._get_market_data(instrument_id, 4)
            
            if market_data.empty or len(market_data) < 20:
                logger.warning(f"Insufficient data for real-time indicators")
                return []
            
            results = []
            for indicator_type in indicators:
                try:
                    result = await self._calculate_indicator(
                        indicator_type,
                        market_data,
                        instrument_id
                    )
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error calculating real-time {indicator_type.value}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting real-time indicators: {e}")
            return []
    
    async def _get_market_data(
        self,
        instrument_id: int,
        lookback_hours: int
    ) -> pd.DataFrame:
        """
        Get historical market data for analysis.
        
        Args:
            instrument_id: ID of instrument.
            lookback_hours: Hours of data to retrieve.
            
        Returns:
            pd.DataFrame: Market data with OHLCV columns.
        """
        # Check cache first
        cache_key = f"{instrument_id}_{lookback_hours}"
        if cache_key in self.data_cache:
            cached_data = self.data_cache[cache_key]
            if not cached_data.empty and (
                datetime.utcnow() - cached_data.index[-1]
            ).total_seconds() < self.cache_max_age:
                return cached_data
        
        try:
            async with get_db_session() as session:
                cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
                
                result = await session.execute(
                    select(MarketData)
                    .where(
                        and_(
                            MarketData.instrument_id == instrument_id,
                            MarketData.timestamp >= cutoff_time
                        )
                    )
                    .order_by(MarketData.timestamp)
                )
                
                market_data_records = result.scalars().all()
                
                if not market_data_records:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = []
                for record in market_data_records:
                    data.append({
                        'timestamp': record.timestamp,
                        'open': float(record.price) if record.price else None,
                        'high': float(record.price) if record.price else None,
                        'low': float(record.price) if record.price else None,
                        'close': float(record.price) if record.price else None,
                        'volume': record.volume if record.volume else 0
                    })
                
                df = pd.DataFrame(data)
                if df.empty:
                    return pd.DataFrame()
                
                df.set_index('timestamp', inplace=True)
                df.fillna(method='ffill', inplace=True)
                
                # Cache the result
                self.data_cache[cache_key] = df
                
                return df
                
        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return pd.DataFrame()
    
    async def _calculate_indicator(
        self,
        indicator_type: TechnicalIndicator,
        market_data: pd.DataFrame,
        instrument_id: int
    ) -> Optional[IndicatorResult]:
        """
        Calculate a specific technical indicator.
        
        Args:
            indicator_type: Type of indicator to calculate.
            market_data: Historical market data.
            instrument_id: ID of instrument.
            
        Returns:
            IndicatorResult: Calculated indicator or None.
        """
        try:
            timestamp = datetime.utcnow()
            values = {}
            metadata = {}
            
            if indicator_type == TechnicalIndicator.RSI:
                period = self.indicator_periods[indicator_type]
                rsi = self._calculate_rsi(market_data['close'], period)
                values = {
                    'rsi': rsi.iloc[-1] if not rsi.empty else 50.0,
                    'overbought': 70.0,
                    'oversold': 30.0
                }
                metadata = {'period': period}
            
            elif indicator_type == TechnicalIndicator.MACD:
                fast, slow, signal = self.indicator_periods[indicator_type]
                macd_line, signal_line, histogram = self._calculate_macd(
                    market_data['close'], fast, slow, signal
                )
                values = {
                    'macd': macd_line.iloc[-1] if not macd_line.empty else 0.0,
                    'signal': signal_line.iloc[-1] if not signal_line.empty else 0.0,
                    'histogram': histogram.iloc[-1] if not histogram.empty else 0.0
                }
                metadata = {'fast': fast, 'slow': slow, 'signal': signal}
            
            elif indicator_type == TechnicalIndicator.BOLLINGER_BANDS:
                period, std_dev = self.indicator_periods[indicator_type]
                upper, middle, lower = self._calculate_bollinger_bands(
                    market_data['close'], period, std_dev
                )
                current_price = market_data['close'].iloc[-1]
                values = {
                    'upper_band': upper.iloc[-1] if not upper.empty else current_price,
                    'middle_band': middle.iloc[-1] if not middle.empty else current_price,
                    'lower_band': lower.iloc[-1] if not lower.empty else current_price,
                    'bandwidth': ((upper.iloc[-1] - lower.iloc[-1]) / middle.iloc[-1]) * 100 if not middle.empty else 0.0
                }
                metadata = {'period': period, 'std_dev': std_dev}
            
            elif indicator_type == TechnicalIndicator.MOVING_AVERAGE:
                periods = self.indicator_periods[indicator_type]
                for period in periods:
                    ma = self._calculate_sma(market_data['close'], period)
                    values[f'ma_{period}'] = ma.iloc[-1] if not ma.empty else market_data['close'].iloc[-1]
                metadata = {'periods': periods}
            
            elif indicator_type == TechnicalIndicator.STOCHASTIC:
                k_period, d_period = self.indicator_periods[indicator_type]
                k_percent, d_percent = self._calculate_stochastic(
                    market_data['high'], market_data['low'], market_data['close'],
                    k_period, d_period
                )
                values = {
                    'k_percent': k_percent.iloc[-1] if not k_percent.empty else 50.0,
                    'd_percent': d_percent.iloc[-1] if not d_percent.empty else 50.0
                }
                metadata = {'k_period': k_period, 'd_period': d_period}
            
            elif indicator_type == TechnicalIndicator.ATR:
                period = self.indicator_periods[indicator_type]
                atr = self._calculate_atr(
                    market_data['high'], market_data['low'], market_data['close'], period
                )
                values = {
                    'atr': atr.iloc[-1] if not atr.empty else 0.0,
                    'atr_percent': (atr.iloc[-1] / market_data['close'].iloc[-1]) * 100 if not atr.empty else 0.0
                }
                metadata = {'period': period}
            
            return IndicatorResult(
                indicator_type=indicator_type,
                timestamp=timestamp,
                instrument_id=instrument_id,
                values=values,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error calculating {indicator_type.value}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        return upper_band, middle_band, lower_band
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean()
    
    def _calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    
    def _calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def _analyze_trend(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze price trend using multiple timeframes.
        
        Args:
            market_data: Historical market data.
            
        Returns:
            Dict: Trend analysis results.
        """
        prices = market_data['close']
        
        # Short-term trend (20 periods)
        ma_20 = prices.rolling(window=20).mean()
        short_trend = "bullish" if prices.iloc[-1] > ma_20.iloc[-1] else "bearish"
        
        # Medium-term trend (50 periods)
        ma_50 = prices.rolling(window=50).mean()
        medium_trend = "bullish" if prices.iloc[-1] > ma_50.iloc[-1] else "bearish"
        
        # Long-term trend (200 periods)
        if len(prices) >= 200:
            ma_200 = prices.rolling(window=200).mean()
            long_trend = "bullish" if prices.iloc[-1] > ma_200.iloc[-1] else "bearish"
        else:
            long_trend = "insufficient_data"
        
        # Calculate trend strength
        price_change_20 = ((prices.iloc[-1] - prices.iloc[-21]) / prices.iloc[-21]) * 100 if len(prices) > 20 else 0
        
        return {
            'short_term': short_trend,
            'medium_term': medium_trend,
            'long_term': long_trend,
            'trend_strength_20d': price_change_20,
            'current_price': prices.iloc[-1],
            'ma_20': ma_20.iloc[-1] if not ma_20.empty else prices.iloc[-1],
            'ma_50': ma_50.iloc[-1] if not ma_50.empty else prices.iloc[-1]
        }
    
    def _calculate_volatility_metrics(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volatility metrics."""
        prices = market_data['close']
        returns = prices.pct_change().dropna()
        
        # Historical volatility (annualized)
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(252) * 100  # 252 trading days
        
        # Average True Range percentage
        if 'high' in market_data.columns and 'low' in market_data.columns:
            atr = self._calculate_atr(market_data['high'], market_data['low'], prices, 14)
            atr_percent = (atr.iloc[-1] / prices.iloc[-1]) * 100 if not atr.empty else 0.0
        else:
            atr_percent = 0.0
        
        return {
            'volatility_annualized': annualized_vol,
            'atr_percent': atr_percent,
            'daily_volatility': daily_vol * 100,
            'volatility_rank': min(annualized_vol / 20.0, 5.0)  # Scale 0-5
        }
    
    def _find_support_resistance(self, market_data: pd.DataFrame) -> Dict[str, List[float]]:
        """Find support and resistance levels using pivot points."""
        prices = market_data['close']
        
        # Find local minima (support) and maxima (resistance)
        window = 10
        support_levels = []
        resistance_levels = []
        
        for i in range(window, len(prices) - window):
            # Check for local minimum (support)
            if prices.iloc[i] == prices.iloc[i-window:i+window+1].min():
                support_levels.append(prices.iloc[i])
            
            # Check for local maximum (resistance)
            if prices.iloc[i] == prices.iloc[i-window:i+window+1].max():
                resistance_levels.append(prices.iloc[i])
        
        # Filter and sort levels
        current_price = prices.iloc[-1]
        
        # Keep only recent and relevant levels
        support_levels = [s for s in support_levels if s < current_price and s > current_price * 0.95]
        resistance_levels = [r for r in resistance_levels if r > current_price and r < current_price * 1.05]
        
        return {
            'support': sorted(support_levels, reverse=True)[:3],  # Top 3 support levels
            'resistance': sorted(resistance_levels)[:3]  # Top 3 resistance levels
        }
    
    def _detect_patterns(self, market_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect basic chart patterns."""
        prices = market_data['close']
        patterns = []
        
        if len(prices) < 20:
            return patterns
        
        # Moving average crossover patterns
        ma_5 = prices.rolling(window=5).mean()
        ma_20 = prices.rolling(window=20).mean()
        
        if len(ma_5) >= 2 and len(ma_20) >= 2:
            # Golden cross
            if (ma_5.iloc[-1] > ma_20.iloc[-1] and 
                ma_5.iloc[-2] <= ma_20.iloc[-2]):
                patterns.append({
                    'pattern': 'golden_cross',
                    'signal': 'bullish',
                    'confidence': 0.7,
                    'description': '5-day MA crossed above 20-day MA'
                })
            
            # Death cross
            elif (ma_5.iloc[-1] < ma_20.iloc[-1] and 
                  ma_5.iloc[-2] >= ma_20.iloc[-2]):
                patterns.append({
                    'pattern': 'death_cross',
                    'signal': 'bearish',
                    'confidence': 0.7,
                    'description': '5-day MA crossed below 20-day MA'
                })
        
        # Price breakout patterns
        recent_high = prices.tail(20).max()
        recent_low = prices.tail(20).min()
        current_price = prices.iloc[-1]
        
        if current_price > recent_high * 1.01:  # 1% above recent high
            patterns.append({
                'pattern': 'breakout_high',
                'signal': 'bullish',
                'confidence': 0.6,
                'description': f'Price broke above recent high of {recent_high:.2f}'
            })
        elif current_price < recent_low * 0.99:  # 1% below recent low
            patterns.append({
                'pattern': 'breakdown_low',
                'signal': 'bearish',
                'confidence': 0.6,
                'description': f'Price broke below recent low of {recent_low:.2f}'
            })
        
        return patterns


# Global analytics engine instance
analytics_engine = AnalyticsEngine()