"""
Database decorator framework for eliminating session management boilerplate.

This module provides decorators that handle common database operations:
- Automatic session management with commit/rollback
- Instrument validation and injection
- Custom error handling with operation context
"""

import structlog
from functools import wraps
from typing import Callable, Optional, Union, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .connection import get_db_session

logger = structlog.get_logger()


def with_db_session(func: Callable) -> Callable:
    """
    Automatic database session management with commit/rollback.
    
    Requirements:
    - Inject AsyncSession as first parameter after self
    - Automatic commit on success
    - Automatic rollback on exception
    - Integration with existing structlog logging
    - Performance overhead <10ms per operation
    - Support for both instance and static methods
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_db_session() as session:
            try:
                # Inject session as first argument after self (if instance method)
                if args and hasattr(args[0], '__dict__'):  # Instance method
                    result = await func(args[0], session, *args[1:], **kwargs)
                else:  # Static/class method or function
                    result = await func(session, *args, **kwargs)
                
                await session.commit()
                return result
                
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Database error in {func.__name__}",
                    error=str(e),
                    function=func.__name__
                )
                raise
                
    return wrapper


def with_validated_instrument(func: Callable) -> Callable:
    """
    Automatic instrument validation and injection.
    
    Requirements:
    - Fetch instrument by ID from database
    - Validate instrument exists and is active
    - Inject validated Instrument object as parameter
    - Raise ValueError with descriptive message on validation failure
    - Compatible with @with_db_session decorator stacking
    - Cache frequently accessed instruments for performance
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Handle decorator stacking with @with_db_session
        if len(args) >= 3 and isinstance(args[1], AsyncSession):
            # Called as: func(self, session, instrument_id, ...)
            self_instance = args[0]
            session = args[1]
            instrument_id = args[2]
            remaining_args = args[3:]
        elif len(args) >= 2 and isinstance(args[0], AsyncSession):
            # Called as: func(session, instrument_id, ...)
            self_instance = None
            session = args[0]
            instrument_id = args[1]
            remaining_args = args[2:]
        else:
            raise ValueError("with_validated_instrument requires session and instrument_id parameters")
        
        # Import here to avoid circular imports
        from ..models.instruments import Instrument, InstrumentStatus
        
        # Fetch and validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
            
        if instrument.status != InstrumentStatus.ACTIVE:
            raise ValueError(f"Instrument {instrument_id} is not active (status: {instrument.status})")
        
        # Call original function with validated instrument
        if self_instance is not None:
            return await func(self_instance, session, instrument, *remaining_args, **kwargs)
        else:
            return await func(session, instrument, *remaining_args, **kwargs)
            
    return wrapper


def handle_db_errors(operation_name: str = "Database operation"):
    """
    Custom error handling with operation context.
    
    Requirements:
    - Wrap exceptions with custom DatabaseOperationError
    - Preserve original exception chain for debugging
    - Log errors with appropriate context and severity
    - Support custom operation names for better error messages
    - Compatible with existing exception handling patterns
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Import here to avoid circular imports
                from .exceptions import DatabaseOperationError
                
                logger.error(
                    f"{operation_name} failed in {func.__name__}",
                    operation=operation_name,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                # Preserve original exception chain for debugging
                raise DatabaseOperationError(f"{operation_name} failed: {str(e)}") from e
                
        return wrapper
    return decorator