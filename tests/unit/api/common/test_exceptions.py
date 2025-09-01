"""
Unit tests for standardized exception hierarchy.

Tests the StandardAPIError framework and all error category subclasses
for proper serialization, error codes, and HTTP status mapping.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.backend.api.common.exceptions import (
    StandardAPIError,
    ValidationError,
    AuthenticationError,
    BusinessLogicError,
    SystemError,
    ErrorResponse,
    CommonErrors
)


class TestStandardAPIError:
    """Test base StandardAPIError class."""
    
    def test_basic_error_creation(self):
        """Test creating basic StandardAPIError with required parameters."""
        error = StandardAPIError(
            error_code="TEST_001",
            message="Test error message"
        )
        
        assert error.error_code == "TEST_001"
        assert error.error_category == "system"
        assert error.status_code == 500
        assert error.correlation_id is not None
        assert isinstance(error.timestamp, datetime)
        
        # Check detail structure
        detail = error.detail
        assert detail["error_code"] == "TEST_001"
        assert detail["error_category"] == "system"
        assert detail["message"] == "Test error message"
        assert "timestamp" in detail
        assert "correlation_id" in detail
    
    def test_error_with_custom_correlation_id(self):
        """Test error with custom correlation ID."""
        custom_id = "custom-correlation-123"
        error = StandardAPIError(
            error_code="TEST_002",
            message="Test message",
            correlation_id=custom_id
        )
        
        assert error.correlation_id == custom_id
        assert error.detail["correlation_id"] == custom_id
    
    def test_error_with_request_path(self):
        """Test error with request path information."""
        error = StandardAPIError(
            error_code="TEST_003",
            message="Test message",
            request_path="/api/test/endpoint"
        )
        
        assert error.request_path == "/api/test/endpoint"
        assert error.detail["request_path"] == "/api/test/endpoint"
    
    def test_error_with_details(self):
        """Test error with additional context details."""
        details = {"user_id": 123, "operation": "test_operation"}
        error = StandardAPIError(
            error_code="TEST_004",
            message="Test message",
            details=details
        )
        
        assert error.error_details == details
        assert error.detail["details"] == details
    
    def test_error_fluent_methods(self):
        """Test fluent interface methods for adding context."""
        error = StandardAPIError(
            error_code="TEST_005",
            message="Test message"
        )
        
        updated_error = error.with_correlation_id("new-id").with_request_path("/api/new")
        
        assert updated_error.correlation_id == "new-id"
        assert updated_error.request_path == "/api/new"
        assert updated_error is error  # Should return same instance


class TestValidationError:
    """Test ValidationError class."""
    
    def test_validation_error_basic(self):
        """Test basic ValidationError creation."""
        error = ValidationError(
            error_code="VALIDATION_001",
            message="Validation failed"
        )
        
        assert error.error_category == "validation"
        assert error.status_code == 422
        assert error.error_code == "VALIDATION_001"
    
    def test_validation_error_with_field_errors(self):
        """Test ValidationError with field-specific errors."""
        field_errors = {
            "email": "Invalid email format",
            "age": "Must be between 18 and 120"
        }
        
        error = ValidationError(
            error_code="VALIDATION_002",
            message="Multiple validation errors",
            field_errors=field_errors
        )
        
        assert error.error_details["field_errors"] == field_errors
        assert error.detail["details"]["field_errors"] == field_errors
    
    def test_validation_error_with_invalid_value(self):
        """Test ValidationError with invalid value context."""
        invalid_value = "invalid@email"
        
        error = ValidationError(
            error_code="VALIDATION_003",
            message="Invalid email address",
            invalid_value=invalid_value
        )
        
        assert error.error_details["invalid_value"] == str(invalid_value)
        assert error.detail["details"]["invalid_value"] == str(invalid_value)


class TestAuthenticationError:
    """Test AuthenticationError class."""
    
    def test_authentication_error_basic(self):
        """Test basic AuthenticationError creation."""
        error = AuthenticationError(
            error_code="AUTH_001",
            message="Authentication failed"
        )
        
        assert error.error_category == "authentication"
        assert error.status_code == 401
        assert error.error_code == "AUTH_001"
    
    def test_authentication_error_with_auth_scheme(self):
        """Test AuthenticationError with authentication scheme."""
        error = AuthenticationError(
            error_code="AUTH_002",
            message="Invalid token",
            auth_scheme="Bearer"
        )
        
        assert error.error_details["auth_scheme"] == "Bearer"
        assert error.detail["details"]["auth_scheme"] == "Bearer"
    
    def test_authentication_error_with_required_scopes(self):
        """Test AuthenticationError with required scopes."""
        required_scopes = ["read:data", "write:data"]
        
        error = AuthenticationError(
            error_code="AUTH_003",
            message="Insufficient permissions",
            required_scopes=required_scopes
        )
        
        assert error.error_details["required_scopes"] == required_scopes
        assert error.detail["details"]["required_scopes"] == required_scopes


class TestBusinessLogicError:
    """Test BusinessLogicError class."""
    
    def test_business_logic_error_basic(self):
        """Test basic BusinessLogicError creation."""
        error = BusinessLogicError(
            error_code="BUSINESS_001",
            message="Business rule violation"
        )
        
        assert error.error_category == "business"
        assert error.status_code == 400
        assert error.error_code == "BUSINESS_001"
    
    def test_business_logic_error_with_rule_violated(self):
        """Test BusinessLogicError with violated rule information."""
        error = BusinessLogicError(
            error_code="BUSINESS_002",
            message="Maximum position size exceeded",
            rule_violated="max_position_size"
        )
        
        assert error.error_details["rule_violated"] == "max_position_size"
        assert error.detail["details"]["rule_violated"] == "max_position_size"
    
    def test_business_logic_error_with_context(self):
        """Test BusinessLogicError with business context."""
        context = {"current_position": 10000, "max_allowed": 5000}
        
        error = BusinessLogicError(
            error_code="BUSINESS_003",
            message="Position limit exceeded",
            context=context
        )
        
        assert error.error_details["context"] == context
        assert error.detail["details"]["context"] == context


class TestSystemError:
    """Test SystemError class."""
    
    def test_system_error_basic(self):
        """Test basic SystemError creation."""
        error = SystemError(
            error_code="SYSTEM_001",
            message="Database connection failed"
        )
        
        assert error.error_category == "system"
        assert error.status_code == 500
        assert error.error_code == "SYSTEM_001"
    
    def test_system_error_with_system_component(self):
        """Test SystemError with system component information."""
        error = SystemError(
            error_code="SYSTEM_002",
            message="External API timeout",
            system_component="schwab_api"
        )
        
        assert error.error_details["system_component"] == "schwab_api"
        assert error.detail["details"]["system_component"] == "schwab_api"
    
    def test_system_error_with_upstream_error(self):
        """Test SystemError with upstream error information."""
        upstream_error = "Connection timeout after 30 seconds"
        
        error = SystemError(
            error_code="SYSTEM_003",
            message="External service unavailable",
            upstream_error=upstream_error
        )
        
        assert error.error_details["upstream_error"] == upstream_error
        assert error.detail["details"]["upstream_error"] == upstream_error


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_error_response_serialization(self):
        """Test ErrorResponse model serialization."""
        now = datetime.utcnow()
        
        response = ErrorResponse(
            error_code="TEST_001",
            error_category="validation",
            message="Test error",
            timestamp=now,
            correlation_id="test-correlation-id"
        )
        
        data = response.model_dump()
        
        assert data["error_code"] == "TEST_001"
        assert data["error_category"] == "validation"
        assert data["message"] == "Test error"
        assert data["correlation_id"] == "test-correlation-id"
        assert "timestamp" in data
    
    def test_error_response_with_details(self):
        """Test ErrorResponse with additional details."""
        details = {"field": "email", "reason": "invalid_format"}
        
        response = ErrorResponse(
            error_code="TEST_002",
            error_category="validation",
            message="Validation failed",
            details=details,
            timestamp=datetime.utcnow(),
            correlation_id="test-id"
        )
        
        data = response.model_dump()
        assert data["details"] == details


class TestCommonErrors:
    """Test CommonErrors constants."""
    
    def test_common_errors_structure(self):
        """Test that common errors have proper structure."""
        error_code, error_message = CommonErrors.INSTRUMENT_NOT_FOUND
        
        assert isinstance(error_code, str)
        assert isinstance(error_message, str)
        assert error_code.startswith("VALIDATION_")
    
    def test_validation_errors(self):
        """Test validation error constants."""
        assert CommonErrors.INSTRUMENT_NOT_FOUND[0] == "VALIDATION_001"
        assert CommonErrors.INVALID_LOOKBACK_HOURS[0] == "VALIDATION_002"
        assert CommonErrors.INVALID_CONFIDENCE_LEVEL[0] == "VALIDATION_003"
        assert CommonErrors.INVALID_PAGINATION[0] == "VALIDATION_004"
        assert CommonErrors.INVALID_DATE_RANGE[0] == "VALIDATION_005"
    
    def test_authentication_errors(self):
        """Test authentication error constants."""
        assert CommonErrors.TOKEN_EXPIRED[0] == "AUTH_001"
        assert CommonErrors.INVALID_TOKEN[0] == "AUTH_002"
        assert CommonErrors.INSUFFICIENT_PERMISSIONS[0] == "AUTH_003"
        assert CommonErrors.AUTHENTICATION_REQUIRED[0] == "AUTH_004"
    
    def test_business_errors(self):
        """Test business logic error constants."""
        assert CommonErrors.INSUFFICIENT_DATA[0] == "BUSINESS_001"
        assert CommonErrors.INVALID_OPERATION[0] == "BUSINESS_002"
        assert CommonErrors.CONSTRAINT_VIOLATION[0] == "BUSINESS_003"
    
    def test_system_errors(self):
        """Test system error constants."""
        assert CommonErrors.DATABASE_CONNECTION_FAILED[0] == "SYSTEM_001"
        assert CommonErrors.EXTERNAL_API_UNAVAILABLE[0] == "SYSTEM_002"
        assert CommonErrors.INTERNAL_SERVER_ERROR[0] == "SYSTEM_003"
        assert CommonErrors.SERVICE_UNAVAILABLE[0] == "SYSTEM_004"


@pytest.fixture
def mock_datetime():
    """Fixture for mocking datetime."""
    with pytest.mock.patch('src.backend.api.common.exceptions.datetime') as mock_dt:
        mock_dt.utcnow.return_value = datetime(2024, 1, 15, 12, 0, 0)
        yield mock_dt


class TestErrorSerializationEdgeCases:
    """Test edge cases for error serialization."""
    
    def test_error_with_none_values(self):
        """Test error creation with None values."""
        error = StandardAPIError(
            error_code="TEST_001",
            message="Test message",
            details=None,
            correlation_id=None,
            request_path=None
        )
        
        assert error.correlation_id is not None  # Should be auto-generated
        assert error.detail["request_path"] is None
    
    def test_error_serialization_with_complex_details(self):
        """Test error serialization with complex detail objects."""
        details = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "mixed": {"numbers": [1, 2], "string": "test"}
        }
        
        error = StandardAPIError(
            error_code="TEST_002",
            message="Complex details test",
            details=details
        )
        
        serialized_details = error.detail["details"]
        assert serialized_details == details
    
    def test_error_message_sanitization(self):
        """Test that error messages are properly handled."""
        # Test with various characters that might cause issues
        message_with_special_chars = "Error with 'quotes' and \"double quotes\" and unicode: ñ"
        
        error = StandardAPIError(
            error_code="TEST_003",
            message=message_with_special_chars
        )
        
        assert error.detail["message"] == message_with_special_chars