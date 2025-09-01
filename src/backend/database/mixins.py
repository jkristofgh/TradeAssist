"""
Database Mixins for TradeAssist.

Provides reusable mixins for database models including:
- TimestampMixin: Automatic created_at/updated_at timestamps
- SoftDeleteMixin: Soft delete functionality with deleted_at timestamp
- EnhancedSerializationMixin: Enhanced serialization and response formatting
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin for automatic timestamp tracking."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when record was last updated"
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Adds a deleted_at timestamp column to track soft deletions.
    Records with non-null deleted_at are considered deleted but
    remain in the database for audit and recovery purposes.
    """
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        doc="Timestamp for soft deletion (NULL = active)"
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None
    
    @property
    def is_active(self) -> bool:
        """Check if record is active (not deleted)."""
        return self.deleted_at is None
    
    def soft_delete(self) -> None:
        """Mark record as deleted with current timestamp."""
        if not self.is_deleted:
            self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore soft deleted record by clearing deleted_at."""
        self.deleted_at = None
    
    def __repr_deleted__(self) -> str:
        """Helper for including deletion status in repr."""
        if self.is_deleted:
            return f" [DELETED at {self.deleted_at}]"
        return ""


class EnhancedSerializationMixin:
    """
    Mixin for database models providing enhanced serialization capabilities.
    
    This mixin provides standardized methods for converting database models
    to dictionaries, handling complex data types, and formatting responses
    consistently across all API endpoints.
    """
    
    def to_dict(
        self,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        include_relationships: bool = False,
        max_depth: int = 1,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """
        Convert model instance to dictionary with configurable field inclusion.
        
        Args:
            include_fields: Optional list of fields to include (whitelist).
            exclude_fields: Optional list of fields to exclude (blacklist).
            include_relationships: Whether to include relationship data.
            max_depth: Maximum depth for relationship traversal.
            current_depth: Current depth in relationship traversal.
            
        Returns:
            Dict[str, Any]: Serialized model data.
        """
        # Prevent infinite recursion
        if current_depth >= max_depth:
            include_relationships = False
            
        # Default exclude sensitive fields
        default_exclude = {'password', 'secret_key', 'api_key', 'token'}
        if exclude_fields:
            exclude_fields = set(exclude_fields) | default_exclude
        else:
            exclude_fields = default_exclude
            
        result = {}
        
        # Process regular columns
        for column in self.__table__.columns:
            column_name = column.name
            
            # Apply field filters
            if include_fields and column_name not in include_fields:
                continue
            if exclude_fields and column_name in exclude_fields:
                continue
                
            value = getattr(self, column_name)
            
            # Handle special data types
            if isinstance(value, datetime):
                result[column_name] = value.isoformat()
            elif isinstance(value, Decimal):
                result[column_name] = float(value)
            elif isinstance(value, bytes):
                result[column_name] = value.decode('utf-8', errors='ignore')
            elif hasattr(value, 'value'):  # Handle enums
                result[column_name] = value.value
            else:
                result[column_name] = value
                
        # Process relationships if requested
        if include_relationships and current_depth < max_depth:
            for relationship in self.__mapper__.relationships:
                rel_name = relationship.key
                
                # Apply field filters
                if include_fields and rel_name not in include_fields:
                    continue
                if exclude_fields and rel_name in exclude_fields:
                    continue
                    
                rel_value = getattr(self, rel_name)
                
                if rel_value is None:
                    result[rel_name] = None
                elif isinstance(rel_value, list):
                    # Handle one-to-many relationships
                    result[rel_name] = [
                        item.to_dict(
                            include_fields=include_fields,
                            exclude_fields=exclude_fields,
                            include_relationships=include_relationships,
                            max_depth=max_depth,
                            current_depth=current_depth + 1
                        ) if hasattr(item, 'to_dict') else str(item)
                        for item in rel_value
                    ]
                else:
                    # Handle many-to-one or one-to-one relationships
                    if hasattr(rel_value, 'to_dict'):
                        result[rel_name] = rel_value.to_dict(
                            include_fields=include_fields,
                            exclude_fields=exclude_fields,
                            include_relationships=include_relationships,
                            max_depth=max_depth,
                            current_depth=current_depth + 1
                        )
                    else:
                        result[rel_name] = str(rel_value)
                        
        return result
    
    def to_response(
        self,
        include_metadata: bool = True,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert model to API response format with optional metadata.
        
        Args:
            include_metadata: Whether to include response metadata.
            include_fields: Optional list of fields to include.
            exclude_fields: Optional list of fields to exclude.
            
        Returns:
            Dict[str, Any]: Formatted response data.
        """
        data = self.to_dict(
            include_fields=include_fields,
            exclude_fields=exclude_fields,
            include_relationships=True,
            max_depth=2
        )
        
        if include_metadata:
            # Add metadata fields if they exist
            metadata_fields = {
                'created_at': getattr(self, 'created_at', None),
                'updated_at': getattr(self, 'updated_at', None),
                'version': getattr(self, 'version', None)
            }
            
            for field, value in metadata_fields.items():
                if value is not None and field not in data:
                    if isinstance(value, datetime):
                        data[field] = value.isoformat()
                    else:
                        data[field] = value
                        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], exclude_fields: Optional[List[str]] = None):
        """
        Create model instance from dictionary data.
        
        Args:
            data: Dictionary containing model data.
            exclude_fields: Optional list of fields to exclude from creation.
            
        Returns:
            Model instance with populated data.
        """
        if exclude_fields:
            data = {k: v for k, v in data.items() if k not in exclude_fields}
            
        # Filter out non-column attributes
        valid_columns = {column.name for column in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}
        
        return cls(**filtered_data)
    
    def update_from_dict(
        self,
        data: Dict[str, Any],
        exclude_fields: Optional[List[str]] = None,
        allow_none: bool = False
    ) -> 'EnhancedSerializationMixin':
        """
        Update model instance from dictionary data.
        
        Args:
            data: Dictionary containing update data.
            exclude_fields: Optional list of fields to exclude from update.
            allow_none: Whether to allow setting fields to None.
            
        Returns:
            Self: Updated model instance for chaining.
        """
        # Default fields that should never be updated this way
        default_exclude = {'id', 'created_at', 'updated_at', 'version'}
        if exclude_fields:
            exclude_fields = set(exclude_fields) | default_exclude
        else:
            exclude_fields = default_exclude
            
        # Get valid column names
        valid_columns = {column.name for column in self.__table__.columns}
        
        for key, value in data.items():
            # Skip excluded fields
            if key in exclude_fields:
                continue
                
            # Skip non-column attributes
            if key not in valid_columns:
                continue
                
            # Skip None values unless explicitly allowed
            if value is None and not allow_none:
                continue
                
            # Update the attribute
            setattr(self, key, value)
            
        return self
    
    def validate_constraints(self) -> List[str]:
        """
        Validate model constraints before database operations.
        
        Returns:
            List[str]: List of validation error messages (empty if valid).
        """
        errors = []
        
        # Check required fields
        for column in self.__table__.columns:
            if not column.nullable and not column.default:
                value = getattr(self, column.name, None)
                if value is None:
                    errors.append(f"Required field '{column.name}' is missing")
                    
        # Check string length constraints
        for column in self.__table__.columns:
            if hasattr(column.type, 'length') and column.type.length:
                value = getattr(self, column.name, None)
                if value and isinstance(value, str) and len(value) > column.type.length:
                    errors.append(
                        f"Field '{column.name}' exceeds maximum length of {column.type.length}"
                    )
                    
        # Check unique constraints (note: actual uniqueness requires DB query)
        # This just validates format/structure
        
        return errors
    
    def get_primary_key(self) -> Any:
        """
        Get the primary key value(s) for this model instance.
        
        Returns:
            Any: Primary key value or tuple of values for composite keys.
        """
        pk_columns = self.__table__.primary_key.columns
        
        if len(pk_columns) == 1:
            # Single primary key
            return getattr(self, list(pk_columns)[0].name)
        else:
            # Composite primary key
            return tuple(getattr(self, col.name) for col in pk_columns)
    
    def __repr__(self) -> str:
        """
        Generate a readable string representation of the model instance.
        
        Returns:
            str: String representation including class name and primary key.
        """
        pk = self.get_primary_key()
        return f"<{self.__class__.__name__}(pk={pk})>"