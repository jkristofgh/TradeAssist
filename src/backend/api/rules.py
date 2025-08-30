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


@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    instrument_id: Optional[int] = None,
    active_only: bool = False,
    rule_type: Optional[RuleType] = None
) -> List[AlertRuleResponse]:
    """
    Get alert rules with optional filtering.
    
    Args:
        instrument_id: Filter by instrument ID (optional).
        active_only: Return only active rules.
        rule_type: Filter by rule type (optional).
    
    Returns:
        List[AlertRuleResponse]: List of alert rules matching filters.
    """
    async with get_db_session() as session:
        # Build query with joins for instrument data
        query = select(AlertRule).options(selectinload(AlertRule.instrument))
        
        if instrument_id:
            query = query.where(AlertRule.instrument_id == instrument_id)
        
        if active_only:
            query = query.where(AlertRule.active == True)
        
        if rule_type:
            query = query.where(AlertRule.rule_type == rule_type)
        
        # Order by creation time (newest first)
        query = query.order_by(AlertRule.created_at.desc())
        
        result = await session.execute(query)
        rules = result.scalars().all()
        
        return [
            AlertRuleResponse(
                id=rule.id,
                instrument_id=rule.instrument_id,
                instrument_symbol=rule.instrument.symbol,
                rule_type=rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
                condition=rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
                threshold=float(rule.threshold),
                active=rule.active,
                name=rule.name,
                description=rule.description,
                time_window_seconds=rule.time_window_seconds,
                moving_average_period=rule.moving_average_period,
                cooldown_seconds=rule.cooldown_seconds,
                last_triggered=rule.last_triggered,
                created_at=rule.created_at,
            )
            for rule in rules
        ]


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(rule_id: int) -> AlertRuleResponse:
    """
    Get specific alert rule by ID.
    
    Args:
        rule_id: Alert rule ID to retrieve.
    
    Returns:
        AlertRuleResponse: Alert rule details.
    
    Raises:
        HTTPException: If rule not found.
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(AlertRule)
            .options(selectinload(AlertRule.instrument))
            .where(AlertRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        return AlertRuleResponse(
            id=rule.id,
            instrument_id=rule.instrument_id,
            instrument_symbol=rule.instrument.symbol,
            rule_type=rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
            condition=rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
            threshold=float(rule.threshold),
            active=rule.active,
            name=rule.name,
            description=rule.description,
            time_window_seconds=rule.time_window_seconds,
            moving_average_period=rule.moving_average_period,
            cooldown_seconds=rule.cooldown_seconds,
            last_triggered=rule.last_triggered,
            created_at=rule.created_at,
        )


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(rule_data: AlertRuleCreate) -> AlertRuleResponse:
    """
    Create a new alert rule.
    
    Args:
        rule_data: Alert rule creation data.
    
    Returns:
        AlertRuleResponse: Created alert rule details.
    
    Raises:
        HTTPException: If instrument not found or validation fails.
    """
    async with get_db_session() as session:
        # Validate instrument exists
        instrument_result = await session.execute(
            select(Instrument).where(Instrument.id == rule_data.instrument_id)
        )
        instrument = instrument_result.scalar_one_or_none()
        
        if not instrument:
            raise HTTPException(
                status_code=404,
                detail=f"Instrument with ID {rule_data.instrument_id} not found"
            )
        
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
        
        return AlertRuleResponse(
            id=rule.id,
            instrument_id=rule.instrument_id,
            instrument_symbol=rule.instrument.symbol,
            rule_type=rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
            condition=rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
            threshold=float(rule.threshold),
            active=rule.active,
            name=rule.name,
            description=rule.description,
            time_window_seconds=rule.time_window_seconds,
            moving_average_period=rule.moving_average_period,
            cooldown_seconds=rule.cooldown_seconds,
            last_triggered=rule.last_triggered,
            created_at=rule.created_at,
        )


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate
) -> AlertRuleResponse:
    """
    Update an existing alert rule.
    
    Args:
        rule_id: Alert rule ID to update.
        rule_update: Fields to update.
    
    Returns:
        AlertRuleResponse: Updated alert rule details.
    
    Raises:
        HTTPException: If rule not found.
    """
    async with get_db_session() as session:
        # Find existing rule
        result = await session.execute(
            select(AlertRule)
            .options(selectinload(AlertRule.instrument))
            .where(AlertRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        # Update fields
        update_data = rule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        
        await session.commit()
        await session.refresh(rule)
        
        return AlertRuleResponse(
            id=rule.id,
            instrument_id=rule.instrument_id,
            instrument_symbol=rule.instrument.symbol,
            rule_type=rule.rule_type.value if hasattr(rule.rule_type, 'value') else rule.rule_type,
            condition=rule.condition.value if hasattr(rule.condition, 'value') else rule.condition,
            threshold=float(rule.threshold),
            active=rule.active,
            name=rule.name,
            description=rule.description,
            time_window_seconds=rule.time_window_seconds,
            moving_average_period=rule.moving_average_period,
            cooldown_seconds=rule.cooldown_seconds,
            last_triggered=rule.last_triggered,
            created_at=rule.created_at,
        )


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: int) -> dict:
    """
    Delete an alert rule.
    
    Args:
        rule_id: Alert rule ID to delete.
    
    Returns:
        dict: Deletion confirmation.
    
    Raises:
        HTTPException: If rule not found.
    """
    async with get_db_session() as session:
        # Check if rule exists
        result = await session.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        # Delete rule (cascade will handle related alert logs)
        await session.execute(
            delete(AlertRule).where(AlertRule.id == rule_id)
        )
        await session.commit()
        
        return {"message": f"Alert rule {rule_id} deleted successfully"}