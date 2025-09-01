"""
Comprehensive WebSocket Message Type System

Implements typed WebSocket message classes with Pydantic validation,
versioning support, and message routing for real-time communication.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageVersion(str, Enum):
    """Message format version enumeration for compatibility management."""
    V1_0 = "1.0"
    CURRENT = V1_0


class WebSocketMessage(BaseModel, ABC):
    """Base class for all WebSocket messages with version support."""
    
    message_type: str = Field(..., description="Type identifier for message routing")
    version: MessageVersion = Field(default=MessageVersion.CURRENT, description="Message format version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    
    @validator('timestamp', pre=True)
    def serialize_timestamp(cls, v):
        if isinstance(v, datetime):
            return v.isoformat() + 'Z'
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


# =============================================================================
# MARKET DATA MESSAGES
# =============================================================================

class MarketDataUpdate(BaseModel):
    """Market data update payload."""
    instrument_id: int
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    change_percent: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None


class MarketDataMessage(WebSocketMessage):
    """Real-time market data updates."""
    message_type: Literal["market_data"] = "market_data"
    data: MarketDataUpdate


# =============================================================================
# ALERT MESSAGES
# =============================================================================

class AlertNotification(BaseModel):
    """Alert notification payload."""
    alert_id: int
    rule_id: int
    instrument_id: int
    symbol: str
    rule_name: str
    condition: str
    target_value: float
    current_value: float
    severity: Literal["low", "medium", "high"]
    message: str
    evaluation_time_ms: Optional[int] = None
    rule_condition: str


class AlertMessage(WebSocketMessage):
    """Alert notifications."""
    message_type: Literal["alert"] = "alert"
    data: AlertNotification


# =============================================================================
# ANALYTICS MESSAGES
# =============================================================================

class AnalyticsUpdate(BaseModel):
    """Analytics update payload."""
    instrument_id: int
    symbol: str
    analysis_type: str
    results: Dict[str, Any]
    calculation_time: datetime
    next_update: Optional[datetime] = None
    confidence_score: Optional[float] = None
    data_quality_score: Optional[float] = None


class AnalyticsMessage(WebSocketMessage):
    """Real-time analytics updates."""
    message_type: Literal["analytics_update"] = "analytics_update"
    data: AnalyticsUpdate


# =============================================================================
# TECHNICAL INDICATOR MESSAGES
# =============================================================================

class TechnicalIndicatorUpdate(BaseModel):
    """Technical indicator update payload."""
    instrument_id: int
    symbol: str
    indicators: Dict[str, Any]  # RSI, MACD, Bollinger Bands, etc.
    calculated_at: datetime
    timeframe: str = "1min"
    indicator_quality: Optional[Dict[str, float]] = None


class TechnicalIndicatorMessage(WebSocketMessage):
    """Real-time technical indicator updates."""
    message_type: Literal["technical_indicators"] = "technical_indicators"
    data: TechnicalIndicatorUpdate


# =============================================================================
# PRICE PREDICTION MESSAGES
# =============================================================================

class PricePredictionUpdate(BaseModel):
    """Price prediction update payload."""
    instrument_id: int
    symbol: str
    predicted_price: float
    confidence_interval: Dict[str, float]  # {"lower": x, "upper": y}
    prediction_horizon_minutes: int
    model_name: str
    prediction_accuracy: Optional[float] = None
    calculated_at: datetime


class PricePredictionMessage(WebSocketMessage):
    """ML-based price prediction updates."""
    message_type: Literal["price_prediction"] = "price_prediction"
    data: PricePredictionUpdate


# =============================================================================
# RISK METRICS MESSAGES
# =============================================================================

class RiskMetricsUpdate(BaseModel):
    """Risk metrics update payload."""
    instrument_id: int
    symbol: str
    var_1d: float  # Value at Risk 1 day
    var_5d: float  # Value at Risk 5 day
    volatility: float
    beta: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    calculated_at: datetime


class RiskMetricsMessage(WebSocketMessage):
    """Risk metrics updates."""
    message_type: Literal["risk_metrics"] = "risk_metrics"
    data: RiskMetricsUpdate


# =============================================================================
# CONNECTION MANAGEMENT MESSAGES
# =============================================================================

class ConnectionStatus(BaseModel):
    """Connection status information."""
    client_id: str
    connected_at: datetime
    subscriptions: List[str]
    last_heartbeat: datetime
    connection_quality: Optional[str] = "good"  # good, degraded, poor
    message_count: Optional[int] = 0


class ConnectionMessage(WebSocketMessage):
    """Connection status and heartbeat messages."""
    message_type: Literal["connection_status"] = "connection_status"
    data: ConnectionStatus


class ErrorDetails(BaseModel):
    """Error information payload."""
    error_code: str
    error_message: str
    request_id: Optional[str] = None
    timestamp: datetime
    severity: Literal["warning", "error", "critical"] = "error"
    retry_after: Optional[int] = None  # Seconds to wait before retry


class ErrorMessage(WebSocketMessage):
    """Error notifications."""
    message_type: Literal["error"] = "error"
    data: ErrorDetails


# =============================================================================
# SUBSCRIPTION MESSAGES
# =============================================================================

class SubscriptionRequest(BaseModel):
    """Subscription request payload."""
    subscription_type: str  # analytics, market_data, technical_indicators
    instrument_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class SubscriptionMessage(WebSocketMessage):
    """Subscription request messages."""
    message_type: Literal["subscribe"] = "subscribe"
    data: SubscriptionRequest


class UnsubscriptionRequest(BaseModel):
    """Unsubscription request payload."""
    subscription_type: str
    instrument_id: Optional[int] = None
    request_id: Optional[str] = None


class UnsubscriptionMessage(WebSocketMessage):
    """Unsubscription request messages."""
    message_type: Literal["unsubscribe"] = "unsubscribe"
    data: UnsubscriptionRequest


class SubscriptionAcknowledgment(BaseModel):
    """Subscription acknowledgment payload."""
    subscription_type: str
    instrument_id: Optional[int] = None
    status: Literal["subscribed", "unsubscribed", "failed"]
    message: Optional[str] = None
    request_id: Optional[str] = None


class SubscriptionAckMessage(WebSocketMessage):
    """Subscription acknowledgment messages."""
    message_type: Literal["subscription_ack"] = "subscription_ack"
    data: SubscriptionAcknowledgment


# =============================================================================
# HEARTBEAT MESSAGES
# =============================================================================

class PingData(BaseModel):
    """Ping message payload."""
    client_time: datetime
    sequence: Optional[int] = None


class PingMessage(WebSocketMessage):
    """Ping messages for connection health."""
    message_type: Literal["ping"] = "ping"
    data: PingData


class PongData(BaseModel):
    """Pong message payload."""
    client_time: datetime
    server_time: datetime
    sequence: Optional[int] = None
    latency_ms: Optional[float] = None


class PongMessage(WebSocketMessage):
    """Pong responses for connection health."""
    message_type: Literal["pong"] = "pong"
    data: PongData


# =============================================================================
# MESSAGE UNIONS
# =============================================================================

# Incoming messages (from client to server)
IncomingMessage = Union[
    PingMessage,
    SubscriptionMessage,
    UnsubscriptionMessage
]

# Outgoing messages (from server to client)
OutgoingMessage = Union[
    MarketDataMessage,
    AlertMessage,
    AnalyticsMessage,
    TechnicalIndicatorMessage,
    PricePredictionMessage,
    RiskMetricsMessage,
    ConnectionMessage,
    ErrorMessage,
    SubscriptionAckMessage,
    PongMessage
]

# All message types
AllMessages = Union[IncomingMessage, OutgoingMessage]


# =============================================================================
# MESSAGE TYPE REGISTRY
# =============================================================================

MESSAGE_TYPE_REGISTRY = {
    "market_data": MarketDataMessage,
    "alert": AlertMessage,
    "analytics_update": AnalyticsMessage,
    "technical_indicators": TechnicalIndicatorMessage,
    "price_prediction": PricePredictionMessage,
    "risk_metrics": RiskMetricsMessage,
    "connection_status": ConnectionMessage,
    "error": ErrorMessage,
    "ping": PingMessage,
    "pong": PongMessage,
    "subscribe": SubscriptionMessage,
    "unsubscribe": UnsubscriptionMessage,
    "subscription_ack": SubscriptionAckMessage,
}


def get_message_class(message_type: str) -> Optional[type]:
    """
    Get message class by type string.
    
    Args:
        message_type: Message type identifier.
        
    Returns:
        Message class or None if not found.
    """
    return MESSAGE_TYPE_REGISTRY.get(message_type)


def validate_message_type(message_type: str) -> bool:
    """
    Validate if message type is supported.
    
    Args:
        message_type: Message type to validate.
        
    Returns:
        True if supported, False otherwise.
    """
    return message_type in MESSAGE_TYPE_REGISTRY