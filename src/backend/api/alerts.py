"""
Alerts API endpoints.

Provides query access to alert history and status information
for dashboard display and historical analysis.
"""

from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from ..database.connection import get_db_session
from ..models.alert_logs import AlertLog, AlertStatus, DeliveryStatus
from ..models.alert_rules import AlertRule
from ..models.instruments import Instrument

# Import standardized API components
from .common.exceptions import StandardAPIError, ValidationError, BusinessLogicError
from .common.responses import InstrumentResponseBuilder
from .common.validators import validate_pagination

router = APIRouter()


class AlertResponse(BaseModel):
    """Alert response model for API endpoints."""
    id: int
    timestamp: datetime
    rule_id: int
    rule_name: Optional[str] = None
    instrument_id: int
    instrument_symbol: str
    trigger_value: float
    threshold_value: float
    fired_status: str
    delivery_status: str
    rule_condition: str
    evaluation_time_ms: Optional[int] = None
    alert_message: Optional[str] = None


class AlertsResponse(BaseModel):
    """Paginated alerts response."""
    alerts: List[AlertResponse]
    total: int
    has_more: bool
    page: int
    limit: int


class AlertStatsResponse(BaseModel):
    """Alert statistics response."""
    total_alerts_today: int
    total_alerts_this_week: int
    avg_evaluation_time_ms: Optional[float] = None
    fastest_evaluation_ms: Optional[int] = None
    slowest_evaluation_ms: Optional[int] = None
    alerts_by_instrument: dict[str, int]
    alerts_by_rule_type: dict[str, int]


@router.get("/alerts")
@validate_pagination(max_per_page=1000)
async def get_alerts(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    per_page: int = Query(50, ge=1, le=1000, description="Number of alerts per page"),
    instrument_id: Optional[int] = Query(None, description="Filter by instrument ID"),
    rule_id: Optional[int] = Query(None, description="Filter by rule ID"),
    fired_status: Optional[AlertStatus] = Query(None, description="Filter by fired status"),
    delivery_status: Optional[DeliveryStatus] = Query(None, description="Filter by delivery status"),
    start_date: Optional[date] = Query(None, description="Filter alerts from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter alerts to date (YYYY-MM-DD)"),
) -> dict:
    """
    Get paginated alert history with filtering options.
    
    Returns alert logs with instrument and rule details for dashboard
    display and historical analysis.
    
    Args:
        page: Page number for pagination (1-based).
        per_page: Number of alerts per page (1-1000).
        instrument_id: Filter by specific instrument.
        rule_id: Filter by specific rule.
        fired_status: Filter by alert firing status.
        delivery_status: Filter by delivery status.
        start_date: Start date for filtering (inclusive).
        end_date: End date for filtering (inclusive).
    
    Returns:
        dict: Paginated alerts with metadata and standardized response format.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            # Build base query with joins
            query = (
                select(AlertLog)
                .join(AlertRule, AlertLog.rule_id == AlertRule.id)
                .join(Instrument, AlertLog.instrument_id == Instrument.id)
                .options(
                    selectinload(AlertLog.rule),
                    selectinload(AlertLog.instrument)
                )
            )
            
            # Apply filters
            if instrument_id:
                query = query.where(AlertLog.instrument_id == instrument_id)
            
            if rule_id:
                query = query.where(AlertLog.rule_id == rule_id)
            
            if fired_status:
                query = query.where(AlertLog.fired_status == fired_status)
            
            if delivery_status:
                query = query.where(AlertLog.delivery_status == delivery_status)
            
            if start_date:
                query = query.where(func.date(AlertLog.timestamp) >= start_date)
            
            if end_date:
                query = query.where(func.date(AlertLog.timestamp) <= end_date)
            
            # Get total count before applying pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Calculate offset from page number
            offset = (page - 1) * per_page
            
            # Apply pagination and ordering
            query = query.order_by(desc(AlertLog.timestamp))
            query = query.offset(offset).limit(per_page)
            
            # Execute query
            result = await session.execute(query)
            alerts = result.scalars().all()
            
            # Prepare response data
            alerts_data = [
                {
                    "id": alert.id,
                    "timestamp": alert.timestamp.isoformat(),
                    "rule_id": alert.rule_id,
                    "rule_name": alert.rule.name,
                    "instrument_id": alert.instrument_id,
                    "instrument_symbol": alert.instrument.symbol,
                    "trigger_value": float(alert.trigger_value),
                    "threshold_value": float(alert.threshold_value),
                    "fired_status": alert.fired_status.value,
                    "delivery_status": alert.delivery_status.value,
                    "rule_condition": alert.rule_condition,
                    "evaluation_time_ms": alert.evaluation_time_ms,
                    "alert_message": alert.alert_message,
                }
                for alert in alerts
            ]
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Build paginated response
            return response_builder.paginated(
                alerts_data,
                total_count=total,
                page=page,
                per_page=per_page
            ).with_performance_metrics(processing_time, len(alerts_data)).build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="ALERTS_001", 
            message="Failed to retrieve alert history",
            details={"error": str(e)}
        )


@router.get("/alerts/stats")
async def get_alert_statistics() -> dict:
    """
    Get alert statistics and performance metrics.
    
    Provides summary statistics for monitoring alert system
    performance and operational insights.
    
    Returns:
        dict: Alert statistics and performance metrics with standardized response format.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            from datetime import timedelta
            
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            
            # Total alerts today
            alerts_today_result = await session.execute(
                select(func.count(AlertLog.id)).where(
                    func.date(AlertLog.timestamp) == today
                )
            )
            total_alerts_today = alerts_today_result.scalar() or 0
            
            # Total alerts this week
            alerts_week_result = await session.execute(
                select(func.count(AlertLog.id)).where(
                    func.date(AlertLog.timestamp) >= week_ago
                )
            )
            total_alerts_this_week = alerts_week_result.scalar() or 0
            
            # Evaluation time statistics
            eval_stats_result = await session.execute(
                select(
                    func.avg(AlertLog.evaluation_time_ms),
                    func.min(AlertLog.evaluation_time_ms),
                    func.max(AlertLog.evaluation_time_ms),
                ).where(
                    func.date(AlertLog.timestamp) >= week_ago,
                    AlertLog.evaluation_time_ms.isnot(None)
                )
            )
            avg_eval, min_eval, max_eval = eval_stats_result.first() or (None, None, None)
            
            # Alerts by instrument
            alerts_by_instrument_result = await session.execute(
                select(
                    Instrument.symbol,
                    func.count(AlertLog.id).label("count")
                )
                .join(AlertLog, AlertLog.instrument_id == Instrument.id)
                .where(func.date(AlertLog.timestamp) >= week_ago)
                .group_by(Instrument.symbol)
            )
            alerts_by_instrument = {
                symbol: count for symbol, count in alerts_by_instrument_result.all()
            }
            
            # Alerts by rule type
            alerts_by_rule_type_result = await session.execute(
                select(
                    AlertRule.rule_type,
                    func.count(AlertLog.id).label("count")
                )
                .join(AlertLog, AlertLog.rule_id == AlertRule.id)
                .where(func.date(AlertLog.timestamp) >= week_ago)
                .group_by(AlertRule.rule_type)
            )
            alerts_by_rule_type = {
                rule_type.value: count for rule_type, count in alerts_by_rule_type_result.all()
            }
            
            stats_data = {
                "total_alerts_today": total_alerts_today,
                "total_alerts_this_week": total_alerts_this_week,
                "avg_evaluation_time_ms": float(avg_eval) if avg_eval else None,
                "fastest_evaluation_ms": min_eval,
                "slowest_evaluation_ms": max_eval,
                "alerts_by_instrument": alerts_by_instrument,
                "alerts_by_rule_type": alerts_by_rule_type,
            }
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return response_builder.success(stats_data) \
                .with_performance_metrics(processing_time, total_alerts_this_week) \
                .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="ALERTS_002", 
            message="Failed to retrieve alert statistics",
            details={"error": str(e)}
        )


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int) -> dict:
    """
    Delete a specific alert log entry.
    
    Args:
        alert_id: Alert log ID to delete.
    
    Returns:
        dict: Deletion confirmation with standardized response format.
    
    Raises:
        ValidationError: If alert not found.
        BusinessLogicError: If deletion fails.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            # Check if alert exists
            result = await session.execute(
                select(AlertLog).where(AlertLog.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise ValidationError(
                    error_code="ALERTS_003",
                    message="Alert log entry not found",
                    details={"alert_id": alert_id}
                )
            
            # Delete alert
            await session.delete(alert)
            await session.commit()
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return response_builder.success({
                "message": f"Alert {alert_id} deleted successfully",
                "deleted_alert_id": alert_id
            }).with_performance_metrics(processing_time, 1).build()
    
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="ALERTS_004", 
            message="Failed to delete alert log entry",
            details={"alert_id": alert_id, "error": str(e)}
        )