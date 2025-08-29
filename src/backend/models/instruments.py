"""
Instrument model definition.

Represents financial instruments (futures, indices, internals) that are monitored
for real-time data and alert generation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, DECIMAL, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class InstrumentType(str, Enum):
    """Types of financial instruments supported."""
    FUTURE = "future"
    INDEX = "index"
    INTERNAL = "internal"


class InstrumentStatus(str, Enum):
    """Status of instrument monitoring."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Instrument(Base, TimestampMixin):
    """
    Financial instrument model.
    
    Represents instruments that are monitored for real-time data,
    including futures (ES, NQ, YM, CL, GC), indices (SPX, NDX, RUT),
    and market internals (VIX, TICK, ADD, TRIN).
    """
    
    __tablename__ = "instruments"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Core instrument data
    symbol: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        doc="Instrument symbol (e.g., ES, NQ, SPX)"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Full instrument name (e.g., E-mini S&P 500)"
    )
    
    type: Mapped[InstrumentType] = mapped_column(
        String(20),
        nullable=False,
        doc="Instrument type: future, index, or internal"
    )
    
    status: Mapped[InstrumentStatus] = mapped_column(
        String(20),
        default=InstrumentStatus.ACTIVE,
        nullable=False,
        doc="Current monitoring status"
    )
    
    # Last tick information
    last_tick: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Timestamp of last received tick"
    )
    
    last_price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 4),
        nullable=True,
        doc="Last received price"
    )
    
    # Relationships
    market_data: Mapped[list["MarketData"]] = relationship(
        "MarketData",
        back_populates="instrument",
        cascade="all, delete-orphan"
    )
    
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        "AlertRule",
        back_populates="instrument",
        cascade="all, delete-orphan"
    )
    
    alert_logs: Mapped[list["AlertLog"]] = relationship(
        "AlertLog",
        back_populates="instrument",
        cascade="all, delete-orphan"
    )
    
    # Performance indexes
    __table_args__ = (
        Index("ix_instruments_symbol", "symbol"),
        Index("ix_instruments_type_status", "type", "status"),
        Index("ix_instruments_last_tick", "last_tick"),
    )
    
    def __repr__(self) -> str:
        """String representation of instrument."""
        return f"<Instrument(id={self.id}, symbol='{self.symbol}', type='{self.type.value}', status='{self.status.value}')>"