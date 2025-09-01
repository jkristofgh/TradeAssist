"""
Alert log model definition.

Represents fired alerts with context capture and delivery tracking
for audit trails and notification management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, Float, String, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from ..database.mixins import SoftDeleteMixin


class AlertStatus(str, Enum):
    """Status of alert firing."""
    FIRED = "fired"
    SUPPRESSED = "suppressed"
    ERROR = "error"


class DeliveryStatus(str, Enum):
    """Status of alert delivery to notification channels."""
    PENDING = "pending"
    IN_APP_SENT = "in_app_sent"
    SOUND_PLAYED = "sound_played"
    SLACK_SENT = "slack_sent"
    ALL_DELIVERED = "all_delivered"
    FAILED = "failed"


class AlertLog(Base, SoftDeleteMixin):
    """
    Alert log entry model.
    
    Records all fired alerts with full context capture including
    rule details, trigger values, and delivery status tracking.
    Optimized for fast insertion and historical queries.
    """
    
    __tablename__ = "alert_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Alert timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        doc="Alert firing timestamp"
    )
    
    # References
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to the rule that fired"
    )
    
    instrument_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to the instrument that triggered the alert"
    )
    
    # Alert context
    trigger_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Value that triggered the alert"
    )
    
    threshold_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Threshold value from the rule"
    )
    
    # Alert processing
    fired_status: Mapped[AlertStatus] = mapped_column(
        String(20),
        default=AlertStatus.FIRED,
        nullable=False,
        doc="Status of alert firing"
    )
    
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        String(20),
        default=DeliveryStatus.PENDING,
        nullable=False,
        doc="Status of alert delivery"
    )
    
    # Performance metrics
    evaluation_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Rule evaluation time in milliseconds"
    )
    
    # Additional context
    rule_condition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Rule condition at time of firing"
    )
    
    alert_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Generated alert message text"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if delivery failed"
    )
    
    # Delivery timestamps
    delivery_attempted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When delivery was attempted"
    )
    
    delivery_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When delivery was completed"
    )
    
    # Relationships
    rule: Mapped["AlertRule"] = relationship(
        "AlertRule",
        back_populates="alert_logs",
        lazy="select"
    )
    
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="alert_logs",
        lazy="select"
    )
    
    # Optimized indexes for high-frequency INSERT performance (Phase 1 optimized)
    __table_args__ = (
        # Primary timestamp index for time-series queries
        Index("ix_alert_logs_timestamp", "timestamp"),
        # Composite index for rule-based queries
        Index("ix_alert_logs_rule_timestamp", "rule_id", "timestamp"),
        # Composite index for instrument-based queries
        Index("ix_alert_logs_timestamp_instrument", "timestamp", "instrument_id"),
        # Composite status index for delivery tracking
        Index("ix_alert_logs_status", "fired_status", "delivery_status"),
    )
    
    def __repr__(self) -> str:
        """String representation of alert log."""
        return (
            f"<AlertLog("
            f"id={self.id}, "
            f"rule_id={self.rule_id}, "
            f"instrument_id={self.instrument_id}, "
            f"timestamp={self.timestamp}, "
            f"trigger_value={self.trigger_value}, "
            f"status='{self.fired_status.value}')>"
        )