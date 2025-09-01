"""
Common API components for standardization.

This module provides standardized components for API responses,
error handling, validation, and configuration management.
"""

from .exceptions import (
    StandardAPIError,
    ValidationError,
    AuthenticationError,
    BusinessLogicError,
    SystemError
)

from .responses import (
    APIResponseBuilder,
    AnalyticsResponseBuilder,
    InstrumentResponseBuilder,
    HealthResponseBuilder
)

from .validators import (
    validate_instrument_exists,
    validate_lookback_hours,
    validate_confidence_level,
    validate_pagination,
    validate_date_range,
    ParameterValidator
)

from .configuration import (
    APILimitsConfig,
    ValidationConfig,
    TechnicalIndicatorConfig,
    CacheConfig
)

__all__ = [
    # Exceptions
    "StandardAPIError",
    "ValidationError", 
    "AuthenticationError",
    "BusinessLogicError",
    "SystemError",
    
    # Response builders
    "APIResponseBuilder",
    "AnalyticsResponseBuilder",
    "InstrumentResponseBuilder", 
    "HealthResponseBuilder",
    
    # Validators
    "validate_instrument_exists",
    "validate_lookback_hours",
    "validate_confidence_level",
    "validate_pagination",
    "validate_date_range",
    "ParameterValidator",
    
    # Configuration
    "APILimitsConfig",
    "ValidationConfig",
    "TechnicalIndicatorConfig",
    "CacheConfig"
]