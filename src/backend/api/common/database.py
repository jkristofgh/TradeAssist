"""
Enhanced database models with standardized serialization and error handling.

This module extends the existing database base classes with standardized
response formatting, validation, and error handling capabilities.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List, Union, Type
from decimal import Decimal

from sqlalchemy.exc import (
    IntegrityError,
    NoResultFound, 
    MultipleResultsFound,
    StatementError,
    DataError,
    OperationalError
)
from sqlalchemy.orm.exc import StaleDataError
from pydantic import BaseModel, validator

from .exceptions import (
    StandardAPIError,
    ValidationError,
    SystemError,
    BusinessLogicError,
    CommonErrors
)


class DatabaseErrorHandler:
    """
    Centralized database error handling with standardized error mapping.
    
    Maps SQLAlchemy exceptions to standardized API errors with appropriate
    HTTP status codes and error categorization.
    """
    
    @staticmethod
    def handle_integrity_error(error: IntegrityError, context: Optional[str] = None) -> StandardAPIError:
        """
        Handle database integrity constraint violations.
        
        Args:
            error: SQLAlchemy IntegrityError
            context: Additional context about the operation
            
        Returns:
            Appropriate StandardAPIError subclass
        """
        error_message = str(error.orig) if hasattr(error, 'orig') else str(error)
        
        # Check for specific constraint types
        if "UNIQUE constraint failed" in error_message or "duplicate key" in error_message.lower():
            return BusinessLogicError(
                error_code="DATABASE_001",
                message="Duplicate entry violation",
                rule_violated="unique_constraint",
                context={"constraint_error": error_message, "operation_context": context}
            )
        
        elif "FOREIGN KEY constraint failed" in error_message or "foreign key" in error_message.lower():
            return BusinessLogicError(
                error_code="DATABASE_002", 
                message="Foreign key constraint violation",
                rule_violated="foreign_key_constraint",
                context={"constraint_error": error_message, "operation_context": context}
            )
        
        elif "NOT NULL constraint failed" in error_message or "not null" in error_message.lower():
            return ValidationError(
                error_code="DATABASE_003",
                message="Required field missing",
                field_errors={"database_constraint": "Required field cannot be null"},
                details={"constraint_error": error_message, "operation_context": context}
            )
        
        else:
            return SystemError(
                error_code="DATABASE_004",
                message="Database integrity constraint violation",
                system_component="database",
                upstream_error=error_message,
                details={"operation_context": context}
            )
    
    @staticmethod
    def handle_not_found_error(
        error: Union[NoResultFound, Exception], 
        entity_type: str,
        entity_id: Union[int, str, None] = None
    ) -> ValidationError:
        """
        Handle entity not found errors.
        
        Args:
            error: Exception indicating entity not found
            entity_type: Type of entity (e.g., "instrument", "alert_rule")
            entity_id: ID of the entity that wasn't found
            
        Returns:
            ValidationError with appropriate details
        """
        message = f"{entity_type.title()} not found"
        if entity_id is not None:
            message += f" (ID: {entity_id})"
        
        return ValidationError(
            error_code="DATABASE_005",
            message=message,
            field_errors={f"{entity_type}_id": f"{entity_type.title()} does not exist"},
            invalid_value=entity_id,
            details={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "original_error": str(error)
            }
        )
    
    @staticmethod
    def handle_multiple_results_error(
        error: MultipleResultsFound,
        entity_type: str,
        query_context: Optional[Dict[str, Any]] = None
    ) -> SystemError:
        """
        Handle multiple results found when expecting single result.
        
        Args:
            error: SQLAlchemy MultipleResultsFound error
            entity_type: Type of entity being queried
            query_context: Context about the query that failed
            
        Returns:
            SystemError indicating data consistency issue
        """
        return SystemError(
            error_code="DATABASE_006",
            message=f"Multiple {entity_type} records found when expecting one",
            system_component="database",
            upstream_error=str(error),
            details={
                "entity_type": entity_type,
                "query_context": query_context,
                "data_integrity_issue": True
            }
        )
    
    @staticmethod
    def handle_constraint_violation(
        error: Exception,
        constraint_type: str,
        entity_type: str,
        constraint_details: Optional[Dict[str, Any]] = None
    ) -> BusinessLogicError:
        """
        Handle business rule constraint violations.
        
        Args:
            error: Constraint violation exception
            constraint_type: Type of constraint (e.g., "business_rule", "data_validation")
            entity_type: Entity type involved in violation
            constraint_details: Additional constraint information
            
        Returns:
            BusinessLogicError with constraint violation details
        """
        return BusinessLogicError(
            error_code="DATABASE_007",
            message=f"Business constraint violation for {entity_type}",
            rule_violated=constraint_type,
            context={
                "entity_type": entity_type,
                "constraint_details": constraint_details,
                "original_error": str(error)
            }
        )
    
    @staticmethod
    def handle_database_connection_error(error: OperationalError) -> SystemError:
        """
        Handle database connection and operational errors.
        
        Args:
            error: SQLAlchemy OperationalError
            
        Returns:
            SystemError indicating database connectivity issue
        """
        return SystemError(
            error_code=CommonErrors.DATABASE_CONNECTION_FAILED[0],
            message="Database connection failed",
            system_component="database",
            upstream_error=str(error),
            details={
                "error_type": "connection_failure",
                "retry_recommended": True
            }
        )
    
    @staticmethod
    def handle_data_error(error: Union[DataError, StatementError]) -> ValidationError:
        """
        Handle data format and statement errors.
        
        Args:
            error: SQLAlchemy DataError or StatementError
            
        Returns:
            ValidationError indicating data format issue
        """
        return ValidationError(
            error_code="DATABASE_008",
            message="Invalid data format or type",
            field_errors={"data_format": "Data format is invalid for database operation"},
            details={
                "original_error": str(error),
                "error_type": type(error).__name__
            }
        )
    
    @staticmethod
    def handle_stale_data_error(error: StaleDataError) -> BusinessLogicError:
        """
        Handle concurrent modification errors.
        
        Args:
            error: SQLAlchemy StaleDataError
            
        Returns:
            BusinessLogicError indicating concurrency conflict
        """
        return BusinessLogicError(
            error_code="DATABASE_009",
            message="Data was modified by another process",
            rule_violated="concurrency_control",
            context={
                "error_type": "stale_data",
                "original_error": str(error),
                "retry_recommended": True
            }
        )
