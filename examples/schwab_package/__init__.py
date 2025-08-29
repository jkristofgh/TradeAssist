"""
Schwab Package - Production-ready market data package.

A clean, simple Python package for Schwab market data with historical and
real-time streaming capabilities.

Example:
    ```python
    from schwab_package import SchwabClient

    # Initialize client
    client = SchwabClient(
        api_key="your_api_key",
        app_secret="your_app_secret",
        callback_url="https://localhost:8080/callback"
    )

    # Get historical data - returns pandas DataFrame
    df = await client.get_historical_data("AAPL", interval="daily", days_back=30)

    # Stream real-time data with callback
    def on_quote(symbol, quote_data):
        print(f"{symbol}: ${quote_data['last']}")

    await client.stream_quotes(["AAPL", "/ES"], callback=on_quote, duration=60)
    ```
"""

from typing import Dict

__version__ = "0.1.0"
__author__ = "SchwabPackage Contributors"
__email__ = "support@schwab-package.com"
__license__ = "MIT"

# Main public API exports
# Convenience functions for quick access
from .client import SchwabClient, SchwabClientError, get_historical_data, stream_quotes
from .models import InstrumentType, Quote, StreamEvent

# Version info
VERSION_INFO = (0, 1, 0)


def get_version() -> str:
    """Get package version string."""
    return __version__


def get_version_info() -> tuple:
    """Get version info tuple."""
    return VERSION_INFO


# Expose metadata for package introspection
__title__ = "schwab-package"
__description__ = "Production-ready Schwab market data package"

# Public API - only export what users need
__all__ = [
    # Main client class
    "SchwabClient",
    "SchwabClientError",
    # Data models
    "Quote",
    "StreamEvent", 
    "InstrumentType",
    # Convenience functions
    "get_historical_data",
    "stream_quotes",
    # Version info
    "__version__",
    "__title__",
    "__description__",
    "__author__",
    "get_version",
    "get_version_info",
    # Features and package info
    "__features__",
    "__package_info__",
]

# Package metadata for introspection
__package_info__ = {
    "name": "schwab-package",
    "version": __version__,
    "description": "Production-ready Schwab market data package",
    "author": __author__,
    "license": __license__,
    "python_requires": ">=3.10",
    "homepage": "https://github.com/your-org/schwab-package",
    "documentation": "https://schwab-package.readthedocs.io",
    "repository": "https://github.com/your-org/schwab-package",
}

# Feature flags for optional dependencies
try:
    import google.cloud.firestore
    import google.cloud.secret_manager

    HAS_GCP_SUPPORT = True
except ImportError:
    HAS_GCP_SUPPORT = False

__features__ = {
    "gcp_support": HAS_GCP_SUPPORT,
    "async_support": True,
    "streaming_support": True,
    "historical_data": True,
    "symbol_analysis": True,
    "rate_limiting": True,
}


def check_dependencies() -> dict[str, bool]:
    """
    Check availability of optional dependencies.

    Returns:
        Dictionary of feature availability
    """
    return __features__.copy()


# Add to public API
__all__.extend(["check_dependencies", "__features__", "__package_info__"])
