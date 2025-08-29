"""
Utility modules for the Schwab demo application.

This package provides utility functions for configuration management,
console output formatting, and mock data generation.
"""

from .config import load_config, validate_credentials
from .console_output import (
    format_dataframe,
    format_quote,
    format_symbol_analysis,
    print_banner,
    print_error,
    print_success,
    print_warning
)
from .mock_data import (
    generate_mock_historical_data,
    generate_mock_quote,
    generate_mock_stream_event
)

__all__ = [
    # Configuration
    "load_config",
    "validate_credentials",
    
    # Console output
    "format_dataframe",
    "format_quote", 
    "format_symbol_analysis",
    "print_banner",
    "print_error",
    "print_success",
    "print_warning",
    
    # Mock data
    "generate_mock_historical_data",
    "generate_mock_quote",
    "generate_mock_stream_event"
]