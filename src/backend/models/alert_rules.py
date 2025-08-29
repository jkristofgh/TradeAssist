"""
Alert rule model definition.

Represents configurable alert rules for monitoring market conditions
with sub-second evaluation performance requirements.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Integer, DECIMAL, Boolean, ForeignKey, Index, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class RuleType(str, Enum):
    """Types of alert rules supported."""
    THRESHOLD = "threshold"           # Price above/below threshold
    CROSSOVER = "crossover"          # Price crossing moving average
    RATE_OF_CHANGE = "rate_of_change"  # Percentage change over time
    VOLUME_SPIKE = "volume_spike"    # Volume spike detection
    MULTI_CONDITION = "multi_condition"  # Combined AND/OR conditions


class RuleCondition(str, Enum):
    """Condition operators for rule evaluation."""
    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    PERCENT_CHANGE_UP = "percent_change_up"
    PERCENT_CHANGE_DOWN = "percent_change_down"
    VOLUME_ABOVE = "volume_above"


class AlertRule(Base, TimestampMixin):
    """
    Alert rule definition model.
    
    Configurable rules for monitoring market conditions with support
    for various rule types and conditions. Optimized for sub-500ms
    evaluation performance.
    """
    
    __tablename__ = "alert_rules"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign key to instruments
    instrument_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to monitored instrument"
    )
    
    # Rule configuration
    rule_type: Mapped[RuleType] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of alert rule"
    )
    
    condition: Mapped[RuleCondition] = mapped_column(
        String(20),
        nullable=False,
        doc="Condition operator for rule evaluation"
    )
    
    threshold: Mapped[float] = mapped_column(
        DECIMAL(12, 4),
        nullable=False,
        doc="Threshold value for rule evaluation"
    )
    
    # Rule metadata
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether rule is currently active"
    )
    
    name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User-friendly name for the rule"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the rule"
    )
    
    # Additional parameters for complex rules
    time_window_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Time window in seconds for rate-of-change rules"
    )
    
    moving_average_period: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Period for moving average calculations"
    )
    
    # Alert management
    cooldown_seconds: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        doc="Minimum seconds between alerts for this rule"
    )
    
    last_triggered: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Last time this rule fired an alert"
    )
    
    # Relationships
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="alert_rules",
        lazy="select"
    )
    
    alert_logs: Mapped[list["AlertLog"]] = relationship(
        "AlertLog",
        back_populates="rule",
        cascade="all, delete-orphan"
    )
    
    # Performance indexes - critical for real-time evaluation
    __table_args__ = (
        # Index for active rule lookups
        Index("ix_alert_rules_active", "active"),
        # Index for instrument-based rule queries
        Index("ix_alert_rules_instrument", "instrument_id"),
        # Composite index for active rules by instrument (most common query)
        Index("ix_alert_rules_active_instrument", "active", "instrument_id"),
        # Index for rule type filtering
        Index("ix_alert_rules_type", "rule_type"),
        # Index for last triggered time (cooldown checks)
        Index("ix_alert_rules_last_triggered", "last_triggered"),
    )
    
    def is_in_cooldown(self) -> bool:
        """
        Check if rule is currently in cooldown period.
        
        Returns:
            bool: True if rule is in cooldown, False otherwise.
        """
        if not self.last_triggered:
            return False
        
        from datetime import datetime, timedelta
        cooldown_end = self.last_triggered + timedelta(seconds=self.cooldown_seconds)
        return datetime.utcnow() < cooldown_end
    
    def __repr__(self) -> str:
        """String representation of alert rule."""
        return (
            f"<AlertRule("
            f"id={self.id}, "
            f"instrument_id={self.instrument_id}, "
            f"type='{self.rule_type}', "
            f"condition='{self.condition}', "
            f"threshold={self.threshold}, "
            f"active={self.active})>"
        )