"""
Unit tests for response builder framework.

Tests the APIResponseBuilder framework and all specialized response builders
for proper response formatting, metadata handling, and timestamp consistency.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.backend.api.common.responses import (
    APIResponseBuilder,
    AnalyticsResponseBuilder,
    InstrumentResponseBuilder,
    HealthResponseBuilder,
    PaginationInfo,
    StandardResponse,
    StandardErrorResponse,
    PaginatedResponse
)
from src.backend.api.common.exceptions import ValidationError


class TestPaginationInfo:
    """Test PaginationInfo model."""
    
    def test_pagination_info_creation(self):
        """Test creating PaginationInfo with all fields."""
        pagination = PaginationInfo(
            page=2,
            per_page=25,
            total=100,
            pages=4,
            has_next=True,
            has_prev=True
        )
        
        assert pagination.page == 2
        assert pagination.per_page == 25
        assert pagination.total == 100
        assert pagination.pages == 4
        assert pagination.has_next is True
        assert pagination.has_prev is True
    
    def test_pagination_info_serialization(self):
        """Test PaginationInfo serialization."""
        pagination = PaginationInfo(
            page=1,
            per_page=10,
            total=50,
            pages=5,
            has_next=True,
            has_prev=False
        )
        
        data = pagination.model_dump()
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert data["total"] == 50
        assert data["pages"] == 5
        assert data["has_next"] is True
        assert data["has_prev"] is False


class TestAPIResponseBuilder:
    """Test base APIResponseBuilder class."""
    
    def test_success_response_basic(self):
        """Test creating basic success response."""
        builder = APIResponseBuilder()
        data = {"id": 1, "name": "test"}
        
        response = builder.success(data)
        
        assert response["data"] == data
        assert "timestamp" in response
        assert isinstance(response["timestamp"], str)
        assert response["metadata"] is None
    
    def test_success_response_with_metadata(self):
        """Test success response with metadata."""
        builder = APIResponseBuilder()
        data = {"id": 1, "name": "test"}
        metadata = {"source": "test", "version": "1.0"}
        
        response = builder.success(data, metadata)
        
        assert response["data"] == data
        assert response["metadata"] == metadata
        assert "timestamp" in response
    
    def test_success_response_with_builder_metadata(self):
        """Test success response with builder-level metadata."""
        builder = APIResponseBuilder()
        builder.with_metadata(operation="test", user_id=123)
        
        data = {"id": 1, "name": "test"}
        response = builder.success(data)
        
        assert response["data"] == data
        assert response["metadata"]["operation"] == "test"
        assert response["metadata"]["user_id"] == 123
    
    def test_success_response_metadata_merge(self):
        """Test metadata merging between builder and method call."""
        builder = APIResponseBuilder()
        builder.with_metadata(operation="test", source="builder")
        
        data = {"id": 1, "name": "test"}
        call_metadata = {"source": "call", "version": "1.0"}
        
        response = builder.success(data, call_metadata)
        
        # Call metadata should override builder metadata
        assert response["metadata"]["source"] == "call"
        assert response["metadata"]["operation"] == "test"
        assert response["metadata"]["version"] == "1.0"
    
    def test_error_response(self):
        """Test error response creation."""
        builder = APIResponseBuilder()
        error = ValidationError(
            error_code="TEST_001",
            message="Test error"
        )
        
        response = builder.error(error)
        
        assert response["error_code"] == "TEST_001"
        assert response["error_category"] == "validation"
        assert response["message"] == "Test error"
        assert "timestamp" in response
        assert "correlation_id" in response
    
    def test_paginated_response(self):
        """Test paginated response creation."""
        builder = APIResponseBuilder()
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        pagination = PaginationInfo(
            page=1,
            per_page=3,
            total=10,
            pages=4,
            has_next=True,
            has_prev=False
        )
        
        response = builder.paginated(items, pagination)
        
        assert response["data"] == items
        assert response["pagination"]["page"] == 1
        assert response["pagination"]["total"] == 10
        assert "timestamp" in response
    
    def test_paginated_response_with_metadata(self):
        """Test paginated response with metadata."""
        builder = APIResponseBuilder()
        builder.with_metadata(query_time=0.15)
        
        items = [{"id": 1}]
        pagination = PaginationInfo(
            page=1, per_page=1, total=1, pages=1, has_next=False, has_prev=False
        )
        
        response = builder.paginated(items, pagination, {"total_query_time": 0.25})
        
        assert response["data"] == items
        assert response["metadata"]["query_time"] == 0.15
        assert response["metadata"]["total_query_time"] == 0.25
    
    def test_with_custom_timestamp(self):
        """Test setting custom timestamp."""
        builder = APIResponseBuilder()
        custom_time = datetime(2024, 1, 15, 12, 0, 0)
        
        builder.with_timestamp(custom_time)
        response = builder.success({"test": "data"})
        
        assert response["timestamp"] == custom_time.isoformat()
    
    def test_method_chaining(self):
        """Test fluent interface method chaining."""
        builder = APIResponseBuilder()
        custom_time = datetime(2024, 1, 15, 12, 0, 0)
        
        response = (builder
                   .with_metadata(operation="test")
                   .with_timestamp(custom_time)
                   .success({"id": 1}))
        
        assert response["data"]["id"] == 1
        assert response["metadata"]["operation"] == "test"
        assert response["timestamp"] == custom_time.isoformat()


class TestAnalyticsResponseBuilder:
    """Test AnalyticsResponseBuilder class."""
    
    def test_performance_metrics(self):
        """Test adding performance metrics to analytics response."""
        builder = AnalyticsResponseBuilder()
        
        builder.with_performance_metrics(
            calculation_time=2.5,
            data_points=1000
        )
        
        response = builder.success({"result": "test"})
        
        perf = response["metadata"]["performance"]
        assert perf["calculation_time_seconds"] == 2.5
        assert perf["data_points_processed"] == 1000
        assert perf["processing_efficiency"] == 400.0  # 1000 / 2.5
    
    def test_performance_metrics_zero_time(self):
        """Test performance metrics with zero calculation time."""
        builder = AnalyticsResponseBuilder()
        
        builder.with_performance_metrics(
            calculation_time=0.0,
            data_points=100
        )
        
        response = builder.success({"result": "test"})
        
        perf = response["metadata"]["performance"]
        assert perf["processing_efficiency"] == 0
    
    def test_confidence_score(self):
        """Test adding confidence score to analytics response."""
        builder = AnalyticsResponseBuilder()
        
        builder.with_confidence_score(0.95)
        
        response = builder.success({"prediction": 125.50})
        
        confidence = response["metadata"]["confidence"]
        assert confidence["level"] == 0.95
        assert confidence["category"] == "high"
    
    def test_confidence_score_categories(self):
        """Test confidence score categorization."""
        test_cases = [
            (0.99, "high"),
            (0.95, "high"),
            (0.90, "medium"),
            (0.80, "medium"),
            (0.70, "low"),
            (0.50, "low")
        ]
        
        for confidence_level, expected_category in test_cases:
            builder = AnalyticsResponseBuilder()
            builder.with_confidence_score(confidence_level)
            response = builder.success({"test": "data"})
            
            actual_category = response["metadata"]["confidence"]["category"]
            assert actual_category == expected_category, f"Confidence {confidence_level} should be {expected_category}, got {actual_category}"
    
    def test_model_metadata(self):
        """Test adding model metadata to analytics response."""
        builder = AnalyticsResponseBuilder()
        
        model_params = {"lookback": 24, "confidence": 0.95}
        builder.with_model_metadata(
            model_type="LSTM",
            version="2.1.0",
            parameters=model_params
        )
        
        response = builder.success({"prediction": 100.0})
        
        model = response["metadata"]["model"]
        assert model["type"] == "LSTM"
        assert model["version"] == "2.1.0"
        assert model["parameters"] == model_params
    
    def test_model_metadata_without_parameters(self):
        """Test model metadata without parameters."""
        builder = AnalyticsResponseBuilder()
        
        builder.with_model_metadata(
            model_type="Linear Regression",
            version="1.0.0"
        )
        
        response = builder.success({"result": "test"})
        
        model = response["metadata"]["model"]
        assert model["type"] == "Linear Regression"
        assert model["version"] == "1.0.0"
        assert "parameters" not in model
    
    def test_data_quality_metrics(self):
        """Test adding data quality metrics to analytics response."""
        builder = AnalyticsResponseBuilder()
        
        builder.with_data_quality_metrics(
            completeness=0.95,
            freshness_minutes=5,
            anomalies_detected=2
        )
        
        response = builder.success({"analysis": "result"})
        
        quality = response["metadata"]["data_quality"]
        assert quality["completeness"] == 0.95
        assert quality["freshness_minutes"] == 5
        assert quality["anomalies_detected"] == 2
        assert 0.0 <= quality["quality_score"] <= 1.0
    
    def test_data_quality_score_calculation(self):
        """Test data quality score calculation."""
        test_cases = [
            # (completeness, freshness_min, anomalies, expected_range)
            (1.0, 0, 0, (0.9, 1.0)),  # Perfect data
            (0.8, 30, 1, (0.5, 0.8)),  # Moderate quality
            (0.5, 120, 5, (0.0, 0.5)),  # Poor quality
        ]
        
        for completeness, freshness, anomalies, (min_score, max_score) in test_cases:
            builder = AnalyticsResponseBuilder()
            builder.with_data_quality_metrics(completeness, freshness, anomalies)
            response = builder.success({"test": "data"})
            
            quality_score = response["metadata"]["data_quality"]["quality_score"]
            assert min_score <= quality_score <= max_score, f"Quality score {quality_score} not in range [{min_score}, {max_score}]"
    
    def test_combined_analytics_metadata(self):
        """Test combining multiple analytics metadata types."""
        builder = AnalyticsResponseBuilder()
        
        response = (builder
                   .with_performance_metrics(1.5, 500)
                   .with_confidence_score(0.90)
                   .with_model_metadata("Random Forest", "1.2.0")
                   .with_data_quality_metrics(0.90, 10, 0)
                   .success({"result": "complex_analysis"}))
        
        metadata = response["metadata"]
        
        assert "performance" in metadata
        assert "confidence" in metadata
        assert "model" in metadata
        assert "data_quality" in metadata
        
        assert metadata["performance"]["calculation_time_seconds"] == 1.5
        assert metadata["confidence"]["level"] == 0.90
        assert metadata["model"]["type"] == "Random Forest"
        assert metadata["data_quality"]["completeness"] == 0.90


class TestInstrumentResponseBuilder:
    """Test InstrumentResponseBuilder class."""
    
    def test_market_status(self):
        """Test adding market status to instrument response."""
        builder = InstrumentResponseBuilder()
        
        builder.with_market_status(
            status="OPEN",
            session_state="REGULAR_HOURS"
        )
        
        response = builder.success({"symbol": "AAPL", "price": 150.00})
        
        market = response["metadata"]["market_status"]
        assert market["status"] == "OPEN"
        assert market["session_state"] == "REGULAR_HOURS"
        assert market["is_trading_active"] is True
    
    def test_market_status_trading_activity(self):
        """Test market status trading activity detection."""
        active_statuses = ["OPEN", "PRE_MARKET", "AFTER_MARKET"]
        inactive_statuses = ["CLOSED", "HALTED", "SUSPENDED"]
        
        for status in active_statuses:
            builder = InstrumentResponseBuilder()
            builder.with_market_status(status)
            response = builder.success({"test": "data"})
            
            assert response["metadata"]["market_status"]["is_trading_active"] is True
        
        for status in inactive_statuses:
            builder = InstrumentResponseBuilder()
            builder.with_market_status(status)
            response = builder.success({"test": "data"})
            
            assert response["metadata"]["market_status"]["is_trading_active"] is False
    
    def test_market_status_with_next_session(self):
        """Test market status with next session start time."""
        builder = InstrumentResponseBuilder()
        next_session = datetime(2024, 1, 16, 9, 30, 0)
        
        builder.with_market_status(
            status="CLOSED",
            next_session_start=next_session
        )
        
        response = builder.success({"symbol": "AAPL"})
        
        market = response["metadata"]["market_status"]
        assert market["next_session_start"] == next_session.isoformat()
    
    def test_last_trade_info(self):
        """Test adding last trade information to instrument response."""
        builder = InstrumentResponseBuilder()
        trade_time = datetime(2024, 1, 15, 15, 30, 0)
        
        builder.with_last_trade_info(
            timestamp=trade_time,
            price=150.25,
            volume=1000,
            bid_ask_spread=0.02
        )
        
        response = builder.success({"symbol": "AAPL"})
        
        trade = response["metadata"]["last_trade"]
        assert trade["timestamp"] == trade_time.isoformat()
        assert trade["price"] == 150.25
        assert trade["volume"] == 1000
        assert trade["bid_ask_spread"] == 0.02
        assert "age_minutes" in trade
    
    def test_last_trade_info_minimal(self):
        """Test last trade info with only required fields."""
        builder = InstrumentResponseBuilder()
        trade_time = datetime(2024, 1, 15, 15, 30, 0)
        
        builder.with_last_trade_info(
            timestamp=trade_time,
            price=150.25
        )
        
        response = builder.success({"symbol": "AAPL"})
        
        trade = response["metadata"]["last_trade"]
        assert trade["timestamp"] == trade_time.isoformat()
        assert trade["price"] == 150.25
        assert "volume" not in trade
        assert "bid_ask_spread" not in trade
        assert "age_minutes" in trade
    
    def test_volatility_info(self):
        """Test adding volatility information to instrument response."""
        builder = InstrumentResponseBuilder()
        
        builder.with_volatility_info(
            current_volatility=0.25,
            volatility_percentile=0.85,
            volatility_category="high"
        )
        
        response = builder.success({"symbol": "AAPL"})
        
        volatility = response["metadata"]["volatility"]
        assert volatility["current"] == 0.25
        assert volatility["percentile"] == 0.85
        assert volatility["category"] == "high"
    
    def test_volatility_info_category_detection(self):
        """Test automatic volatility category detection."""
        test_cases = [
            (0.95, "high"),
            (0.80, "high"),
            (0.70, "elevated"),
            (0.60, "elevated"),
            (0.50, "normal"),
            (0.40, "normal"),
            (0.30, "low"),
            (0.20, "low"),
            (0.10, "very_low"),
            (0.05, "very_low")
        ]
        
        for percentile, expected_category in test_cases:
            builder = InstrumentResponseBuilder()
            builder.with_volatility_info(
                current_volatility=0.20,
                volatility_percentile=percentile
            )
            response = builder.success({"test": "data"})
            
            actual_category = response["metadata"]["volatility"]["category"]
            assert actual_category == expected_category, f"Percentile {percentile} should be {expected_category}, got {actual_category}"
    
    def test_combined_instrument_metadata(self):
        """Test combining multiple instrument metadata types."""
        builder = InstrumentResponseBuilder()
        trade_time = datetime(2024, 1, 15, 15, 30, 0)
        
        response = (builder
                   .with_market_status("OPEN", "REGULAR_HOURS")
                   .with_last_trade_info(trade_time, 150.00, 500)
                   .with_volatility_info(0.20, 0.65)
                   .success({"symbol": "AAPL", "price": 150.00}))
        
        metadata = response["metadata"]
        
        assert "market_status" in metadata
        assert "last_trade" in metadata
        assert "volatility" in metadata
        
        assert metadata["market_status"]["status"] == "OPEN"
        assert metadata["last_trade"]["price"] == 150.00
        assert metadata["volatility"]["category"] == "elevated"


class TestHealthResponseBuilder:
    """Test HealthResponseBuilder class."""
    
    def test_system_metrics(self):
        """Test adding system metrics to health response."""
        builder = HealthResponseBuilder()
        
        builder.with_system_metrics(
            cpu_usage=0.45,
            memory_usage=0.60,
            disk_usage=0.30,
            uptime_seconds=86400
        )
        
        response = builder.success({"status": "healthy"})
        
        metrics = response["metadata"]["system_metrics"]
        assert metrics["cpu_usage"] == 0.45
        assert metrics["memory_usage"] == 0.60
        assert metrics["disk_usage"] == 0.30
        assert metrics["uptime_seconds"] == 86400
        assert metrics["uptime_hours"] == 24.0
        assert "overall_health" in metrics
    
    def test_system_metrics_minimal(self):
        """Test system metrics with only required fields."""
        builder = HealthResponseBuilder()
        
        builder.with_system_metrics(
            cpu_usage=0.20,
            memory_usage=0.40
        )
        
        response = builder.success({"status": "healthy"})
        
        metrics = response["metadata"]["system_metrics"]
        assert metrics["cpu_usage"] == 0.20
        assert metrics["memory_usage"] == 0.40
        assert "disk_usage" not in metrics
        assert "uptime_seconds" not in metrics
        assert metrics["overall_health"] == "healthy"
    
    def test_system_health_calculation(self):
        """Test overall system health calculation."""
        test_cases = [
            # (cpu, memory, disk, expected_health)
            (0.10, 0.20, 0.15, "healthy"),
            (0.70, 0.60, 0.50, "healthy"),
            (0.85, 0.75, 0.60, "degraded"),
            (0.90, 0.70, None, "degraded"),
            (0.98, 0.95, 0.90, "critical"),
            (0.99, 0.80, None, "critical"),
        ]
        
        for cpu, memory, disk, expected_health in test_cases:
            builder = HealthResponseBuilder()
            
            if disk is not None:
                builder.with_system_metrics(cpu, memory, disk)
            else:
                builder.with_system_metrics(cpu, memory)
            
            response = builder.success({"status": "test"})
            
            actual_health = response["metadata"]["system_metrics"]["overall_health"]
            assert actual_health == expected_health, f"CPU:{cpu}, MEM:{memory}, DISK:{disk} should be {expected_health}, got {actual_health}"
    
    def test_service_status(self):
        """Test adding service status information to health response."""
        builder = HealthResponseBuilder()
        
        services = {
            "database": {"healthy": True, "response_time_ms": 15},
            "schwab_api": {"healthy": True, "response_time_ms": 120},
            "cache": {"healthy": False, "error": "Connection timeout"}
        }
        
        builder.with_service_status(services)
        
        response = builder.success({"status": "degraded"})
        
        assert response["metadata"]["services"] == services
        
        summary = response["metadata"]["service_summary"]
        assert summary["total_services"] == 3
        assert summary["healthy_services"] == 2
        assert summary["degraded_services"] == 1
        assert summary["overall_service_health"] == 2/3
    
    def test_service_status_empty(self):
        """Test service status with empty services."""
        builder = HealthResponseBuilder()
        
        builder.with_service_status({})
        
        response = builder.success({"status": "healthy"})
        
        summary = response["metadata"]["service_summary"]
        assert summary["total_services"] == 0
        assert summary["healthy_services"] == 0
        assert summary["overall_service_health"] == 1.0
    
    def test_performance_indicators(self):
        """Test adding performance indicators to health response."""
        builder = HealthResponseBuilder()
        
        builder.with_performance_indicators(
            response_time_ms=85.5,
            throughput_rps=150.0,
            error_rate=0.02
        )
        
        response = builder.success({"status": "healthy"})
        
        perf = response["metadata"]["performance"]
        assert perf["response_time_ms"] == 85.5
        assert perf["throughput_rps"] == 150.0
        assert perf["error_rate"] == 0.02
        assert perf["response_time_category"] == "excellent"
        assert perf["error_category"] == "good"
    
    def test_response_time_categories(self):
        """Test response time categorization."""
        test_cases = [
            (50, "excellent"),
            (100, "excellent"),
            (200, "good"),
            (500, "good"),
            (800, "acceptable"),
            (1000, "acceptable"),
            (1500, "slow"),
            (2000, "slow"),
            (3000, "critical")
        ]
        
        for response_time, expected_category in test_cases:
            builder = HealthResponseBuilder()
            builder.with_performance_indicators(response_time)
            response = builder.success({"test": "data"})
            
            actual_category = response["metadata"]["performance"]["response_time_category"]
            assert actual_category == expected_category
    
    def test_error_rate_categories(self):
        """Test error rate categorization."""
        test_cases = [
            (0.005, "excellent"),  # 0.5%
            (0.01, "excellent"),   # 1%
            (0.03, "good"),        # 3%
            (0.05, "good"),        # 5%
            (0.08, "acceptable"),  # 8%
            (0.10, "acceptable"),  # 10%
            (0.15, "critical")     # 15%
        ]
        
        for error_rate, expected_category in test_cases:
            builder = HealthResponseBuilder()
            builder.with_performance_indicators(100.0, error_rate=error_rate)
            response = builder.success({"test": "data"})
            
            actual_category = response["metadata"]["performance"]["error_category"]
            assert actual_category == expected_category
    
    def test_combined_health_metadata(self):
        """Test combining multiple health metadata types."""
        builder = HealthResponseBuilder()
        
        services = {"db": {"healthy": True}}
        
        response = (builder
                   .with_system_metrics(0.30, 0.50, uptime_seconds=3600)
                   .with_service_status(services)
                   .with_performance_indicators(120.0, 100.0, 0.01)
                   .success({"status": "healthy"}))
        
        metadata = response["metadata"]
        
        assert "system_metrics" in metadata
        assert "services" in metadata
        assert "service_summary" in metadata
        assert "performance" in metadata
        
        assert metadata["system_metrics"]["overall_health"] == "healthy"
        assert metadata["service_summary"]["healthy_services"] == 1
        assert metadata["performance"]["response_time_category"] == "good"