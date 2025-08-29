"""
Pytest configuration and shared fixtures.

Provides test fixtures for database, API client, and service mocking
with proper test isolation and async support.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
import tempfile
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.backend.config import Settings
from src.backend.database.connection import get_db_session
from src.backend.main import create_app
from src.backend.models.base import Base
from src.backend.models.instruments import Instrument, InstrumentType, InstrumentStatus
from src.backend.models.alert_rules import AlertRule, RuleType, RuleCondition
from src.backend.services.data_ingestion import DataIngestionService
from src.backend.services.alert_engine import AlertEngine


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine with in-memory SQLite."""
    # Use in-memory SQLite for tests
    database_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        # Start a transaction
        transaction = await session.begin()
        
        yield session
        
        # Rollback transaction to clean up
        await transaction.rollback()


@pytest.fixture
def test_settings():
    """Create test configuration settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        SCHWAB_CLIENT_ID="test_client_id",
        SCHWAB_CLIENT_SECRET="test_client_secret",
        SCHWAB_REDIRECT_URI="http://localhost:8080/callback",
        SOUND_ALERTS_ENABLED=False,
        SLACK_BOT_TOKEN="",
        TARGET_FUTURES=["ES", "NQ"],
        TARGET_INDICES=["SPX"],
        TARGET_INTERNALS=["VIX"],
    )


@pytest_asyncio.fixture
async def test_app(test_settings, monkeypatch):
    """Create test FastAPI application with mocked dependencies."""
    # Mock the settings
    monkeypatch.setattr("src.backend.config.settings", test_settings)
    
    # Create test app
    app = create_app()
    
    yield app


@pytest_asyncio.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=test_app, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def sample_instruments(test_session):
    """Create sample instruments for testing."""
    instruments = [
        Instrument(
            symbol="ES",
            name="E-mini S&P 500",
            type=InstrumentType.FUTURE,
            status=InstrumentStatus.ACTIVE,
        ),
        Instrument(
            symbol="NQ",
            name="E-mini Nasdaq-100",
            type=InstrumentType.FUTURE,
            status=InstrumentStatus.ACTIVE,
        ),
        Instrument(
            symbol="SPX",
            name="S&P 500 Index",
            type=InstrumentType.INDEX,
            status=InstrumentStatus.ACTIVE,
        ),
    ]
    
    for instrument in instruments:
        test_session.add(instrument)
    
    await test_session.commit()
    
    # Refresh to get IDs
    for instrument in instruments:
        await test_session.refresh(instrument)
    
    return instruments


@pytest_asyncio.fixture
async def sample_alert_rule(test_session, sample_instruments) -> AlertRule:
    """Create a sample alert rule for testing."""
    rule = AlertRule(
        instrument_id=sample_instruments[0].id,
        rule_type=RuleType.THRESHOLD,
        condition=RuleCondition.ABOVE,
        threshold=4500.0,
        active=True,
        name="Test Rule",
        description="Test alert rule",
        cooldown_seconds=60,
    )
    
    test_session.add(rule)
    await test_session.commit()
    await test_session.refresh(rule)
    
    return rule


@pytest.fixture
def mock_schwab_data():
    """Mock Schwab API market data responses."""
    return {
        "ES": {
            "symbol": "ES",
            "lastPrice": 4525.75,
            "bid": 4525.50,
            "ask": 4525.75,
            "volume": 1000,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "NQ": {
            "symbol": "NQ",
            "lastPrice": 15250.25,
            "bid": 15250.00,
            "ask": 15250.25,
            "volume": 500,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@pytest.fixture
def mock_schwab_client(monkeypatch, mock_schwab_data):
    """Mock Schwab API client for testing."""
    class MockSchwabClient:
        def __init__(self):
            self.data_callback = None
            self.is_connected = False
        
        def set_data_callback(self, callback):
            self.data_callback = callback
        
        async def start_streaming(self, symbols):
            self.is_connected = True
            # Simulate data callback
            if self.data_callback:
                for symbol in symbols:
                    if symbol in mock_schwab_data:
                        await self.data_callback(symbol, mock_schwab_data[symbol])
            return True
        
        async def stop_streaming(self):
            self.is_connected = False
        
        async def close(self):
            await self.stop_streaming()
    
    # Patch the real Schwab client
    monkeypatch.setattr(
        "src.backend.services.data_ingestion.SchwabRealTimeClient",
        lambda: MockSchwabClient()
    )
    
    return MockSchwabClient()


@pytest_asyncio.fixture
async def data_ingestion_service(test_settings, mock_schwab_client):
    """Create test data ingestion service with mocked Schwab client."""
    service = DataIngestionService()
    # Replace the Schwab client with mock
    service.schwab_client = mock_schwab_client
    return service


@pytest_asyncio.fixture
async def alert_engine_service():
    """Create test alert engine service."""
    return AlertEngine()


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_market_data_tick(
        symbol: str = "ES",
        price: float = 4500.0,
        volume: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """Create normalized market data tick."""
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow(),
            "price": price,
            "volume": volume,
            "bid": kwargs.get("bid", price - 0.25),
            "ask": kwargs.get("ask", price + 0.25),
            "bid_size": kwargs.get("bid_size", 10),
            "ask_size": kwargs.get("ask_size", 10),
            "open_price": kwargs.get("open_price", price - 10),
            "high_price": kwargs.get("high_price", price + 5),
            "low_price": kwargs.get("low_price", price - 5),
        }


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory