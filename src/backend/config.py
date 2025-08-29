"""
Application Configuration Management.

Uses Pydantic settings for type-safe configuration management
with environment variable support and validation.
"""

from enum import Enum
from pathlib import Path
from typing import List

from pydantic import Field
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
    
    # Target Instruments for Real-time Streaming
    TARGET_FUTURES: List[str] = Field(
        default=["ES", "NQ", "YM", "CL", "GC"],
        description="Futures symbols for real-time streaming"
    )
    TARGET_INDICES: List[str] = Field(
        default=["SPX", "NDX", "RUT"],
        description="Index symbols for real-time streaming"
    )
    TARGET_INTERNALS: List[str] = Field(
        default=["VIX", "TICK", "ADD", "TRIN"],
        description="Market internals symbols for real-time streaming"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


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