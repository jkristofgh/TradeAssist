"""
Enhanced Market Data Processor

Provides advanced market data processing, aggregation, and real-time analysis
for the TradeAssist platform Phase 4 implementation.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import defaultdict, deque

from ..database.connection import get_db_session
from ..models.market_data import MarketData
from ..models.instruments import Instrument
from ..websocket.realtime import get_websocket_manager
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class DataFrequency(Enum):
    """Data aggregation frequencies."""
    TICK = "tick"
    SECOND = "1s"
    MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    HOUR = "1h"
    DAILY = "1d"


class MarketDataType(Enum):
    """Types of market data."""
    PRICE = "price"
    VOLUME = "volume"
    BID_ASK = "bid_ask"
    LEVEL2 = "level2"
    TRADES = "trades"
    NEWS = "news"
    SENTIMENT = "sentiment"


@dataclass
class OHLCV:
    """Open, High, Low, Close, Volume data structure."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    trade_count: Optional[int] = None


@dataclass
class MarketSentiment:
    """Market sentiment analysis result."""
    timestamp: datetime
    instrument_id: int
    sentiment_score: float  # -1.0 (bearish) to 1.0 (bullish)
    confidence: float
    news_count: int
    social_mentions: int
    key_themes: List[str]
    source_breakdown: Dict[str, float]


@dataclass
class VolumeProfile:
    """Volume profile analysis."""
    timestamp: datetime
    price_levels: List[float]
    volume_at_price: List[int]
    poc: float  # Point of Control (highest volume)
    value_area_high: float
    value_area_low: float
    total_volume: int


@dataclass
class MarketMicrostructure:
    """Market microstructure metrics."""
    timestamp: datetime
    instrument_id: int
    bid_ask_spread: float
    market_impact: float
    order_flow_imbalance: float
    effective_spread: float
    price_improvement: float
    fill_rate: float


class EnhancedMarketDataProcessor:
    """
    Enhanced market data processor with advanced analytics.
    
    Provides real-time data aggregation, sentiment analysis, volume profiling,
    and market microstructure analysis for sophisticated trading strategies.
    """
    
    def __init__(self):
        # Real-time data buffers
        self.tick_buffers: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.ohlcv_cache: Dict[Tuple[int, DataFrequency], List[OHLCV]] = {}
        self.sentiment_cache: Dict[int, MarketSentiment] = {}
        
        # Processing configuration
        self.buffer_size = 10000
        self.aggregation_intervals = {
            DataFrequency.MINUTE: 60,
            DataFrequency.FIVE_MINUTES: 300,
            DataFrequency.FIFTEEN_MINUTES: 900,
            DataFrequency.HOUR: 3600
        }
        
        # Websocket manager for broadcasting
        self.websocket_manager = None
        
        # Market data quality metrics
        self.quality_metrics = {
            'total_ticks_processed': 0,
            'missing_data_points': 0,
            'late_data_points': 0,
            'duplicated_data_points': 0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the enhanced market data processor.
        
        Returns:
            bool: True if initialization successful.
        """
        try:
            self.websocket_manager = get_websocket_manager()
            
            # Start background aggregation tasks
            asyncio.create_task(self._aggregation_worker())
            asyncio.create_task(self._sentiment_analyzer_worker())
            
            logger.info("Enhanced market data processor initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing market data processor: {e}")
            return False
    
    async def process_tick_data(
        self,
        instrument_id: int,
        timestamp: datetime,
        price: float,
        volume: int,
        bid: Optional[float] = None,
        ask: Optional[float] = None
    ) -> None:
        """
        Process incoming tick data.
        
        Args:
            instrument_id: ID of the instrument.
            timestamp: Timestamp of the tick.
            price: Last traded price.
            volume: Volume traded.
            bid: Best bid price (optional).
            ask: Best ask price (optional).
        """
        try:
            tick_data = {
                'timestamp': timestamp,
                'price': price,
                'volume': volume,
                'bid': bid,
                'ask': ask
            }
            
            # Add to tick buffer
            self.tick_buffers[instrument_id].append(tick_data)
            
            # Update quality metrics
            self.quality_metrics['total_ticks_processed'] += 1
            
            # Check for data quality issues
            await self._check_data_quality(instrument_id, tick_data)
            
            # Broadcast real-time update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_market_data(
                    instrument_id=instrument_id,
                    price=price,
                    volume=volume,
                    timestamp=timestamp,
                    bid=bid,
                    ask=ask
                )
            
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
    
    async def get_ohlcv_data(
        self,
        instrument_id: int,
        frequency: DataFrequency,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[OHLCV]:
        """
        Get OHLCV data for specified frequency and time range.
        
        Args:
            instrument_id: ID of the instrument.
            frequency: Data frequency (1m, 5m, 1h, etc.).
            start_time: Start time for data (optional).
            end_time: End time for data (optional).
            limit: Maximum number of bars to return.
            
        Returns:
            List[OHLCV]: OHLCV data bars.
        """
        try:
            cache_key = (instrument_id, frequency)
            
            # Check cache first
            if cache_key in self.ohlcv_cache and not start_time:
                cached_data = self.ohlcv_cache[cache_key]
                return cached_data[-limit:] if cached_data else []
            
            # Generate OHLCV from tick data if available
            if instrument_id in self.tick_buffers:
                ohlcv_data = await self._aggregate_ticks_to_ohlcv(
                    instrument_id, frequency, start_time, end_time
                )
                
                # Cache the result
                self.ohlcv_cache[cache_key] = ohlcv_data
                return ohlcv_data[-limit:]
            
            # Fall back to database query
            return await self._get_ohlcv_from_database(
                instrument_id, frequency, start_time, end_time, limit
            )
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {e}")
            return []
    
    async def analyze_volume_profile(
        self,
        instrument_id: int,
        lookback_hours: int = 24,
        price_bins: int = 100
    ) -> Optional[VolumeProfile]:
        """
        Analyze volume profile for an instrument.
        
        Args:
            instrument_id: ID of the instrument.
            lookback_hours: Hours of data to analyze.
            price_bins: Number of price levels for analysis.
            
        Returns:
            VolumeProfile: Volume profile analysis or None.
        """
        try:
            # Get tick data for analysis
            if instrument_id not in self.tick_buffers:
                return None
            
            ticks = list(self.tick_buffers[instrument_id])
            if not ticks:
                return None
            
            # Filter by time range
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            recent_ticks = [
                tick for tick in ticks
                if tick['timestamp'] >= cutoff_time
            ]
            
            if len(recent_ticks) < 10:
                return None
            
            # Create price and volume arrays
            prices = np.array([tick['price'] for tick in recent_ticks])
            volumes = np.array([tick['volume'] for tick in recent_ticks])
            
            # Create price bins
            min_price = np.min(prices)
            max_price = np.max(prices)
            price_levels = np.linspace(min_price, max_price, price_bins)
            
            # Calculate volume at each price level
            volume_at_price = []
            for i in range(len(price_levels) - 1):
                low_price = price_levels[i]
                high_price = price_levels[i + 1]
                
                mask = (prices >= low_price) & (prices < high_price)
                volume_sum = np.sum(volumes[mask])
                volume_at_price.append(int(volume_sum))
            
            # Find Point of Control (POC) - price level with highest volume
            max_volume_index = np.argmax(volume_at_price)
            poc = price_levels[max_volume_index]
            
            # Calculate Value Area (70% of volume around POC)
            total_volume = np.sum(volume_at_price)
            target_volume = total_volume * 0.7
            
            # Find value area boundaries
            value_area_volume = 0
            lower_bound = max_volume_index
            upper_bound = max_volume_index
            
            while value_area_volume < target_volume and (lower_bound > 0 or upper_bound < len(volume_at_price) - 1):
                # Expand in direction with more volume
                lower_vol = volume_at_price[lower_bound - 1] if lower_bound > 0 else 0
                upper_vol = volume_at_price[upper_bound + 1] if upper_bound < len(volume_at_price) - 1 else 0
                
                if lower_vol >= upper_vol and lower_bound > 0:
                    lower_bound -= 1
                    value_area_volume += lower_vol
                elif upper_bound < len(volume_at_price) - 1:
                    upper_bound += 1
                    value_area_volume += upper_vol
                else:
                    break
            
            value_area_high = price_levels[upper_bound]
            value_area_low = price_levels[lower_bound]
            
            return VolumeProfile(
                timestamp=datetime.utcnow(),
                price_levels=price_levels.tolist(),
                volume_at_price=volume_at_price,
                poc=float(poc),
                value_area_high=float(value_area_high),
                value_area_low=float(value_area_low),
                total_volume=int(total_volume)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return None
    
    async def calculate_market_microstructure(
        self,
        instrument_id: int,
        lookback_minutes: int = 60
    ) -> Optional[MarketMicrostructure]:
        """
        Calculate market microstructure metrics.
        
        Args:
            instrument_id: ID of the instrument.
            lookback_minutes: Minutes of data to analyze.
            
        Returns:
            MarketMicrostructure: Microstructure metrics or None.
        """
        try:
            if instrument_id not in self.tick_buffers:
                return None
            
            ticks = list(self.tick_buffers[instrument_id])
            if not ticks:
                return None
            
            # Filter recent ticks with bid/ask data
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            recent_ticks = [
                tick for tick in ticks
                if tick['timestamp'] >= cutoff_time and tick['bid'] and tick['ask']
            ]
            
            if len(recent_ticks) < 10:
                return None
            
            # Calculate metrics
            spreads = []
            midpoints = []
            effective_spreads = []
            
            for tick in recent_ticks:
                bid = tick['bid']
                ask = tick['ask']
                price = tick['price']
                
                spread = ask - bid
                midpoint = (bid + ask) / 2
                effective_spread = 2 * abs(price - midpoint)
                
                spreads.append(spread)
                midpoints.append(midpoint)
                effective_spreads.append(effective_spread)
            
            # Calculate averages
            avg_spread = np.mean(spreads)
            avg_effective_spread = np.mean(effective_spreads)
            
            # Calculate order flow imbalance (simplified)
            # This would require more detailed order book data in practice
            order_flow_imbalance = 0.0  # Placeholder
            
            # Market impact (simplified)
            prices = [tick['price'] for tick in recent_ticks]
            price_changes = np.diff(prices)
            market_impact = np.std(price_changes) if len(price_changes) > 1 else 0.0
            
            # Price improvement (simplified)
            price_improvement = max(0, avg_spread - avg_effective_spread)
            
            # Fill rate (simplified - assume 100% for now)
            fill_rate = 1.0
            
            return MarketMicrostructure(
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                bid_ask_spread=float(avg_spread),
                market_impact=float(market_impact),
                order_flow_imbalance=order_flow_imbalance,
                effective_spread=float(avg_effective_spread),
                price_improvement=float(price_improvement),
                fill_rate=fill_rate
            )
            
        except Exception as e:
            logger.error(f"Error calculating market microstructure: {e}")
            return None
    
    async def get_market_sentiment(
        self,
        instrument_id: int,
        lookback_hours: int = 24
    ) -> Optional[MarketSentiment]:
        """
        Get market sentiment analysis for an instrument.
        
        Args:
            instrument_id: ID of the instrument.
            lookback_hours: Hours of data to analyze.
            
        Returns:
            MarketSentiment: Sentiment analysis or None.
        """
        try:
            # Check cache first
            if instrument_id in self.sentiment_cache:
                cached_sentiment = self.sentiment_cache[instrument_id]
                cache_age = (datetime.utcnow() - cached_sentiment.timestamp).total_seconds()
                if cache_age < 3600:  # Use cache if less than 1 hour old
                    return cached_sentiment
            
            # For now, create a mock sentiment analysis
            # In production, this would integrate with news APIs, social media, etc.
            sentiment = await self._analyze_sentiment_from_price_action(
                instrument_id, lookback_hours
            )
            
            if sentiment:
                self.sentiment_cache[instrument_id] = sentiment
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return None
    
    async def _aggregate_ticks_to_ohlcv(
        self,
        instrument_id: int,
        frequency: DataFrequency,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[OHLCV]:
        """Aggregate tick data to OHLCV bars."""
        try:
            ticks = list(self.tick_buffers[instrument_id])
            if not ticks:
                return []
            
            # Filter by time range if specified
            if start_time or end_time:
                filtered_ticks = []
                for tick in ticks:
                    if start_time and tick['timestamp'] < start_time:
                        continue
                    if end_time and tick['timestamp'] > end_time:
                        continue
                    filtered_ticks.append(tick)
                ticks = filtered_ticks
            
            if not ticks:
                return []
            
            # Convert to DataFrame for easier aggregation
            df = pd.DataFrame(ticks)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Determine resampling rule
            resample_rule = self._get_resample_rule(frequency)
            if not resample_rule:
                return []
            
            # Aggregate OHLCV
            agg_dict = {
                'price': ['first', 'max', 'min', 'last'],
                'volume': 'sum'
            }
            
            resampled = df.resample(resample_rule).agg(agg_dict)
            
            # Flatten column names
            resampled.columns = ['open', 'high', 'low', 'close', 'volume']
            resampled.dropna(inplace=True)
            
            # Convert to OHLCV objects
            ohlcv_data = []
            for timestamp, row in resampled.iterrows():
                # Calculate VWAP if we have enough data
                period_ticks = df.loc[timestamp:timestamp + pd.Timedelta(resample_rule)]
                if not period_ticks.empty:
                    vwap = np.average(period_ticks['price'], weights=period_ticks['volume'])
                    trade_count = len(period_ticks)
                else:
                    vwap = row['close']
                    trade_count = 1
                
                ohlcv = OHLCV(
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    vwap=float(vwap),
                    trade_count=trade_count
                )
                ohlcv_data.append(ohlcv)
            
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error aggregating ticks to OHLCV: {e}")
            return []
    
    async def _get_ohlcv_from_database(
        self,
        instrument_id: int,
        frequency: DataFrequency,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int
    ) -> List[OHLCV]:
        """Get OHLCV data from database."""
        try:
            async with get_db_session() as session:
                query = select(MarketData).where(MarketData.instrument_id == instrument_id)
                
                if start_time:
                    query = query.where(MarketData.timestamp >= start_time)
                if end_time:
                    query = query.where(MarketData.timestamp <= end_time)
                
                query = query.order_by(MarketData.timestamp.desc()).limit(limit)
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                if not records:
                    return []
                
                # Convert to OHLCV (simplified - using price as OHLC)
                ohlcv_data = []
                for record in reversed(records):  # Reverse to get chronological order
                    price = float(record.price) if record.price else 0.0
                    volume = record.volume if record.volume else 0
                    
                    ohlcv = OHLCV(
                        timestamp=record.timestamp,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=volume
                    )
                    ohlcv_data.append(ohlcv)
                
                return ohlcv_data
                
        except Exception as e:
            logger.error(f"Error getting OHLCV from database: {e}")
            return []
    
    def _get_resample_rule(self, frequency: DataFrequency) -> Optional[str]:
        """Get pandas resample rule for frequency."""
        rules = {
            DataFrequency.SECOND: '1S',
            DataFrequency.MINUTE: '1T',
            DataFrequency.FIVE_MINUTES: '5T',
            DataFrequency.FIFTEEN_MINUTES: '15T',
            DataFrequency.HOUR: '1H',
            DataFrequency.DAILY: '1D'
        }
        return rules.get(frequency)
    
    async def _analyze_sentiment_from_price_action(
        self,
        instrument_id: int,
        lookback_hours: int
    ) -> Optional[MarketSentiment]:
        """Analyze sentiment based on price action (mock implementation)."""
        try:
            if instrument_id not in self.tick_buffers:
                return None
            
            ticks = list(self.tick_buffers[instrument_id])
            if len(ticks) < 100:
                return None
            
            # Analyze price movement trend
            recent_ticks = ticks[-100:]  # Last 100 ticks
            prices = [tick['price'] for tick in recent_ticks]
            
            # Calculate price momentum
            price_change = (prices[-1] - prices[0]) / prices[0]
            volatility = np.std(prices) / np.mean(prices)
            
            # Simple sentiment scoring based on price action
            if price_change > 0.01:  # +1% move
                sentiment_score = min(price_change * 10, 1.0)
            elif price_change < -0.01:  # -1% move
                sentiment_score = max(price_change * 10, -1.0)
            else:
                sentiment_score = 0.0
            
            # Confidence based on volatility (less volatile = more confident)
            confidence = max(0.1, 1.0 - volatility * 5)
            
            return MarketSentiment(
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                sentiment_score=sentiment_score,
                confidence=min(confidence, 1.0),
                news_count=0,  # Would be populated from news feeds
                social_mentions=0,  # Would be populated from social media
                key_themes=[],
                source_breakdown={'price_action': 1.0}
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment from price action: {e}")
            return None
    
    async def _check_data_quality(self, instrument_id: int, tick_data: Dict) -> None:
        """Check data quality and update metrics."""
        try:
            # Check for late data (more than 5 seconds old)
            data_age = (datetime.utcnow() - tick_data['timestamp']).total_seconds()
            if data_age > 5:
                self.quality_metrics['late_data_points'] += 1
            
            # Check for duplicate timestamps (simplified check)
            buffer = self.tick_buffers[instrument_id]
            if len(buffer) >= 2 and buffer[-2]['timestamp'] == tick_data['timestamp']:
                self.quality_metrics['duplicated_data_points'] += 1
            
        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
    
    async def _aggregation_worker(self) -> None:
        """Background worker for data aggregation."""
        while True:
            try:
                # Aggregate data for all active instruments
                for instrument_id in self.tick_buffers.keys():
                    if self.tick_buffers[instrument_id]:
                        # Aggregate to different frequencies
                        for frequency in [DataFrequency.MINUTE, DataFrequency.FIVE_MINUTES]:
                            ohlcv_data = await self._aggregate_ticks_to_ohlcv(
                                instrument_id, frequency
                            )
                            
                            # Cache the aggregated data
                            cache_key = (instrument_id, frequency)
                            self.ohlcv_cache[cache_key] = ohlcv_data
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Error in aggregation worker: {e}")
                await asyncio.sleep(60)
    
    async def _sentiment_analyzer_worker(self) -> None:
        """Background worker for sentiment analysis."""
        while True:
            try:
                # Update sentiment for active instruments
                for instrument_id in self.tick_buffers.keys():
                    if instrument_id not in self.sentiment_cache or (
                        datetime.utcnow() - self.sentiment_cache[instrument_id].timestamp
                    ).total_seconds() > 3600:  # Update every hour
                        
                        sentiment = await self._analyze_sentiment_from_price_action(
                            instrument_id, 24
                        )
                        if sentiment:
                            self.sentiment_cache[instrument_id] = sentiment
                
                await asyncio.sleep(1800)  # Run every 30 minutes
                
            except Exception as e:
                logger.error(f"Error in sentiment analyzer worker: {e}")
                await asyncio.sleep(1800)
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics."""
        return {
            **self.quality_metrics,
            'active_instruments': len(self.tick_buffers),
            'total_buffered_ticks': sum(len(buffer) for buffer in self.tick_buffers.values()),
            'cache_size': len(self.ohlcv_cache)
        }


# Global market data processor instance
market_data_processor = EnhancedMarketDataProcessor()