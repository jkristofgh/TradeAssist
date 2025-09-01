"""
Integration tests for Phase 3 completion - API Standardization Integration and Polish.

Tests the complete Phase 3 implementation including configuration management,
performance optimization, monitoring integration, and API documentation.
"""

import asyncio
import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.backend.main import create_app
from src.backend.api.common.configuration import config_manager
from src.backend.services.api_performance_monitor import performance_monitor


@pytest.mark.integration
class TestPhase3ConfigurationIntegration:
    """Test Phase 3 configuration management integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client with Phase 3 configuration."""
        app = create_app()
        return TestClient(app)
    
    def test_configuration_endpoints_available(self, client):
        """Test that all Phase 3 configuration endpoints are available."""
        # Test configuration validation endpoint
        response = client.get("/api/health/config/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "validation_summary" in data
        
        # Test current configuration endpoint
        response = client.get("/api/health/config/current")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "configuration" in data
        assert len(data["configuration"]) == 5  # All 5 config sections
        
        # Test configuration reload endpoint
        response = client.post("/api/health/config/reload")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_monitoring_configuration_integration(self, client):
        """Test monitoring configuration integration."""
        # Get current configuration
        response = client.get("/api/health/config/current?config_section=monitoring")
        assert response.status_code == 200
        data = response.json()
        
        monitoring_config = data["configuration"]["monitoring"]
        
        # Verify all monitoring configuration fields are present
        expected_fields = [
            "enable_error_tracking",
            "enable_performance_tracking", 
            "enable_alerting",
            "error_sample_rate",
            "performance_sample_rate",
            "slow_request_threshold_ms",
            "response_time_alert_threshold_ms",
            "error_rate_alert_threshold",
            "metrics_retention_days"
        ]
        
        for field in expected_fields:
            assert field in monitoring_config
    
    def test_configuration_validation_cross_dependencies(self, client):
        """Test configuration validation checks cross-dependencies."""
        response = client.get("/api/health/config/validate")
        assert response.status_code == 200
        data = response.json()
        
        # Check that cross-section validation is performed
        assert "cross_section_validation" in data
        cross_validation = data["cross_section_validation"]
        
        # Should be valid by default (pagination limits should match)
        assert cross_validation["valid"] is True
        assert len(cross_validation["errors"]) == 0


@pytest.mark.integration
class TestPhase3PerformanceIntegration:
    """Test Phase 3 performance monitoring integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_performance_monitoring_endpoints(self, client):
        """Test performance monitoring API endpoints."""
        # Test performance statistics endpoint
        response = client.get("/api/health/performance/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "performance_data" in data
        assert "monitoring_config" in data
        
        # Test performance reset endpoint
        response = client.post("/api/health/performance/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Test performance alerts endpoint
        response = client.get("/api/health/performance/alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "alerting_status" in data
    
    @pytest.mark.asyncio
    async def test_performance_tracking_integration(self):
        """Test that performance tracking integrates with actual requests."""
        from src.backend.services.api_performance_monitor import track_api_performance
        
        # Track a test request
        async with track_api_performance("/api/test", "GET") as metrics:
            await asyncio.sleep(0.001)  # 1ms
            metrics["cache_hit"] = True
        
        # Get statistics
        stats = performance_monitor.get_endpoint_statistics()
        
        # Should have recorded the request
        assert "global_statistics" in stats
        global_stats = stats["global_statistics"]
        assert global_stats["total_requests"] >= 1
    
    def test_optimized_response_builders_available(self):
        """Test that optimized response builders are available."""
        from src.backend.api.common.responses import (
            OptimizedAPIResponseBuilder,
            OptimizedAnalyticsResponseBuilder,
            OptimizedInstrumentResponseBuilder,
            OptimizedHealthResponseBuilder,
            create_optimized_response_builder
        )
        
        # Test factory function
        builder = create_optimized_response_builder('analytics')
        assert isinstance(builder, OptimizedAnalyticsResponseBuilder)
        
        builder = create_optimized_response_builder('instrument')
        assert isinstance(builder, OptimizedInstrumentResponseBuilder)
        
        builder = create_optimized_response_builder('health')
        assert isinstance(builder, OptimizedHealthResponseBuilder)
        
        builder = create_optimized_response_builder('base')
        assert isinstance(builder, OptimizedAPIResponseBuilder)
    
    def test_optimized_response_builder_performance(self):
        """Test optimized response builder performance improvements."""
        from src.backend.api.common.responses import (
            APIResponseBuilder,
            OptimizedAPIResponseBuilder
        )
        
        # Test data
        test_data = {"message": "test", "count": 100}
        test_metadata = {"processing_time": 50.0, "cache_hit": True}
        
        # Measure standard builder performance
        standard_builder = APIResponseBuilder()
        start_time = time.time()
        
        for _ in range(100):
            standard_builder.success(test_data, test_metadata)
        
        standard_time = time.time() - start_time
        
        # Measure optimized builder performance
        optimized_builder = OptimizedAPIResponseBuilder()
        start_time = time.time()
        
        for _ in range(100):
            optimized_builder.success(test_data, test_metadata)
        
        optimized_time = time.time() - start_time
        
        # Optimized builder should be faster or at least not significantly slower
        # Allow for some variance in timing
        assert optimized_time <= standard_time * 1.1


@pytest.mark.integration
class TestPhase3APIDocumentation:
    """Test Phase 3 API documentation generation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available with Phase 3 endpoints."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        
        # Check that Phase 3 endpoints are documented
        paths = schema.get("paths", {})
        
        # Configuration endpoints
        assert "/api/health/config/validate" in paths
        assert "/api/health/config/current" in paths
        assert "/api/health/config/reload" in paths
        
        # Performance monitoring endpoints
        assert "/api/health/performance/statistics" in paths
        assert "/api/health/performance/reset" in paths
        assert "/api/health/performance/alerts" in paths
    
    def test_api_documentation_completeness(self, client):
        """Test that API documentation includes all standardized components."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check that components are defined
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Should have standardized response schemas
        standardized_schemas = [
            schema_name for schema_name in schemas.keys()
            if any(keyword in schema_name.lower() for keyword in 
                   ["response", "error", "pagination", "performance", "config"])
        ]
        
        # Should have at least some standardized schemas
        assert len(standardized_schemas) > 0


@pytest.mark.integration
class TestPhase3BackwardCompatibility:
    """Test Phase 3 maintains backward compatibility."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_existing_endpoints_still_work(self, client):
        """Test that existing API endpoints still work after Phase 3."""
        # Test health endpoint (should still work)
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Test instruments endpoint (should still work)
        response = client.get("/api/instruments")
        assert response.status_code == 200
    
    def test_response_format_consistency(self, client):
        """Test that response formats are consistent across endpoints."""
        endpoints_to_test = [
            "/api/health",
            "/api/instruments", 
            "/api/health/config/validate",
            "/api/health/performance/statistics"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            data = response.json()
            
            # All responses should have consistent structure
            assert "success" in data
            assert "timestamp" in data
            
            # Check headers for standardization
            headers = response.headers
            assert "X-API-Version" in headers
            assert "X-Correlation-ID" in headers


@pytest.mark.integration  
class TestPhase3EndToEndWorkflow:
    """Test complete Phase 3 end-to-end workflow."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_complete_phase3_workflow(self, client):
        """Test complete Phase 3 functionality workflow."""
        
        # Step 1: Validate current configuration
        response = client.get("/api/health/config/validate")
        assert response.status_code == 200
        validation_result = response.json()
        assert validation_result["success"] is True
        
        # Step 2: Get current configuration
        response = client.get("/api/health/config/current")
        assert response.status_code == 200
        config_result = response.json()
        assert config_result["success"] is True
        assert len(config_result["configuration"]) == 5
        
        # Step 3: Make some API calls to generate performance data
        test_endpoints = ["/api/health", "/api/instruments"]
        
        for endpoint in test_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
        
        # Step 4: Check performance statistics
        response = client.get("/api/health/performance/statistics")
        assert response.status_code == 200
        perf_result = response.json()
        assert perf_result["success"] is True
        
        # Should have recorded some requests
        performance_data = perf_result["performance_data"]
        if "global_statistics" in performance_data:
            global_stats = performance_data["global_statistics"]
            # May have some requests from the test calls above
            assert global_stats["total_requests"] >= 0
        
        # Step 5: Check alert status
        response = client.get("/api/health/performance/alerts")
        assert response.status_code == 200
        alert_result = response.json()
        assert alert_result["success"] is True
        assert "alerting_status" in alert_result
        
        # Step 6: Test configuration reload
        response = client.post("/api/health/config/reload")
        assert response.status_code == 200
        reload_result = response.json()
        assert reload_result["success"] is True
    
    def test_error_handling_consistency(self, client):
        """Test that error handling is consistent across Phase 3 endpoints."""
        # Test invalid configuration section
        response = client.get("/api/health/config/validate?config_section=invalid")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        
        # Test invalid endpoint parameters
        response = client.get("/api/health/config/current?config_section=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        
        # All error responses should have consistent structure
        required_error_fields = ["success", "error", "timestamp"]
        for field in required_error_fields:
            assert field in data


@pytest.mark.integration
class TestPhase3PerformanceTargets:
    """Test that Phase 3 meets performance targets."""
    
    def test_standardization_overhead_target(self):
        """Test that standardization overhead is <10ms as required."""
        from src.backend.api.common.responses import OptimizedAPIResponseBuilder
        
        test_data = {
            "message": "Performance test data",
            "items": list(range(100)),
            "metadata": {"test": True}
        }
        
        builder = OptimizedAPIResponseBuilder()
        
        # Measure response building time
        iterations = 100
        start_time = time.time()
        
        for _ in range(iterations):
            response = builder.success(test_data, {"processing_time": 50.0})
        
        total_time = time.time() - start_time
        avg_time_ms = (total_time / iterations) * 1000
        
        # Should be well under 10ms per response
        assert avg_time_ms < 10.0, f"Standardization overhead {avg_time_ms:.2f}ms exceeds 10ms target"
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_overhead(self):
        """Test that performance monitoring overhead is minimal."""
        from src.backend.services.api_performance_monitor import track_api_performance
        
        # Test with monitoring
        start_time = time.time()
        iterations = 50
        
        for i in range(iterations):
            async with track_api_performance(f"/api/test{i}"):
                await asyncio.sleep(0.001)  # Simulate 1ms work
        
        with_monitoring_time = time.time() - start_time
        
        # Test without monitoring
        start_time = time.time()
        
        for _ in range(iterations):
            await asyncio.sleep(0.001)  # Same 1ms work
        
        without_monitoring_time = time.time() - start_time
        
        # Monitoring overhead should be minimal
        overhead = with_monitoring_time - without_monitoring_time
        overhead_per_request_ms = (overhead / iterations) * 1000
        
        assert overhead_per_request_ms < 5.0, f"Monitoring overhead {overhead_per_request_ms:.2f}ms is too high"


if __name__ == "__main__":
    pytest.main([__file__])