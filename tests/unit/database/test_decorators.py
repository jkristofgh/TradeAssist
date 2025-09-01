"""
Unit tests for database decorators.

Comprehensive testing for database decorators including:
- Test successful session management (commit scenarios)
- Test error handling and rollback behavior  
- Test instrument validation success and failure cases
- Test decorator stacking combinations
- Test performance overhead measurement
- Test integration with existing database patterns
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.backend.database.decorators import (
    with_db_session,
    with_validated_instrument,
    handle_db_errors
)
from src.backend.database.exceptions import (
    DatabaseOperationError,
    InstrumentValidationError
)


class TestDatabaseDecorators:
    """
    Comprehensive testing for database decorators.
    
    Requirements:
    - Test successful session management (commit scenarios)
    - Test error handling and rollback behavior  
    - Test instrument validation success and failure cases
    - Test decorator stacking combinations
    - Test performance overhead measurement
    - Test integration with existing database patterns
    """

    @pytest.mark.asyncio
    async def test_with_db_session_success_instance_method(self):
        """Test successful database session management for instance methods."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Create mock service instance
        mock_service = MagicMock()
        mock_service.__dict__ = {}  # Indicates this is an instance
        
        # Define test function
        @with_db_session
        async def test_method(self, session, param1):
            assert isinstance(session, AsyncMock)
            return f"result-{param1}"
        
        # Mock the get_db_session function
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            result = await test_method(mock_service, "test")
            
        assert result == "result-test"
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_db_session_success_static_method(self):
        """Test successful database session management for static methods."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Define test function (no self parameter)
        @with_db_session
        async def test_function(session, param1):
            assert isinstance(session, AsyncMock)
            return f"result-{param1}"
        
        # Mock the get_db_session function
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            result = await test_function("test")
            
        assert result == "result-test"
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_db_session_rollback_on_error(self):
        """Test rollback behavior on exceptions."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Define failing function
        @with_db_session
        async def failing_function(session):
            raise ValueError("Test error")
        
        # Mock the get_db_session function
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            with pytest.raises(ValueError, match="Test error"):
                await failing_function()
                
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_validated_instrument_success(self):
        """Test successful instrument validation and injection."""
        # Create mock session and instrument
        mock_session = AsyncMock(spec=AsyncSession)
        mock_instrument = MagicMock()
        mock_instrument.status = "active"  # Use actual enum value
        
        # Mock the database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_instrument)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Define test function
        @with_validated_instrument
        async def test_function(session, instrument, param1):
            assert instrument == mock_instrument
            return f"result-{param1}"
        
        # Mock the imports at the module level
        with patch('src.backend.models.instruments.InstrumentStatus') as mock_status:
            mock_status.ACTIVE = "active"
            result = await test_function(mock_session, 123, "test")
            
        assert result == "result-test"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_validated_instrument_not_found(self):
        """Test instrument validation failure when instrument not found."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock the database query to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Define test function
        @with_validated_instrument
        async def test_function(session, instrument, param1):
            return f"result-{param1}"
        
        with pytest.raises(ValueError, match="Instrument 123 not found"):
            await test_function(mock_session, 123, "test")

    @pytest.mark.asyncio
    async def test_with_validated_instrument_inactive(self):
        """Test instrument validation failure when instrument is inactive."""
        # Create mock session and inactive instrument
        mock_session = AsyncMock(spec=AsyncSession)
        mock_instrument = MagicMock()
        mock_instrument.status = "inactive"  # Use actual enum value
        
        # Mock the database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_instrument)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Define test function
        @with_validated_instrument
        async def test_function(session, instrument, param1):
            return f"result-{param1}"
        
        # Mock the InstrumentStatus enum at the right location
        with patch('src.backend.models.instruments.InstrumentStatus') as mock_status:
            mock_status.ACTIVE = "active"
            with pytest.raises(ValueError, match="Instrument 123 is not active"):
                await test_function(mock_session, 123, "test")

    @pytest.mark.asyncio
    async def test_decorator_stacking_success(self):
        """Test successful decorator stacking with @with_db_session and @with_validated_instrument."""
        # Create mock session and instrument
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_instrument = MagicMock()
        mock_instrument.status = "ACTIVE"
        
        # Mock the database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_instrument)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Create mock service instance
        mock_service = MagicMock()
        mock_service.__dict__ = {}
        
        # Define test function with stacked decorators
        @with_db_session
        @with_validated_instrument
        async def test_method(self, session, instrument, param1):
            assert isinstance(session, AsyncMock)
            assert instrument == mock_instrument
            return f"result-{param1}"
        
        # Mock dependencies
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session), \
             patch('src.backend.database.decorators.InstrumentStatus') as mock_status:
            mock_status.ACTIVE = "ACTIVE"
            result = await test_method(mock_service, 123, "test")
            
        assert result == "result-test"
        mock_session.commit.assert_called_once()
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_db_errors_success(self):
        """Test handle_db_errors decorator with successful operation."""
        @handle_db_errors("Test operation")
        async def test_function(param1):
            return f"result-{param1}"
        
        result = await test_function("test")
        assert result == "result-test"

    @pytest.mark.asyncio
    async def test_handle_db_errors_exception_handling(self):
        """Test handle_db_errors decorator with exception handling."""
        @handle_db_errors("Test operation")
        async def failing_function():
            raise SQLAlchemyError("Database error")
        
        with pytest.raises(DatabaseOperationError) as exc_info:
            await failing_function()
        
        assert "Test operation failed" in str(exc_info.value)
        assert exc_info.value.__cause__.__class__ == SQLAlchemyError

    @pytest.mark.asyncio
    async def test_handle_db_errors_preserve_database_operation_error(self):
        """Test that handle_db_errors preserves existing DatabaseOperationError."""
        @handle_db_errors("Test operation")
        async def failing_function():
            raise DatabaseOperationError("Original database error")
        
        with pytest.raises(DatabaseOperationError, match="Original database error"):
            await failing_function()

    @pytest.mark.asyncio
    async def test_decorator_logging_integration(self):
        """Test that decorators integrate properly with structlog logging."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        @with_db_session
        async def failing_function(session):
            raise ValueError("Test error for logging")
        
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session), \
             patch('src.backend.database.decorators.logger') as mock_logger:
            
            with pytest.raises(ValueError):
                await failing_function()
                
            # Verify logging was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Database error in failing_function" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_performance_overhead_measurement(self):
        """Test that decorator performance overhead is minimal."""
        import time
        
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Test function that does minimal work
        @with_db_session
        async def minimal_function(session):
            return "done"
        
        # Measure performance
        iterations = 100
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            start_time = time.time()
            
            tasks = []
            for _ in range(iterations):
                task = minimal_function()
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time_per_call = total_time / iterations
        
        # Performance requirement: <10ms per operation
        assert avg_time_per_call < 10, f"Decorator overhead too high: {avg_time_per_call}ms"

    @pytest.mark.asyncio
    async def test_complex_decorator_stacking_with_error_handling(self):
        """Test complex decorator stacking with all three decorators."""
        # Create mock session and instrument
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_instrument = MagicMock()
        mock_instrument.status = "ACTIVE"
        
        # Mock the database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_instrument)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Create mock service instance
        mock_service = MagicMock()
        mock_service.__dict__ = {}
        
        # Define test function with all three decorators
        @handle_db_errors("Complex operation")
        @with_db_session
        @with_validated_instrument
        async def complex_method(self, session, instrument, param1):
            return f"complex-result-{param1}"
        
        # Test successful execution
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session), \
             patch('src.backend.database.decorators.InstrumentStatus') as mock_status:
            mock_status.ACTIVE = "ACTIVE"
            result = await complex_method(mock_service, 123, "test")
            
        assert result == "complex-result-test"
        mock_session.commit.assert_called_once()
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_propagation_in_stacked_decorators(self):
        """Test proper error propagation through stacked decorators."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock instrument not found scenario
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Create mock service instance
        mock_service = MagicMock()
        mock_service.__dict__ = {}
        
        @handle_db_errors("Error propagation test")
        @with_db_session
        @with_validated_instrument
        async def failing_method(self, session, instrument, param1):
            return "should not reach here"
        
        with patch('src.backend.database.decorators.get_db_session', return_value=mock_session):
            with pytest.raises(DatabaseOperationError) as exc_info:
                await failing_method(mock_service, 123, "test")
            
            # Verify the original ValueError was preserved in the chain
            assert isinstance(exc_info.value.__cause__, ValueError)
            assert "Instrument 123 not found" in str(exc_info.value.__cause__)
            
        # Verify rollback was called due to the exception
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()