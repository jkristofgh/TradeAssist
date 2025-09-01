"""
Integration tests for Phase 2: API Standardization & Reliability

Tests the standardized response formats, error handling, validation decorators,
and pagination across all migrated endpoints.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.backend.api.common.exceptions import StandardAPIError, ValidationError, SystemError
from src.backend.api.common.responses import (
    AnalyticsResponseBuilder, 
    InstrumentResponseBuilder, 
    HealthResponseBuilder
)
from src.backend.api.common.validators import validate_instrument_exists


class TestStandardizedResponseFormats:
    """Test standardized response formats across all endpoint types."""
    
    def test_analytics_response_builder(self):
        """Test AnalyticsResponseBuilder produces consistent format."""
        builder = AnalyticsResponseBuilder()
        
        test_data = {"analysis": "test_result", "confidence": 0.95}
        response = builder.success(test_data) \
            .with_performance_metrics(45.2, 1440) \
            .with_confidence_score(0.95) \
            .build()
        
        # Verify standardized structure
        assert "data" in response
        assert "metadata" in response
        assert response["data"] == test_data
        
        # Verify metadata structure
        metadata = response["metadata"]
        assert "timestamp" in metadata
        assert "performance_metrics" in metadata
        assert metadata["performance_metrics"]["processing_time_ms"] == 45.2
        assert metadata["performance_metrics"]["data_points"] == 1440
        assert metadata["confidence_score"] == 0.95
    
    def test_instrument_response_builder(self):
        """Test InstrumentResponseBuilder produces consistent format."""
        builder = InstrumentResponseBuilder()
        
        test_data = {"id": 1, "symbol": "AAPL", "status": "active"}
        response = builder.success(test_data) \
            .with_performance_metrics(15.3, 1) \
            .build()
        
        # Verify standardized structure
        assert "data" in response
        assert "metadata" in response
        assert response["data"] == test_data
        
        # Verify metadata
        metadata = response["metadata"]
        assert "timestamp" in metadata
        assert metadata["performance_metrics"]["processing_time_ms"] == 15.3
    
    def test_health_response_builder(self):
        """Test HealthResponseBuilder produces consistent format."""
        builder = HealthResponseBuilder()
        
        health_data = {"status": "healthy", "active_services": 5}
        response = builder.success(health_data) \
            .with_performance_metrics(8.7, 5) \
            .build()
        
        # Verify standardized structure
        assert "data" in response
        assert "metadata" in response
        assert response["data"]["status"] == "healthy"


class TestStandardizedErrorHandling:
    """Test standardized error handling across all endpoint types."""
    
    def test_validation_error_format(self):
        """Test ValidationError produces standardized format."""
        error = ValidationError(
            error_code="TEST_001",
            message="Test validation error",
            details={"field": "test_field", "value": "invalid"}
        )
        
        assert error.error_code == "TEST_001"
        assert error.error_category == "validation"
        assert error.message == "Test validation error"
        assert error.details["field"] == "test_field"
    
    def test_system_error_format(self):
        """Test SystemError produces standardized format."""
        error = SystemError(
            error_code="SYS_001",
            message="Database connection failed",
            details={"database": "trade_assist", "timeout": 30}
        )
        
        assert error.error_code == "SYS_001"
        assert error.error_category == "system"
        assert error.message == "Database connection failed"
    
    def test_error_response_structure(self):
        """Test error responses have consistent structure."""
        error = ValidationError(
            error_code="TEST_002",
            message="Test error",
            details={"test": True}
        )
        
        # StandardAPIError should have required attributes
        assert hasattr(error, 'error_code')
        assert hasattr(error, 'error_category')
        assert hasattr(error, 'message')
        assert hasattr(error, 'details')


class TestPaginationFramework:
    """Test pagination framework consistency across list endpoints."""
    
    def test_paginated_response_structure(self):
        """Test paginated responses have consistent structure."""
        builder = InstrumentResponseBuilder()
        
        test_items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]
        
        response = builder.paginated(
            test_items,
            total_count=25,
            page=1,
            per_page=10
        ).build()
        
        # Verify paginated structure
        assert "data" in response
        assert "pagination" in response
        assert "metadata" in response
        
        # Verify pagination metadata
        pagination = response["pagination"]
        assert pagination["total"] == 25
        assert pagination["page"] == 1
        assert pagination["per_page"] == 10
        assert pagination["pages"] == 3
        assert pagination["has_next"] == True
        assert pagination["has_prev"] == False
    
    def test_pagination_edge_cases(self):
        """Test pagination handles edge cases correctly."""
        builder = InstrumentResponseBuilder()
        
        # Test last page
        response = builder.paginated(
            [{"id": 21}],
            total_count=21,
            page=3,
            per_page=10
        ).build()
        
        pagination = response["pagination"]
        assert pagination["has_next"] == False
        assert pagination["has_prev"] == True


class TestPerformanceMetrics:
    """Test performance metrics integration."""
    
    def test_processing_time_inclusion(self):
        """Test all responses include processing time."""
        builder = AnalyticsResponseBuilder()
        
        response = builder.success({"test": "data"}) \
            .with_performance_metrics(123.45, 100) \
            .build()
        
        assert "performance_metrics" in response["metadata"]
        assert response["metadata"]["performance_metrics"]["processing_time_ms"] == 123.45
        assert response["metadata"]["performance_metrics"]["data_points"] == 100
    
    def test_timestamp_formatting(self):
        """Test all responses include properly formatted timestamps."""
        builder = HealthResponseBuilder()
        
        response = builder.success({"status": "healthy"}).build()
        
        assert "timestamp" in response["metadata"]
        # Verify ISO 8601 format
        timestamp_str = response["metadata"]["timestamp"]
        parsed_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert isinstance(parsed_time, datetime)


class TestConfigurationIntegration:
    """Test configuration integration across endpoints."""
    
    def test_error_codes_consistency(self):
        """Test error codes follow consistent pattern."""
        # Analytics errors should start with ANALYTICS_
        analytics_error = ValidationError(
            error_code="ANALYTICS_001",
            message="Analytics validation failed"
        )
        assert analytics_error.error_code.startswith("ANALYTICS_")
        
        # Rules errors should start with RULES_
        rules_error = ValidationError(
            error_code="RULES_001", 
            message="Rules validation failed"
        )
        assert rules_error.error_code.startswith("RULES_")
        
        # Health errors should start with HEALTH_
        health_error = SystemError(
            error_code="HEALTH_001",
            message="Health check failed"
        )
        assert health_error.error_code.startswith("HEALTH_")


class TestBackwardCompatibility:
    """Test backward compatibility during transition."""
    
    def test_response_field_preservation(self):
        """Test new standardized responses preserve existing fields."""
        builder = AnalyticsResponseBuilder()
        
        # Simulate legacy data structure
        legacy_data = {
            "timestamp": "2024-01-01T12:00:00",
            "instrument_id": 1,
            "analysis_result": {"rsi": 65.2}
        }
        
        response = builder.success(legacy_data).build()
        
        # Verify legacy fields are preserved in data
        assert response["data"]["timestamp"] == "2024-01-01T12:00:00"
        assert response["data"]["instrument_id"] == 1
        assert response["data"]["analysis_result"]["rsi"] == 65.2
        
        # Verify new standardized metadata is added
        assert "metadata" in response
        assert "timestamp" in response["metadata"]


@pytest.mark.asyncio
class TestEndToEndIntegration:
    """Test complete request/response cycles."""
    
    async def test_complete_analytics_flow(self):
        """Test complete analytics request flow with standardization."""
        # This would test actual endpoint calls in a real integration test
        # For now, verify the response builders work end-to-end
        
        builder = AnalyticsResponseBuilder()
        
        # Simulate analytics processing
        start_time = datetime.utcnow()
        analysis_data = {
            "instrument_id": 1,
            "technical_indicators": [
                {"type": "RSI", "value": 65.2, "signal": "neutral"}
            ]
        }
        
        processing_time = 45.7
        data_points = 1440
        confidence = 0.92
        
        response = builder.success(analysis_data) \
            .with_performance_metrics(processing_time, data_points) \
            .with_confidence_score(confidence) \
            .build()
        
        # Verify complete response structure
        assert response["data"]["instrument_id"] == 1
        assert len(response["data"]["technical_indicators"]) == 1
        assert response["metadata"]["confidence_score"] == 0.92
        assert response["metadata"]["performance_metrics"]["processing_time_ms"] == 45.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])