"""
Schwab Package Basic Demo Application

This package provides comprehensive demonstrations of the schwab-package library,
showcasing historical data retrieval, real-time streaming, symbol analysis,
and multi-asset trading capabilities.

Main components:
- demos: Demonstration modules for different features
- models: Pydantic data models for configuration
- utils: Utility functions for configuration, console output, and mock data
"""

__version__ = "1.0.0"
__author__ = "Claude Code Demo"

# Main exports
from .main import main

__all__ = ["main"]