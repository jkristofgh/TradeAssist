"""
Base database model definitions.

Contains common base classes and configurations for all SQLAlchemy models.
Enhanced with standardized serialization and response formatting capabilities.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Import enhanced serialization capabilities from database mixins to avoid circular imports
from ..database.mixins import EnhancedSerializationMixin


class Base(DeclarativeBase, EnhancedSerializationMixin):
    """
    Base class for all database models.
    
    Enhanced with standardized serialization capabilities for consistent
    API responses and database error handling.
    """
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        return name


class TimestampMixin:
    """Mixin for models that require timestamp tracking."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        nullable=False,
        doc="Record creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        doc="Record last update timestamp"
    )