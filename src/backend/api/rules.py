"""
Alert rules API endpoints.

Provides CRUD operations for alert rule management with validation
and performance optimization for sub-second evaluation.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from ..database.connection import get_db_session
from ..models.alert_rules import AlertRule, RuleType, RuleCondition
from ..models.instruments import Instrument

# Import standardized API components
from .common.exceptions import StandardAPIError, ValidationError, BusinessLogicError
from .common.responses import InstrumentResponseBuilder
from .common.validators import validate_instrument_exists, validate_pagination

router = APIRouter()


class AlertRuleResponse(BaseModel):
    """Alert rule response model for API endpoints."""
    id: int
    instrument_id: int
    instrument_symbol: str
    rule_type: str
    condition: str
    threshold: float
    active: bool
    name: Optional[str] = None
    description: Optional[str] = None
    time_window_seconds: Optional[int] = None
    moving_average_period: Optional[int] = None
    cooldown_seconds: int
    last_triggered: Optional[datetime] = None
    created_at: datetime


class AlertRuleCreate(BaseModel):
    """Model for creating new alert rules."""
    instrument_id: int
    rule_type: RuleType
    condition: RuleCondition
    threshold: float = Field(ge=0, description="Threshold value must be non-negative")
    active: bool = True
    name: Optional[str] = None
    description: Optional[str] = None
    time_window_seconds: Optional[int] = Field(None, ge=1, le=3600)
    moving_average_period: Optional[int] = Field(None, ge=1, le=1000)
    cooldown_seconds: int = Field(60, ge=0, le=3600)


class AlertRuleUpdate(BaseModel):
    """Model for updating existing alert rules."""
    rule_type: Optional[RuleType] = None
    condition: Optional[RuleCondition] = None
    threshold: Optional[float] = Field(None, ge=0)
    active: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None
    time_window_seconds: Optional[int] = Field(None, ge=1, le=3600)
    moving_average_period: Optional[int] = Field(None, ge=1, le=1000)
    cooldown_seconds: Optional[int] = Field(None, ge=0, le=3600)


@router.get("/rules")
@validate_pagination(max_per_page=100)
async def get_alert_rules(
    instrument_id: Optional[int] = None,
    active_only: bool = False,
    rule_type: Optional[RuleType] = None,
    page: int = 1,
    per_page: int = 20
) -> dict:
    """
    Get alert rules with optional filtering and pagination.
    
    Args:
        instrument_id: Filter by instrument ID (optional).
        active_only: Return only active rules.
        rule_type: Filter by rule type (optional).
        page: Page number (starts from 1).
        per_page: Number of rules per page.
    
    Returns:
        dict: Paginated response with alert rules matching filters.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            # Build base query with joins for instrument data
            base_query = select(AlertRule).options(selectinload(AlertRule.instrument))
            
            if instrument_id:
                base_query = base_query.where(AlertRule.instrument_id == instrument_id)
            
            if active_only:
                base_query = base_query.where(AlertRule.active == True)
            
            if rule_type:
                base_query = base_query.where(AlertRule.rule_type == rule_type)
            
            # Get total count for pagination
            count_query = select(AlertRule.id)
            if instrument_id:
                count_query = count_query.where(AlertRule.instrument_id == instrument_id)
            if active_only:
                count_query = count_query.where(AlertRule.active == True)
            if rule_type:
                count_query = count_query.where(AlertRule.rule_type == rule_type)
            
            count_result = await session.execute(count_query)
            total_count = len(count_result.scalars().all())
            
            # Apply pagination and ordering
            offset = (page - 1) * per_page
            query = base_query.order_by(AlertRule.created_at.desc()).offset(offset).limit(per_page)
            
            result = await session.execute(query)
            rules = result.scalars().all()
            
            # Prepare response data
            rules_data = [
                {
                    "id": rule.id,
                    "instrument_id": rule.instrument_id,
                    "instrument_symbol": rule.instrument.symbol,
                    "rule_type": rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
                    "condition": rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
                    "threshold": float(rule.threshold),
                    "active": rule.active,
                    "name": rule.name,
                    "description": rule.description,
                    "time_window_seconds": rule.time_window_seconds,
                    "moving_average_period": rule.moving_average_period,
                    "cooldown_seconds": rule.cooldown_seconds,
                    "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
                    "created_at": rule.created_at.isoformat(),
                }
                for rule in rules
            ]
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Build paginated response
            return response_builder.paginated(
                rules_data,
                total_count=total_count,
                page=page,
                per_page=per_page
            ).with_performance_metrics(processing_time, len(rules_data)).build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="RULES_001", 
            message="Failed to retrieve alert rules",
            details={"error": str(e)}
        )


@router.get("/rules/{rule_id}")
async def get_alert_rule(rule_id: int) -> dict:
    """
    Get specific alert rule by ID.
    
    Args:
        rule_id: Alert rule ID.
    
    Returns:
        dict: Alert rule details with standardized response format.
    
    Raises:
        ValidationError: If rule not found.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(AlertRule).options(selectinload(AlertRule.instrument))
                .where(AlertRule.id == rule_id)
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise ValidationError(
                    error_code="RULES_002",
                    message="Alert rule not found",
                    details={"rule_id": rule_id}
                )
            
            rule_data = {
                "id": rule.id,
                "instrument_id": rule.instrument_id,
                "instrument_symbol": rule.instrument.symbol,
                "rule_type": rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
                "condition": rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
                "threshold": float(rule.threshold),
                "active": rule.active,
                "name": rule.name,
                "description": rule.description,
                "time_window_seconds": rule.time_window_seconds,
                "moving_average_period": rule.moving_average_period,
                "cooldown_seconds": rule.cooldown_seconds,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
                "created_at": rule.created_at.isoformat(),
            }
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return response_builder.success(rule_data) \
                .with_performance_metrics(processing_time, 1) \
                .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="RULES_003", 
            message="Failed to retrieve alert rule",
            details={"rule_id": rule_id, "error": str(e)}
        )


@router.post("/rules")
@validate_instrument_exists
async def create_alert_rule(rule_data: AlertRuleCreate) -> dict:
    """
    Create a new alert rule.
    
    Args:
        rule_data: Alert rule creation data.
    
    Returns:
        dict: Created alert rule details with standardized response format.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            # Get instrument (validation decorator already confirmed it exists)
            instrument_result = await session.execute(
                select(Instrument).where(Instrument.id == rule_data.instrument_id)
            )
            instrument = instrument_result.scalar_one()
            
            # Create new alert rule
            rule = AlertRule(
                instrument_id=rule_data.instrument_id,
                rule_type=rule_data.rule_type,
                condition=rule_data.condition,
                threshold=rule_data.threshold,
                active=rule_data.active,
                name=rule_data.name,
                description=rule_data.description,
                time_window_seconds=rule_data.time_window_seconds,
                moving_average_period=rule_data.moving_average_period,
                cooldown_seconds=rule_data.cooldown_seconds,
            )
            
            session.add(rule)
            await session.commit()
            await session.refresh(rule, ["instrument"])
            
            rule_data = {
                "id": rule.id,
                "instrument_id": rule.instrument_id,
                "instrument_symbol": rule.instrument.symbol,
                "rule_type": rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
                "condition": rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
                "threshold": float(rule.threshold),
                "active": rule.active,
                "name": rule.name,
                "description": rule.description,
                "time_window_seconds": rule.time_window_seconds,
                "moving_average_period": rule.moving_average_period,
                "cooldown_seconds": rule.cooldown_seconds,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
                "created_at": rule.created_at.isoformat(),
            }
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return response_builder.success(rule_data) \
                .with_performance_metrics(processing_time, 1) \
                .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="RULES_004", 
            message="Failed to create alert rule",
            details={"instrument_id": rule_data.instrument_id, "error": str(e)}
        )


@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate
) -> dict:
    """
    Update an existing alert rule.
    
    Args:
        rule_id: Alert rule ID to update.
        rule_update: Fields to update.
    
    Returns:
        dict: Updated alert rule details with standardized response format.
    
    Raises:
        ValidationError: If rule not found.
        BusinessLogicError: If update fails.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            # Find existing rule
            result = await session.execute(
                select(AlertRule)
                .options(selectinload(AlertRule.instrument))
                .where(AlertRule.id == rule_id)
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise ValidationError(
                    error_code="RULES_005",
                    message="Alert rule not found",
                    details={"rule_id": rule_id}
                )
            
            # Update fields
            update_data = rule_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(rule, field, value)
            
            await session.commit()
            await session.refresh(rule)
            
            rule_data = {
                "id": rule.id,
                "instrument_id": rule.instrument_id,
                "instrument_symbol": rule.instrument.symbol,
                "rule_type": rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
                "condition": rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
                "threshold": float(rule.threshold),
                "active": rule.active,
                "name": rule.name,
                "description": rule.description,
                "time_window_seconds": rule.time_window_seconds,
                "moving_average_period": rule.moving_average_period,
                "cooldown_seconds": rule.cooldown_seconds,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
                "created_at": rule.created_at.isoformat(),
            }
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return response_builder.success(rule_data) \
                .with_performance_metrics(processing_time, 1) \
                .build()
    
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="RULES_006", 
            message="Failed to update alert rule",
            details={"rule_id": rule_id, "error": str(e)}
        )


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: int) -> dict:
    """
    Delete an alert rule.
    
    Args:
        rule_id: Alert rule ID to delete.
    
    Returns:
        dict: Success message with standardized response format.
    
    Raises:
        ValidationError: If rule not found.
        BusinessLogicError: If deletion fails.
    """
    start_time = datetime.utcnow()
    response_builder = InstrumentResponseBuilder()
    
    try:
        async with get_db_session() as session:
            # Check if rule exists
            result = await session.execute(
                select(AlertRule).where(AlertRule.id == rule_id)
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise ValidationError(
                    error_code="RULES_007",
                    message="Alert rule not found",
                    details={"rule_id": rule_id}
                )
            
            # Delete the rule
            await session.execute(
                delete(AlertRule).where(AlertRule.id == rule_id)
            )
            await session.commit()
            
            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return response_builder.success({
                "message": f"Alert rule {rule_id} deleted successfully",
                "deleted_rule_id": rule_id
            }).with_performance_metrics(processing_time, 1).build()
    
    except StandardAPIError:
        raise
    except Exception as e:
        raise BusinessLogicError(
            error_code="RULES_008", 
            message="Failed to delete alert rule",
            details={"rule_id": rule_id, "error": str(e)}
        )