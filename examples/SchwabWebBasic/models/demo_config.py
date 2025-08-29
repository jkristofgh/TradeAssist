"""
Pydantic models for demo configuration and data validation.

This module defines type-safe configuration models for the Schwab demo application,
ensuring proper validation of environment variables, symbol configurations, and
demo settings.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class SymbolDemo(BaseModel):
    """Configuration for individual symbol demonstrations."""
    
    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, /ES, $SPX)")
    interval: str = Field(default="daily", description="Data interval")
    days_back: int = Field(default=30, ge=1, le=365, description="Days of historical data")
    enabled: bool = Field(default=True, description="Whether symbol is enabled for demos")
    description: Optional[str] = Field(None, description="Human-readable description")
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        """Validate symbol format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()
    
    @validator('interval')
    def interval_must_be_valid(cls, v):
        """Validate interval format."""
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "daily", "weekly"]
        if v not in valid_intervals:
            raise ValueError(f'Interval must be one of: {valid_intervals}')
        return v


class StreamingConfig(BaseModel):
    """Configuration for streaming demonstrations."""
    
    duration: int = Field(default=60, ge=10, le=3600, description="Streaming duration in seconds")
    symbols: List[str] = Field(default_factory=list, description="Symbols to stream")
    auto_reconnect: bool = Field(default=True, description="Enable auto-reconnect")
    alert_threshold: float = Field(default=0.02, ge=0.001, le=0.1, description="Price change alert threshold")
    
    @validator('symbols')
    def symbols_must_not_be_empty(cls, v):
        """Ensure at least one symbol for streaming."""
        if not v:
            return ["AAPL", "MSFT", "SPY"]  # Default symbols
        return [s.strip().upper() for s in v]


class AnalysisConfig(BaseModel):
    """Configuration for analysis demonstrations."""
    
    enable_technical_analysis: bool = Field(default=True, description="Enable technical indicators")
    enable_portfolio_analysis: bool = Field(default=True, description="Enable portfolio analysis")
    portfolio_weights: Dict[str, float] = Field(
        default_factory=lambda: {"AAPL": 0.25, "MSFT": 0.25, "GOOGL": 0.20, "AMZN": 0.15, "TSLA": 0.15},
        description="Portfolio symbol weights"
    )
    lookback_days: int = Field(default=252, ge=50, le=1000, description="Analysis lookback period")
    symbols: List[str] = Field(default_factory=list, description="Symbols to analyze")
    
    @validator('symbols')
    def symbols_must_not_be_empty(cls, v):
        """Ensure at least one symbol for analysis."""
        if not v:
            return ["AAPL", "MSFT", "SPY"]  # Default symbols
        return [s.strip().upper() for s in v]
    
    @validator('portfolio_weights')
    def weights_must_sum_to_one(cls, v):
        """Validate portfolio weights sum to approximately 1.0."""
        if v:
            total = sum(v.values())
            if not (0.95 <= total <= 1.05):  # Allow small rounding errors
                raise ValueError(f'Portfolio weights must sum to 1.0, got {total}')
        return v


class DemoConfig(BaseModel):
    """Main configuration for the demo application."""
    
    # Authentication
    api_key: str = Field(..., description="Schwab API key")
    app_secret: str = Field(..., description="Schwab app secret")
    callback_url: str = Field(default="https://localhost:8080/callback", description="OAuth callback URL")
    
    # Demo symbols
    demo_symbols: List[str] = Field(
        default_factory=lambda: ["AAPL", "MSFT", "GOOGL", "SPY", "/ES", "$SPX"],
        description="Default symbols for demonstrations"
    )
    
    # Default settings
    default_interval: str = Field(default="daily", description="Default data interval")
    default_days_back: int = Field(default=30, ge=1, le=365, description="Default historical period")
    
    # Mode settings
    mock_mode: bool = Field(default=False, description="Use mock data instead of API calls")
    verbose_output: bool = Field(default=True, description="Enable verbose console output")
    
    # Sub-configurations
    streaming_config: StreamingConfig = Field(default_factory=StreamingConfig)
    analysis_config: AnalysisConfig = Field(default_factory=AnalysisConfig)
    
    # Individual symbol configurations
    symbol_configs: List[SymbolDemo] = Field(default_factory=list, description="Per-symbol configurations")
    
    @validator('api_key', 'app_secret')
    def credentials_must_not_be_empty(cls, v):
        """Ensure credentials are provided (unless in mock mode)."""
        if not v or v.strip() == "" or "your_" in v.lower():
            # We'll handle this in the configuration loader based on mock_mode
            return v
        return v.strip()
    
    @validator('demo_symbols')
    def demo_symbols_must_not_be_empty(cls, v):
        """Ensure at least one demo symbol."""
        if not v:
            raise ValueError('At least one demo symbol must be specified')
        return [s.strip().upper() for s in v]
    
    @validator('callback_url')
    def callback_url_must_be_valid(cls, v):
        """Validate callback URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Callback URL must start with http:// or https://')
        return v
    
    def get_symbol_config(self, symbol: str) -> Optional[SymbolDemo]:
        """Get configuration for a specific symbol."""
        for config in self.symbol_configs:
            if config.symbol == symbol.upper():
                return config
        return None
    
    def get_enabled_symbols(self) -> List[str]:
        """Get list of enabled symbols from configurations."""
        enabled = [config.symbol for config in self.symbol_configs if config.enabled]
        if not enabled:
            return self.demo_symbols
        return enabled
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "SCHWAB_"
        case_sensitive = False
        validate_assignment = True