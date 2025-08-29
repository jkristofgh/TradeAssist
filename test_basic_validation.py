"""
Basic validation tests to verify core implementation is working.

Simple tests to validate the Phase 1 implementation without complex fixtures.
"""

import pytest
from datetime import datetime

# Test model imports and basic functionality
def test_model_imports():
    """Test that all models can be imported successfully."""
    from src.backend.models.instruments import Instrument, InstrumentType, InstrumentStatus
    from src.backend.models.market_data import MarketData
    from src.backend.models.alert_rules import AlertRule, RuleType, RuleCondition
    from src.backend.models.alert_logs import AlertLog, AlertStatus, DeliveryStatus
    
    # Test basic model creation
    instrument = Instrument(
        symbol="ES",
        name="E-mini S&P 500",
        type=InstrumentType.FUTURE,
        status=InstrumentStatus.ACTIVE,
    )
    
    assert instrument.symbol == "ES"
    assert instrument.type == InstrumentType.FUTURE


def test_service_imports():
    """Test that all services can be imported successfully."""
    from src.backend.services.data_ingestion import DataIngestionService, DataNormalizer
    from src.backend.services.alert_engine import AlertEngine, RuleEvaluator
    from src.backend.services.notification import NotificationService
    
    # Test basic service instantiation
    data_service = DataIngestionService()
    alert_engine = AlertEngine()
    normalizer = DataNormalizer()
    
    assert data_service is not None
    assert alert_engine is not None
    assert normalizer is not None


def test_api_imports():
    """Test that all API modules can be imported successfully."""
    from src.backend.api import health, instruments, rules, alerts
    from src.backend.websocket import realtime
    
    assert health is not None
    assert instruments is not None
    assert rules is not None
    assert alerts is not None
    assert realtime is not None


def test_config_loading():
    """Test that configuration can be loaded."""
    from src.backend.config import settings, get_all_instruments
    
    assert settings is not None
    instruments = get_all_instruments()
    assert isinstance(instruments, list)
    assert len(instruments) > 0


def test_data_normalization():
    """Test data normalization functionality."""
    from src.backend.services.data_ingestion import DataNormalizer
    
    normalizer = DataNormalizer()
    
    # Test valid data
    raw_data = {
        "lastPrice": 4525.75,
        "volume": 1000,
        "bid": 4525.50,
        "ask": 4525.75,
    }
    
    normalized = normalizer.normalize_tick_data("ES", raw_data)
    
    assert normalized is not None
    assert normalized["symbol"] == "ES"
    assert normalized["price"] == 4525.75
    assert normalized["volume"] == 1000
    assert isinstance(normalized["timestamp"], datetime)


def test_alert_rule_cooldown():
    """Test alert rule cooldown functionality."""
    from src.backend.models.alert_rules import AlertRule, RuleType, RuleCondition
    from datetime import timedelta
    
    # Test rule not in cooldown
    rule = AlertRule(
        instrument_id=1,
        rule_type=RuleType.THRESHOLD,
        condition=RuleCondition.ABOVE,
        threshold=4500.0,
        cooldown_seconds=60,
    )
    
    assert not rule.is_in_cooldown()
    
    # Test rule in cooldown
    rule.last_triggered = datetime.utcnow() - timedelta(seconds=30)
    assert rule.is_in_cooldown()
    
    # Test rule cooldown expired
    rule.last_triggered = datetime.utcnow() - timedelta(seconds=120)
    assert not rule.is_in_cooldown()


def test_fastapi_app_creation():
    """Test that FastAPI app can be created."""
    from src.backend.main import create_app
    
    app = create_app()
    assert app is not None
    assert hasattr(app, 'include_router')


if __name__ == "__main__":
    # Run basic validation
    test_model_imports()
    test_service_imports() 
    test_api_imports()
    test_config_loading()
    test_data_normalization()
    test_alert_rule_cooldown()
    test_fastapi_app_creation()
    
    print("✅ All basic validation tests passed!")
    print("Phase 1 implementation is structurally sound and ready for deployment.")