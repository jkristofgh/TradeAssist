"""
API Performance Monitoring Service - Phase 3 Integration
Enhanced monitoring integration for API standardization framework.

This service provides comprehensive performance monitoring with
integration to the monitoring configuration system.
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import statistics
from contextlib import asynccontextmanager

from ..api.common.configuration import config_manager


logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Container for performance metrics data."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count: int = 0
        self.total_requests: int = 0
        self.start_time: datetime = datetime.utcnow()
        self.cache_hits: int = 0
        self.cache_misses: int = 0
    
    def add_response_time(self, response_time_ms: float):
        """Add response time measurement."""
        self.response_times.append(response_time_ms)
        self.total_requests += 1
        
        # Keep only last 1000 measurements for memory efficiency
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-500:]
    
    def add_error(self):
        """Record an error occurrence."""
        self.error_count += 1
    
    def add_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1
    
    def add_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.response_times:
            return {
                "total_requests": self.total_requests,
                "error_count": self.error_count,
                "error_rate": 0.0,
                "cache_hit_rate": 0.0
            }
        
        sorted_times = sorted(self.response_times)
        total_cache_requests = self.cache_hits + self.cache_misses
        
        return {
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.total_requests if self.total_requests > 0 else 0.0,
            "response_times": {
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": sorted_times[int(0.95 * len(sorted_times))] if len(sorted_times) > 0 else 0,
                "p99": sorted_times[int(0.99 * len(sorted_times))] if len(sorted_times) > 0 else 0,
                "min": min(self.response_times),
                "max": max(self.response_times)
            },
            "cache_statistics": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0.0
            },
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }


class APIPerformanceMonitor:
    """
    Comprehensive API performance monitoring service.
    
    Integrates with the monitoring configuration system to provide
    real-time performance tracking and alerting capabilities.
    """
    
    def __init__(self):
        """Initialize performance monitor with configuration."""
        self.config = config_manager.monitoring
        self.endpoint_metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self.global_metrics = PerformanceMetrics()
        self.alert_timestamps: Dict[str, datetime] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_monitoring(self):
        """Start the performance monitoring background task."""
        if self._is_running:
            return
        
        self._is_running = True
        if self.config.enable_performance_tracking:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("API performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop the performance monitoring background task."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("API performance monitoring stopped")
    
    @asynccontextmanager
    async def track_request(self, endpoint: str, method: str = "GET"):
        """
        Context manager for tracking request performance.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            
        Usage:
            async with monitor.track_request("/api/analytics/market-analysis"):
                # Your endpoint logic here
                pass
        """
        if not self.config.enable_performance_tracking:
            yield {}
            return
        
        start_time = time.time()
        request_key = f"{method} {endpoint}"
        metrics = {}
        
        try:
            yield metrics
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record metrics if sampling allows
            if self._should_sample_performance():
                self.endpoint_metrics[request_key].add_response_time(response_time_ms)
                self.global_metrics.add_response_time(response_time_ms)
                
                # Record cache metrics if provided
                if metrics.get('cache_hit'):
                    self.endpoint_metrics[request_key].add_cache_hit()
                    self.global_metrics.add_cache_hit()
                elif metrics.get('cache_miss'):
                    self.endpoint_metrics[request_key].add_cache_miss()
                    self.global_metrics.add_cache_miss()
                
                # Check for slow requests
                if response_time_ms > self.config.slow_request_threshold_ms:
                    logger.warning(
                        f"Slow request detected: {request_key} took {response_time_ms:.2f}ms"
                    )
                    await self._check_performance_alerts(request_key, response_time_ms)
        
        except Exception as e:
            # Record error
            if self._should_sample_errors():
                self.endpoint_metrics[request_key].add_error()
                self.global_metrics.add_error()
            
            # Check for error rate alerts
            await self._check_error_rate_alerts(request_key)
            raise
    
    def _should_sample_performance(self) -> bool:
        """Determine if performance tracking should be sampled."""
        return (self.config.enable_performance_tracking and 
                (self.config.performance_sample_rate >= 1.0 or 
                 time.time() % (1.0 / self.config.performance_sample_rate) < 1.0))
    
    def _should_sample_errors(self) -> bool:
        """Determine if error tracking should be sampled."""
        return (self.config.enable_error_tracking and
                (self.config.error_sample_rate >= 1.0 or
                 time.time() % (1.0 / self.config.error_sample_rate) < 1.0))
    
    async def _check_performance_alerts(self, endpoint: str, response_time_ms: float):
        """Check if performance alerts should be triggered."""
        if not self.config.enable_alerting:
            return
        
        alert_key = f"performance_{endpoint}"
        now = datetime.utcnow()
        
        # Check alert cooldown
        if alert_key in self.alert_timestamps:
            time_since_last_alert = now - self.alert_timestamps[alert_key]
            if time_since_last_alert < timedelta(minutes=self.config.alert_cooldown_minutes):
                return
        
        if response_time_ms > self.config.response_time_alert_threshold_ms:
            logger.error(
                f"PERFORMANCE ALERT: {endpoint} exceeded threshold "
                f"({response_time_ms:.2f}ms > {self.config.response_time_alert_threshold_ms}ms)"
            )
            self.alert_timestamps[alert_key] = now
            
            # TODO: Integrate with external alerting system if configured
            if self.config.external_monitoring_enabled:
                await self._send_external_alert("performance", {
                    "endpoint": endpoint,
                    "response_time_ms": response_time_ms,
                    "threshold_ms": self.config.response_time_alert_threshold_ms
                })
    
    async def _check_error_rate_alerts(self, endpoint: str):
        """Check if error rate alerts should be triggered."""
        if not self.config.enable_alerting:
            return
        
        metrics = self.endpoint_metrics[endpoint]
        if metrics.total_requests < 10:  # Need minimum requests for meaningful rate
            return
        
        error_rate = metrics.error_count / metrics.total_requests
        
        if error_rate > self.config.error_rate_alert_threshold:
            alert_key = f"error_rate_{endpoint}"
            now = datetime.utcnow()
            
            # Check alert cooldown
            if alert_key in self.alert_timestamps:
                time_since_last_alert = now - self.alert_timestamps[alert_key]
                if time_since_last_alert < timedelta(minutes=self.config.alert_cooldown_minutes):
                    return
            
            logger.error(
                f"ERROR RATE ALERT: {endpoint} error rate {error_rate:.2%} "
                f"exceeds threshold {self.config.error_rate_alert_threshold:.2%}"
            )
            self.alert_timestamps[alert_key] = now
            
            # TODO: Integrate with external alerting system if configured
            if self.config.external_monitoring_enabled:
                await self._send_external_alert("error_rate", {
                    "endpoint": endpoint,
                    "error_rate": error_rate,
                    "threshold": self.config.error_rate_alert_threshold,
                    "total_requests": metrics.total_requests,
                    "error_count": metrics.error_count
                })
    
    async def _send_external_alert(self, alert_type: str, data: Dict[str, Any]):
        """Send alert to external monitoring system."""
        # Placeholder for external monitoring integration
        # This would integrate with systems like PagerDuty, Slack, etc.
        logger.info(f"External alert ({alert_type}): {data}")
    
    async def _monitoring_loop(self):
        """Background monitoring loop for periodic tasks."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.metrics_aggregation_interval_seconds)
                
                if not self._is_running:
                    break
                
                # Perform periodic maintenance
                await self._cleanup_old_metrics()
                await self._log_performance_summary()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory growth."""
        cutoff_time = datetime.utcnow() - timedelta(days=self.config.metrics_retention_days)
        
        # Reset metrics for endpoints with no recent activity
        inactive_endpoints = []
        for endpoint, metrics in self.endpoint_metrics.items():
            if (datetime.utcnow() - metrics.start_time).days > self.config.metrics_retention_days:
                inactive_endpoints.append(endpoint)
        
        for endpoint in inactive_endpoints:
            del self.endpoint_metrics[endpoint]
        
        if inactive_endpoints:
            logger.info(f"Cleaned up metrics for {len(inactive_endpoints)} inactive endpoints")
    
    async def _log_performance_summary(self):
        """Log periodic performance summary."""
        if not self.config.enable_detailed_metrics:
            return
        
        global_stats = self.global_metrics.get_statistics()
        
        logger.info(
            f"Performance Summary: {global_stats['total_requests']} requests, "
            f"{global_stats['error_rate']:.2%} error rate, "
            f"{global_stats['response_times']['mean']:.2f}ms avg response time"
        )
    
    def get_endpoint_statistics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics for specific endpoint or all endpoints.
        
        Args:
            endpoint: Specific endpoint to get stats for, or None for all
            
        Returns:
            Dict containing performance statistics
        """
        if endpoint:
            if endpoint not in self.endpoint_metrics:
                return {"error": f"No metrics found for endpoint: {endpoint}"}
            return {
                "endpoint": endpoint,
                "statistics": self.endpoint_metrics[endpoint].get_statistics()
            }
        
        # Return statistics for all endpoints
        result = {
            "global_statistics": self.global_metrics.get_statistics(),
            "endpoint_statistics": {}
        }
        
        for endpoint, metrics in self.endpoint_metrics.items():
            result["endpoint_statistics"][endpoint] = metrics.get_statistics()
        
        return result
    
    def reset_statistics(self, endpoint: Optional[str] = None):
        """
        Reset performance statistics.
        
        Args:
            endpoint: Specific endpoint to reset, or None to reset all
        """
        if endpoint:
            if endpoint in self.endpoint_metrics:
                self.endpoint_metrics[endpoint] = PerformanceMetrics()
                logger.info(f"Reset statistics for endpoint: {endpoint}")
        else:
            self.endpoint_metrics.clear()
            self.global_metrics = PerformanceMetrics()
            logger.info("Reset all performance statistics")


# Global performance monitor instance
performance_monitor = APIPerformanceMonitor()


# Convenience functions for easy integration
async def track_api_performance(endpoint: str, method: str = "GET"):
    """Convenience context manager for tracking API performance."""
    return performance_monitor.track_request(endpoint, method)


async def start_performance_monitoring():
    """Start the global performance monitoring service."""
    await performance_monitor.start_monitoring()


async def stop_performance_monitoring():
    """Stop the global performance monitoring service."""
    await performance_monitor.stop_monitoring()


def get_performance_statistics(endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Get performance statistics for monitoring dashboards."""
    return performance_monitor.get_endpoint_statistics(endpoint)