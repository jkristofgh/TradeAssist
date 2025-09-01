"""
Standardized exception hierarchy for API error handling.

This module provides a consistent exception framework for all API endpoints,
ensuring uniform error responses and proper error categorization.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error_code: str
    error_category: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    correlation_id: str
    request_path: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class StandardAPIError(HTTPException):
    """
    Base class for all API errors with consistent formatting.
    
    Provides structured error responses with categorization, correlation IDs,
    and standardized formatting across all API endpoints.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        request_path: Optional[str] = None
    ):
        """
        Initialize standardized API error.
        
        Args:
            error_code: Structured error code (e.g., "VALIDATION_001")
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error context
            correlation_id: Request correlation ID for debugging
            request_path: API endpoint that generated the error
        """
        self.error_code = error_code
        self.error_category = self._get_error_category()
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.request_path = request_path
        self.error_details = details or {}
        
        # Create structured error response
        error_response = ErrorResponse(
            error_code=self.error_code,
            error_category=self.error_category,
            message=message,
            details=self.error_details,
            timestamp=self.timestamp,
            correlation_id=self.correlation_id,
            request_path=self.request_path
        )
        
        # Use model_dump_json and then parse back to dict to ensure proper serialization
        import json
        super().__init__(
            status_code=status_code,
            detail=json.loads(error_response.model_dump_json())
        )
    
    def _get_error_category(self) -> str:
        """Get error category based on exception type."""
        return "system"
    
    def with_correlation_id(self, correlation_id: str) -> 'StandardAPIError':
        """Add correlation ID to existing error."""
        self.correlation_id = correlation_id
        return self
    
    def with_request_path(self, request_path: str) -> 'StandardAPIError':
        """Add request path to existing error."""
        self.request_path = request_path
        return self


class ValidationError(StandardAPIError):
    """
    Validation-specific errors with field-level details.
    
    Used for input validation failures, parameter errors,
    and data format violations.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        field_errors: Optional[Dict[str, str]] = None,
        invalid_value: Any = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            error_code: Validation error code (e.g., "VALIDATION_001")
            message: Human-readable validation error message
            field_errors: Field-specific validation errors
            invalid_value: The invalid value that caused the error
            **kwargs: Additional StandardAPIError parameters
        """
        details = kwargs.pop("details", {})
        if field_errors:
            details["field_errors"] = field_errors
        if invalid_value is not None:
            details["invalid_value"] = str(invalid_value)
        
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            **kwargs
        )
    
    def _get_error_category(self) -> str:
        """Get error category for validation errors."""
        return "validation"


class AuthenticationError(StandardAPIError):
    """
    Authentication and authorization errors.
    
    Used for authentication failures, token validation errors,
    and authorization violations.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        auth_scheme: Optional[str] = None,
        required_scopes: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize authentication error.
        
        Args:
            error_code: Authentication error code (e.g., "AUTH_001")
            message: Human-readable authentication error message
            auth_scheme: Authentication scheme (e.g., "Bearer", "OAuth2")
            required_scopes: Required authorization scopes
            **kwargs: Additional StandardAPIError parameters
        """
        details = kwargs.pop("details", {})
        if auth_scheme:
            details["auth_scheme"] = auth_scheme
        if required_scopes:
            details["required_scopes"] = required_scopes
        
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            **kwargs
        )
    
    def _get_error_category(self) -> str:
        """Get error category for authentication errors."""
        return "authentication"


class BusinessLogicError(StandardAPIError):
    """
    Business rule violations and logic errors.
    
    Used for domain-specific rule violations, invalid operations,
    and business constraint failures.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        rule_violated: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize business logic error.
        
        Args:
            error_code: Business logic error code (e.g., "BUSINESS_001")
            message: Human-readable business error message
            rule_violated: Specific business rule that was violated
            context: Business context information
            **kwargs: Additional StandardAPIError parameters
        """
        details = kwargs.pop("details", {})
        if rule_violated:
            details["rule_violated"] = rule_violated
        if context:
            details["context"] = context
        
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            **kwargs
        )
    
    def _get_error_category(self) -> str:
        """Get error category for business logic errors."""
        return "business"


class SystemError(StandardAPIError):
    """
    System-level errors including database and external API failures.
    
    Used for infrastructure failures, database connection issues,
    external service timeouts, and other system-level problems.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        system_component: Optional[str] = None,
        upstream_error: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize system error.
        
        Args:
            error_code: System error code (e.g., "SYSTEM_001")
            message: Human-readable system error message
            system_component: System component that failed (e.g., "database", "schwab_api")
            upstream_error: Original error message from upstream system
            **kwargs: Additional StandardAPIError parameters
        """
        details = kwargs.pop("details", {})
        if system_component:
            details["system_component"] = system_component
        if upstream_error:
            details["upstream_error"] = str(upstream_error)
        
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )
    
    def _get_error_category(self) -> str:
        """Get error category for system errors."""
        return "system"


# Predefined common errors
class CommonErrors:
    """Common error definitions for consistent usage across the API."""
    
    # Validation Errors
    INSTRUMENT_NOT_FOUND = ("VALIDATION_001", "Instrument not found")
    INVALID_LOOKBACK_HOURS = ("VALIDATION_002", "Invalid lookback hours parameter")
    INVALID_CONFIDENCE_LEVEL = ("VALIDATION_003", "Invalid confidence level parameter")
    INVALID_PAGINATION = ("VALIDATION_004", "Invalid pagination parameters")
    INVALID_DATE_RANGE = ("VALIDATION_005", "Invalid date range parameters")
    MISSING_REQUIRED_PARAMETER = ("VALIDATION_006", "Missing required parameter")
    
    # Authentication Errors
    TOKEN_EXPIRED = ("AUTH_001", "Access token has expired")
    INVALID_TOKEN = ("AUTH_002", "Invalid access token")
    INSUFFICIENT_PERMISSIONS = ("AUTH_003", "Insufficient permissions")
    AUTHENTICATION_REQUIRED = ("AUTH_004", "Authentication required")
    
    # Business Logic Errors
    INSUFFICIENT_DATA = ("BUSINESS_001", "Insufficient data for operation")
    INVALID_OPERATION = ("BUSINESS_002", "Operation not allowed in current state")
    CONSTRAINT_VIOLATION = ("BUSINESS_003", "Business constraint violation")
    
    # System Errors
    DATABASE_CONNECTION_FAILED = ("SYSTEM_001", "Database connection failed")
    EXTERNAL_API_UNAVAILABLE = ("SYSTEM_002", "External API unavailable")
    INTERNAL_SERVER_ERROR = ("SYSTEM_003", "Internal server error")
    SERVICE_UNAVAILABLE = ("SYSTEM_004", "Service temporarily unavailable")