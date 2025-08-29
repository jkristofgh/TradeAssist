"""
Configuration management and environment variable loading.

This module handles loading configuration from environment variables using
python-dotenv, validates credentials, and provides the main configuration
object for the demo application.
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import ValidationError

from ..models.demo_config import DemoConfig, SymbolDemo, StreamingConfig, AnalysisConfig


def load_config() -> DemoConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        DemoConfig: Validated configuration object
        
    Raises:
        ValidationError: If configuration validation fails
        ValueError: If required credentials are missing in non-mock mode
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse comma-separated demo symbols - this is the master list for ALL demos
    demo_symbols_str = os.getenv("DEMO_SYMBOLS", "AAPL,MSFT,GOOGL,SPY,/ES,$SPX")
    demo_symbols = [s.strip() for s in demo_symbols_str.split(",") if s.strip()]
    
    # Parse mock mode
    mock_mode = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes", "on")
    
    # Symbol hierarchy: DEMO_SYMBOLS is used for ALL demos unless overridden
    # - Historical demos: Always use DEMO_SYMBOLS (via config.get_enabled_symbols())
    # - Streaming demos: Use STREAMING_SYMBOLS if set, otherwise DEMO_SYMBOLS
    # - Analysis demos: Use ANALYSIS_SYMBOLS if set, otherwise DEMO_SYMBOLS
    
    # Parse streaming symbols (default to demo symbols if not specified)
    streaming_symbols_str = os.getenv("STREAMING_SYMBOLS", demo_symbols_str)
    streaming_symbols = [s.strip() for s in streaming_symbols_str.split(",") if s.strip()]
    
    # Parse analysis symbols (default to demo symbols if not specified)
    analysis_symbols_str = os.getenv("ANALYSIS_SYMBOLS", demo_symbols_str)  
    analysis_symbols = [s.strip() for s in analysis_symbols_str.split(",") if s.strip()]
    
    # Create streaming configuration
    streaming_config = StreamingConfig(
        duration=int(os.getenv("STREAMING_DURATION", "60")),
        symbols=streaming_symbols,
        auto_reconnect=os.getenv("STREAMING_AUTO_RECONNECT", "true").lower() in ("true", "1", "yes"),
        alert_threshold=float(os.getenv("STREAMING_ALERT_THRESHOLD", "0.02"))
    )
    
    # Create analysis configuration
    analysis_config = AnalysisConfig(
        enable_technical_analysis=os.getenv("ENABLE_TECHNICAL_ANALYSIS", "true").lower() in ("true", "1", "yes"),
        enable_portfolio_analysis=os.getenv("ENABLE_PORTFOLIO_ANALYSIS", "true").lower() in ("true", "1", "yes"),
        lookback_days=int(os.getenv("ANALYSIS_LOOKBACK_DAYS", "252")),
        symbols=analysis_symbols  # Add symbols to analysis config
    )
    
    try:
        config = DemoConfig(
            # Authentication
            api_key=os.getenv("SCHWAB_API_KEY", ""),
            app_secret=os.getenv("SCHWAB_APP_SECRET", ""),
            callback_url=os.getenv("SCHWAB_CALLBACK_URL", "https://localhost:8080/callback"),
            
            # Demo settings
            demo_symbols=demo_symbols,
            default_interval=os.getenv("DEFAULT_INTERVAL", "daily"),
            default_days_back=int(os.getenv("DEFAULT_DAYS_BACK", "30")),
            
            # Mode settings
            mock_mode=mock_mode,
            verbose_output=os.getenv("VERBOSE_OUTPUT", "true").lower() in ("true", "1", "yes"),
            
            # Sub-configurations
            streaming_config=streaming_config,
            analysis_config=analysis_config
        )
        
        # Validate credentials unless in mock mode
        if not mock_mode:
            validate_credentials(config)
            
        return config
        
    except ValidationError as e:
        print(f"Configuration validation error: {e}")
        raise
    except ValueError as e:
        print(f"Configuration error: {e}")
        raise


def validate_credentials(config: DemoConfig) -> None:
    """
    Validate that required credentials are provided.
    
    Args:
        config: DemoConfig object to validate
        
    Raises:
        ValueError: If required credentials are missing or invalid
    """
    if not config.api_key or config.api_key.strip() == "":
        raise ValueError(
            "SCHWAB_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    if "your_" in config.api_key.lower():
        raise ValueError(
            "Please replace the placeholder API key with your actual Schwab API key. "
            "Get your credentials from https://developer.schwab.com"
        )
    
    if not config.app_secret or config.app_secret.strip() == "":
        raise ValueError(
            "SCHWAB_APP_SECRET environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    if "your_" in config.app_secret.lower():
        raise ValueError(
            "Please replace the placeholder app secret with your actual Schwab app secret. "
            "Get your credentials from https://developer.schwab.com"
        )
    
    if not config.callback_url.startswith(('http://', 'https://')):
        raise ValueError(
            "SCHWAB_CALLBACK_URL must be a valid URL starting with http:// or https://"
        )


def get_environment_info() -> dict:
    """
    Get information about the current environment configuration.
    
    Returns:
        dict: Environment information
    """
    load_dotenv()
    
    return {
        "env_file_exists": os.path.exists(".env"),
        "api_key_set": bool(os.getenv("SCHWAB_API_KEY")),
        "app_secret_set": bool(os.getenv("SCHWAB_APP_SECRET")),
        "callback_url": os.getenv("SCHWAB_CALLBACK_URL", "Not set"),
        "mock_mode": os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes", "on"),
        "demo_symbols": os.getenv("DEMO_SYMBOLS", "Not set"),
        "verbose_output": os.getenv("VERBOSE_OUTPUT", "true").lower() in ("true", "1", "yes")
    }


def create_symbol_configs(symbols: List[str], default_interval: str = "daily", 
                         default_days_back: int = 30) -> List[SymbolDemo]:
    """
    Create SymbolDemo configurations for a list of symbols.
    
    Args:
        symbols: List of trading symbols
        default_interval: Default data interval
        default_days_back: Default historical period
        
    Returns:
        List[SymbolDemo]: List of symbol configurations
    """
    configs = []
    
    for symbol in symbols:
        # Set description based on symbol type
        description = _get_symbol_description(symbol)
        
        config = SymbolDemo(
            symbol=symbol,
            interval=default_interval,
            days_back=default_days_back,
            enabled=True,
            description=description
        )
        configs.append(config)
    
    return configs


def _get_symbol_description(symbol: str) -> str:
    """
    Get a human-readable description for a symbol.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        str: Symbol description
    """
    symbol = symbol.upper()
    
    if symbol.startswith('/'):
        return f"Futures contract: {symbol}"
    elif symbol.startswith('$'):
        return f"Index: {symbol}"
    elif symbol in ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT']:
        return f"ETF: {symbol}"
    elif '/' in symbol:
        return f"Forex pair: {symbol}"
    else:
        return f"Equity: {symbol}"