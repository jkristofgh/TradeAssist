"""
Demo modules for showcasing schwab-package capabilities.

This package contains demonstration modules for different aspects of the
schwab-package library including historical data, streaming, analysis,
and multi-asset trading.
"""

from .historical_demo import (
    demo_basic_historical,
    demo_multiple_intervals,
    demo_date_ranges
)

from .streaming_demo import (
    demo_basic_streaming,
    demo_price_alerts,
    demo_market_scanner
)

from .analysis_demo import (
    demo_symbol_analysis,
    demo_technical_analysis,
    demo_portfolio_analysis
)

from .multi_asset_demo import (
    demo_asset_types,
    demo_futures_equities,
    demo_symbol_detection
)

__all__ = [
    # Historical demos
    "demo_basic_historical",
    "demo_multiple_intervals", 
    "demo_date_ranges",
    
    # Streaming demos
    "demo_basic_streaming",
    "demo_price_alerts",
    "demo_market_scanner",
    
    # Analysis demos
    "demo_symbol_analysis",
    "demo_technical_analysis",
    "demo_portfolio_analysis",
    
    # Multi-asset demos
    "demo_asset_types",
    "demo_futures_equities",
    "demo_symbol_detection"
]