"""
Custom exception classes for database operations.

This module provides specialized exceptions that integrate with the
database decorator framework and existing error handling patterns.
"""


class DatabaseOperationError(Exception):
    """
    Custom exception for database operations with context.
    
    This exception wraps database-related errors with additional context
    about the operation that failed. It preserves the original exception
    chain for debugging purposes.
    
    Attributes:
        message: Human-readable error message
        operation: Name of the database operation that failed
        original_error: The original exception that was caught
    """
    
    def __init__(self, message: str, operation: str = None, original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.original_error = original_error
    
    def __str__(self) -> str:
        if self.operation:
            return f"{self.operation}: {self.message}"
        return self.message


class InstrumentValidationError(ValueError):
    """
    Specific exception for instrument validation failures.
    
    Raised when instrument validation fails in the @with_validated_instrument
    decorator. This is a subclass of ValueError to maintain compatibility
    with existing error handling that expects ValueError for validation failures.
    
    Attributes:
        instrument_id: ID of the instrument that failed validation
        reason: Reason for validation failure
    """
    
    def __init__(self, message: str, instrument_id: int = None, reason: str = None):
        super().__init__(message)
        self.instrument_id = instrument_id
        self.reason = reason
    
    def __str__(self) -> str:
        if self.instrument_id:
            return f"Instrument {self.instrument_id} validation failed: {super().__str__()}"
        return super().__str__()


class SessionManagementError(Exception):
    """
    Exception for database session lifecycle issues.
    
    Raised when there are problems with database session creation,
    management, or cleanup. This helps distinguish session management
    issues from business logic errors.
    
    Attributes:
        session_info: Information about the session that failed
        phase: Phase of session lifecycle where error occurred
    """
    
    def __init__(self, message: str, session_info: str = None, phase: str = None):
        super().__init__(message)
        self.session_info = session_info
        self.phase = phase
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.phase:
            parts.append(f"Phase: {self.phase}")
        if self.session_info:
            parts.append(f"Session: {self.session_info}")
        return " | ".join(parts)