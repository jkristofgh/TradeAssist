"""
Application Configuration Management.

Uses Pydantic settings for type-safe configuration management
with environment variable support and validation.
"""

from enum import Enum
from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    """Available logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    """
    
    # Application Settings
    HOST: str = Field(default="127.0.0.1", description="API host address")
    PORT: int = Field(default=8000, description="API port")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/trade_assist.db",
        description="SQLite database file path"
    )
    MARKET_DATA_RETENTION_DAYS: int = Field(
        default=30,
        description="Number of days to retain market data"
    )
    
    # Schwab API Configuration
    SCHWAB_CLIENT_ID: str = Field(
        default="",
        description="Schwab API client identifier"
    )
    SCHWAB_CLIENT_SECRET: str = Field(
        default="",
        description="Schwab API client secret"
    )
    SCHWAB_REDIRECT_URI: str = Field(
        default="http://localhost:8080/callback",
        description="OAuth redirect URI"
    )
    
    # Historical Data Service Configuration
    HISTORICAL_DATA_CACHE_TTL: int = Field(
        default=300,  # 5 minutes
        description="Historical data cache TTL in seconds"
    )
    HISTORICAL_DATA_MAX_SYMBOLS_PER_REQUEST: int = Field(
        default=50,
        description="Maximum symbols per historical data request"
    )
    HISTORICAL_DATA_MAX_RECORDS_DEFAULT: int = Field(
        default=10000,
        description="Default maximum records per symbol for historical data requests"
    )
    HISTORICAL_DATA_RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Historical data API rate limit requests per minute"
    )
    HISTORICAL_DATA_BATCH_SIZE: int = Field(
        default=25,
        description="Batch size for historical data fetching from Schwab API"
    )
    HISTORICAL_DATA_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Number of retry attempts for failed historical data requests"
    )
    HISTORICAL_DATA_RETRY_DELAY: int = Field(
        default=1,
        description="Delay between retry attempts in seconds"
    )
    
    # Database Connection and Query Settings
    DATABASE_QUERY_TIMEOUT: int = Field(
        default=30,
        description="Database query timeout in seconds"
    )
    DATABASE_CONNECTION_POOL_SIZE: int = Field(
        default=10,
        description="Database connection pool size"
    )
    DATABASE_CONNECTION_OVERFLOW: int = Field(
        default=20,
        description="Database connection pool overflow size"
    )
    
    # Performance Configuration
    MAX_WEBSOCKET_CONNECTIONS: int = Field(
        default=10,
        description="Maximum concurrent WebSocket connections"
    )
    ALERT_EVALUATION_INTERVAL_MS: int = Field(
        default=100,
        description="Alert evaluation interval in milliseconds"
    )
    DATA_INGESTION_BATCH_SIZE: int = Field(
        default=100,
        description="Batch size for data ingestion"
    )
    
    # Cache Configuration (Redis-compatible for future use)
    CACHE_BACKEND: str = Field(
        default="memory",
        description="Cache backend type (memory, redis)"
    )
    CACHE_REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching (when cache backend is redis)"
    )
    CACHE_DEFAULT_TTL: int = Field(
        default=300,
        description="Default cache TTL in seconds"
    )
    
    # Notification Configuration
    SLACK_BOT_TOKEN: str = Field(
        default="",
        description="Slack bot token for notifications"
    )
    SLACK_CHANNEL: str = Field(
        default="#trading-alerts",
        description="Default Slack channel for alerts"
    )
    SOUND_ALERTS_ENABLED: bool = Field(
        default=True,
        description="Enable sound alerts"
    )
    
    # Google Cloud Configuration
    GCP_PROJECT_ID: str = Field(
        default="",
        description="Google Cloud Project ID for Secret Manager"
    )
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(
        default="",
        description="Path to Google Cloud service account credentials JSON"
    )
    
    # Production Logging Configuration
    LOG_TO_FILE: bool = Field(
        default=False,
        description="Enable logging to file"
    )
    LOG_FILE_PATH: str = Field(
        default="./logs/tradeassist.log",
        description="Log file path"
    )
    LOG_FILE_MAX_SIZE: int = Field(
        default=10485760,  # 10MB
        description="Maximum log file size in bytes"
    )
    LOG_FILE_BACKUP_COUNT: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    # Demo mode for testing
    DEMO_MODE: bool = Field(
        default=False,
        description="Run in demo mode without real API connections"
    )
    
    # Target Instruments for Real-time Streaming (as strings from env)
    TARGET_FUTURES_STR: str = Field(
        default="ES,NQ,YM,CL,GC",
        description="Futures symbols for real-time streaming (comma-separated)"
    )
    TARGET_INDICES_STR: str = Field(
        default="SPX,NDX,RUT",
        description="Index symbols for real-time streaming (comma-separated)"
    )
    TARGET_INTERNALS_STR: str = Field(
        default="VIX,TICK,ADD,TRIN",
        description="Market internals symbols for real-time streaming (comma-separated)"
    )
    
    @property
    def TARGET_FUTURES(self) -> List[str]:
        """Get futures symbols as list."""
        if not self.TARGET_FUTURES_STR.strip():
            return []
        return [item.strip() for item in self.TARGET_FUTURES_STR.split(',') if item.strip()]
    
    @property
    def TARGET_INDICES(self) -> List[str]:
        """Get index symbols as list."""
        if not self.TARGET_INDICES_STR.strip():
            return []
        return [item.strip() for item in self.TARGET_INDICES_STR.split(',') if item.strip()]
    
    @property
    def TARGET_INTERNALS(self) -> List[str]:
        """Get market internals symbols as list."""
        if not self.TARGET_INTERNALS_STR.strip():
            return []
        return [item.strip() for item in self.TARGET_INTERNALS_STR.split(',') if item.strip()]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()


def get_all_instruments() -> List[str]:
    """
    Get all configured instruments for monitoring.
    
    Returns:
        List[str]: All instrument symbols to be monitored.
    """
    return (
        settings.TARGET_FUTURES +
        settings.TARGET_INDICES +
        settings.TARGET_INTERNALS
    )


def get_database_path() -> Path:
    """
    Get the database file path from configuration.
    
    Returns:
        Path: Database file path.
    """
    # Extract path from SQLite URL
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    return Path(db_path)


def ensure_data_directory() -> None:
    """
    Ensure the data directory exists for the database file.
    """
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)