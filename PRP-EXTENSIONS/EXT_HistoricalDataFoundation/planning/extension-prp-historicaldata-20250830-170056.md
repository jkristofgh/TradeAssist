# Comprehensive Extension Product Requirements Prompt

## Extension Context
- **Extension Name**: Historical Data Foundation
- **Target Project**: TradeAssist  
- **Extension Type**: Feature Enhancement
- **Extension Version**: 1.0.0
- **Base Project Version**: Phase 3 Complete (Multi-Channel Notifications & Enterprise Resilience)

## Existing System Understanding

### Current Architecture Overview
TradeAssist is a sophisticated real-time trading alert system with:

- **High-performance architecture** with sub-500ms alert evaluation targets
- **Real-time data processing** using WebSocket connections and async processing  
- **Clean separation of concerns** with distinct API, service, and data layers
- **FastAPI backend** (Python) with **React/TypeScript frontend**
- **SQLite database** with SQLAlchemy ORM and async operations
- **Advanced analytics capabilities** including ML models and technical indicators
- **Enterprise-ready features** like circuit breakers, secret management, and monitoring

### Key System Components
- **Backend**: `src/backend/` with FastAPI, services, models, database layers
- **Frontend**: `src/frontend/src/` with React components, context providers, hooks
- **Real-time**: WebSocket system for live data streaming  
- **Database**: SQLite with WAL mode, async connections
- **External Integration**: Schwab API via schwab-py package
- **Testing**: Comprehensive unit, integration, and performance test suites

### Available Integration Points
- **API Router Pattern**: FastAPI routers with `/api/v1/` prefix
- **Service Layer**: Async service classes with lifecycle management
- **Database Models**: SQLAlchemy Base class with TimestampMixin
- **WebSocket Messages**: Extensible real-time message system
- **Frontend Components**: Feature-based React component organization
- **Configuration**: Pydantic-settings environment management

### Existing Code Patterns
- **Service Pattern**: Async services with start/stop lifecycle, background tasks
- **Database Pattern**: Base models, async sessions, relationship handling
- **API Pattern**: Router-based endpoints with Pydantic validation
- **Frontend Pattern**: Context providers, custom hooks, component composition
- **Testing Pattern**: Pytest with async support, mocking, performance testing

## Extension Requirements Analysis

### Primary Extension Objectives
1. **Historical Market Data Retrieval**: Pull OHLCV bars for stocks, indexes, futures
2. **Flexible Parameter Support**: Date ranges, frequencies, symbol selection
3. **Data Storage Optimization**: Store at lowest granularity with aggregation capability
4. **UI Integration**: Simple interface for data queries and visualization

### Functional Requirements
- **Asset Class Support**: Stocks, indexes, futures with appropriate data handling
- **Timeframe Flexibility**: 1m, 5m, 10m, 30m, 1h, 1d, 2d, 1w frequencies
- **Date Range Options**: Absolute dates, relative ranges (back X days/months), presets
- **Futures Handling**: Continuous series with roll policy and adjustment metadata
- **Data Aggregation**: Higher timeframes calculated from stored base data
- **UI Workflow**: Query configuration → Preview (table + chart) → Optional save/rerun

### Integration Requirements
- **Charts Module**: Provide bar series for visualization (no indicator computation)  
- **Indicators Module**: Supply bar series as inputs for technical analysis
- **Existing API Compatibility**: Maintain current endpoint behavior
- **UI Consistency**: Follow established design system and patterns

### Non-Functional Requirements
- **Performance**: Efficient data retrieval and storage patterns
- **Reliability**: Gap-free data for valid trading sessions
- **Scalability**: Handle multiple symbols and large date ranges
- **Compatibility**: No breaking changes to existing functionality

## Comprehensive Technical Architecture

### 1. Database Design

#### Core Historical Data Model
```python
# src/backend/models/historical_data.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
from datetime import datetime
from typing import Optional

class MarketDataBar(Base, TimestampMixin):
    """Base market data bar storage for all asset classes."""
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Symbol identification
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_class: Mapped[str] = mapped_column(String(20), nullable=False)  # stock, index, future
    
    # Time identification
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(10), nullable=False)  # 1m, 5m, etc.
    
    # OHLCV data
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False) 
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    adjustment_factor: Mapped[Optional[float]] = mapped_column(Float, default=1.0)
    split_factor: Mapped[Optional[float]] = mapped_column(Float, default=1.0)
    dividend_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    
    # Futures-specific fields
    continuous_series: Mapped[Optional[bool]] = mapped_column(default=False)
    contract_month: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    roll_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'frequency', name='unique_bar'),
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_symbol_frequency', 'symbol', 'frequency'),
        Index('idx_timestamp_frequency', 'timestamp', 'frequency'),
    )

class DataSource(Base, TimestampMixin):
    """Track data sources and their metadata."""
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)
    
    # Configuration
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer)
    max_symbols_per_request: Mapped[Optional[int]] = mapped_column(Integer)
    supported_frequencies: Mapped[str] = mapped_column(String(200))  # JSON array as string
    supported_asset_classes: Mapped[str] = mapped_column(String(200))  # JSON array as string

class DataQuery(Base, TimestampMixin):
    """Store user data queries for reuse and tracking."""
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Query parameters (stored as JSON)
    symbols: Mapped[str] = mapped_column(String(1000), nullable=False)  # JSON array
    asset_class: Mapped[str] = mapped_column(String(20), nullable=False)
    frequency: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_range_type: Mapped[str] = mapped_column(String(20))  # absolute, relative, preset
    date_range_value: Mapped[Optional[str]] = mapped_column(String(100))  # "30days", "YTD", etc.
    
    # Futures-specific
    continuous_series: Mapped[bool] = mapped_column(default=False)
    roll_policy: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Usage tracking
    last_executed: Mapped[Optional[datetime]] = mapped_column(DateTime)
    execution_count: Mapped[int] = mapped_column(default=0)
```

#### Database Migration Strategy
```python
# Migration: Add historical data tables
def upgrade():
    # Create market_data_bar table
    op.create_table(
        'market_data_bar',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(50), nullable=False),
        sa.Column('asset_class', sa.String(20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('frequency', sa.String(10), nullable=False),
        sa.Column('open_price', sa.Float(), nullable=False),
        sa.Column('high_price', sa.Float(), nullable=False),
        sa.Column('low_price', sa.Float(), nullable=False),
        sa.Column('close_price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Integer()),
        sa.Column('adjustment_factor', sa.Float(), default=1.0),
        sa.Column('split_factor', sa.Float(), default=1.0),
        sa.Column('dividend_amount', sa.Float(), default=0.0),
        sa.Column('continuous_series', sa.Boolean(), default=False),
        sa.Column('contract_month', sa.String(10)),
        sa.Column('roll_date', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'timestamp', 'frequency', name='unique_bar')
    )
    
    # Create indexes for performance
    op.create_index('idx_symbol_timestamp', 'market_data_bar', ['symbol', 'timestamp'])
    op.create_index('idx_symbol_frequency', 'market_data_bar', ['symbol', 'frequency'])
    op.create_index('idx_timestamp_frequency', 'market_data_bar', ['timestamp', 'frequency'])
```

### 2. Service Layer Architecture

#### Historical Data Service
```python
# src/backend/services/historical_data_service.py
import asyncio
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from src.backend.database.connection import get_db_session
from src.backend.models.historical_data import MarketDataBar, DataSource, DataQuery
from src.backend.integrations.schwab_client import SchwabClient
from src.backend.services.circuit_breaker import CircuitBreakerService

logger = structlog.get_logger()

class HistoricalDataService:
    """
    Service for managing historical market data retrieval, storage, and aggregation.
    
    Provides comprehensive functionality for:
    - Data fetching from external providers (Schwab API)
    - Storage optimization with lowest granularity preference
    - Real-time aggregation for higher timeframes
    - Query management and caching
    - Integration with existing TradeAssist architecture
    """
    
    def __init__(self):
        self.is_running = False
        self._background_tasks: List[asyncio.Task] = []
        self.circuit_breaker = CircuitBreakerService(failure_threshold=5, recovery_timeout=60)
        self.schwab_client: Optional[SchwabClient] = None
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Frequency hierarchy for aggregation
        self.frequency_hierarchy = {
            '1m': 1, '5m': 5, '10m': 10, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '1d': 1440, '1w': 10080
        }
    
    async def start(self) -> None:
        """Start the historical data service with proper lifecycle management."""
        if self.is_running:
            logger.warning("Historical data service already running")
            return
        
        logger.info("Starting historical data service")
        self.is_running = True
        
        # Initialize Schwab client
        self.schwab_client = SchwabClient()
        await self.schwab_client.initialize()
        
        # Start background maintenance tasks
        maintenance_task = asyncio.create_task(self._maintenance_loop())
        self._background_tasks.append(maintenance_task)
        
        logger.info("Historical data service started successfully")
    
    async def stop(self) -> None:
        """Stop the service gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping historical data service")
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        # Cleanup Schwab client
        if self.schwab_client:
            await self.schwab_client.cleanup()
        
        logger.info("Historical data service stopped")
    
    async def fetch_historical_data(
        self,
        symbols: List[str],
        asset_class: str,
        frequency: str,
        start_date: datetime,
        end_date: datetime,
        continuous_series: bool = False,
        roll_policy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical data for given parameters.
        
        Args:
            symbols: List of symbol tickers
            asset_class: 'stock', 'index', or 'future' 
            frequency: Time frequency ('1m', '5m', '1h', '1d', etc.)
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            continuous_series: Whether to create continuous futures series
            roll_policy: Roll adjustment policy for futures
            
        Returns:
            List of OHLCV bar dictionaries
        """
        try:
            # Check cache first
            cache_key = f"{'-'.join(symbols)}:{asset_class}:{frequency}:{start_date}:{end_date}"
            cached_data = await self._get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Retrieved cached data for {len(symbols)} symbols")
                return cached_data
            
            # Check database for existing data
            async with get_db_session() as session:
                existing_data = await self._query_stored_data(
                    session, symbols, frequency, start_date, end_date
                )
                
                # Identify missing data gaps
                missing_ranges = await self._identify_missing_data(
                    existing_data, symbols, frequency, start_date, end_date
                )
                
                # Fetch missing data from external source
                if missing_ranges:
                    await self._fetch_missing_data(session, missing_ranges, asset_class)
                
                # Query complete dataset
                complete_data = await self._query_stored_data(
                    session, symbols, frequency, start_date, end_date
                )
                
                # Aggregate to requested frequency if needed
                if await self._needs_aggregation(frequency):
                    complete_data = await self._aggregate_data(
                        session, complete_data, frequency
                    )
                
                # Apply futures adjustments if needed
                if asset_class == 'future' and continuous_series:
                    complete_data = await self._apply_futures_adjustments(
                        complete_data, roll_policy
                    )
                
                # Cache results
                await self._set_cached_data(cache_key, complete_data)
                
                logger.info(f"Retrieved {len(complete_data)} bars for {len(symbols)} symbols")
                return complete_data
        
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    async def _query_stored_data(
        self, 
        session, 
        symbols: List[str], 
        frequency: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MarketDataBar]:
        """Query stored data from database."""
        result = await session.execute(
            select(MarketDataBar)
            .where(
                and_(
                    MarketDataBar.symbol.in_(symbols),
                    MarketDataBar.frequency == frequency,
                    MarketDataBar.timestamp >= start_date,
                    MarketDataBar.timestamp <= end_date
                )
            )
            .order_by(MarketDataBar.symbol, MarketDataBar.timestamp)
        )
        return result.scalars().all()
    
    async def _fetch_missing_data(
        self, 
        session, 
        missing_ranges: List[Dict], 
        asset_class: str
    ) -> None:
        """Fetch missing data from external API."""
        if not self.schwab_client:
            raise ValueError("Schwab client not initialized")
        
        for range_info in missing_ranges:
            symbol = range_info['symbol']
            start_date = range_info['start_date'] 
            end_date = range_info['end_date']
            frequency = range_info['frequency']
            
            try:
                # Use circuit breaker for external API calls
                await self.circuit_breaker.call(
                    self._fetch_from_schwab,
                    session, symbol, asset_class, frequency, start_date, end_date
                )
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                continue
    
    async def _fetch_from_schwab(
        self,
        session,
        symbol: str,
        asset_class: str, 
        frequency: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """Fetch data from Schwab API and store in database."""
        try:
            # Convert frequency to Schwab API format
            schwab_frequency = self._convert_frequency_to_schwab(frequency)
            
            # Make API call based on asset class
            if asset_class == 'stock':
                raw_data = await self.schwab_client.get_stock_history(
                    symbol, schwab_frequency, start_date, end_date
                )
            elif asset_class == 'future':
                raw_data = await self.schwab_client.get_futures_history(
                    symbol, schwab_frequency, start_date, end_date
                )
            else:
                raw_data = await self.schwab_client.get_index_history(
                    symbol, schwab_frequency, start_date, end_date
                )
            
            # Convert and store data
            bar_objects = []
            for bar_data in raw_data:
                bar = MarketDataBar(
                    symbol=symbol,
                    asset_class=asset_class,
                    timestamp=datetime.fromisoformat(bar_data['datetime']),
                    frequency=frequency,
                    open_price=bar_data['open'],
                    high_price=bar_data['high'],
                    low_price=bar_data['low'],
                    close_price=bar_data['close'],
                    volume=bar_data.get('volume', 0)
                )
                bar_objects.append(bar)
            
            # Bulk insert
            session.add_all(bar_objects)
            await session.commit()
            
            logger.info(f"Stored {len(bar_objects)} bars for {symbol}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error fetching from Schwab API: {e}")
            raise
    
    async def _aggregate_data(
        self, 
        session,
        base_data: List[MarketDataBar], 
        target_frequency: str
    ) -> List[Dict[str, Any]]:
        """Aggregate base frequency data to higher timeframe."""
        if not base_data:
            return []
        
        # Group by symbol and time buckets
        aggregated_bars = []
        current_symbol = None
        current_bucket_start = None
        current_bucket_data = []
        
        bucket_size_minutes = self.frequency_hierarchy[target_frequency]
        
        for bar in base_data:
            # Calculate time bucket for this bar
            bucket_start = self._get_time_bucket_start(bar.timestamp, bucket_size_minutes)
            
            # New symbol or new time bucket
            if (current_symbol != bar.symbol or 
                current_bucket_start != bucket_start):
                
                # Process previous bucket
                if current_bucket_data:
                    agg_bar = self._create_aggregated_bar(
                        current_bucket_data, target_frequency
                    )
                    aggregated_bars.append(agg_bar)
                
                # Start new bucket
                current_symbol = bar.symbol
                current_bucket_start = bucket_start
                current_bucket_data = [bar]
            else:
                # Add to current bucket
                current_bucket_data.append(bar)
        
        # Process final bucket
        if current_bucket_data:
            agg_bar = self._create_aggregated_bar(current_bucket_data, target_frequency)
            aggregated_bars.append(agg_bar)
        
        return aggregated_bars
    
    async def save_query(self, query_params: Dict[str, Any]) -> int:
        """Save a user query for reuse."""
        async with get_db_session() as session:
            query = DataQuery(
                name=query_params['name'],
                description=query_params.get('description'),
                symbols=str(query_params['symbols']),  # Convert to JSON string
                asset_class=query_params['asset_class'],
                frequency=query_params['frequency'],
                start_date=query_params.get('start_date'),
                end_date=query_params.get('end_date'),
                date_range_type=query_params['date_range_type'],
                date_range_value=query_params.get('date_range_value'),
                continuous_series=query_params.get('continuous_series', False),
                roll_policy=query_params.get('roll_policy')
            )
            
            session.add(query)
            await session.commit()
            
            logger.info(f"Saved query: {query.name}")
            return query.id
    
    async def _maintenance_loop(self) -> None:
        """Background maintenance tasks."""
        while self.is_running:
            try:
                # Clear expired cache entries
                await self._cleanup_cache()
                
                # Update data source statistics
                await self._update_data_source_stats()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(60)  # Error backoff
    
    # ... additional helper methods for caching, time bucket calculations, etc.
```

#### Data Aggregation Service
```python  
# src/backend/services/data_aggregation_service.py
import structlog
from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.backend.models.historical_data import MarketDataBar

logger = structlog.get_logger()

class DataAggregationService:
    """
    Service for aggregating market data to higher timeframes.
    
    Provides deterministic aggregation from base frequency data to
    higher frequencies while maintaining data integrity and performance.
    """
    
    def __init__(self):
        self.frequency_multipliers = {
            '1m': 1, '5m': 5, '10m': 10, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, 
            '1d': 1440, '1w': 10080
        }
    
    def aggregate_bars(
        self, 
        bars: List[MarketDataBar], 
        target_frequency: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate bars to target frequency using OHLC rules.
        
        Args:
            bars: List of base frequency bars (sorted by timestamp)
            target_frequency: Target aggregation frequency
            
        Returns:
            List of aggregated bar dictionaries
        """
        if not bars:
            return []
        
        aggregated = []
        current_group = []
        current_bucket_start = None
        
        target_minutes = self.frequency_multipliers[target_frequency]
        
        for bar in bars:
            bucket_start = self._get_bucket_start(bar.timestamp, target_minutes)
            
            if current_bucket_start != bucket_start:
                # Process previous group
                if current_group:
                    agg_bar = self._aggregate_group(current_group, target_frequency)
                    aggregated.append(agg_bar)
                
                # Start new group
                current_bucket_start = bucket_start
                current_group = [bar]
            else:
                current_group.append(bar)
        
        # Process final group
        if current_group:
            agg_bar = self._aggregate_group(current_group, target_frequency)
            aggregated.append(agg_bar)
        
        return aggregated
    
    def _aggregate_group(
        self, 
        bars: List[MarketDataBar], 
        frequency: str
    ) -> Dict[str, Any]:
        """Aggregate a group of bars using OHLC rules."""
        if not bars:
            return {}
        
        # Sort by timestamp to ensure correct OHLC calculation
        sorted_bars = sorted(bars, key=lambda x: x.timestamp)
        first_bar = sorted_bars[0]
        last_bar = sorted_bars[-1]
        
        return {
            'symbol': first_bar.symbol,
            'asset_class': first_bar.asset_class,
            'timestamp': first_bar.timestamp,  # Use bucket start time
            'frequency': frequency,
            'open_price': first_bar.open_price,
            'high_price': max(bar.high_price for bar in sorted_bars),
            'low_price': min(bar.low_price for bar in sorted_bars),
            'close_price': last_bar.close_price,
            'volume': sum(bar.volume or 0 for bar in sorted_bars),
            'bar_count': len(sorted_bars)
        }
    
    def _get_bucket_start(self, timestamp: datetime, minutes: int) -> datetime:
        """Calculate the start time for aggregation bucket."""
        # Handle different frequency bucketing rules
        if minutes < 60:  # Intraday: align to market open or hour boundaries
            base_hour = timestamp.replace(minute=0, second=0, microsecond=0)
            minute_offset = (timestamp.minute // minutes) * minutes
            return base_hour + timedelta(minutes=minute_offset)
        elif minutes < 1440:  # Hours: align to midnight
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # Daily+: align to Sunday for weekly, month start for monthly
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
```

### 3. API Layer Implementation

#### Historical Data API Router
```python
# src/backend/api/historical_data.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from src.backend.models.base import get_db_session
from src.backend.services.historical_data_service import HistoricalDataService
from src.backend.services.data_aggregation_service import DataAggregationService
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/historical-data", tags=["historical-data"])

# Pydantic Models for Request/Response
class HistoricalDataRequest(BaseModel):
    """Request model for historical data queries."""
    
    symbols: List[str] = Field(..., min_items=1, max_items=50)
    asset_class: str = Field(..., regex="^(stock|index|future)$")
    frequency: str = Field(..., regex="^(1m|5m|10m|30m|1h|2h|4h|1d|1w)$")
    
    # Date range options
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    date_range_type: str = Field(default="absolute", regex="^(absolute|relative|preset)$")
    date_range_value: Optional[str] = None  # "30days", "YTD", etc.
    
    # Futures-specific options
    continuous_series: bool = Field(default=False)
    roll_policy: Optional[str] = Field(None, regex="^(volume|open_interest|calendar)$")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        # Clean and validate symbols
        cleaned = [symbol.strip().upper() for symbol in v if symbol.strip()]
        if not cleaned:
            raise ValueError('At least one valid symbol required')
        return cleaned
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and values['start_date'] and v:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v

class HistoricalDataResponse(BaseModel):
    """Response model for historical data queries."""
    
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    message: str = "Success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SavedQuery(BaseModel):
    """Model for saved queries."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    query_params: HistoricalDataRequest

class SavedQueryResponse(BaseModel):
    """Response for saved query operations."""
    
    query_id: int
    message: str = "Query saved successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Dependencies
async def get_historical_data_service() -> HistoricalDataService:
    """Dependency to get historical data service instance."""
    # This would be injected from the app state in production
    return HistoricalDataService()

# API Endpoints
@router.post("/fetch", response_model=HistoricalDataResponse)
async def fetch_historical_data(
    request: HistoricalDataRequest,
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> HistoricalDataResponse:
    """
    Fetch historical market data based on query parameters.
    
    Supports flexible date ranges, multiple symbols, and various asset classes.
    Returns OHLCV data with metadata about the query execution.
    """
    try:
        # Convert date range parameters
        start_date, end_date = await _resolve_date_range(request)
        
        # Execute data fetch
        bars = await service.fetch_historical_data(
            symbols=request.symbols,
            asset_class=request.asset_class,
            frequency=request.frequency,
            start_date=start_date,
            end_date=end_date,
            continuous_series=request.continuous_series,
            roll_policy=request.roll_policy
        )
        
        # Prepare response metadata
        metadata = {
            "query_params": request.dict(),
            "resolved_date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "bars_count": len(bars),
            "symbols_count": len(request.symbols),
            "frequency": request.frequency,
            "data_source": "schwab_api"
        }
        
        logger.info(f"Fetched {len(bars)} bars for {len(request.symbols)} symbols")
        
        return HistoricalDataResponse(
            data=bars,
            metadata=metadata
        )
    
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch historical data: {str(e)}"
        )

@router.get("/frequencies")
async def get_supported_frequencies() -> Dict[str, Any]:
    """Get list of supported data frequencies."""
    return {
        "frequencies": [
            {"value": "1m", "label": "1 Minute", "intraday": True},
            {"value": "5m", "label": "5 Minutes", "intraday": True},
            {"value": "10m", "label": "10 Minutes", "intraday": True}, 
            {"value": "30m", "label": "30 Minutes", "intraday": True},
            {"value": "1h", "label": "1 Hour", "intraday": True},
            {"value": "2h", "label": "2 Hours", "intraday": True},
            {"value": "4h", "label": "4 Hours", "intraday": True},
            {"value": "1d", "label": "1 Day", "intraday": False},
            {"value": "1w", "label": "1 Week", "intraday": False}
        ],
        "asset_classes": ["stock", "index", "future"],
        "date_range_presets": ["1d", "5d", "1m", "3m", "6m", "1y", "2y", "5y", "YTD"]
    }

@router.post("/queries/save", response_model=SavedQueryResponse)
async def save_query(
    saved_query: SavedQuery,
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> SavedQueryResponse:
    """Save a historical data query for reuse."""
    try:
        query_id = await service.save_query({
            'name': saved_query.name,
            'description': saved_query.description,
            **saved_query.query_params.dict()
        })
        
        return SavedQueryResponse(query_id=query_id)
    
    except Exception as e:
        logger.error(f"Error saving query: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to save query: {str(e)}"
        )

@router.get("/queries")
async def get_saved_queries() -> Dict[str, Any]:
    """Get list of saved queries."""
    try:
        async with get_db_session() as session:
            # Implementation to fetch saved queries
            queries = []  # Would fetch from database
            
            return {
                "queries": queries,
                "count": len(queries)
            }
    
    except Exception as e:
        logger.error(f"Error fetching saved queries: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch saved queries: {str(e)}"
        )

@router.post("/queries/{query_id}/execute", response_model=HistoricalDataResponse)  
async def execute_saved_query(
    query_id: int,
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> HistoricalDataResponse:
    """Execute a previously saved query."""
    try:
        # Implementation to load and execute saved query
        # Would fetch query parameters from database and execute
        pass
    
    except Exception as e:
        logger.error(f"Error executing saved query: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to execute saved query: {str(e)}"
        )

# Helper Functions
async def _resolve_date_range(request: HistoricalDataRequest) -> tuple[datetime, datetime]:
    """Resolve date range based on request parameters."""
    if request.date_range_type == "absolute":
        if not request.start_date or not request.end_date:
            raise ValueError("start_date and end_date required for absolute date range")
        return (
            datetime.combine(request.start_date, datetime.min.time()),
            datetime.combine(request.end_date, datetime.max.time())
        )
    
    elif request.date_range_type == "relative":
        # Handle relative ranges like "30days", "6months"
        end_date = datetime.now()
        
        if request.date_range_value == "1d":
            start_date = end_date - timedelta(days=1)
        elif request.date_range_value == "5d":
            start_date = end_date - timedelta(days=5)
        elif request.date_range_value == "1m":
            start_date = end_date - timedelta(days=30)
        elif request.date_range_value == "3m":
            start_date = end_date - timedelta(days=90)
        elif request.date_range_value == "6m":
            start_date = end_date - timedelta(days=180)
        elif request.date_range_value == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            raise ValueError(f"Unsupported relative date range: {request.date_range_value}")
        
        return start_date, end_date
    
    elif request.date_range_type == "preset":
        # Handle presets like "YTD", "QTD"
        end_date = datetime.now()
        
        if request.date_range_value == "YTD":
            start_date = datetime(end_date.year, 1, 1)
        elif request.date_range_value == "QTD":
            quarter_start = ((end_date.month - 1) // 3) * 3 + 1
            start_date = datetime(end_date.year, quarter_start, 1)
        else:
            raise ValueError(f"Unsupported preset: {request.date_range_value}")
        
        return start_date, end_date
    
    else:
        raise ValueError(f"Unsupported date range type: {request.date_range_type}")
```

### 4. Frontend Implementation Architecture

#### Historical Data Component Structure
```typescript
// src/frontend/src/components/HistoricalData/HistoricalDataPage.tsx
import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../context/WebSocketContext';
import { apiClient } from '../../services/apiClient';
import { HistoricalDataQuery, HistoricalDataResponse } from '../../types/historicalData';
import QueryForm from './QueryForm';
import DataPreview from './DataPreview';
import SavedQueries from './SavedQueries';
import './HistoricalDataPage.css';

interface HistoricalDataPageProps {}

const HistoricalDataPage: React.FC<HistoricalDataPageProps> = () => {
  const { isConnected } = useWebSocketContext();
  const [queryParams, setQueryParams] = useState<HistoricalDataQuery | null>(null);
  const [queryResults, setQueryResults] = useState<HistoricalDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'query' | 'saved'>('query');

  const handleQuerySubmit = async (params: HistoricalDataQuery) => {
    try {
      setLoading(true);
      setError(null);
      setQueryParams(params);
      
      const response = await apiClient.post('/api/v1/historical-data/fetch', params);
      setQueryResults(response.data);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuery = async (name: string, description?: string) => {
    if (!queryParams) return;
    
    try {
      await apiClient.post('/api/v1/historical-data/queries/save', {
        name,
        description,
        query_params: queryParams
      });
      
      // Show success notification
      alert('Query saved successfully');
      
    } catch (err) {
      alert('Failed to save query');
    }
  };

  return (
    <div className="historical-data-page">
      <div className="page-header">
        <h1>Historical Market Data</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="page-content">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'query' ? 'active' : ''}`}
            onClick={() => setActiveTab('query')}
          >
            New Query
          </button>
          <button 
            className={`tab ${activeTab === 'saved' ? 'active' : ''}`}
            onClick={() => setActiveTab('saved')}
          >
            Saved Queries
          </button>
        </div>

        {activeTab === 'query' && (
          <div className="query-section">
            <QueryForm 
              onSubmit={handleQuerySubmit} 
              loading={loading}
              error={error}
            />
            
            {queryResults && (
              <DataPreview 
                data={queryResults}
                onSave={handleSaveQuery}
                canSave={!!queryParams}
              />
            )}
          </div>
        )}

        {activeTab === 'saved' && (
          <SavedQueries onExecute={handleQuerySubmit} />
        )}
      </div>
    </div>
  );
};

export default HistoricalDataPage;
```

#### Query Form Component
```typescript
// src/frontend/src/components/HistoricalData/QueryForm.tsx
import React, { useState, useEffect } from 'react';
import { HistoricalDataQuery, AssetClass, Frequency, DateRangeType } from '../../types/historicalData';

interface QueryFormProps {
  onSubmit: (params: HistoricalDataQuery) => void;
  loading: boolean;
  error: string | null;
}

const QueryForm: React.FC<QueryFormProps> = ({ onSubmit, loading, error }) => {
  const [formData, setFormData] = useState<HistoricalDataQuery>({
    symbols: [''],
    asset_class: 'stock',
    frequency: '1d',
    date_range_type: 'relative',
    date_range_value: '30d',
    continuous_series: false
  });

  const [availableFrequencies, setAvailableFrequencies] = useState<any[]>([]);
  const [symbolInput, setSymbolInput] = useState('');

  useEffect(() => {
    loadSupportedFrequencies();
  }, []);

  const loadSupportedFrequencies = async () => {
    try {
      const response = await apiClient.get('/api/v1/historical-data/frequencies');
      setAvailableFrequencies(response.data.frequencies);
    } catch (err) {
      console.error('Failed to load frequencies:', err);
    }
  };

  const handleSymbolsChange = (value: string) => {
    setSymbolInput(value);
    const symbols = value.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    setFormData({ ...formData, symbols });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.symbols.length === 0 || formData.symbols[0] === '') {
      alert('Please enter at least one symbol');
      return;
    }
    
    onSubmit(formData);
  };

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <div className="form-section">
        <h3>Asset Selection</h3>
        
        <div className="form-group">
          <label>Asset Class</label>
          <select 
            value={formData.asset_class}
            onChange={(e) => setFormData({...formData, asset_class: e.target.value as AssetClass})}
          >
            <option value="stock">Stocks</option>
            <option value="index">Indexes</option>
            <option value="future">Futures</option>
          </select>
        </div>

        <div className="form-group">
          <label>Symbols (comma-separated)</label>
          <input
            type="text"
            value={symbolInput}
            onChange={(e) => handleSymbolsChange(e.target.value)}
            placeholder="AAPL, GOOGL, SPY"
            className="symbols-input"
          />
          <div className="symbols-preview">
            {formData.symbols.filter(s => s).map((symbol, i) => (
              <span key={i} className="symbol-tag">{symbol}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>Time Parameters</h3>
        
        <div className="form-group">
          <label>Frequency</label>
          <select
            value={formData.frequency}
            onChange={(e) => setFormData({...formData, frequency: e.target.value as Frequency})}
          >
            {availableFrequencies.map(freq => (
              <option key={freq.value} value={freq.value}>
                {freq.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Date Range</label>
          <select
            value={formData.date_range_type}
            onChange={(e) => setFormData({...formData, date_range_type: e.target.value as DateRangeType})}
          >
            <option value="relative">Relative (Last X days)</option>
            <option value="preset">Preset (YTD, etc.)</option>
            <option value="absolute">Absolute (Start/End dates)</option>
          </select>
        </div>

        {formData.date_range_type === 'relative' && (
          <div className="form-group">
            <label>Period</label>
            <select
              value={formData.date_range_value || '30d'}
              onChange={(e) => setFormData({...formData, date_range_value: e.target.value})}
            >
              <option value="1d">1 Day</option>
              <option value="5d">5 Days</option>
              <option value="1m">1 Month</option>
              <option value="3m">3 Months</option>
              <option value="6m">6 Months</option>
              <option value="1y">1 Year</option>
              <option value="2y">2 Years</option>
            </select>
          </div>
        )}

        {formData.date_range_type === 'preset' && (
          <div className="form-group">
            <label>Preset</label>
            <select
              value={formData.date_range_value || 'YTD'}
              onChange={(e) => setFormData({...formData, date_range_value: e.target.value})}
            >
              <option value="YTD">Year to Date</option>
              <option value="QTD">Quarter to Date</option>
              <option value="MTD">Month to Date</option>
            </select>
          </div>
        )}

        {formData.date_range_type === 'absolute' && (
          <>
            <div className="form-group">
              <label>Start Date</label>
              <input
                type="date"
                value={formData.start_date || ''}
                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label>End Date</label>
              <input
                type="date"
                value={formData.end_date || ''}
                onChange={(e) => setFormData({...formData, end_date: e.target.value})}
              />
            </div>
          </>
        )}
      </div>

      {formData.asset_class === 'future' && (
        <div className="form-section">
          <h3>Futures Options</h3>
          
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={formData.continuous_series}
                onChange={(e) => setFormData({...formData, continuous_series: e.target.checked})}
              />
              Continuous Series
            </label>
          </div>

          {formData.continuous_series && (
            <div className="form-group">
              <label>Roll Policy</label>
              <select
                value={formData.roll_policy || 'volume'}
                onChange={(e) => setFormData({...formData, roll_policy: e.target.value})}
              >
                <option value="volume">Volume Based</option>
                <option value="open_interest">Open Interest Based</option>
                <option value="calendar">Calendar Based</option>
              </select>
            </div>
          )}
        </div>
      )}

      <div className="form-actions">
        <button type="submit" disabled={loading} className="primary-button">
          {loading ? 'Loading...' : 'Preview Data'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </form>
  );
};

export default QueryForm;
```

#### Data Preview Component
```typescript
// src/frontend/src/components/HistoricalData/DataPreview.tsx
import React, { useState, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { HistoricalDataResponse } from '../../types/historicalData';

interface DataPreviewProps {
  data: HistoricalDataResponse;
  onSave: (name: string, description?: string) => void;
  canSave: boolean;
}

const DataPreview: React.FC<DataPreviewProps> = ({ data, onSave, canSave }) => {
  const [viewMode, setViewMode] = useState<'table' | 'chart'>('table');
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!data.data || data.data.length === 0) return null;

    // Group data by symbol for multi-symbol charts
    const symbolGroups = data.data.reduce((acc, bar) => {
      if (!acc[bar.symbol]) {
        acc[bar.symbol] = [];
      }
      acc[bar.symbol].push(bar);
      return acc;
    }, {} as Record<string, any[]>);

    const datasets = Object.entries(symbolGroups).map(([symbol, bars], index) => ({
      label: symbol,
      data: bars.map(bar => ({
        x: bar.timestamp,
        y: bar.close_price
      })),
      borderColor: `hsl(${index * 137.5}, 70%, 50%)`,
      backgroundColor: `hsla(${index * 137.5}, 70%, 50%, 0.1)`,
      fill: false,
      tension: 0.1
    }));

    return {
      datasets
    };
  }, [data.data]);

  const chartOptions = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Price Chart'
      },
      legend: {
        display: true,
        position: 'top' as const
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            day: 'MMM DD',
            hour: 'HH:mm',
            minute: 'HH:mm'
          }
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Price'
        }
      }
    }
  };

  const handleSave = () => {
    if (!saveName.trim()) {
      alert('Please enter a name for the query');
      return;
    }
    
    onSave(saveName.trim(), saveDescription.trim() || undefined);
    setShowSaveModal(false);
    setSaveName('');
    setSaveDescription('');
  };

  return (
    <div className="data-preview">
      <div className="preview-header">
        <div className="preview-info">
          <h3>Query Results</h3>
          <div className="metadata">
            <span>Bars: {data.metadata.bars_count}</span>
            <span>Symbols: {data.metadata.symbols_count}</span>
            <span>Frequency: {data.metadata.frequency}</span>
            <span>Range: {new Date(data.metadata.resolved_date_range.start_date).toLocaleDateString()} - {new Date(data.metadata.resolved_date_range.end_date).toLocaleDateString()}</span>
          </div>
        </div>
        
        <div className="preview-actions">
          <div className="view-toggle">
            <button 
              className={viewMode === 'table' ? 'active' : ''}
              onClick={() => setViewMode('table')}
            >
              Table
            </button>
            <button 
              className={viewMode === 'chart' ? 'active' : ''}
              onClick={() => setViewMode('chart')}
            >
              Chart
            </button>
          </div>
          
          {canSave && (
            <button 
              className="save-button"
              onClick={() => setShowSaveModal(true)}
            >
              Save Query
            </button>
          )}
        </div>
      </div>

      <div className="preview-content">
        {viewMode === 'table' && (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Timestamp</th>
                  <th>Open</th>
                  <th>High</th>
                  <th>Low</th>
                  <th>Close</th>
                  <th>Volume</th>
                </tr>
              </thead>
              <tbody>
                {data.data.slice(0, 100).map((bar, index) => (
                  <tr key={index}>
                    <td>{bar.symbol}</td>
                    <td>{new Date(bar.timestamp).toLocaleString()}</td>
                    <td>{bar.open_price.toFixed(2)}</td>
                    <td>{bar.high_price.toFixed(2)}</td>
                    <td>{bar.low_price.toFixed(2)}</td>
                    <td>{bar.close_price.toFixed(2)}</td>
                    <td>{bar.volume?.toLocaleString() || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {data.data.length > 100 && (
              <div className="table-footer">
                Showing first 100 of {data.data.length} bars
              </div>
            )}
          </div>
        )}

        {viewMode === 'chart' && chartData && (
          <div className="chart-container">
            <Line data={chartData} options={chartOptions} />
          </div>
        )}
      </div>

      {showSaveModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Save Query</h3>
              <button onClick={() => setShowSaveModal(false)}>×</button>
            </div>
            
            <div className="modal-content">
              <div className="form-group">
                <label>Query Name</label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="Enter query name"
                />
              </div>
              
              <div className="form-group">
                <label>Description (optional)</label>
                <textarea
                  value={saveDescription}
                  onChange={(e) => setSaveDescription(e.target.value)}
                  placeholder="Enter description"
                  rows={3}
                />
              </div>
            </div>
            
            <div className="modal-actions">
              <button onClick={() => setShowSaveModal(false)}>
                Cancel
              </button>
              <button onClick={handleSave} className="primary-button">
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataPreview;
```

### 5. Testing Strategy Implementation

#### Service Layer Tests
```python
# src/tests/unit/test_historical_data_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from src.backend.services.historical_data_service import HistoricalDataService
from src.backend.models.historical_data import MarketDataBar

class TestHistoricalDataService:
    """Comprehensive test suite for HistoricalDataService."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        service = HistoricalDataService()
        service.schwab_client = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_bars(self):
        """Create sample market data bars."""
        base_time = datetime(2024, 1, 1, 9, 30)
        return [
            MarketDataBar(
                symbol='AAPL',
                asset_class='stock',
                timestamp=base_time + timedelta(minutes=i),
                frequency='1m',
                open_price=150.0 + i * 0.1,
                high_price=150.5 + i * 0.1,
                low_price=149.5 + i * 0.1,
                close_price=150.2 + i * 0.1,
                volume=1000 + i * 10
            )
            for i in range(5)
        ]
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, service):
        """Test service start and stop operations."""
        # Test start
        await service.start()
        assert service.is_running
        
        # Test stop
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_cache_hit(self, service, sample_bars):
        """Test cache hit scenario."""
        # Setup cache
        cache_key = "AAPL:stock:1d:2024-01-01 00:00:00:2024-01-02 00:00:00"
        await service._set_cached_data(cache_key, sample_bars)
        
        # Fetch data
        result = await service.fetch_historical_data(
            symbols=['AAPL'],
            asset_class='stock',
            frequency='1d',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2)
        )
        
        assert len(result) == len(sample_bars)
        # Verify Schwab client not called (cache hit)
        service.schwab_client.get_stock_history.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_api_call(self, service):
        """Test API call when data not in cache."""
        # Mock Schwab API response
        mock_api_data = [
            {
                'datetime': '2024-01-01T09:30:00',
                'open': 150.0,
                'high': 150.5,
                'low': 149.5,
                'close': 150.2,
                'volume': 1000
            }
        ]
        service.schwab_client.get_stock_history.return_value = mock_api_data
        
        # Mock database session
        with patch('src.backend.services.historical_data_service.get_db_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            # Mock query results (no existing data)
            mock_session_instance.execute.return_value.scalars.return_value.all.return_value = []
            
            result = await service.fetch_historical_data(
                symbols=['AAPL'],
                asset_class='stock', 
                frequency='1d',
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2)
            )
            
            # Verify API was called
            service.schwab_client.get_stock_history.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_data_aggregation(self, service, sample_bars):
        """Test data aggregation from 1m to higher timeframes."""
        # Test 5-minute aggregation
        aggregated = await service._aggregate_data(None, sample_bars, '5m')
        
        assert len(aggregated) == 1  # 5 1-minute bars -> 1 5-minute bar
        
        agg_bar = aggregated[0]
        assert agg_bar['open_price'] == sample_bars[0].open_price  # First bar open
        assert agg_bar['close_price'] == sample_bars[-1].close_price  # Last bar close
        assert agg_bar['high_price'] == max(bar.high_price for bar in sample_bars)
        assert agg_bar['low_price'] == min(bar.low_price for bar in sample_bars)
        assert agg_bar['volume'] == sum(bar.volume for bar in sample_bars)
    
    @pytest.mark.asyncio
    async def test_save_query(self, service):
        """Test saving user queries."""
        query_params = {
            'name': 'Test Query',
            'description': 'Test Description',
            'symbols': ['AAPL', 'GOOGL'],
            'asset_class': 'stock',
            'frequency': '1d',
            'date_range_type': 'relative',
            'date_range_value': '30d'
        }
        
        with patch('src.backend.services.historical_data_service.get_db_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            # Mock query ID return
            mock_query = Mock()
            mock_query.id = 123
            mock_session_instance.add.return_value = None
            
            result = await service.save_query(query_params)
            
            mock_session_instance.add.assert_called_once()
            mock_session_instance.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, service):
        """Test circuit breaker functionality."""
        # Simulate repeated failures
        service.schwab_client.get_stock_history.side_effect = Exception("API Error")
        
        # First few calls should fail and trigger circuit breaker
        for i in range(6):  # Threshold is 5
            with pytest.raises(Exception):
                await service._fetch_from_schwab(
                    None, 'AAPL', 'stock', '1d',
                    datetime(2024, 1, 1), datetime(2024, 1, 2)
                )
        
        # Circuit should now be open
        assert service.circuit_breaker.is_open()
    
    def test_frequency_hierarchy(self, service):
        """Test frequency hierarchy validation."""
        assert service.frequency_hierarchy['1m'] == 1
        assert service.frequency_hierarchy['5m'] == 5
        assert service.frequency_hierarchy['1h'] == 60
        assert service.frequency_hierarchy['1d'] == 1440
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, service):
        """Test cache expiration functionality."""
        # Set data in cache
        cache_key = "test_key"
        test_data = {"test": "data"}
        await service._set_cached_data(cache_key, test_data)
        
        # Should be available immediately
        result = await service._get_cached_data(cache_key)
        assert result == test_data
        
        # Manually expire cache by setting old timestamp
        service._cache_timestamps[cache_key] = datetime.utcnow() - timedelta(seconds=400)
        
        # Should be None (expired)
        result = await service._get_cached_data(cache_key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_data(self, service):
        """Test error handling for missing required data."""
        with pytest.raises(ValueError, match="Schwab client not initialized"):
            service.schwab_client = None
            await service._fetch_missing_data(None, [], 'stock')
    
    @pytest.mark.asyncio
    async def test_futures_continuous_series(self, service):
        """Test futures continuous series handling."""
        # This would test the futures-specific logic
        # Implementation depends on futures data structure
        pass

# Performance Tests
class TestHistoricalDataPerformance:
    """Performance tests for historical data operations."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_aggregation_performance(self):
        """Test aggregation performance with large datasets."""
        service = HistoricalDataService()
        
        # Create large dataset (simulating 1 day of 1-minute data)
        large_dataset = []
        base_time = datetime(2024, 1, 1, 9, 30)
        
        for i in range(390):  # 6.5 hours * 60 minutes
            bar = MarketDataBar(
                symbol='AAPL',
                asset_class='stock', 
                timestamp=base_time + timedelta(minutes=i),
                frequency='1m',
                open_price=150.0 + (i % 100) * 0.01,
                high_price=150.1 + (i % 100) * 0.01,
                low_price=149.9 + (i % 100) * 0.01, 
                close_price=150.0 + ((i + 1) % 100) * 0.01,
                volume=1000 + i
            )
            large_dataset.append(bar)
        
        # Time the aggregation
        start_time = time.time()
        result = await service._aggregate_data(None, large_dataset, '1h')
        end_time = time.time()
        
        # Should complete within reasonable time (<100ms for 390 bars)
        assert (end_time - start_time) < 0.1
        assert len(result) == 7  # 6.5 hours -> 7 hourly bars
    
    @pytest.mark.asyncio
    async def test_concurrent_fetch_performance(self):
        """Test concurrent data fetching performance."""
        service = HistoricalDataService()
        service.schwab_client = AsyncMock()
        
        # Mock fast API responses
        service.schwab_client.get_stock_history.return_value = [
            {
                'datetime': '2024-01-01T09:30:00',
                'open': 150.0, 'high': 150.5, 'low': 149.5, 'close': 150.2,
                'volume': 1000
            }
        ]
        
        # Test concurrent fetches
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        start_time = time.time()
        tasks = [
            service.fetch_historical_data(
                symbols=[symbol],
                asset_class='stock',
                frequency='1d', 
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2)
            )
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Should complete all 5 fetches efficiently
        assert (end_time - start_time) < 2.0
        assert len([r for r in results if not isinstance(r, Exception)]) >= 4
```

#### API Integration Tests
```python
# src/tests/integration/test_historical_data_api.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date
from src.backend.main import create_app

@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)

class TestHistoricalDataAPI:
    """Integration tests for Historical Data API."""
    
    def test_fetch_historical_data_stocks(self, client):
        """Test fetching stock data."""
        request_data = {
            "symbols": ["AAPL"],
            "asset_class": "stock",
            "frequency": "1d",
            "date_range_type": "relative",
            "date_range_value": "5d"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert data["metadata"]["symbols_count"] == 1
        assert data["metadata"]["frequency"] == "1d"
    
    def test_fetch_multiple_symbols(self, client):
        """Test fetching data for multiple symbols."""
        request_data = {
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "asset_class": "stock", 
            "frequency": "1h",
            "date_range_type": "relative",
            "date_range_value": "1d"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["metadata"]["symbols_count"] == 3
        
        # Verify data contains all symbols
        symbols_in_data = set(bar["symbol"] for bar in data["data"])
        assert symbols_in_data == {"AAPL", "GOOGL", "MSFT"}
    
    def test_absolute_date_range(self, client):
        """Test absolute date range queries."""
        request_data = {
            "symbols": ["SPY"],
            "asset_class": "index",
            "frequency": "1d", 
            "date_range_type": "absolute",
            "start_date": "2024-01-01",
            "end_date": "2024-01-05"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        metadata = data["metadata"]
        assert "2024-01-01" in metadata["resolved_date_range"]["start_date"]
        assert "2024-01-05" in metadata["resolved_date_range"]["end_date"]
    
    def test_futures_continuous_series(self, client):
        """Test futures with continuous series."""
        request_data = {
            "symbols": ["/ES"],
            "asset_class": "future",
            "frequency": "1h",
            "date_range_type": "relative", 
            "date_range_value": "1d",
            "continuous_series": True,
            "roll_policy": "volume"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["metadata"]["symbols_count"] == 1
    
    def test_invalid_symbols_validation(self, client):
        """Test validation of invalid symbols."""
        request_data = {
            "symbols": [],  # Empty symbols list
            "asset_class": "stock",
            "frequency": "1d",
            "date_range_type": "relative",
            "date_range_value": "1d"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_frequency_validation(self, client):
        """Test validation of invalid frequency."""
        request_data = {
            "symbols": ["AAPL"],
            "asset_class": "stock",
            "frequency": "invalid",  # Invalid frequency
            "date_range_type": "relative",
            "date_range_value": "1d"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 422
    
    def test_get_supported_frequencies(self, client):
        """Test frequencies endpoint."""
        response = client.get("/api/v1/historical-data/frequencies")
        assert response.status_code == 200
        
        data = response.json()
        assert "frequencies" in data
        assert "asset_classes" in data
        assert "date_range_presets" in data
        
        # Verify expected frequencies are present
        freq_values = [f["value"] for f in data["frequencies"]]
        assert "1m" in freq_values
        assert "1d" in freq_values
        assert "1w" in freq_values
    
    def test_save_query(self, client):
        """Test saving a query."""
        request_data = {
            "name": "Test Query",
            "description": "Test query for integration testing",
            "query_params": {
                "symbols": ["AAPL"],
                "asset_class": "stock",
                "frequency": "1d",
                "date_range_type": "relative", 
                "date_range_value": "30d"
            }
        }
        
        response = client.post("/api/v1/historical-data/queries/save", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "query_id" in data
        assert data["message"] == "Query saved successfully"
    
    def test_get_saved_queries(self, client):
        """Test retrieving saved queries.""" 
        response = client.get("/api/v1/historical-data/queries")
        assert response.status_code == 200
        
        data = response.json()
        assert "queries" in data
        assert "count" in data
    
    def test_rate_limiting_behavior(self, client):
        """Test API behavior under load."""
        # Make multiple concurrent requests
        request_data = {
            "symbols": ["AAPL"],
            "asset_class": "stock",
            "frequency": "1d",
            "date_range_type": "relative",
            "date_range_value": "1d"
        }
        
        responses = []
        for i in range(5):
            response = client.post("/api/v1/historical-data/fetch", json=request_data)
            responses.append(response)
        
        # All requests should succeed (with caching)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 4  # Allow for 1 potential failure
    
    def test_error_handling_invalid_dates(self, client):
        """Test error handling for invalid date ranges."""
        request_data = {
            "symbols": ["AAPL"],
            "asset_class": "stock", 
            "frequency": "1d",
            "date_range_type": "absolute",
            "start_date": "2024-01-05",  # End before start
            "end_date": "2024-01-01"
        }
        
        response = client.post("/api/v1/historical-data/fetch", json=request_data)
        assert response.status_code == 422  # Validation error
```

#### Frontend Component Tests
```typescript
// src/frontend/src/components/__tests__/HistoricalDataPage.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HistoricalDataPage from '../HistoricalData/HistoricalDataPage';
import { WebSocketProvider } from '../../context/WebSocketContext';
import { apiClient } from '../../services/apiClient';

// Mock API client
jest.mock('../../services/apiClient');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

const MockWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <WebSocketProvider>
      {children}
    </WebSocketProvider>
  </BrowserRouter>
);

describe('HistoricalDataPage', () => {
  beforeEach(() => {
    mockApiClient.post.mockReset();
    mockApiClient.get.mockReset();
  });

  it('renders without crashing', () => {
    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );
    
    expect(screen.getByText('Historical Market Data')).toBeInTheDocument();
    expect(screen.getByText('New Query')).toBeInTheDocument();
    expect(screen.getByText('Saved Queries')).toBeInTheDocument();
  });

  it('loads supported frequencies on mount', async () => {
    const mockFrequencies = {
      frequencies: [
        { value: '1m', label: '1 Minute', intraday: true },
        { value: '1d', label: '1 Day', intraday: false }
      ]
    };

    mockApiClient.get.mockResolvedValue({ data: mockFrequencies });

    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    await waitFor(() => {
      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/historical-data/frequencies');
    });
  });

  it('submits query and displays results', async () => {
    const mockQueryResult = {
      data: [
        {
          symbol: 'AAPL',
          timestamp: '2024-01-01T09:30:00',
          open_price: 150.0,
          high_price: 150.5,
          low_price: 149.5,
          close_price: 150.2,
          volume: 1000
        }
      ],
      metadata: {
        bars_count: 1,
        symbols_count: 1,
        frequency: '1d',
        resolved_date_range: {
          start_date: '2024-01-01T00:00:00',
          end_date: '2024-01-02T00:00:00'
        }
      }
    };

    mockApiClient.post.mockResolvedValue({ data: mockQueryResult });

    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    // Fill in form
    const symbolInput = screen.getByPlaceholderText(/AAPL, GOOGL, SPY/);
    fireEvent.change(symbolInput, { target: { value: 'AAPL' } });

    const submitButton = screen.getByText('Preview Data');
    fireEvent.click(submitButton);

    // Wait for results
    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/v1/historical-data/fetch',
        expect.objectContaining({
          symbols: ['AAPL']
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Query Results')).toBeInTheDocument();
      expect(screen.getByText('Bars: 1')).toBeInTheDocument();
    });
  });

  it('handles form validation errors', async () => {
    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    // Try to submit without symbols
    const submitButton = screen.getByText('Preview Data');
    fireEvent.click(submitButton);

    // Should show validation message
    await waitFor(() => {
      expect(screen.getByText(/Please enter at least one symbol/)).toBeInTheDocument();
    });
  });

  it('switches between table and chart views', async () => {
    const mockQueryResult = {
      data: [
        {
          symbol: 'AAPL',
          timestamp: '2024-01-01T09:30:00',
          open_price: 150.0,
          high_price: 150.5,
          low_price: 149.5,
          close_price: 150.2,
          volume: 1000
        }
      ],
      metadata: {
        bars_count: 1,
        symbols_count: 1,
        frequency: '1d'
      }
    };

    mockApiClient.post.mockResolvedValue({ data: mockQueryResult });

    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    // Submit query first
    const symbolInput = screen.getByPlaceholderText(/AAPL, GOOGL, SPY/);
    fireEvent.change(symbolInput, { target: { value: 'AAPL' } });

    const submitButton = screen.getByText('Preview Data');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Query Results')).toBeInTheDocument();
    });

    // Should start with table view
    expect(screen.getByRole('table')).toBeInTheDocument();

    // Switch to chart view
    const chartButton = screen.getByText('Chart');
    fireEvent.click(chartButton);

    // Chart canvas should be present
    expect(screen.getByRole('img')).toBeInTheDocument(); // Chart.js canvas has img role
  });

  it('saves queries successfully', async () => {
    mockApiClient.post
      .mockResolvedValueOnce({ data: { data: [], metadata: {} } }) // Query result
      .mockResolvedValueOnce({ data: { query_id: 123 } }); // Save result

    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    // Submit a query first
    const symbolInput = screen.getByPlaceholderText(/AAPL, GOOGL, SPY/);
    fireEvent.change(symbolInput, { target: { value: 'AAPL' } });

    const submitButton = screen.getByText('Preview Data');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Save Query')).toBeInTheDocument();
    });

    // Click save button
    const saveButton = screen.getByText('Save Query');
    fireEvent.click(saveButton);

    // Fill in save modal
    const nameInput = screen.getByPlaceholderText('Enter query name');
    fireEvent.change(nameInput, { target: { value: 'Test Query' } });

    const saveFinalButton = screen.getByRole('button', { name: 'Save' });
    fireEvent.click(saveFinalButton);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/v1/historical-data/queries/save',
        expect.objectContaining({
          name: 'Test Query'
        })
      );
    });
  });

  it('handles API errors gracefully', async () => {
    mockApiClient.post.mockRejectedValue(new Error('Network error'));

    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    const symbolInput = screen.getByPlaceholderText(/AAPL, GOOGL, SPY/);
    fireEvent.change(symbolInput, { target: { value: 'AAPL' } });

    const submitButton = screen.getByText('Preview Data');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it('displays loading states correctly', async () => {
    // Create a promise that we can resolve manually
    let resolvePromise: (value: any) => void;
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockApiClient.post.mockReturnValue(mockPromise);

    render(
      <MockWrapper>
        <HistoricalDataPage />
      </MockWrapper>
    );

    const symbolInput = screen.getByPlaceholderText(/AAPL, GOOGL, SPY/);
    fireEvent.change(symbolInput, { target: { value: 'AAPL' } });

    const submitButton = screen.getByText('Preview Data');
    fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Resolve the promise
    resolvePromise!({ data: { data: [], metadata: {} } });

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });
});
```

### 6. Configuration and Environment Setup

#### Environment Variables
```python
# src/backend/config.py - Add Historical Data settings
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Historical Data Extension Settings
    HISTORICAL_DATA_ENABLED: bool = Field(
        default=True,
        description="Enable historical data extension"
    )
    HISTORICAL_DATA_CACHE_TTL: int = Field(
        default=300,
        description="Cache TTL in seconds for historical data"
    )
    HISTORICAL_DATA_MAX_SYMBOLS: int = Field(
        default=50,
        description="Maximum symbols per request"
    )
    HISTORICAL_DATA_MAX_DAYS: int = Field(
        default=730,
        description="Maximum days in single request (2 years)"
    )
    HISTORICAL_DATA_DEFAULT_FREQUENCY: str = Field(
        default="1d",
        description="Default frequency for historical data queries"
    )
    
    # Schwab API Configuration  
    SCHWAB_API_TIMEOUT: int = Field(
        default=30,
        description="Timeout for Schwab API requests"
    )
    SCHWAB_API_RATE_LIMIT: int = Field(
        default=120,
        description="Rate limit per minute for Schwab API"
    )
    
    # Data Storage Configuration
    HISTORICAL_DATA_RETENTION_DAYS: int = Field(
        default=1095,  # 3 years
        description="Days to retain historical data"
    )
    HISTORICAL_DATA_CLEANUP_INTERVAL: int = Field(
        default=86400,  # 24 hours
        description="Interval in seconds for data cleanup tasks"
    )
```

#### Frontend Environment Configuration
```typescript
// src/frontend/.env additions
REACT_APP_HISTORICAL_DATA_ENABLED=true
REACT_APP_MAX_SYMBOLS_PER_QUERY=50
REACT_APP_MAX_CHART_POINTS=1000
REACT_APP_DEFAULT_DATE_RANGE=30d
REACT_APP_CACHE_ENABLED=true
```

## Complete Implementation Roadmap

### Phase 1: Foundation Setup (Days 1-2)
**Objective**: Establish core infrastructure and database schema

#### Database Layer Implementation
1. **Create Database Models** (`src/backend/models/historical_data.py`)
   - Implement `MarketDataBar` model with full OHLCV structure
   - Implement `DataSource` model for provider tracking
   - Implement `DataQuery` model for saved queries
   - Add proper indexes and constraints for performance
   - Create timestamp mixins and validation

2. **Database Migration**
   - Generate Alembic migration for new tables
   - Add performance indexes for time-series queries
   - Test migration rollback capabilities
   - Validate foreign key relationships

3. **Database Connection Integration**
   - Update connection pool settings for increased load
   - Add query timeout configurations
   - Implement connection monitoring

#### Testing Foundation
1. **Unit Test Structure**
   - Create test database fixtures
   - Implement model validation tests
   - Create mock data generators
   - Set up performance benchmarks

### Phase 2: Core Service Layer (Days 3-5)
**Objective**: Build robust data retrieval and processing services

#### Historical Data Service Implementation  
1. **Service Class Structure** (`src/backend/services/historical_data_service.py`)
   - Implement service lifecycle management (start/stop)
   - Create cache management system with TTL
   - Implement circuit breaker integration
   - Add background maintenance tasks

2. **Data Fetching Logic**
   - Build Schwab API integration layer
   - Implement data normalization and validation
   - Create batch processing for multiple symbols
   - Add error handling and retry logic
   - Implement rate limiting compliance

3. **Data Storage Optimization**
   - Implement efficient bulk insert operations
   - Create data deduplication logic
   - Add data integrity validation
   - Implement gap detection and filling

#### Data Aggregation Service
1. **Aggregation Engine** (`src/backend/services/data_aggregation_service.py`)
   - Implement OHLC aggregation rules
   - Create time bucket calculation logic
   - Add frequency conversion functions
   - Implement deterministic aggregation algorithms

2. **Performance Optimization**
   - Add streaming aggregation for large datasets
   - Implement memory-efficient processing
   - Create parallel processing for multiple symbols
   - Add caching for frequently requested aggregations

#### Testing Implementation
1. **Service Layer Tests**
   - Unit tests for all service methods
   - Mock external API interactions
   - Performance tests for aggregation logic
   - Concurrency testing for parallel processing
   - Cache behavior validation tests

### Phase 3: API Layer Development (Days 6-7)
**Objective**: Create comprehensive API endpoints with proper validation

#### API Router Implementation
1. **Core Endpoints** (`src/backend/api/historical_data.py`)
   - Implement `/fetch` endpoint with comprehensive validation
   - Create `/frequencies` endpoint for supported options
   - Build query saving/loading endpoints
   - Add metadata and status endpoints

2. **Request/Response Models**
   - Create Pydantic models for all request types
   - Implement comprehensive validation rules
   - Add proper error response structures
   - Create response metadata standards

3. **Integration with Main Application**
   - Register router in main.py
   - Add service dependency injection
   - Implement middleware integration
   - Add proper CORS configuration

#### API Testing
1. **Integration Tests**
   - Test all endpoints with various parameter combinations
   - Validate error handling scenarios
   - Test rate limiting behavior
   - Validate response formats and schemas

### Phase 4: Frontend Implementation (Days 8-10)
**Objective**: Build intuitive user interface for historical data queries

#### Core Components Development
1. **Main Page Component** (`src/frontend/src/components/HistoricalData/`)
   - Implement `HistoricalDataPage` with tab navigation
   - Create responsive layout structure
   - Add WebSocket integration for real-time status
   - Implement error boundary patterns

2. **Query Form Component**
   - Build comprehensive form with all parameter options
   - Implement dynamic validation and user feedback
   - Add symbol auto-completion functionality
   - Create date range picker with presets

3. **Data Preview Component**
   - Implement table view with sorting and pagination
   - Build Chart.js integration for visualizations
   - Add export functionality for data
   - Create save query modal interface

#### Advanced Frontend Features
1. **Saved Queries Management**
   - Build query list component with search/filter
   - Implement query execution and modification
   - Add query sharing and export functionality
   - Create query performance analytics

2. **Real-time Integration**
   - Integrate with existing WebSocket system
   - Add real-time query status updates
   - Implement progress indicators for long queries
   - Create notification system for query completion

#### Frontend Testing
1. **Component Tests**
   - Unit tests for all React components
   - Integration tests for user workflows
   - Mock API interactions comprehensively
   - Test error handling and edge cases

### Phase 5: System Integration (Days 11-12)
**Objective**: Integrate extension with existing TradeAssist systems

#### Service Registration and Lifecycle
1. **Main Application Integration**
   - Register service in lifespan manager
   - Add proper startup/shutdown sequences
   - Integrate with existing monitoring systems
   - Add health check endpoints

2. **WebSocket Integration**
   - Extend message types for historical data updates
   - Add broadcast capability for query status
   - Integrate with existing real-time data flows
   - Create subscription management for updates

#### Charts and Indicators Integration
1. **Charts Module Integration**
   - Create data adapters for existing chart components
   - Add historical data source options
   - Implement chart timeframe synchronization
   - Add comparative analysis capabilities

2. **Future Indicators Integration**
   - Design data export interfaces for indicator calculations
   - Create standardized data format specifications
   - Add caching layer for indicator input data
   - Plan integration points for future technical analysis

#### Configuration Integration
1. **Settings Integration**
   - Add historical data settings to config system
   - Create user preference management
   - Implement feature flags for extension components
   - Add environment-specific configurations

### Phase 6: Performance Optimization (Days 13-14)
**Objective**: Optimize system performance for production workloads

#### Database Performance
1. **Query Optimization**
   - Analyze and optimize database query patterns
   - Add additional indexes based on usage patterns
   - Implement connection pooling optimizations
   - Add query result caching strategies

2. **Storage Efficiency**
   - Implement data compression strategies
   - Add automated cleanup processes
   - Optimize storage for time-series data patterns
   - Create archival strategies for old data

#### Service Performance  
1. **Caching Strategy**
   - Implement multi-layer caching (memory, disk, distributed)
   - Add cache warming strategies
   - Create cache invalidation patterns
   - Optimize cache hit ratios

2. **Processing Optimization**
   - Add parallel processing for multiple symbol queries
   - Implement streaming for large dataset operations
   - Optimize memory usage for aggregation operations
   - Add CPU profiling and optimization

#### Frontend Performance
1. **Loading Optimization**
   - Implement progressive loading for large datasets
   - Add virtualization for large data tables
   - Optimize chart rendering performance
   - Create efficient data pagination strategies

### Phase 7: Testing and Quality Assurance (Days 15-16)
**Objective**: Comprehensive testing and quality validation

#### Comprehensive Test Suite
1. **Backend Testing**
   - Complete unit test coverage (>90%)
   - Integration test coverage for all API endpoints
   - Performance testing with realistic data volumes
   - Load testing for concurrent user scenarios
   - Error handling and edge case validation

2. **Frontend Testing**
   - Component unit tests with full coverage
   - User interaction testing scenarios
   - Cross-browser compatibility testing
   - Mobile responsiveness validation
   - Accessibility compliance testing

#### End-to-End Testing
1. **Full Workflow Testing**
   - Complete user journey testing
   - Multi-symbol query scenarios
   - Large date range handling
   - Error recovery scenarios
   - Performance under load scenarios

2. **Integration Validation**
   - Test with existing TradeAssist features
   - Validate WebSocket message flows
   - Test service startup/shutdown sequences
   - Validate configuration management

### Phase 8: Documentation and Deployment (Days 17-18)
**Objective**: Complete documentation and production deployment preparation

#### Documentation Creation
1. **API Documentation**
   - Complete OpenAPI/Swagger documentation
   - Add example requests and responses
   - Create integration guides for other systems
   - Document error codes and handling

2. **User Documentation**
   - Update USER_GUIDE.md with historical data features
   - Create feature walkthrough guides
   - Add troubleshooting documentation
   - Create FAQ section for common questions

3. **Developer Documentation**
   - Update technical architecture documentation
   - Document extension patterns for future development
   - Create maintenance and operational guides
   - Add performance tuning recommendations

#### Deployment Preparation
1. **Configuration Management**
   - Update .env.example with new configuration options
   - Create environment-specific configuration guides
   - Add deployment verification scripts
   - Update DEPLOYMENT.md with new requirements

2. **Monitoring Integration**
   - Add application metrics for historical data operations
   - Create alerting rules for performance and errors
   - Add logging enhancements for troubleshooting
   - Create operational runbooks

### Phase 9: Production Validation (Days 19-20)
**Objective**: Final validation and production readiness verification

#### Production Testing
1. **Staging Environment Validation**
   - Deploy to staging environment
   - Execute full regression test suite
   - Performance testing with production data volumes
   - Load testing with expected concurrent users
   - Failover and recovery scenario testing

2. **User Acceptance Testing**
   - Conduct user workflow validation
   - Validate against original BRD requirements
   - Performance validation against success criteria
   - Collect user feedback and address issues

#### Final Preparation
1. **Production Deployment**
   - Create deployment runbook and rollback procedures
   - Prepare monitoring and alerting configurations
   - Schedule production deployment window
   - Create post-deployment validation checklist

2. **Knowledge Transfer**
   - Conduct technical handoff sessions
   - Create operational procedures documentation
   - Train support staff on new features
   - Document known issues and workarounds

## Implementation Success Criteria

### Functional Success Criteria
- [ ] **Complete Data Retrieval**: Users can fetch historical OHLCV data for stocks, indexes, and futures
- [ ] **Flexible Parameters**: Support for all specified frequencies, date ranges, and symbol selections
- [ ] **Data Integrity**: Gap-free data for valid trading sessions with proper validation
- [ ] **Aggregation Accuracy**: Higher timeframe data matches deterministic aggregation of base data
- [ ] **UI Integration**: Intuitive interface with preview, chart visualization, and query management
- [ ] **Futures Support**: Continuous series with roll adjustments and metadata
- [ ] **Query Management**: Save, load, and manage user queries effectively
- [ ] **System Integration**: Seamless integration with existing charts and future indicators modules

### Technical Success Criteria  
- [ ] **Performance**: Sub-200ms API response times for typical queries
- [ ] **Scalability**: Handle 50+ concurrent users without performance degradation
- [ ] **Reliability**: 99.9% uptime with proper error handling and recovery
- [ ] **Compatibility**: Zero breaking changes to existing TradeAssist functionality
- [ ] **Security**: Proper input validation, authentication integration, and secure data handling
- [ ] **Code Quality**: 90%+ test coverage with comprehensive unit and integration tests
- [ ] **Documentation**: Complete API documentation and user guides
- [ ] **Monitoring**: Full observability with metrics, logging, and alerting

### User Experience Success Criteria
- [ ] **Intuitive Interface**: Users can create queries without training
- [ ] **Fast Loading**: Data preview loads within 3 seconds for typical queries
- [ ] **Clear Feedback**: Appropriate loading states, error messages, and user guidance
- [ ] **Mobile Responsive**: Full functionality on tablet and mobile devices
- [ ] **Accessibility**: WCAG 2.1 AA compliance for accessibility standards
- [ ] **Integration Consistency**: UI follows existing TradeAssist design patterns

## Backward Compatibility Strategy

### API Compatibility
- **Maintain Existing Endpoints**: No changes to current API structure or responses
- **Additive Changes Only**: New endpoints follow `/api/v1/historical-data/` pattern
- **Configuration Compatibility**: New settings have sensible defaults
- **Database Schema**: Only additive changes, no modifications to existing tables

### Frontend Compatibility  
- **Component Isolation**: New components in dedicated directory structure
- **Route Addition**: New routes without modifying existing navigation
- **Context Preservation**: Maintain existing WebSocket context structure
- **Styling Consistency**: Use existing CSS classes and design tokens

### Service Integration
- **Dependency Injection**: New services integrate through existing lifespan manager
- **Message Compatibility**: WebSocket messages use existing protocol extensions
- **Error Handling**: Follow existing error response patterns and structures
- **Logging Integration**: Use existing structlog configuration and formats

## Risk Mitigation Strategy

### Technical Risks
1. **External API Reliability**: Implement circuit breaker and retry logic
2. **Database Performance**: Add comprehensive indexing and query optimization
3. **Memory Usage**: Implement streaming and pagination for large datasets
4. **Concurrency Issues**: Use proper async patterns and connection pooling

### Business Risks  
1. **Data Accuracy**: Implement comprehensive validation and testing
2. **Performance Impact**: Isolate new functionality with feature flags
3. **User Adoption**: Create intuitive UI with comprehensive documentation
4. **Maintenance Overhead**: Follow existing patterns and create comprehensive tests

### Operational Risks
1. **Deployment Complexity**: Use staged deployment with rollback capabilities
2. **Monitoring Gaps**: Implement comprehensive metrics and alerting
3. **Support Burden**: Create detailed documentation and troubleshooting guides
4. **Configuration Errors**: Provide clear configuration examples and validation

## Completion Validation

### Pre-Deployment Checklist
- [ ] All functional requirements implemented and tested
- [ ] Performance benchmarks met in staging environment
- [ ] Security review completed and issues addressed
- [ ] Documentation updated and reviewed
- [ ] User acceptance testing completed successfully
- [ ] Rollback procedures tested and validated
- [ ] Monitoring and alerting configured
- [ ] Support team trained and ready

### Post-Deployment Validation
- [ ] All endpoints responding correctly in production
- [ ] Performance metrics within expected ranges
- [ ] Error rates below acceptable thresholds
- [ ] User workflows functioning as expected
- [ ] Integration with existing features working
- [ ] Real-time features operating correctly
- [ ] Data accuracy validated with spot checks

This comprehensive extension PRP provides complete technical architecture, implementation roadmap, and success criteria for building the Historical Data Foundation extension. The implementation follows TradeAssist patterns while adding powerful historical data capabilities that integrate seamlessly with the existing system.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Read and analyze the Extension BRD file", "status": "completed", "activeForm": "Reading and analyzing the Extension BRD file"}, {"content": "Load shared codebase analysis and integration points", "status": "completed", "activeForm": "Loading shared codebase analysis and integration points"}, {"content": "Load extension PRP base template", "status": "completed", "activeForm": "Loading extension PRP base template"}, {"content": "Generate comprehensive technical architecture", "status": "completed", "activeForm": "Generating comprehensive technical architecture"}, {"content": "Create complete implementation roadmap", "status": "in_progress", "activeForm": "Creating complete implementation roadmap"}, {"content": "Generate timestamped comprehensive PRP file", "status": "pending", "activeForm": "Generating timestamped comprehensive PRP file"}, {"content": "Create extension directory structure and config", "status": "pending", "activeForm": "Creating extension directory structure and config"}]