"""
Health check API endpoints.

Provides system health monitoring and status information
for operational visibility and monitoring.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func

from ..database.connection import get_db_session
from ..models.instruments import Instrument
from ..models.market_data import MarketData

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    ingestion_active: bool
    last_tick: Optional[datetime] = None
    api_connected: bool
    active_instruments: int
    total_rules: int
    last_alert: Optional[datetime] = None


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


@router.get("/health", response_model=HealthResponse)
async def get_health_status() -> HealthResponse:
    """
    Get basic health status of the TradeAssist system.
    
    Returns system health including ingestion status, connectivity,
    and basic operational metrics for monitoring.
    
    Returns:
        HealthResponse: Current system health status.
    """
    try:
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
            
            return HealthResponse(
                status="healthy" if api_connected else "degraded",
                ingestion_active=ingestion_active,
                last_tick=last_tick,
                api_connected=api_connected,
                active_instruments=active_instruments,
                total_rules=total_rules,
                last_alert=last_alert,
            )
            
    except Exception as e:
        # Return error status if health check fails
        return HealthResponse(
            status="unhealthy",
            ingestion_active=False,
            api_connected=False,
            active_instruments=0,
            total_rules=0,
        )


@router.get("/health/detailed", response_model=SystemStats)
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