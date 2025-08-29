"""
Unit tests for database models.

Tests model validation, relationships, and business logic
with comprehensive coverage of all model classes.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.backend.models.instruments import Instrument, InstrumentType, InstrumentStatus
from src.backend.models.market_data import MarketData
from src.backend.models.alert_rules import AlertRule, RuleType, RuleCondition
from src.backend.models.alert_logs import AlertLog, AlertStatus, DeliveryStatus


class TestInstrumentModel:
    """Test cases for Instrument model."""
    
    def test_instrument_creation(self):
        """Test creating an instrument with valid data."""
        instrument = Instrument(
            symbol="ES",
            name="E-mini S&P 500",
            type=InstrumentType.FUTURE,
            status=InstrumentStatus.ACTIVE,
        )
        
        assert instrument.symbol == "ES"
        assert instrument.name == "E-mini S&P 500"
        assert instrument.type == InstrumentType.FUTURE
        assert instrument.status == InstrumentStatus.ACTIVE
        assert instrument.last_tick is None
        assert instrument.last_price is None
    
    def test_instrument_with_last_tick(self):
        """Test instrument with last tick data."""
        now = datetime.utcnow()
        instrument = Instrument(
            symbol="NQ",
            name="E-mini Nasdaq-100",
            type=InstrumentType.FUTURE,
            status=InstrumentStatus.ACTIVE,
            last_tick=now,
            last_price=Decimal("15250.25"),
        )
        
        assert instrument.last_tick == now
        assert instrument.last_price == Decimal("15250.25")
    
    def test_instrument_string_representation(self):
        """Test instrument string representation."""
        instrument = Instrument(
            id=1,
            symbol="SPX",
            name="S&P 500 Index",
            type=InstrumentType.INDEX,
            status=InstrumentStatus.ACTIVE,
        )
        
        expected = "<Instrument(id=1, symbol='SPX', type='index', status='active')>"
        assert repr(instrument) == expected


class TestMarketDataModel:
    """Test cases for MarketData model."""
    
    @pytest.mark.asyncio
    async def test_market_data_creation(self, sample_instruments):
        """Test creating market data with valid data."""
        instrument = sample_instruments[0]
        now = datetime.utcnow()
        
        market_data = MarketData(
            timestamp=now,
            instrument_id=instrument.id,
            price=Decimal("4525.75"),
            volume=1000,
            bid=Decimal("4525.50"),
            ask=Decimal("4525.75"),
        )
        
        assert market_data.timestamp == now
        assert market_data.instrument_id == instrument.id
        assert market_data.price == Decimal("4525.75")
        assert market_data.volume == 1000
        assert market_data.bid == Decimal("4525.50")
        assert market_data.ask == Decimal("4525.75")
    
    @pytest.mark.asyncio
    async def test_market_data_optional_fields(self, sample_instruments):
        """Test market data with optional fields."""
        instrument = sample_instruments[0]
        
        market_data = MarketData(
            timestamp=datetime.utcnow(),
            instrument_id=instrument.id,
            price=Decimal("4500.00"),
            bid_size=50,
            ask_size=25,
            open_price=Decimal("4490.00"),
            high_price=Decimal("4510.00"),
            low_price=Decimal("4485.00"),
        )
        
        assert market_data.bid_size == 50
        assert market_data.ask_size == 25
        assert market_data.open_price == Decimal("4490.00")
        assert market_data.high_price == Decimal("4510.00")
        assert market_data.low_price == Decimal("4485.00")
        assert market_data.volume is None  # Optional field


class TestAlertRuleModel:
    """Test cases for AlertRule model."""
    
    @pytest.mark.asyncio
    async def test_alert_rule_creation(self, sample_instruments):
        """Test creating an alert rule with valid data."""
        instrument = sample_instruments[0]
        
        rule = AlertRule(
            instrument_id=instrument.id,
            rule_type=RuleType.THRESHOLD,
            condition=RuleCondition.ABOVE,
            threshold=Decimal("4500.00"),
            active=True,
            name="Test Threshold Rule",
            description="Alert when ES is above 4500",
            cooldown_seconds=60,
        )
        
        assert rule.instrument_id == instrument.id
        assert rule.rule_type == RuleType.THRESHOLD
        assert rule.condition == RuleCondition.ABOVE
        assert rule.threshold == Decimal("4500.00")
        assert rule.active is True
        assert rule.name == "Test Threshold Rule"
        assert rule.cooldown_seconds == 60
    
    @pytest.mark.asyncio
    async def test_alert_rule_rate_of_change(self, sample_instruments):
        """Test rate-of-change alert rule."""
        instrument = sample_instruments[0]
        
        rule = AlertRule(
            instrument_id=instrument.id,
            rule_type=RuleType.RATE_OF_CHANGE,
            condition=RuleCondition.PERCENT_CHANGE_UP,
            threshold=Decimal("2.5"),  # 2.5% change
            time_window_seconds=300,  # 5 minutes
            active=True,
        )
        
        assert rule.rule_type == RuleType.RATE_OF_CHANGE
        assert rule.condition == RuleCondition.PERCENT_CHANGE_UP
        assert rule.threshold == Decimal("2.5")
        assert rule.time_window_seconds == 300
    
    def test_cooldown_check_no_trigger(self):
        """Test cooldown check when rule has never been triggered."""
        rule = AlertRule(
            instrument_id=1,
            rule_type=RuleType.THRESHOLD,
            condition=RuleCondition.ABOVE,
            threshold=Decimal("4500.00"),
            cooldown_seconds=60,
        )
        
        # Should not be in cooldown if never triggered
        assert not rule.is_in_cooldown()
    
    def test_cooldown_check_recently_triggered(self):
        """Test cooldown check when rule was recently triggered."""
        rule = AlertRule(
            instrument_id=1,
            rule_type=RuleType.THRESHOLD,
            condition=RuleCondition.ABOVE,
            threshold=Decimal("4500.00"),
            cooldown_seconds=60,
            last_triggered=datetime.utcnow() - timedelta(seconds=30),  # 30 seconds ago
        )
        
        # Should be in cooldown
        assert rule.is_in_cooldown()
    
    def test_cooldown_check_expired(self):
        """Test cooldown check when cooldown period has expired."""
        rule = AlertRule(
            instrument_id=1,
            rule_type=RuleType.THRESHOLD,
            condition=RuleCondition.ABOVE,
            threshold=Decimal("4500.00"),
            cooldown_seconds=60,
            last_triggered=datetime.utcnow() - timedelta(seconds=120),  # 2 minutes ago
        )
        
        # Should not be in cooldown
        assert not rule.is_in_cooldown()


class TestAlertLogModel:
    """Test cases for AlertLog model."""
    
    @pytest.mark.asyncio
    async def test_alert_log_creation(self, sample_alert_rule):
        """Test creating an alert log entry."""
        rule = sample_alert_rule
        now = datetime.utcnow()
        
        alert_log = AlertLog(
            timestamp=now,
            rule_id=rule.id,
            instrument_id=rule.instrument_id,
            trigger_value=Decimal("4525.75"),
            threshold_value=Decimal("4500.00"),
            fired_status=AlertStatus.FIRED,
            delivery_status=DeliveryStatus.PENDING,
            rule_condition=rule.condition.value,
            evaluation_time_ms=450,
            alert_message="ES price 4525.75 above threshold 4500.00",
        )
        
        assert alert_log.timestamp == now
        assert alert_log.rule_id == rule.id
        assert alert_log.instrument_id == rule.instrument_id
        assert alert_log.trigger_value == Decimal("4525.75")
        assert alert_log.threshold_value == Decimal("4500.00")
        assert alert_log.fired_status == AlertStatus.FIRED
        assert alert_log.delivery_status == DeliveryStatus.PENDING
        assert alert_log.evaluation_time_ms == 450
    
    @pytest.mark.asyncio
    async def test_alert_log_with_delivery_timestamps(self, sample_alert_rule):
        """Test alert log with delivery timestamps."""
        rule = sample_alert_rule
        now = datetime.utcnow()
        delivered_at = now + timedelta(milliseconds=100)
        
        alert_log = AlertLog(
            timestamp=now,
            rule_id=rule.id,
            instrument_id=rule.instrument_id,
            trigger_value=Decimal("4525.75"),
            threshold_value=Decimal("4500.00"),
            fired_status=AlertStatus.FIRED,
            delivery_status=DeliveryStatus.ALL_DELIVERED,
            rule_condition=rule.condition.value,
            delivery_attempted_at=now + timedelta(milliseconds=50),
            delivery_completed_at=delivered_at,
        )
        
        assert alert_log.delivery_attempted_at == now + timedelta(milliseconds=50)
        assert alert_log.delivery_completed_at == delivered_at
        assert alert_log.delivery_status == DeliveryStatus.ALL_DELIVERED
    
    def test_alert_log_string_representation(self):
        """Test alert log string representation."""
        alert_log = AlertLog(
            id=1,
            rule_id=10,
            instrument_id=5,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            trigger_value=Decimal("4525.75"),
            threshold_value=Decimal("4500.00"),
            fired_status=AlertStatus.FIRED,
            delivery_status=DeliveryStatus.PENDING,
            rule_condition="above",
        )
        
        expected = (
            "<AlertLog("
            "id=1, "
            "rule_id=10, "
            "instrument_id=5, "
            "timestamp=2025-01-01 12:00:00, "
            "trigger_value=4525.75, "
            "status='fired')>"
        )
        assert repr(alert_log) == expected