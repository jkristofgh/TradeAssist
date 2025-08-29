"""
Market data model definition.

Represents real-time and historical market data for all monitored instruments
with optimized time-series storage and querying capabilities.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class MarketData(Base):
    """
    Market data tick model.
    
    Stores time-series market data with sub-second timestamp precision
    for real-time alert evaluation and historical analysis.
    Optimized for high-frequency data ingestion and fast queries.
    """
    
    __tablename__ = "market_data"
    
    # Primary key - auto-incrementing for insertion performance
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Timestamp with sub-second precision
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        doc="Tick timestamp with sub-second precision"
    )
    
    # Foreign key to instruments
    instrument_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to monitored instrument"
    )
    
    # Core market data fields
    price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4),
        nullable=True,
        doc="Current price (last trade price)"
    )
    
    volume: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Trade volume"
    )
    
    bid: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4),
        nullable=True,
        doc="Best bid price"
    )
    
    ask: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4),
        nullable=True,
        doc="Best ask price"
    )
    
    # Additional market data fields
    bid_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Bid size"
    )
    
    ask_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Ask size"
    )
    
    open_price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4),
        nullable=True,
        doc="Session open price"
    )
    
    high_price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4),
        nullable=True,
        doc="Session high price"
    )
    
    low_price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4),
        nullable=True,
        doc="Session low price"
    )
    
    # Relationship to instrument
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="market_data",
        lazy="select"
    )
    
    # Performance indexes - critical for real-time queries
    __table_args__ = (
        # Composite index for timestamp + instrument lookups (most common query)
        Index("ix_market_data_timestamp_instrument", "timestamp", "instrument_id"),
        # Individual indexes for common filters
        Index("ix_market_data_timestamp", "timestamp"),
        Index("ix_market_data_instrument", "instrument_id"),
        # Index for price-based queries (alert evaluation)
        Index("ix_market_data_price", "price"),
        # Covering index for latest data queries
        Index("ix_market_data_latest", "instrument_id", "timestamp", "price"),
    )
    
    def __repr__(self) -> str:
        """String representation of market data tick."""
        return (
            f"<MarketData("
            f"id={self.id}, "
            f"instrument_id={self.instrument_id}, "
            f"timestamp={self.timestamp}, "
            f"price={self.price})>"
        )