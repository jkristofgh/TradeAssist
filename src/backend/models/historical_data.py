"""
Historical Data Models.

Database models for historical market data storage, data sources,
and user queries.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    Integer, String, DateTime, DECIMAL,
    ForeignKey, Text, Boolean, Index, UniqueConstraint,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class DataFrequency(str, Enum):
    """Supported data frequencies."""
    ONE_MINUTE = "1min"
    FIVE_MINUTE = "5min"
    FIFTEEN_MINUTE = "15min"
    THIRTY_MINUTE = "30min"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


class DataSource(Base, TimestampMixin):
    """
    Data source configuration and tracking.
    
    Tracks different data providers and their configurations,
    allowing for multiple data sources and provider management.
    """
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Data source name (e.g., 'Schwab', 'Yahoo', 'Alpha Vantage')"
    )
    
    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Provider type identifier"
    )
    
    base_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        doc="API base URL if applicable"
    )
    
    api_key_secret_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        doc="Secret manager ID for API key"
    )
    
    rate_limit_per_minute: Mapped[int] = mapped_column(
        default=60,
        doc="API rate limit per minute"
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether this data source is currently active"
    )
    
    configuration: Mapped[Optional[str]] = mapped_column(
        Text,
        doc="JSON configuration for provider-specific settings"
    )
    
    # Relationships
    market_data_bars: Mapped[List["MarketDataBar"]] = relationship(
        "MarketDataBar",
        back_populates="data_source",
        cascade="all, delete-orphan"
    )


class MarketDataBar(Base, TimestampMixin):
    """
    OHLCV market data storage.
    
    Stores historical market data bars with support for different
    frequencies and asset types including futures contracts.
    """
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Symbol and timing information
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Trading symbol (e.g., 'AAPL', '/ES', 'ESZ24')"
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        doc="Bar timestamp (start time of the period)"
    )
    
    frequency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Time frequency (1min, 5min, 1h, 1d, etc.)"
    )
    
    # OHLCV data
    open_price: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=4),
        nullable=False,
        doc="Opening price"
    )
    
    high_price: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=4),
        nullable=False,
        doc="Highest price during the period"
    )
    
    low_price: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=4),
        nullable=False,
        doc="Lowest price during the period"
    )
    
    close_price: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=4),
        nullable=False,
        doc="Closing price"
    )
    
    volume: Mapped[int] = mapped_column(
        default=0,
        doc="Trading volume during the period"
    )
    
    # Futures-specific fields
    open_interest: Mapped[Optional[int]] = mapped_column(
        doc="Open interest for futures contracts"
    )
    
    contract_month: Mapped[Optional[str]] = mapped_column(
        String(10),
        doc="Contract month for futures (e.g., 'DEC24')"
    )
    
    # Metadata fields
    data_source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id"),
        nullable=False,
        doc="Reference to data source"
    )
    
    is_adjusted: Mapped[bool] = mapped_column(
        default=False,
        doc="Whether prices are split/dividend adjusted"
    )
    
    quality_score: Mapped[Optional[int]] = mapped_column(
        doc="Data quality score (0-100)"
    )
    
    # Relationships
    data_source: Mapped["DataSource"] = relationship(
        "DataSource",
        back_populates="market_data_bars"
    )
    
    # Indexes for performance
    __table_args__ = (
        # Composite index for time-series queries
        Index(
            'idx_symbol_timestamp_freq',
            'symbol', 'timestamp', 'frequency'
        ),
        Index(
            'idx_symbol_freq_timestamp',
            'symbol', 'frequency', 'timestamp'
        ),
        # Unique constraint to prevent duplicates
        UniqueConstraint(
            'symbol', 'timestamp', 'frequency', 'data_source_id',
            name='uq_market_data_bar'
        ),
        # Data quality constraints
        CheckConstraint(
            'open_price > 0 AND high_price > 0 AND low_price > 0 AND close_price > 0',
            name='ck_positive_prices'
        ),
        CheckConstraint(
            'high_price >= open_price AND high_price >= close_price',
            name='ck_high_price_valid'
        ),
        CheckConstraint(
            'low_price <= open_price AND low_price <= close_price',
            name='ck_low_price_valid'
        ),
        CheckConstraint(
            'volume >= 0',
            name='ck_volume_non_negative'
        ),
        CheckConstraint(
            'quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)',
            name='ck_quality_score_range'
        )
    )


class DataQuery(Base, TimestampMixin):
    """
    User query storage and reuse.
    
    Stores user-defined queries for historical data to enable
    query reuse, scheduling, and performance optimization.
    """
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User-defined query name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        doc="Optional query description"
    )
    
    # Query parameters
    symbols: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="JSON array of symbols to query"
    )
    
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        doc="Query start date (null for all available)"
    )
    
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        doc="Query end date (null for current)"
    )
    
    frequency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=DataFrequency.DAILY.value,
        doc="Data frequency"
    )
    
    filters: Mapped[Optional[str]] = mapped_column(
        Text,
        doc="JSON object with additional filters"
    )
    
    # Query metadata
    is_favorite: Mapped[bool] = mapped_column(
        default=False,
        doc="Whether query is marked as favorite"
    )
    
    last_executed: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        doc="Last execution timestamp"
    )
    
    execution_count: Mapped[int] = mapped_column(
        default=0,
        doc="Number of times query has been executed"
    )
    
    average_execution_time_ms: Mapped[Optional[int]] = mapped_column(
        doc="Average execution time in milliseconds"
    )
    
    # Tags for organization
    tags: Mapped[Optional[str]] = mapped_column(
        String(500),
        doc="Comma-separated tags for query organization"
    )