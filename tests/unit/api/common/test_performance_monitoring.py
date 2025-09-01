"""
Unit tests for API Performance Monitoring Service - Phase 3.

Tests the comprehensive performance monitoring integration with
configuration management and alerting capabilities.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.services.api_performance_monitor import (
    APIPerformanceMonitor,
    PerformanceMetrics,
    track_api_performance,
    get_performance_statistics
)


class TestPerformanceMetrics:
    """Test the PerformanceMetrics container class."""
    
    def test_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        
        assert metrics.response_times == []
        assert metrics.error_count == 0
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert isinstance(metrics.start_time, datetime)
    
    def test_add_response_time(self):
        """Test adding response times."""
        metrics = PerformanceMetrics()
        
        metrics.add_response_time(100.5)
        metrics.add_response_time(250.0)
        
        assert metrics.response_times == [100.5, 250.0]
        assert metrics.total_requests == 2
    
    def test_response_time_limit(self):
        """Test response time memory management."""
        metrics = PerformanceMetrics()
        
        # Add more than 1000 response times
        for i in range(1500):
            metrics.add_response_time(float(i))
        
        # Should keep only last 500 measurements
        assert len(metrics.response_times) == 500
        assert metrics.total_requests == 1500
    
    def test_add_error(self):
        """Test error counting."""
        metrics = PerformanceMetrics()
        
        metrics.add_error()
        metrics.add_error()
        
        assert metrics.error_count == 2
    
    def test_cache_metrics(self):
        """Test cache hit/miss tracking."""
        metrics = PerformanceMetrics()
        
        metrics.add_cache_hit()
        metrics.add_cache_hit()
        metrics.add_cache_miss()
        
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
    
    def test_get_statistics_empty(self):
        """Test statistics with no data."""
        metrics = PerformanceMetrics()
        
        stats = metrics.get_statistics()
        
        assert stats["total_requests"] == 0
        assert stats["error_count"] == 0
        assert stats["error_rate"] == 0.0
        assert stats["cache_hit_rate"] == 0.0
    
    def test_get_statistics_with_data(self):
        """Test statistics calculation with data."""
        metrics = PerformanceMetrics()
        
        # Add response times
        response_times = [100.0, 200.0, 150.0, 300.0, 250.0]
        for rt in response_times:
            metrics.add_response_time(rt)
        
        # Add errors and cache metrics
        metrics.add_error()
        metrics.add_cache_hit()
        metrics.add_cache_hit()
        metrics.add_cache_miss()
        
        stats = metrics.get_statistics()
        
        assert stats["total_requests"] == 5
        assert stats["error_count"] == 1
        assert stats["error_rate"] == 0.2  # 1/5
        
        # Check response time statistics
        assert stats["response_times"]["mean"] == 200.0
        assert stats["response_times"]["median"] == 200.0
        assert stats["response_times"]["min"] == 100.0
        assert stats["response_times"]["max"] == 300.0
        
        # Check cache statistics
        assert stats["cache_statistics"]["hits"] == 2
        assert stats["cache_statistics"]["misses"] == 1
        assert stats["cache_statistics"]["hit_rate"] == 2/3


@pytest.fixture
def mock_config():
    """Mock monitoring configuration."""
    config = MagicMock()
    config.enable_performance_tracking = True
    config.enable_error_tracking = True
    config.enable_alerting = False
    config.performance_sample_rate = 1.0
    config.error_sample_rate = 1.0
    config.slow_request_threshold_ms = 1000.0
    config.response_time_alert_threshold_ms = 5000.0
    config.error_rate_alert_threshold = 0.05
    config.alert_cooldown_minutes = 15
    config.metrics_retention_days = 30
    config.metrics_aggregation_interval_seconds = 60
    config.enable_detailed_metrics = True
    config.external_monitoring_enabled = False
    return config


class TestAPIPerformanceMonitor:
    """Test the APIPerformanceMonitor service."""
    
    @pytest.fixture
    async def monitor(self, mock_config):
        """Create a performance monitor with mocked config."""
        with patch('src.backend.services.api_performance_monitor.config_manager') as mock_manager:
            mock_manager.monitoring = mock_config
            monitor = APIPerformanceMonitor()
            yield monitor
            await monitor.stop_monitoring()
    
    def test_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.endpoint_metrics == {}
        assert monitor.global_metrics is not None
        assert monitor.alert_timestamps == {}
        assert monitor._is_running is False
    
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring."""
        assert not monitor._is_running
        
        await monitor.start_monitoring()
        assert monitor._is_running
        
        await monitor.stop_monitoring()
        assert not monitor._is_running
    
    async def test_track_request_success(self, monitor, mock_config):
        """Test tracking successful requests."""
        endpoint = "/api/test"
        
        async with monitor.track_request(endpoint) as metrics:
            # Simulate some work
            await asyncio.sleep(0.01)
            metrics["cache_hit"] = True
        
        # Check metrics were recorded
        assert endpoint in monitor.endpoint_metrics
        endpoint_stats = monitor.endpoint_metrics[endpoint].get_statistics()
        
        assert endpoint_stats["total_requests"] == 1
        assert endpoint_stats["error_count"] == 0
        assert endpoint_stats["cache_statistics"]["hits"] == 1
    
    async def test_track_request_error(self, monitor, mock_config):
        """Test tracking requests with errors."""
        endpoint = "/api/test"
        
        try:
            async with monitor.track_request(endpoint) as metrics:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Check error was recorded
        endpoint_stats = monitor.endpoint_metrics[endpoint].get_statistics()
        
        assert endpoint_stats["total_requests"] == 0  # No successful completion
        assert endpoint_stats["error_count"] == 1
    
    async def test_performance_sampling(self, monitor, mock_config):
        """Test performance sampling configuration."""
        mock_config.performance_sample_rate = 0.0  # No sampling
        
        async with monitor.track_request("/api/test"):
            pass
        
        # Should not record metrics due to sampling
        assert "/api/test" not in monitor.endpoint_metrics
    
    async def test_slow_request_detection(self, monitor, mock_config):
        """Test slow request detection and logging."""
        mock_config.slow_request_threshold_ms = 10.0  # Very low threshold
        
        with patch('src.backend.services.api_performance_monitor.logger') as mock_logger:
            async with monitor.track_request("/api/slow"):
                await asyncio.sleep(0.02)  # 20ms - above threshold
            
            # Check warning was logged
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0]
            assert "Slow request detected" in call_args[0]
    
    def test_get_endpoint_statistics(self, monitor):
        """Test getting endpoint statistics."""
        # Add some metrics
        monitor.endpoint_metrics["/api/test"].add_response_time(100.0)
        monitor.global_metrics.add_response_time(100.0)
        
        # Get all statistics
        stats = monitor.get_endpoint_statistics()
        
        assert "global_statistics" in stats
        assert "endpoint_statistics" in stats
        assert "/api/test" in stats["endpoint_statistics"]
        
        # Get specific endpoint statistics
        endpoint_stats = monitor.get_endpoint_statistics("/api/test")
        
        assert endpoint_stats["endpoint"] == "/api/test"
        assert "statistics" in endpoint_stats
    
    def test_get_nonexistent_endpoint_statistics(self, monitor):
        """Test getting statistics for non-existent endpoint."""
        stats = monitor.get_endpoint_statistics("/api/nonexistent")
        
        assert "error" in stats
        assert "No metrics found" in stats["error"]
    
    def test_reset_statistics(self, monitor):
        """Test resetting performance statistics."""
        # Add some metrics
        monitor.endpoint_metrics["/api/test"].add_response_time(100.0)
        monitor.global_metrics.add_response_time(100.0)
        
        # Reset specific endpoint
        monitor.reset_statistics("/api/test")
        
        # Check endpoint was reset but global metrics remain
        endpoint_stats = monitor.endpoint_metrics["/api/test"].get_statistics()
        assert endpoint_stats["total_requests"] == 0
        
        global_stats = monitor.global_metrics.get_statistics()
        assert global_stats["total_requests"] == 1
        
        # Reset all statistics
        monitor.reset_statistics()
        
        # Check all metrics were reset
        assert len(monitor.endpoint_metrics) == 0
        global_stats = monitor.global_metrics.get_statistics()
        assert global_stats["total_requests"] == 0
    
    async def test_alert_cooldown(self, monitor, mock_config):
        """Test alert cooldown mechanism."""
        mock_config.enable_alerting = True
        mock_config.response_time_alert_threshold_ms = 50.0
        mock_config.alert_cooldown_minutes = 1
        
        endpoint = "/api/test"
        
        with patch('src.backend.services.api_performance_monitor.logger') as mock_logger:
            # First slow request - should trigger alert
            async with monitor.track_request(endpoint):
                await asyncio.sleep(0.06)  # 60ms - above threshold
            
            # Second slow request immediately - should not trigger alert (cooldown)
            async with monitor.track_request(endpoint):
                await asyncio.sleep(0.06)  # 60ms - above threshold
            
            # Only first request should have triggered alert
            assert mock_logger.error.call_count == 1
    
    @patch('asyncio.sleep')
    async def test_monitoring_loop_cleanup(self, mock_sleep, monitor, mock_config):
        """Test monitoring loop cleanup functionality."""
        mock_config.metrics_retention_days = 1
        
        # Add old metrics
        old_endpoint = "/api/old"
        monitor.endpoint_metrics[old_endpoint].start_time = datetime.utcnow() - timedelta(days=2)
        
        # Add recent metrics  
        recent_endpoint = "/api/recent"
        monitor.endpoint_metrics[recent_endpoint].start_time = datetime.utcnow()
        
        # Start monitoring and let one cycle complete
        await monitor.start_monitoring()
        await asyncio.sleep(0.01)  # Let monitoring loop run once
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Check old metrics were cleaned up
        assert old_endpoint not in monitor.endpoint_metrics
        assert recent_endpoint in monitor.endpoint_metrics


class TestConvenienceFunctions:
    """Test convenience functions for easy integration."""
    
    async def test_track_api_performance(self):
        """Test the track_api_performance convenience function."""
        with patch('src.backend.services.api_performance_monitor.performance_monitor') as mock_monitor:
            mock_monitor.track_request.return_value.__aenter__ = AsyncMock(return_value={})
            mock_monitor.track_request.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with track_api_performance("/api/test", "GET") as metrics:
                pass
            
            mock_monitor.track_request.assert_called_once_with("/api/test", "GET")
    
    def test_get_performance_statistics(self):
        """Test the get_performance_statistics convenience function."""
        with patch('src.backend.services.api_performance_monitor.performance_monitor') as mock_monitor:
            expected_stats = {"test": "data"}
            mock_monitor.get_endpoint_statistics.return_value = expected_stats
            
            result = get_performance_statistics("/api/test")
            
            assert result == expected_stats
            mock_monitor.get_endpoint_statistics.assert_called_once_with("/api/test")


@pytest.mark.integration
class TestPerformanceMonitoringIntegration:
    """Integration tests for performance monitoring."""
    
    async def test_full_request_cycle(self):
        """Test full request tracking cycle."""
        with patch('src.backend.services.api_performance_monitor.config_manager') as mock_manager:
            # Configure mock
            config = MagicMock()
            config.enable_performance_tracking = True
            config.enable_error_tracking = True
            config.enable_alerting = False
            config.performance_sample_rate = 1.0
            config.error_sample_rate = 1.0
            config.slow_request_threshold_ms = 1000.0
            mock_manager.monitoring = config
            
            monitor = APIPerformanceMonitor()
            
            # Track multiple requests
            for i in range(5):
                async with monitor.track_request(f"/api/test{i}") as metrics:
                    await asyncio.sleep(0.001)  # 1ms
                    if i % 2 == 0:
                        metrics["cache_hit"] = True
                    else:
                        metrics["cache_miss"] = True
            
            # Track an error request
            try:
                async with monitor.track_request("/api/error"):
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Check global statistics
            stats = monitor.get_endpoint_statistics()
            global_stats = stats["global_statistics"]
            
            assert global_stats["total_requests"] == 5  # Errors don't count as completed requests
            assert global_stats["error_count"] == 1
            assert global_stats["cache_statistics"]["hits"] == 3
            assert global_stats["cache_statistics"]["misses"] == 2
            
            # Check endpoint-specific statistics
            endpoint_stats = stats["endpoint_statistics"]
            assert len(endpoint_stats) == 6  # 5 test endpoints + 1 error endpoint


if __name__ == "__main__":
    pytest.main([__file__])