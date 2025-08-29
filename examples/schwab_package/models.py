"""
Simplified data models for Schwab Package.

Provides clean, simple data structures for quotes, streaming events, and instrument types
optimized for package consumers rather than internal complexity.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class InstrumentType(str, Enum):
    """Instrument types supported by Schwab API."""

    EQUITY = "EQUITY"
    ETF = "ETF"
    INDEX = "INDEX"
    MUTUAL_FUND = "MUTUAL_FUND"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    FOREX = "FOREX"
    BOND = "BOND"


@dataclass
class Quote:
    """
    Simple quote data structure for real-time market data.

    Contains essential quote information in an easy-to-use format.
    All monetary values are returned as float for simplicity.
    """

    symbol: str
    last: float | None = None
    bid: float | None = None
    ask: float | None = None
    volume: int | None = None
    timestamp: datetime | None = None

    # Price change information
    change: float | None = None
    change_percent: float | None = None

    # Daily price information
    open: float | None = None
    high: float | None = None
    low: float | None = None
    previous_close: float | None = None

    # Market information
    exchange: str | None = None
    instrument_type: str | None = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def spread(self) -> float | None:
        """Calculate bid-ask spread."""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None

    @property
    def mid_price(self) -> float | None:
        """Calculate mid-point price between bid and ask."""
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / 2
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert quote to dictionary."""
        return {
            "symbol": self.symbol,
            "last": self.last,
            "bid": self.bid,
            "ask": self.ask,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "change": self.change,
            "change_percent": self.change_percent,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "previous_close": self.previous_close,
            "exchange": self.exchange,
            "instrument_type": self.instrument_type,
            "spread": self.spread,
            "mid_price": self.mid_price,
        }


@dataclass
class StreamEvent:
    """
    Streaming data event structure for real-time callbacks.

    Simple container for streaming market data events with metadata.
    """

    symbol: str
    event_type: str  # 'quote', 'trade', 'chart', etc.
    data: dict[str, Any]
    timestamp: datetime | None = None
    sequence_id: int | None = None
    exchange: str | None = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_quote(self) -> Quote | None:
        """
        Convert stream event to Quote object if applicable.

        Returns:
            Quote object if event contains quote data, None otherwise
        """
        if self.event_type != "quote":
            return None

        return Quote(
            symbol=self.symbol,
            last=self.data.get("last"),
            bid=self.data.get("bid"),
            ask=self.data.get("ask"),
            volume=self.data.get("volume"),
            timestamp=self.timestamp,
            change=self.data.get("change"),
            change_percent=self.data.get("change_percent"),
            open=self.data.get("open"),
            high=self.data.get("high"),
            low=self.data.get("low"),
            previous_close=self.data.get("previous_close"),
            exchange=self.exchange,
            instrument_type=self.data.get("instrument_type"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert stream event to dictionary."""
        return {
            "symbol": self.symbol,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sequence_id": self.sequence_id,
            "exchange": self.exchange,
        }


# Utility functions for creating models from API responses
def create_quote_from_api_response(symbol: str, api_data: dict[str, Any]) -> Quote:
    """
    Create Quote object from Schwab API response data.

    Args:
        symbol: Trading symbol
        api_data: Raw API response data

    Returns:
        Quote object with normalized data
    """
    # Handle different API response formats
    # This function normalizes various Schwab API response formats into our simple Quote structure

    def safe_float(value: Any) -> float | None:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def safe_int(value: Any) -> int | None:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    # Extract values with multiple possible field names from different API endpoints
    last = (
        safe_float(api_data.get("lastPrice"))
        or safe_float(api_data.get("last"))
        or safe_float(api_data.get("mark"))
    )

    bid = safe_float(api_data.get("bidPrice")) or safe_float(api_data.get("bid"))

    ask = safe_float(api_data.get("askPrice")) or safe_float(api_data.get("ask"))

    volume = safe_int(api_data.get("totalVolume")) or safe_int(api_data.get("volume"))

    # Calculate change if not provided
    change = safe_float(api_data.get("netChange"))
    change_percent = safe_float(api_data.get("netPercentChangeInDouble"))

    return Quote(
        symbol=symbol,
        last=last,
        bid=bid,
        ask=ask,
        volume=volume,
        change=change,
        change_percent=change_percent,
        open=safe_float(api_data.get("openPrice")),
        high=safe_float(api_data.get("highPrice")),
        low=safe_float(api_data.get("lowPrice")),
        previous_close=safe_float(api_data.get("closePrice")),
        exchange=api_data.get("exchange"),
        instrument_type=api_data.get("assetType"),
    )


def create_stream_event_from_message(
    symbol: str, message_data: dict[str, Any], event_type: str = "quote"
) -> StreamEvent:
    """
    Create StreamEvent from streaming message data.

    Args:
        symbol: Trading symbol
        message_data: Raw streaming message data
        event_type: Type of streaming event

    Returns:
        StreamEvent object
    """
    return StreamEvent(
        symbol=symbol,
        event_type=event_type,
        data=message_data,
        sequence_id=message_data.get("sequence"),
        exchange=message_data.get("exchange"),
    )


# Type aliases for convenience
QuoteDict = dict[str, Any]
StreamEventDict = dict[str, Any]

# Export symbols for easy imports
__all__ = [
    "InstrumentType",
    "Quote",
    "StreamEvent",
    "create_quote_from_api_response",
    "create_stream_event_from_message",
    "QuoteDict",
    "StreamEventDict",
]
