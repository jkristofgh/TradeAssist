"""
Instruments API endpoints.

Provides CRUD operations for financial instruments management
including futures, indices, and market internals.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database.connection import get_db_session
from ..models.instruments import Instrument, InstrumentType, InstrumentStatus

router = APIRouter()


class InstrumentResponse(BaseModel):
    """Instrument response model for API endpoints."""
    id: int
    symbol: str
    name: str
    type: str
    status: str
    last_tick: Optional[datetime] = None
    last_price: Optional[float] = None
    created_at: datetime


class InstrumentCreate(BaseModel):
    """Model for creating new instruments."""
    symbol: str
    name: str
    type: InstrumentType
    status: InstrumentStatus = InstrumentStatus.ACTIVE


class InstrumentUpdate(BaseModel):
    """Model for updating existing instruments."""
    name: Optional[str] = None
    status: Optional[InstrumentStatus] = None


@router.get("/instruments", response_model=List[InstrumentResponse])
async def get_instruments(
    type: Optional[InstrumentType] = None,
    status: Optional[InstrumentStatus] = None,
    active_only: bool = False
) -> List[InstrumentResponse]:
    """
    Get all monitored instruments with optional filtering.
    
    Args:
        type: Filter by instrument type (optional).
        status: Filter by status (optional).
        active_only: Return only active instruments.
    
    Returns:
        List[InstrumentResponse]: List of instruments matching filters.
    """
    async with get_db_session() as session:
        # Build query with optional filters
        query = select(Instrument)
        
        if type:
            query = query.where(Instrument.type == type)
        
        if status:
            query = query.where(Instrument.status == status)
        elif active_only:
            query = query.where(Instrument.status == InstrumentStatus.ACTIVE)
        
        # Order by symbol for consistent results
        query = query.order_by(Instrument.symbol)
        
        result = await session.execute(query)
        instruments = result.scalars().all()
        
        return [
            InstrumentResponse(
                id=inst.id,
                symbol=inst.symbol,
                name=inst.name,
                type=inst.type.value if hasattr(inst.type, 'value') else inst.type,
                status=inst.status.value if hasattr(inst.status, 'value') else inst.status,
                last_tick=inst.last_tick,
                last_price=float(inst.last_price) if inst.last_price else None,
                created_at=inst.created_at,
            )
            for inst in instruments
        ]


@router.get("/instruments/{instrument_id}", response_model=InstrumentResponse)
async def get_instrument(instrument_id: int) -> InstrumentResponse:
    """
    Get specific instrument by ID.
    
    Args:
        instrument_id: Instrument ID to retrieve.
    
    Returns:
        InstrumentResponse: Instrument details.
    
    Raises:
        HTTPException: If instrument not found.
    """
    async with get_db_session() as session:
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        return InstrumentResponse(
            id=instrument.id,
            symbol=instrument.symbol,
            name=instrument.name,
            type=instrument.type.value,
            status=instrument.status.value,
            last_tick=instrument.last_tick,
            last_price=float(instrument.last_price) if instrument.last_price else None,
            created_at=instrument.created_at,
        )


@router.post("/instruments", response_model=InstrumentResponse)
async def create_instrument(instrument_data: InstrumentCreate) -> InstrumentResponse:
    """
    Create a new instrument for monitoring.
    
    Args:
        instrument_data: Instrument creation data.
    
    Returns:
        InstrumentResponse: Created instrument details.
    
    Raises:
        HTTPException: If symbol already exists or validation fails.
    """
    async with get_db_session() as session:
        # Check if symbol already exists
        existing_result = await session.execute(
            select(Instrument).where(Instrument.symbol == instrument_data.symbol)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Instrument with symbol '{instrument_data.symbol}' already exists"
            )
        
        # Create new instrument
        instrument = Instrument(
            symbol=instrument_data.symbol.upper(),
            name=instrument_data.name,
            type=instrument_data.type,
            status=instrument_data.status,
        )
        
        session.add(instrument)
        await session.commit()
        await session.refresh(instrument)
        
        return InstrumentResponse(
            id=instrument.id,
            symbol=instrument.symbol,
            name=instrument.name,
            type=instrument.type.value,
            status=instrument.status.value,
            last_tick=instrument.last_tick,
            last_price=float(instrument.last_price) if instrument.last_price else None,
            created_at=instrument.created_at,
        )


@router.put("/instruments/{instrument_id}", response_model=InstrumentResponse)
async def update_instrument(
    instrument_id: int,
    instrument_update: InstrumentUpdate
) -> InstrumentResponse:
    """
    Update an existing instrument.
    
    Args:
        instrument_id: Instrument ID to update.
        instrument_update: Fields to update.
    
    Returns:
        InstrumentResponse: Updated instrument details.
    
    Raises:
        HTTPException: If instrument not found.
    """
    async with get_db_session() as session:
        # Find existing instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Update fields
        if instrument_update.name is not None:
            instrument.name = instrument_update.name
        
        if instrument_update.status is not None:
            instrument.status = instrument_update.status
        
        await session.commit()
        await session.refresh(instrument)
        
        return InstrumentResponse(
            id=instrument.id,
            symbol=instrument.symbol,
            name=instrument.name,
            type=instrument.type.value,
            status=instrument.status.value,
            last_tick=instrument.last_tick,
            last_price=float(instrument.last_price) if instrument.last_price else None,
            created_at=instrument.created_at,
        )