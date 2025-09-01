"""
Validation decorator system for API endpoints.

This module provides reusable validation decorators for common patterns
across API endpoints, reducing code duplication and ensuring consistent
validation behavior.
"""

import inspect
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Union

from fastapi import Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import here to avoid circular imports during module loading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...models.instruments import Instrument

from ...database.connection import get_db_session
from .exceptions import ValidationError, CommonErrors
from .configuration import ValidationConfig


class ParameterValidator:
    """
    Core parameter validation class with configurable rules.
    
    Provides reusable validation logic for common parameter types
    with configuration-driven validation rules.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize parameter validator.
        
        Args:
            config: Validation configuration instance
        """
        self.config = config or ValidationConfig()
    
    async def validate_instrument_exists(
        self, 
        instrument_id: int, 
        session: AsyncSession
    ) -> "Instrument":
        """
        Validate that instrument exists in database.
        
        Args:
            instrument_id: Instrument ID to validate
            session: Database session
            
        Returns:
            Instrument instance if found
            
        Raises:
            ValidationError: If instrument not found
        """
        # Import here to avoid circular imports
        from ...models.instruments import Instrument
        
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        
        if not instrument:
            raise ValidationError(
                error_code=CommonErrors.INSTRUMENT_NOT_FOUND[0],
                message=f"Instrument with ID {instrument_id} not found",
                field_errors={"instrument_id": "Instrument does not exist"},
                invalid_value=instrument_id
            )
        
        return instrument
    
    def validate_lookback_hours(
        self, 
        lookback_hours: int, 
        min_hours: Optional[int] = None, 
        max_hours: Optional[int] = None
    ) -> int:
        """
        Validate lookback hours parameter.
        
        Args:
            lookback_hours: Hours to look back
            min_hours: Minimum allowed hours (defaults to config)
            max_hours: Maximum allowed hours (defaults to config)
            
        Returns:
            Validated lookback hours
            
        Raises:
            ValidationError: If hours outside valid range
        """
        min_val = min_hours if min_hours is not None else self.config.min_lookback_hours
        max_val = max_hours if max_hours is not None else self.config.max_lookback_hours
        
        if not (min_val <= lookback_hours <= max_val):
            raise ValidationError(
                error_code=CommonErrors.INVALID_LOOKBACK_HOURS[0],
                message=f"Lookback hours must be between {min_val} and {max_val}",
                field_errors={"lookback_hours": f"Value must be between {min_val} and {max_val}"},
                invalid_value=lookback_hours,
                details={
                    "min_allowed": min_val,
                    "max_allowed": max_val
                }
            )
        
        return lookback_hours
    
    def validate_confidence_level(
        self, 
        confidence: float, 
        allowed_levels: Optional[List[float]] = None
    ) -> float:
        """
        Validate confidence level parameter.
        
        Args:
            confidence: Confidence level to validate
            allowed_levels: List of allowed confidence levels (defaults to config)
            
        Returns:
            Validated confidence level
            
        Raises:
            ValidationError: If confidence level not in allowed values
        """
        allowed = allowed_levels if allowed_levels is not None else self.config.allowed_confidence_levels
        
        if confidence not in allowed:
            raise ValidationError(
                error_code=CommonErrors.INVALID_CONFIDENCE_LEVEL[0],
                message=f"Confidence level must be one of: {allowed}",
                field_errors={"confidence": f"Must be one of: {allowed}"},
                invalid_value=confidence,
                details={
                    "allowed_values": allowed
                }
            )
        
        return confidence
    
    def validate_pagination(
        self, 
        page: int, 
        per_page: int, 
        max_per_page: Optional[int] = None
    ) -> tuple[int, int]:
        """
        Validate pagination parameters.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            max_per_page: Maximum items per page (defaults to config)
            
        Returns:
            Tuple of (page, per_page)
            
        Raises:
            ValidationError: If pagination parameters invalid
        """
        max_items = max_per_page if max_per_page is not None else self.config.max_per_page
        
        field_errors = {}
        
        if page < 1:
            field_errors["page"] = "Page number must be at least 1"
        
        if per_page < 1:
            field_errors["per_page"] = "Items per page must be at least 1"
        elif per_page > max_items:
            field_errors["per_page"] = f"Items per page cannot exceed {max_items}"
        
        if field_errors:
            raise ValidationError(
                error_code=CommonErrors.INVALID_PAGINATION[0],
                message="Invalid pagination parameters",
                field_errors=field_errors,
                details={
                    "max_per_page": max_items
                }
            )
        
        return page, per_page
    
    def validate_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        max_days: Optional[int] = None
    ) -> tuple[datetime, datetime]:
        """
        Validate date range parameters.
        
        Args:
            start_date: Start date
            end_date: End date
            max_days: Maximum allowed date range in days (defaults to config)
            
        Returns:
            Tuple of (start_date, end_date)
            
        Raises:
            ValidationError: If date range invalid
        """
        max_range_days = max_days if max_days is not None else self.config.max_date_range_days
        
        field_errors = {}
        
        if start_date >= end_date:
            field_errors["date_range"] = "Start date must be before end date"
        
        date_range_days = (end_date - start_date).days
        if date_range_days > max_range_days:
            field_errors["date_range"] = f"Date range cannot exceed {max_range_days} days"
        
        if start_date > datetime.utcnow():
            field_errors["start_date"] = "Start date cannot be in the future"
        
        if field_errors:
            raise ValidationError(
                error_code=CommonErrors.INVALID_DATE_RANGE[0],
                message="Invalid date range parameters",
                field_errors=field_errors,
                details={
                    "max_range_days": max_range_days,
                    "actual_range_days": date_range_days
                }
            )
        
        return start_date, end_date


# Global validator instance
_validator = ParameterValidator()


def validate_instrument_exists(func: Callable) -> Callable:
    """
    Decorator to validate instrument exists before endpoint execution.
    
    Extracts instrument_id from function parameters and validates existence
    in database before proceeding with endpoint logic.
    
    Args:
        func: Endpoint function to decorate
        
    Returns:
        Decorated function with instrument validation
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract instrument_id from function parameters
        instrument_id = _extract_parameter_value("instrument_id", args, kwargs, func)
        if instrument_id is None:
            raise ValidationError(
                error_code=CommonErrors.MISSING_REQUIRED_PARAMETER[0],
                message="Missing required parameter: instrument_id",
                field_errors={"instrument_id": "This parameter is required"}
            )
        
        # Get database session
        session = _extract_parameter_value("session", args, kwargs, func)
        if session is None:
            # Try to get session from dependency
            session_dep = Depends(get_db_session)
            session = await session_dep
        
        # Validate instrument exists
        instrument = await _validator.validate_instrument_exists(instrument_id, session)
        
        # Add instrument to kwargs for use in endpoint
        kwargs["validated_instrument"] = instrument
        
        return await func(*args, **kwargs)
    
    return wrapper


def validate_lookback_hours(
    min_hours: int = 1, 
    max_hours: int = 8760
) -> Callable:
    """
    Decorator to validate lookback_hours parameter.
    
    Args:
        min_hours: Minimum allowed hours
        max_hours: Maximum allowed hours
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            lookback_hours = _extract_parameter_value("lookback_hours", args, kwargs, func)
            if lookback_hours is not None:
                validated_hours = _validator.validate_lookback_hours(
                    lookback_hours, min_hours, max_hours
                )
                kwargs["validated_lookback_hours"] = validated_hours
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_confidence_level(allowed: List[float] = None) -> Callable:
    """
    Decorator to validate confidence_level parameter.
    
    Args:
        allowed: List of allowed confidence levels
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            confidence = _extract_parameter_value("confidence", args, kwargs, func)
            if confidence is not None:
                validated_confidence = _validator.validate_confidence_level(
                    confidence, allowed
                )
                kwargs["validated_confidence"] = validated_confidence
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_pagination(max_per_page: int = 100) -> Callable:
    """
    Decorator to validate pagination parameters.
    
    Args:
        max_per_page: Maximum items per page
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            page = _extract_parameter_value("page", args, kwargs, func)
            per_page = _extract_parameter_value("per_page", args, kwargs, func)
            
            if page is not None and per_page is not None:
                validated_page, validated_per_page = _validator.validate_pagination(
                    page, per_page, max_per_page
                )
                kwargs["validated_page"] = validated_page
                kwargs["validated_per_page"] = validated_per_page
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_date_range(max_days: int = 365) -> Callable:
    """
    Decorator to validate date range parameters.
    
    Args:
        max_days: Maximum allowed date range in days
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_date = _extract_parameter_value("start_date", args, kwargs, func)
            end_date = _extract_parameter_value("end_date", args, kwargs, func)
            
            if start_date is not None and end_date is not None:
                validated_start, validated_end = _validator.validate_date_range(
                    start_date, end_date, max_days
                )
                kwargs["validated_start_date"] = validated_start
                kwargs["validated_end_date"] = validated_end
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_required_parameters(*required_params: str) -> Callable:
    """
    Decorator to validate that required parameters are present.
    
    Args:
        *required_params: Names of required parameters
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            missing_params = []
            
            for param_name in required_params:
                value = _extract_parameter_value(param_name, args, kwargs, func)
                if value is None:
                    missing_params.append(param_name)
            
            if missing_params:
                field_errors = {
                    param: "This parameter is required" 
                    for param in missing_params
                }
                raise ValidationError(
                    error_code=CommonErrors.MISSING_REQUIRED_PARAMETER[0],
                    message=f"Missing required parameters: {', '.join(missing_params)}",
                    field_errors=field_errors
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def sanitize_input(*param_names: str) -> Callable:
    """
    Decorator to sanitize input parameters.
    
    Args:
        *param_names: Names of parameters to sanitize
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for param_name in param_names:
                value = _extract_parameter_value(param_name, args, kwargs, func)
                if value is not None and isinstance(value, str):
                    # Basic input sanitization
                    sanitized_value = _sanitize_string(value)
                    kwargs[f"sanitized_{param_name}"] = sanitized_value
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def _extract_parameter_value(
    param_name: str, 
    args: tuple, 
    kwargs: dict, 
    func: Callable
) -> Any:
    """
    Extract parameter value from function arguments.
    
    Args:
        param_name: Parameter name to extract
        args: Function positional arguments
        kwargs: Function keyword arguments
        func: Function being decorated
        
    Returns:
        Parameter value or None if not found
    """
    # First check kwargs
    if param_name in kwargs:
        return kwargs[param_name]
    
    # Then check positional args based on function signature
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    
    if param_name in param_names:
        param_index = param_names.index(param_name)
        if param_index < len(args):
            return args[param_index]
    
    return None


def _sanitize_string(value: str) -> str:
    """
    Basic string sanitization for input parameters.
    
    Args:
        value: String value to sanitize
        
    Returns:
        Sanitized string value
    """
    # Remove control characters and normalize whitespace
    sanitized = "".join(char for char in value if ord(char) >= 32 or char in ['\n', '\t'])
    sanitized = ' '.join(sanitized.split())  # Normalize whitespace
    
    # Basic length limitation
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


# Validation decorator combinations for common patterns
def validate_analytics_request(func: Callable) -> Callable:
    """
    Combined validation decorator for analytics endpoints.
    
    Validates instrument existence, lookback hours, and confidence level.
    """
    @validate_instrument_exists
    @validate_lookback_hours(min_hours=1, max_hours=8760)
    @validate_confidence_level()
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    return wrapper


def validate_list_request(func: Callable) -> Callable:
    """
    Combined validation decorator for list endpoints.
    
    Validates pagination parameters and optional filtering.
    """
    @validate_pagination(max_per_page=100)
    @sanitize_input("search", "filter")
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    return wrapper


def validate_historical_request(func: Callable) -> Callable:
    """
    Combined validation decorator for historical data endpoints.
    
    Validates instrument existence, date range, and pagination.
    """
    @validate_instrument_exists
    @validate_date_range(max_days=365)
    @validate_pagination(max_per_page=1000)
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    return wrapper