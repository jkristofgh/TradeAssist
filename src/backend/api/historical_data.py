"""
Historical Data API endpoints.

REST API endpoints for historical market data retrieval,
query management, and data source information.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator
import structlog

from ..services.historical_data_service import (
    HistoricalDataService,
    HistoricalDataRequest,
    HistoricalDataResult,
    AggregationRequest
)
from ..models.historical_data import DataFrequency
from ..database.connection import get_db_session

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/historical-data", tags=["historical-data"])

# Global service instance (will be set by main.py)
historical_data_service: Optional[HistoricalDataService] = None


def get_historical_data_service() -> HistoricalDataService:
    """
    Dependency to get historical data service instance.
    
    Returns:
        HistoricalDataService: Service instance
        
    Raises:
        HTTPException: If service not initialized
    """
    if not historical_data_service:
        raise HTTPException(
            status_code=503,
            detail="Historical data service not initialized"
        )
    return historical_data_service


# Pydantic models for request/response

class HistoricalDataFetchRequest(BaseModel):
    """Request model for historical data fetch."""
    
    symbols: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of trading symbols (e.g., ['AAPL', '/ES', 'SPY'])"
    )
    
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for historical data (ISO format)"
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="End date for historical data (ISO format)"
    )
    
    frequency: str = Field(
        default=DataFrequency.DAILY.value,
        description="Data frequency (1min, 5min, 1h, 1d, etc.)"
    )
    
    include_extended_hours: bool = Field(
        default=False,
        description="Include extended hours trading data"
    )
    
    max_records: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Maximum number of records per symbol"
    )
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbols list."""
        if not v:
            raise ValueError("At least one symbol is required")
        
        # Clean and validate symbols
        cleaned = []
        for symbol in v:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            if len(symbol) > 50:
                raise ValueError(f"Symbol too long: {symbol}")
            cleaned.append(symbol)
        
        if not cleaned:
            raise ValueError("No valid symbols provided")
        
        return cleaned
    
    @validator('frequency')
    def validate_frequency(cls, v):
        """Validate frequency value."""
        try:
            DataFrequency(v)
        except ValueError:
            valid_frequencies = [f.value for f in DataFrequency]
            raise ValueError(
                f"Invalid frequency '{v}'. "
                f"Valid options: {', '.join(valid_frequencies)}"
            )
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError("End date must be after start date")
        return v


class HistoricalDataBar(BaseModel):
    """Single bar of historical data."""
    
    timestamp: datetime
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(default=0, ge=0, description="Trading volume")
    open_interest: Optional[int] = Field(None, ge=0, description="Open interest (futures)")


class HistoricalDataResponse(BaseModel):
    """Response model for historical data."""
    
    symbol: str
    frequency: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_bars: int
    data_source: str
    cached: bool
    bars: List[HistoricalDataBar]


class HistoricalDataFetchResponse(BaseModel):
    """Response model for fetch operation."""
    
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_symbols: int
    data: List[HistoricalDataResponse]


class DataSourceInfo(BaseModel):
    """Data source information."""
    
    name: str
    provider_type: str
    is_active: bool
    rate_limit_per_minute: int
    supported_frequencies: List[str]


class DataSourcesResponse(BaseModel):
    """Response model for data sources."""
    
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: List[DataSourceInfo]


class QuerySaveRequest(BaseModel):
    """Request model for saving queries."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Query name")
    description: Optional[str] = Field(None, max_length=500, description="Query description")
    symbols: List[str] = Field(..., min_items=1, description="List of symbols")
    frequency: str = Field(default=DataFrequency.DAILY.value, description="Data frequency")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    is_favorite: bool = Field(default=False, description="Mark as favorite")


class QuerySaveResponse(BaseModel):
    """Response model for query save operation."""
    
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query_id: int


class QueryLoadResponse(BaseModel):
    """Response model for query load operation."""
    
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query: Optional[Dict[str, Any]] = None


class ServiceStatsResponse(BaseModel):
    """Response model for service statistics."""
    
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stats: Dict[str, Any]


# API Endpoints

@router.post("/fetch", response_model=HistoricalDataFetchResponse)
async def fetch_historical_data(
    request: HistoricalDataFetchRequest,
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> HistoricalDataFetchResponse:
    """
    Fetch historical market data for specified symbols and parameters.
    
    Retrieves historical OHLCV data with caching and performance optimization.
    Supports multiple symbols, flexible date ranges, and various frequencies.
    
    Args:
        request: Historical data fetch parameters
        
    Returns:
        HistoricalDataFetchResponse: Retrieved historical data
        
    Raises:
        HTTPException: If request validation fails or data retrieval errors occur
    """
    logger.info(
        f"Historical data fetch requested for {len(request.symbols)} symbols",
        symbols=request.symbols,
        frequency=request.frequency
    )
    
    try:
        # Create service request
        service_request = HistoricalDataRequest(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            include_extended_hours=request.include_extended_hours,
            max_records=request.max_records
        )
        
        # Fetch data from service
        results = await service.fetch_historical_data(service_request)
        
        # Convert to response format
        data_responses = []
        for result in results:
            bars = [
                HistoricalDataBar(
                    timestamp=bar["timestamp"],
                    open=bar["open"],
                    high=bar["high"],
                    low=bar["low"],
                    close=bar["close"],
                    volume=bar.get("volume", 0),
                    open_interest=bar.get("open_interest")
                )
                for bar in result.bars
            ]
            
            data_responses.append(
                HistoricalDataResponse(
                    symbol=result.symbol,
                    frequency=result.frequency,
                    start_date=result.start_date,
                    end_date=result.end_date,
                    total_bars=result.total_bars,
                    data_source=result.data_source,
                    cached=result.cached,
                    bars=bars
                )
            )
        
        response = HistoricalDataFetchResponse(
            success=True,
            message=f"Retrieved historical data for {len(results)} symbols",
            total_symbols=len(results),
            data=data_responses
        )
        
        logger.info(f"Historical data fetch completed: {len(results)} symbols")
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Historical data fetch failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical data: {str(e)}"
        )


@router.get("/frequencies", response_model=List[str])
async def get_supported_frequencies() -> List[str]:
    """
    Get list of supported data frequencies.
    
    Returns:
        List[str]: Available frequency options (1min, 5min, 1h, 1d, etc.)
    """
    return [frequency.value for frequency in DataFrequency]


@router.get("/sources", response_model=DataSourcesResponse)
async def get_data_sources() -> DataSourcesResponse:
    """
    Get information about available data sources.
    
    Returns:
        DataSourcesResponse: List of configured data sources with capabilities
    """
    try:
        # For now, return static information
        # In production, this would query the database
        sources = [
            DataSourceInfo(
                name="Schwab",
                provider_type="schwab_api",
                is_active=True,
                rate_limit_per_minute=120,
                supported_frequencies=[f.value for f in DataFrequency]
            ),
            DataSourceInfo(
                name="Demo",
                provider_type="mock_data",
                is_active=True,
                rate_limit_per_minute=1000,
                supported_frequencies=[f.value for f in DataFrequency]
            )
        ]
        
        return DataSourcesResponse(
            success=True,
            message=f"Retrieved {len(sources)} data sources",
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Failed to get data sources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve data sources: {str(e)}"
        )


@router.post("/queries/save", response_model=QuerySaveResponse)
async def save_query(
    request: QuerySaveRequest,
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> QuerySaveResponse:
    """
    Save a query configuration for reuse.
    
    Allows users to save frequently used query parameters
    for easy reuse and sharing.
    
    Args:
        request: Query save parameters
        
    Returns:
        QuerySaveResponse: Save operation result with query ID
    """
    logger.info(f"Saving query: {request.name}")
    
    try:
        query_id = await service.save_query(
            name=request.name,
            description=request.description or "",
            symbols=request.symbols,
            frequency=request.frequency,
            start_date=request.start_date,
            end_date=request.end_date,
            filters=request.filters,
            is_favorite=request.is_favorite
        )
        
        return QuerySaveResponse(
            success=True,
            message=f"Query '{request.name}' saved successfully",
            query_id=query_id
        )
        
    except Exception as e:
        logger.error(f"Failed to save query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save query: {str(e)}"
        )


@router.get("/queries/{query_id}", response_model=QueryLoadResponse)
async def load_query(
    query_id: int,
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> QueryLoadResponse:
    """
    Load a saved query configuration.
    
    Args:
        query_id: ID of the query to load
        
    Returns:
        QueryLoadResponse: Loaded query configuration
    """
    logger.info(f"Loading query: {query_id}")
    
    try:
        query_data = await service.load_query(query_id)
        
        if not query_data:
            raise HTTPException(
                status_code=404,
                detail=f"Query {query_id} not found"
            )
        
        return QueryLoadResponse(
            success=True,
            message=f"Query {query_id} loaded successfully",
            query=query_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load query {query_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load query: {str(e)}"
        )


@router.get("/stats", response_model=ServiceStatsResponse)
async def get_service_statistics(
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> ServiceStatsResponse:
    """
    Get historical data service performance statistics.
    
    Returns:
        ServiceStatsResponse: Service performance metrics and statistics
    """
    try:
        stats = service.get_performance_stats()
        
        return ServiceStatsResponse(
            success=True,
            message="Service statistics retrieved successfully",
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get service statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# Health check endpoint for the historical data system
@router.get("/health")
async def health_check(
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> Dict[str, Any]:
    """
    Health check for historical data service.
    
    Returns:
        Dict: Health status and basic metrics
    """
    try:
        stats = service.get_performance_stats()
        
        health_status = {
            "status": "healthy" if stats["service_running"] else "unhealthy",
            "service_running": stats["service_running"],
            "schwab_client_connected": stats["schwab_client_connected"],
            "cache_size": stats["cache_size"],
            "total_requests": stats["requests_served"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def set_historical_data_service(service: HistoricalDataService) -> None:
    """
    Set the global historical data service instance.
    
    Called by main.py during application startup.
    
    Args:
        service: HistoricalDataService instance
    """
    global historical_data_service
    historical_data_service = service
    logger.info("Historical data service dependency configured")