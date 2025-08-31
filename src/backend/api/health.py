"""
Health check API endpoints.

Provides system health monitoring and status information
for operational visibility and monitoring.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ..database.connection import get_db_session
from ..models.instruments import Instrument
from ..models.market_data import MarketData

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall system status: healthy, degraded, or unhealthy")
    ingestion_active: bool = Field(..., description="Whether data ingestion is currently active")
    last_tick: Optional[datetime] = Field(None, description="Timestamp of last received market data")
    api_connected: bool = Field(..., description="Whether external API connection is active") 
    active_instruments: int = Field(..., description="Number of active trading instruments")
    total_rules: int = Field(..., description="Total number of alert rules configured")
    last_alert: Optional[datetime] = Field(None, description="Timestamp of last triggered alert")
    
    # Historical data service health
    historical_data_service: Optional[Dict[str, Any]] = Field(None, description="Historical data service health metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "ingestion_active": True,
                "last_tick": "2024-01-15T14:30:00Z",
                "api_connected": True,
                "active_instruments": 150,
                "total_rules": 25,
                "last_alert": "2024-01-15T14:28:15Z",
                "historical_data_service": {
                    "status": "healthy",
                    "service_running": True,
                    "schwab_client_connected": True,
                    "cache_size": 1250,
                    "total_requests": 1487,
                    "database_healthy": True,
                    "data_freshness_minutes": 5
                }
            }
        }


class SystemStats(BaseModel):
    """Detailed system statistics."""
    database_status: str
    total_instruments: int
    active_instruments: int
    total_rules: int
    active_rules: int
    total_ticks_today: int
    total_alerts_today: int
    avg_evaluation_time_ms: Optional[float] = None


@router.get(
    "/health", 
    response_model=HealthResponse,
    summary="Get System Health Status",
    description="""
    Get comprehensive health status of the TradeAssist system.
    
    **Includes:**
    - Real-time data ingestion status
    - External API connectivity status
    - Active instruments and alert rules count
    - Historical data service health metrics
    - Recent activity timestamps
    
    **Health Status Levels:**
    - **healthy**: All systems operational
    - **degraded**: Some issues detected but system functional
    - **unhealthy**: Critical issues requiring attention
    """,
    tags=["System Health"]
)
async def get_health_status() -> HealthResponse:
    """
    Get basic health status of the TradeAssist system.
    
    Returns system health including ingestion status, connectivity,
    and basic operational metrics for monitoring.
    
    Returns:
        HealthResponse: Current system health status.
    """
    try:
        # Get historical data service health
        historical_data_health = None
        try:
            from ..services.historical_data_service import HistoricalDataService
            from ..database.connection import get_db_session
            
            # Try to get service instance and health stats
            service = HistoricalDataService()
            stats = service.get_performance_stats()
            
            # Check database health for historical data
            async with get_db_session() as session:
                from ..models.historical_data import MarketDataBar
                recent_data_result = await session.execute(
                    select(func.max(MarketDataBar.timestamp))
                )
                last_historical_data = recent_data_result.scalar()
                
                data_freshness_minutes = None
                if last_historical_data:
                    data_freshness_minutes = int((datetime.utcnow() - last_historical_data).total_seconds() / 60)
            
            historical_data_health = {
                "status": "healthy" if stats["service_running"] and stats["schwab_client_connected"] else "degraded",
                "service_running": stats["service_running"],
                "schwab_client_connected": stats["schwab_client_connected"],
                "cache_size": stats["cache_size"],
                "total_requests": stats["requests_served"],
                "database_healthy": True,
                "data_freshness_minutes": data_freshness_minutes
            }
        except Exception as e:
            historical_data_health = {
                "status": "unhealthy",
                "service_running": False,
                "error": str(e)
            }
        
        async with get_db_session() as session:
            # Check database connectivity
            await session.execute(select(1))
            
            # Get active instruments count
            active_instruments_result = await session.execute(
                select(func.count(Instrument.id)).where(
                    Instrument.status == "active"
                )
            )
            active_instruments = active_instruments_result.scalar() or 0
            
            # Get total rules count
            from ..models.alert_rules import AlertRule
            total_rules_result = await session.execute(
                select(func.count(AlertRule.id))
            )
            total_rules = total_rules_result.scalar() or 0
            
            # Get last tick timestamp
            last_tick_result = await session.execute(
                select(func.max(MarketData.timestamp))
            )
            last_tick = last_tick_result.scalar()
            
            # Get last alert timestamp
            from ..models.alert_logs import AlertLog
            last_alert_result = await session.execute(
                select(func.max(AlertLog.timestamp))
            )
            last_alert = last_alert_result.scalar()
            
            # Determine ingestion status
            ingestion_active = False
            api_connected = False
            
            if last_tick:
                # Consider ingestion active if we received data in last 60 seconds
                time_diff = (datetime.utcnow() - last_tick).total_seconds()
                ingestion_active = time_diff < 60
                api_connected = time_diff < 300  # 5 minutes for API connection
            
            # Determine overall status
            overall_status = "healthy"
            if not api_connected:
                overall_status = "degraded"
            if historical_data_health and historical_data_health.get("status") == "unhealthy":
                overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
            
            return HealthResponse(
                status=overall_status,
                ingestion_active=ingestion_active,
                last_tick=last_tick,
                api_connected=api_connected,
                active_instruments=active_instruments,
                total_rules=total_rules,
                last_alert=last_alert,
                historical_data_service=historical_data_health
            )
            
    except Exception as e:
        # Return error status if health check fails
        return HealthResponse(
            status="unhealthy",
            ingestion_active=False,
            api_connected=False,
            active_instruments=0,
            total_rules=0,
            historical_data_service={"status": "unhealthy", "error": str(e)}
        )


@router.get(
    "/health/detailed", 
    response_model=SystemStats,
    summary="Get Detailed System Statistics",
    description="""
    Get comprehensive system statistics and performance metrics.
    
    **Detailed Metrics Include:**
    - Database connectivity and status
    - Instrument and rule counts (total vs active)
    - Today's activity metrics (ticks and alerts processed)
    - Performance metrics (average evaluation times)
    
    **Use Cases:**
    - System monitoring dashboards
    - Performance analysis and optimization
    - Capacity planning and scaling decisions
    - Operational troubleshooting and diagnostics
    """,
    tags=["System Health"]
)
async def get_detailed_system_stats() -> SystemStats:
    """
    Get detailed system statistics and performance metrics.
    
    Provides comprehensive system status including performance
    metrics for operational monitoring and optimization.
    
    Returns:
        SystemStats: Detailed system statistics.
    """
    async with get_db_session() as session:
        # Database status
        await session.execute(select(1))
        database_status = "connected"
        
        # Instrument counts
        total_instruments_result = await session.execute(
            select(func.count(Instrument.id))
        )
        total_instruments = total_instruments_result.scalar() or 0
        
        active_instruments_result = await session.execute(
            select(func.count(Instrument.id)).where(
                Instrument.status == "active"
            )
        )
        active_instruments = active_instruments_result.scalar() or 0
        
        # Rule counts
        from ..models.alert_rules import AlertRule
        total_rules_result = await session.execute(
            select(func.count(AlertRule.id))
        )
        total_rules = total_rules_result.scalar() or 0
        
        active_rules_result = await session.execute(
            select(func.count(AlertRule.id)).where(
                AlertRule.active == True
            )
        )
        active_rules = active_rules_result.scalar() or 0
        
        # Today's activity (UTC day boundary)
        today = datetime.utcnow().date()
        
        # Ticks today
        ticks_today_result = await session.execute(
            select(func.count(MarketData.id)).where(
                func.date(MarketData.timestamp) == today
            )
        )
        total_ticks_today = ticks_today_result.scalar() or 0
        
        # Alerts today
        from ..models.alert_logs import AlertLog
        alerts_today_result = await session.execute(
            select(func.count(AlertLog.id)).where(
                func.date(AlertLog.timestamp) == today
            )
        )
        total_alerts_today = alerts_today_result.scalar() or 0
        
        # Average evaluation time
        avg_eval_time_result = await session.execute(
            select(func.avg(AlertLog.evaluation_time_ms)).where(
                func.date(AlertLog.timestamp) == today,
                AlertLog.evaluation_time_ms.isnot(None)
            )
        )
        avg_evaluation_time_ms = avg_eval_time_result.scalar()
        
        return SystemStats(
            database_status=database_status,
            total_instruments=total_instruments,
            active_instruments=active_instruments,
            total_rules=total_rules,
            active_rules=active_rules,
            total_ticks_today=total_ticks_today,
            total_alerts_today=total_alerts_today,
            avg_evaluation_time_ms=avg_evaluation_time_ms,
        )