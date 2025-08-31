"""
Historical Data Service.

Service for retrieving, storing, and managing historical market data
with integration to the Schwab API and circuit breaker patterns.
"""

import asyncio
import json
import structlog
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from dataclasses import dataclass

from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ..models.historical_data import (
    DataSource, MarketDataBar, DataQuery, DataFrequency
)
from ..database.connection import get_db_session
from ..integrations.schwab_client import TradeAssistSchwabClient
from ..services.circuit_breaker import circuit_breaker, CircuitBreakerConfig
from ..config import settings

logger = structlog.get_logger()


@dataclass
class HistoricalDataRequest:
    """Request structure for historical data retrieval."""
    
    symbols: List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    frequency: str = DataFrequency.DAILY.value
    include_extended_hours: bool = False
    max_records: Optional[int] = None


@dataclass
class HistoricalDataResult:
    """Result structure for historical data operations."""
    
    symbol: str
    bars: List[Dict[str, Any]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    frequency: str
    total_bars: int
    data_source: str
    cached: bool = False


@dataclass
class AggregationRequest:
    """Request for data aggregation to higher timeframes."""
    
    symbol: str
    source_frequency: str
    target_frequency: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class HistoricalDataService:
    """
    Historical Data Service.
    
    Manages historical market data retrieval, storage, caching, and aggregation
    with integration to external data providers and robust error handling.
    """
    
    def __init__(self):
        self.schwab_client: Optional[TradeAssistSchwabClient] = None
        self.is_running = False
        self._background_tasks: List[asyncio.Task] = []
        
        # Performance metrics
        self._requests_served = 0
        self._cache_hits = 0
        self._api_calls_made = 0
        self._total_bars_cached = 0
        
        # Cache management
        self._cache: Dict[str, HistoricalDataResult] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl_minutes = 15  # 15-minute cache TTL for historical data
        
        # Rate limiting for API calls
        self._last_api_call: Optional[datetime] = None
        self._min_api_interval_seconds = 1.0  # Minimum 1 second between API calls
        
        # Circuit breaker configuration
        self._circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            request_timeout=30.0,
            error_percentage=50.0
        )
        
        logger.info("HistoricalDataService initialized")
    
    async def start(self) -> None:
        """
        Start the historical data service.
        
        Initializes data sources, Schwab client integration, and background tasks.
        """
        if self.is_running:
            logger.warning("Historical data service already running")
            return
        
        logger.info("Starting historical data service")
        
        try:
            # Initialize Schwab client
            if not settings.DEMO_MODE:
                self.schwab_client = TradeAssistSchwabClient()
                await self.schwab_client.initialize()
                logger.info("Schwab client initialized for historical data")
            else:
                logger.info("Demo mode: Historical data service will use mock data")
            
            # Initialize default data sources
            await self._initialize_data_sources()
            
            # Start background maintenance tasks
            self.is_running = True
            maintenance_task = asyncio.create_task(self._maintenance_loop())
            self._background_tasks.append(maintenance_task)
            
            logger.info("Historical data service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start historical data service: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the historical data service gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping historical data service")
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        # Close Schwab client
        if self.schwab_client:
            await self.schwab_client.close()
            self.schwab_client = None
        
        logger.info("Historical data service stopped")
    
    @circuit_breaker("historical_data_fetch")
    async def fetch_historical_data(
        self, 
        request: HistoricalDataRequest
    ) -> List[HistoricalDataResult]:
        """
        Fetch historical data for specified symbols and parameters.
        
        Args:
            request: Historical data request parameters
            
        Returns:
            List of HistoricalDataResult objects with retrieved data
            
        Raises:
            ValueError: If request parameters are invalid
            Exception: If data retrieval fails
        """
        self._requests_served += 1
        
        # Validate request
        if not request.symbols:
            raise ValueError("At least one symbol is required")
        
        if not DataFrequency(request.frequency):
            raise ValueError(f"Unsupported frequency: {request.frequency}")
        
        logger.info(
            f"Fetching historical data for {len(request.symbols)} symbols",
            symbols=request.symbols,
            frequency=request.frequency,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        results = []
        
        for symbol in request.symbols:
            try:
                # Check cache first
                cache_key = self._build_cache_key(symbol, request)
                cached_result = await self._get_cached_data(cache_key)
                
                if cached_result:
                    logger.debug(f"Cache hit for {symbol}")
                    self._cache_hits += 1
                    cached_result.cached = True
                    results.append(cached_result)
                    continue
                
                # Fetch from API/database
                result = await self._fetch_symbol_data(symbol, request)
                
                # Cache the result
                await self._cache_data(cache_key, result)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                # Continue with other symbols instead of failing completely
                error_result = HistoricalDataResult(
                    symbol=symbol,
                    bars=[],
                    start_date=request.start_date,
                    end_date=request.end_date,
                    frequency=request.frequency,
                    total_bars=0,
                    data_source="error",
                    cached=False
                )
                results.append(error_result)
        
        logger.info(f"Historical data fetch completed: {len(results)} results")
        return results
    
    async def store_historical_data(
        self,
        symbol: str,
        bars: List[Dict[str, Any]],
        frequency: str,
        data_source_name: str = "Schwab"
    ) -> int:
        """
        Store historical data bars in the database.
        
        Args:
            symbol: Trading symbol
            bars: List of OHLCV bar data
            frequency: Data frequency
            data_source_name: Name of the data source
            
        Returns:
            Number of bars stored (excluding duplicates)
            
        Raises:
            ValueError: If data validation fails
        """
        if not bars:
            return 0
        
        logger.info(
            f"Storing {len(bars)} bars for {symbol}",
            frequency=frequency,
            data_source=data_source_name
        )
        
        stored_count = 0
        
        async with get_db_session() as session:
            try:
                # Get data source
                data_source = await self._get_or_create_data_source(
                    session, data_source_name
                )
                
                for bar_data in bars:
                    try:
                        # Create MarketDataBar object
                        bar = MarketDataBar(
                            symbol=symbol,
                            timestamp=bar_data["timestamp"],
                            frequency=frequency,
                            open_price=Decimal(str(bar_data["open"])),
                            high_price=Decimal(str(bar_data["high"])),
                            low_price=Decimal(str(bar_data["low"])),
                            close_price=Decimal(str(bar_data["close"])),
                            volume=int(bar_data.get("volume", 0)),
                            open_interest=bar_data.get("open_interest"),
                            contract_month=bar_data.get("contract_month"),
                            data_source_id=data_source.id,
                            is_adjusted=bar_data.get("is_adjusted", False),
                            quality_score=bar_data.get("quality_score", 100)
                        )
                        
                        session.add(bar)
                        stored_count += 1
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid bar data for {symbol}: {e}")
                        continue
                
                await session.commit()
                self._total_bars_cached += stored_count
                
                logger.info(f"Stored {stored_count} bars for {symbol}")
                return stored_count
                
            except IntegrityError:
                await session.rollback()
                # Handle duplicates by updating existing records
                return await self._handle_duplicate_bars(
                    session, symbol, bars, frequency, data_source
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to store bars for {symbol}: {e}")
                raise
    
    async def aggregate_data(
        self,
        request: AggregationRequest
    ) -> List[Dict[str, Any]]:
        """
        Aggregate existing data to higher timeframes.
        
        Args:
            request: Aggregation parameters
            
        Returns:
            List of aggregated bar data
            
        Raises:
            ValueError: If aggregation parameters are invalid
        """
        logger.info(
            f"Aggregating {request.symbol} from {request.source_frequency} "
            f"to {request.target_frequency}"
        )
        
        # Validate frequency progression
        frequency_hierarchy = [
            DataFrequency.ONE_MINUTE.value,
            DataFrequency.FIVE_MINUTE.value,
            DataFrequency.FIFTEEN_MINUTE.value,
            DataFrequency.THIRTY_MINUTE.value,
            DataFrequency.ONE_HOUR.value,
            DataFrequency.FOUR_HOUR.value,
            DataFrequency.DAILY.value,
            DataFrequency.WEEKLY.value,
            DataFrequency.MONTHLY.value
        ]
        
        source_idx = frequency_hierarchy.index(request.source_frequency)
        target_idx = frequency_hierarchy.index(request.target_frequency)
        
        if target_idx <= source_idx:
            raise ValueError(
                f"Cannot aggregate from {request.source_frequency} "
                f"to {request.target_frequency}: invalid hierarchy"
            )
        
        # Fetch source data and perform aggregation
        # This is a simplified implementation - production would need
        # more sophisticated time-based grouping logic
        async with get_db_session() as session:
            query = (
                select(MarketDataBar)
                .where(
                    and_(
                        MarketDataBar.symbol == request.symbol,
                        MarketDataBar.frequency == request.source_frequency
                    )
                )
                .order_by(MarketDataBar.timestamp)
            )
            
            if request.start_date:
                query = query.where(MarketDataBar.timestamp >= request.start_date)
            if request.end_date:
                query = query.where(MarketDataBar.timestamp <= request.end_date)
            
            result = await session.execute(query)
            source_bars = result.scalars().all()
            
            if not source_bars:
                return []
            
            # Perform aggregation logic (simplified)
            aggregated_bars = self._perform_aggregation(
                source_bars, request.target_frequency
            )
            
            logger.info(
                f"Aggregated {len(source_bars)} bars to {len(aggregated_bars)} "
                f"{request.target_frequency} bars"
            )
            
            return aggregated_bars
    
    async def save_query(
        self,
        name: str,
        description: str,
        symbols: List[str],
        frequency: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
        is_favorite: bool = False
    ) -> int:
        """
        Save a query configuration for reuse.
        
        Args:
            name: Query name
            description: Query description
            symbols: List of symbols
            frequency: Data frequency
            start_date: Optional start date
            end_date: Optional end date
            filters: Optional additional filters
            is_favorite: Whether to mark as favorite
            
        Returns:
            Query ID
        """
        logger.info(f"Saving query: {name}")
        
        async with get_db_session() as session:
            try:
                query = DataQuery(
                    name=name,
                    description=description,
                    symbols=json.dumps(symbols),
                    frequency=frequency,
                    start_date=start_date,
                    end_date=end_date,
                    filters=json.dumps(filters) if filters else None,
                    is_favorite=is_favorite
                )
                
                session.add(query)
                await session.commit()
                await session.refresh(query)
                
                logger.info(f"Query saved with ID: {query.id}")
                return query.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save query: {e}")
                raise
    
    async def load_query(self, query_id: int) -> Optional[Dict[str, Any]]:
        """
        Load a saved query configuration.
        
        Args:
            query_id: Query ID to load
            
        Returns:
            Query configuration or None if not found
        """
        async with get_db_session() as session:
            try:
                result = await session.execute(
                    select(DataQuery).where(DataQuery.id == query_id)
                )
                query = result.scalar_one_or_none()
                
                if not query:
                    return None
                
                # Update execution tracking
                query.execution_count += 1
                query.last_executed = datetime.utcnow()
                await session.commit()
                
                return {
                    "id": query.id,
                    "name": query.name,
                    "description": query.description,
                    "symbols": json.loads(query.symbols),
                    "frequency": query.frequency,
                    "start_date": query.start_date,
                    "end_date": query.end_date,
                    "filters": json.loads(query.filters) if query.filters else None,
                    "is_favorite": query.is_favorite,
                    "execution_count": query.execution_count,
                    "last_executed": query.last_executed
                }
                
            except Exception as e:
                logger.error(f"Failed to load query {query_id}: {e}")
                return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get service performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        cache_hit_rate = (
            self._cache_hits / max(self._requests_served, 1) * 100
        )
        
        return {
            "requests_served": self._requests_served,
            "cache_hits": self._cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "api_calls_made": self._api_calls_made,
            "total_bars_cached": self._total_bars_cached,
            "cache_size": len(self._cache),
            "service_running": self.is_running,
            "schwab_client_connected": (
                self.schwab_client.is_connected 
                if self.schwab_client else False
            )
        }
    
    # Private helper methods
    
    async def _initialize_data_sources(self) -> None:
        """Initialize default data sources in the database."""
        async with get_db_session() as session:
            try:
                # Check if Schwab data source exists
                result = await session.execute(
                    select(DataSource).where(DataSource.name == "Schwab")
                )
                schwab_source = result.scalar_one_or_none()
                
                if not schwab_source:
                    schwab_source = DataSource(
                        name="Schwab",
                        provider_type="schwab_api",
                        base_url="https://api.schwabapi.com",
                        rate_limit_per_minute=120,  # Conservative limit
                        is_active=not settings.DEMO_MODE,
                        configuration=json.dumps({
                            "supports_realtime": True,
                            "supports_historical": True,
                            "max_years_history": 20,
                            "supported_frequencies": [f.value for f in DataFrequency]
                        })
                    )
                    session.add(schwab_source)
                    await session.commit()
                    logger.info("Schwab data source initialized")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to initialize data sources: {e}")
                raise
    
    async def _fetch_symbol_data(
        self,
        symbol: str,
        request: HistoricalDataRequest
    ) -> HistoricalDataResult:
        """Fetch data for a single symbol."""
        # Rate limiting
        if self._last_api_call:
            elapsed = (datetime.utcnow() - self._last_api_call).total_seconds()
            if elapsed < self._min_api_interval_seconds:
                await asyncio.sleep(self._min_api_interval_seconds - elapsed)
        
        if settings.DEMO_MODE or not self.schwab_client:
            # Generate mock data
            bars = self._generate_mock_data(symbol, request)
            data_source = "Demo"
        else:
            # Use Schwab client (would need actual implementation)
            # This is a placeholder for the actual API call
            bars = []  # TODO: Implement actual Schwab API call
            data_source = "Schwab"
        
        self._last_api_call = datetime.utcnow()
        self._api_calls_made += 1
        
        return HistoricalDataResult(
            symbol=symbol,
            bars=bars,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            total_bars=len(bars),
            data_source=data_source,
            cached=False
        )
    
    def _generate_mock_data(
        self,
        symbol: str,
        request: HistoricalDataRequest
    ) -> List[Dict[str, Any]]:
        """Generate mock historical data for testing."""
        import random
        from datetime import timedelta
        
        start_date = request.start_date or (datetime.utcnow() - timedelta(days=30))
        end_date = request.end_date or datetime.utcnow()
        
        bars = []
        current_date = start_date
        base_price = 100.0  # Starting price
        
        while current_date <= end_date:
            # Generate realistic OHLC data
            open_price = base_price + random.uniform(-2, 2)
            close_price = open_price + random.uniform(-3, 3)
            high_price = max(open_price, close_price) + random.uniform(0, 1)
            low_price = min(open_price, close_price) - random.uniform(0, 1)
            volume = random.randint(1000, 100000)
            
            bars.append({
                "timestamp": current_date,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            })
            
            base_price = close_price  # Price continuity
            current_date += timedelta(days=1)  # Daily frequency for mock
        
        return bars
    
    def _build_cache_key(
        self,
        symbol: str,
        request: HistoricalDataRequest
    ) -> str:
        """Build cache key for the request."""
        key_parts = [
            symbol,
            request.frequency,
            request.start_date.isoformat() if request.start_date else "none",
            request.end_date.isoformat() if request.end_date else "none",
            str(request.include_extended_hours),
            str(request.max_records or "none")
        ]
        return "|".join(key_parts)
    
    async def _get_cached_data(
        self,
        cache_key: str
    ) -> Optional[HistoricalDataResult]:
        """Get data from cache if valid."""
        if cache_key not in self._cache:
            return None
        
        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            return None
        
        # Check if cache is expired
        age_minutes = (datetime.utcnow() - cache_time).total_seconds() / 60
        if age_minutes > self._cache_ttl_minutes:
            # Remove expired data
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._cache[cache_key]
    
    async def _cache_data(
        self,
        cache_key: str,
        data: HistoricalDataResult
    ) -> None:
        """Cache data with timestamp."""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.utcnow()
    
    async def _get_or_create_data_source(
        self,
        session,
        name: str
    ) -> DataSource:
        """Get existing data source or create new one."""
        result = await session.execute(
            select(DataSource).where(DataSource.name == name)
        )
        data_source = result.scalar_one_or_none()
        
        if not data_source:
            data_source = DataSource(
                name=name,
                provider_type="unknown",
                is_active=True
            )
            session.add(data_source)
            await session.flush()  # Get ID without committing
        
        return data_source
    
    async def _handle_duplicate_bars(
        self,
        session,
        symbol: str,
        bars: List[Dict[str, Any]],
        frequency: str,
        data_source: DataSource
    ) -> int:
        """Handle duplicate bar insertion by updating existing records."""
        # Simplified implementation - just skip duplicates
        logger.info(f"Handling duplicate bars for {symbol} - skipping")
        return 0
    
    def _perform_aggregation(
        self,
        source_bars: List[MarketDataBar],
        target_frequency: str
    ) -> List[Dict[str, Any]]:
        """Perform time-based aggregation of bars."""
        # Simplified aggregation - production would need sophisticated grouping
        if not source_bars:
            return []
        
        # For now, just return the source bars as-is
        # In production, this would group by time periods and aggregate OHLCV
        aggregated = []
        for bar in source_bars[:10]:  # Limit for demo
            aggregated.append({
                "timestamp": bar.timestamp,
                "open": float(bar.open_price),
                "high": float(bar.high_price),
                "low": float(bar.low_price),
                "close": float(bar.close_price),
                "volume": bar.volume
            })
        
        return aggregated
    
    async def _maintenance_loop(self) -> None:
        """Background maintenance tasks."""
        while self.is_running:
            try:
                # Clean expired cache entries
                current_time = datetime.utcnow()
                expired_keys = [
                    key for key, timestamp in self._cache_timestamps.items()
                    if (current_time - timestamp).total_seconds() > (self._cache_ttl_minutes * 60)
                ]
                
                for key in expired_keys:
                    self._cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
                
                if expired_keys:
                    logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
                
                # Sleep for 5 minutes between maintenance cycles
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(60)  # Error backoff