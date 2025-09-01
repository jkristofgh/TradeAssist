"""
Standardized response builder framework for API endpoints.

This module provides consistent response formatting across all API endpoints,
with specialized builders for different domain contexts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import time
from pydantic import BaseModel

from .exceptions import StandardAPIError


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""
    
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class StandardResponse(BaseModel):
    """Base standardized response model."""
    
    data: Any
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class StandardErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error_code: str
    error_category: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    correlation_id: str
    request_path: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class PaginatedResponse(BaseModel):
    """Standardized paginated response model."""
    
    data: List[Any]
    pagination: PaginationInfo
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class APIResponseBuilder:
    """
    Base response builder for consistent API responses.
    
    Provides standardized methods for building success, error, and paginated
    responses with consistent metadata and timestamp formatting.
    """
    
    def __init__(self):
        """Initialize response builder with default metadata."""
        self._metadata = {}
        self._timestamp = datetime.utcnow()
    
    def success(
        self, 
        data: Any, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create successful response with data and metadata.
        
        Args:
            data: Response data payload
            metadata: Additional response metadata
            
        Returns:
            Dict containing standardized success response
        """
        combined_metadata = {**self._metadata}
        if metadata:
            combined_metadata.update(metadata)
        
        response = StandardResponse(
            data=data,
            metadata=combined_metadata if combined_metadata else None,
            timestamp=self._timestamp
        )
        
        # Use model_dump with mode='python' and then handle datetime serialization
        result = response.model_dump()
        result["timestamp"] = self._timestamp.isoformat()
        return result
    
    def error(self, error: StandardAPIError) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            error: StandardAPIError instance
            
        Returns:
            Dict containing standardized error response
        """
        return error.detail
    
    def paginated(
        self, 
        items: List[Any], 
        pagination: PaginationInfo,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create paginated response with items and pagination info.
        
        Args:
            items: List of items for current page
            pagination: Pagination information
            metadata: Additional response metadata
            
        Returns:
            Dict containing standardized paginated response
        """
        combined_metadata = {**self._metadata}
        if metadata:
            combined_metadata.update(metadata)
        
        response = PaginatedResponse(
            data=items,
            pagination=pagination,
            metadata=combined_metadata if combined_metadata else None,
            timestamp=self._timestamp
        )
        
        # Use model_dump and then handle datetime serialization
        result = response.model_dump()
        result["timestamp"] = self._timestamp.isoformat()
        return result
    
    def with_metadata(self, **kwargs) -> 'APIResponseBuilder':
        """
        Add metadata to response builder.
        
        Args:
            **kwargs: Metadata key-value pairs
            
        Returns:
            Self for method chaining
        """
        self._metadata.update(kwargs)
        return self
    
    def with_timestamp(self, timestamp: datetime) -> 'APIResponseBuilder':
        """
        Set custom timestamp for response.
        
        Args:
            timestamp: Custom timestamp
            
        Returns:
            Self for method chaining
        """
        self._timestamp = timestamp
        return self


class AnalyticsResponseBuilder(APIResponseBuilder):
    """
    Specialized response builder for analytics endpoints.
    
    Provides analytics-specific metadata including performance metrics,
    confidence scores, and model information.
    """
    
    def with_performance_metrics(
        self, 
        calculation_time: float, 
        data_points: int
    ) -> 'AnalyticsResponseBuilder':
        """
        Add performance metrics to analytics response.
        
        Args:
            calculation_time: Time taken for calculation in seconds
            data_points: Number of data points processed
            
        Returns:
            Self for method chaining
        """
        self._metadata.update({
            "performance": {
                "calculation_time_seconds": calculation_time,
                "data_points_processed": data_points,
                "processing_efficiency": data_points / calculation_time if calculation_time > 0 else 0
            }
        })
        return self
    
    def with_confidence_score(self, confidence: float) -> 'AnalyticsResponseBuilder':
        """
        Add confidence score to analytics response.
        
        Args:
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Self for method chaining
        """
        self._metadata.update({
            "confidence": {
                "level": confidence,
                "category": self._get_confidence_category(confidence)
            }
        })
        return self
    
    def with_model_metadata(
        self, 
        model_type: str, 
        version: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> 'AnalyticsResponseBuilder':
        """
        Add model metadata to analytics response.
        
        Args:
            model_type: Type of analytical model used
            version: Model version
            parameters: Model parameters used
            
        Returns:
            Self for method chaining
        """
        model_metadata = {
            "model": {
                "type": model_type,
                "version": version
            }
        }
        
        if parameters:
            model_metadata["model"]["parameters"] = parameters
        
        self._metadata.update(model_metadata)
        return self
    
    def with_data_quality_metrics(
        self,
        completeness: float,
        freshness_minutes: int,
        anomalies_detected: int = 0
    ) -> 'AnalyticsResponseBuilder':
        """
        Add data quality metrics to analytics response.
        
        Args:
            completeness: Data completeness percentage (0.0 to 1.0)
            freshness_minutes: Age of data in minutes
            anomalies_detected: Number of anomalies detected in data
            
        Returns:
            Self for method chaining
        """
        self._metadata.update({
            "data_quality": {
                "completeness": completeness,
                "freshness_minutes": freshness_minutes,
                "anomalies_detected": anomalies_detected,
                "quality_score": self._calculate_quality_score(
                    completeness, freshness_minutes, anomalies_detected
                )
            }
        })
        return self
    
    def _get_confidence_category(self, confidence: float) -> str:
        """Get confidence category based on confidence level."""
        if confidence >= 0.95:
            return "high"
        elif confidence >= 0.80:
            return "medium"
        else:
            return "low"
    
    def _calculate_quality_score(
        self, 
        completeness: float, 
        freshness_minutes: int, 
        anomalies: int
    ) -> float:
        """Calculate overall data quality score."""
        # Base score from completeness
        score = completeness
        
        # Penalize stale data
        freshness_penalty = min(freshness_minutes / 60, 0.2)  # Max 20% penalty for old data
        score -= freshness_penalty
        
        # Penalize anomalies
        anomaly_penalty = min(anomalies * 0.05, 0.3)  # Max 30% penalty for anomalies
        score -= anomaly_penalty
        
        return max(0.0, min(1.0, score))


class InstrumentResponseBuilder(APIResponseBuilder):
    """
    Specialized response builder for instrument endpoints.
    
    Provides instrument-specific metadata including market status
    and trading information.
    """
    
    def with_market_status(
        self, 
        status: str,
        session_state: Optional[str] = None,
        next_session_start: Optional[datetime] = None
    ) -> 'InstrumentResponseBuilder':
        """
        Add market status to instrument response.
        
        Args:
            status: Market status (e.g., "OPEN", "CLOSED", "PRE_MARKET")
            session_state: Current trading session state
            next_session_start: When next trading session starts
            
        Returns:
            Self for method chaining
        """
        market_metadata = {
            "market_status": {
                "status": status,
                "is_trading_active": status in ["OPEN", "PRE_MARKET", "AFTER_MARKET"]
            }
        }
        
        if session_state:
            market_metadata["market_status"]["session_state"] = session_state
        
        if next_session_start:
            market_metadata["market_status"]["next_session_start"] = next_session_start.isoformat()
        
        self._metadata.update(market_metadata)
        return self
    
    def with_last_trade_info(
        self, 
        timestamp: datetime, 
        price: float,
        volume: Optional[int] = None,
        bid_ask_spread: Optional[float] = None
    ) -> 'InstrumentResponseBuilder':
        """
        Add last trade information to instrument response.
        
        Args:
            timestamp: Last trade timestamp
            price: Last trade price
            volume: Last trade volume
            bid_ask_spread: Current bid-ask spread
            
        Returns:
            Self for method chaining
        """
        trade_info = {
            "last_trade": {
                "timestamp": timestamp.isoformat(),
                "price": price,
                "age_minutes": (datetime.utcnow() - timestamp).total_seconds() / 60
            }
        }
        
        if volume is not None:
            trade_info["last_trade"]["volume"] = volume
        
        if bid_ask_spread is not None:
            trade_info["last_trade"]["bid_ask_spread"] = bid_ask_spread
        
        self._metadata.update(trade_info)
        return self
    
    def with_volatility_info(
        self,
        current_volatility: float,
        volatility_percentile: float,
        volatility_category: Optional[str] = None
    ) -> 'InstrumentResponseBuilder':
        """
        Add volatility information to instrument response.
        
        Args:
            current_volatility: Current volatility measure
            volatility_percentile: Volatility percentile (0.0 to 1.0)
            volatility_category: Volatility category (e.g., "low", "normal", "high")
            
        Returns:
            Self for method chaining
        """
        volatility_info = {
            "volatility": {
                "current": current_volatility,
                "percentile": volatility_percentile,
                "category": volatility_category or self._get_volatility_category(volatility_percentile)
            }
        }
        
        self._metadata.update(volatility_info)
        return self
    
    def _get_volatility_category(self, percentile: float) -> str:
        """Get volatility category based on percentile."""
        if percentile >= 0.8:
            return "high"
        elif percentile >= 0.6:
            return "elevated"
        elif percentile >= 0.4:
            return "normal"
        elif percentile >= 0.2:
            return "low"
        else:
            return "very_low"


class HealthResponseBuilder(APIResponseBuilder):
    """
    Specialized response builder for health monitoring endpoints.
    
    Provides health-specific metadata including system metrics,
    service status, and performance indicators.
    """
    
    def with_system_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: Optional[float] = None,
        uptime_seconds: Optional[int] = None
    ) -> 'HealthResponseBuilder':
        """
        Add system metrics to health response.
        
        Args:
            cpu_usage: CPU usage percentage (0.0 to 1.0)
            memory_usage: Memory usage percentage (0.0 to 1.0)
            disk_usage: Disk usage percentage (0.0 to 1.0)
            uptime_seconds: System uptime in seconds
            
        Returns:
            Self for method chaining
        """
        system_metrics = {
            "system_metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "overall_health": self._calculate_system_health(cpu_usage, memory_usage, disk_usage)
            }
        }
        
        if disk_usage is not None:
            system_metrics["system_metrics"]["disk_usage"] = disk_usage
        
        if uptime_seconds is not None:
            system_metrics["system_metrics"]["uptime_seconds"] = uptime_seconds
            system_metrics["system_metrics"]["uptime_hours"] = uptime_seconds / 3600
        
        self._metadata.update(system_metrics)
        return self
    
    def with_service_status(
        self,
        services: Dict[str, Dict[str, Any]]
    ) -> 'HealthResponseBuilder':
        """
        Add service status information to health response.
        
        Args:
            services: Dictionary of service names to status information
            
        Returns:
            Self for method chaining
        """
        healthy_services = sum(1 for s in services.values() if s.get("healthy", False))
        total_services = len(services)
        
        service_metadata = {
            "services": services,
            "service_summary": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "degraded_services": total_services - healthy_services,
                "overall_service_health": healthy_services / total_services if total_services > 0 else 1.0
            }
        }
        
        self._metadata.update(service_metadata)
        return self
    
    def with_performance_indicators(
        self,
        response_time_ms: float,
        throughput_rps: Optional[float] = None,
        error_rate: Optional[float] = None
    ) -> 'HealthResponseBuilder':
        """
        Add performance indicators to health response.
        
        Args:
            response_time_ms: Average response time in milliseconds
            throughput_rps: Requests per second
            error_rate: Error rate percentage (0.0 to 1.0)
            
        Returns:
            Self for method chaining
        """
        performance_info = {
            "performance": {
                "response_time_ms": response_time_ms,
                "response_time_category": self._get_response_time_category(response_time_ms)
            }
        }
        
        if throughput_rps is not None:
            performance_info["performance"]["throughput_rps"] = throughput_rps
        
        if error_rate is not None:
            performance_info["performance"]["error_rate"] = error_rate
            performance_info["performance"]["error_category"] = self._get_error_rate_category(error_rate)
        
        self._metadata.update(performance_info)
        return self
    
    def _calculate_system_health(
        self, 
        cpu_usage: float, 
        memory_usage: float, 
        disk_usage: Optional[float] = None
    ) -> str:
        """Calculate overall system health based on resource usage."""
        high_usage_threshold = 0.8
        critical_usage_threshold = 0.95
        
        max_usage = max(cpu_usage, memory_usage)
        if disk_usage is not None:
            max_usage = max(max_usage, disk_usage)
        
        if max_usage >= critical_usage_threshold:
            return "critical"
        elif max_usage >= high_usage_threshold:
            return "degraded"
        else:
            return "healthy"
    
    def _get_response_time_category(self, response_time_ms: float) -> str:
        """Get response time category based on milliseconds."""
        if response_time_ms <= 100:
            return "excellent"
        elif response_time_ms <= 500:
            return "good"
        elif response_time_ms <= 1000:
            return "acceptable"
        elif response_time_ms <= 2000:
            return "slow"
        else:
            return "critical"
    
    def _get_error_rate_category(self, error_rate: float) -> str:
        """Get error rate category based on percentage."""
        if error_rate <= 0.01:  # 1%
            return "excellent"
        elif error_rate <= 0.05:  # 5%
            return "good"
        elif error_rate <= 0.10:  # 10%
            return "acceptable"
        else:
            return "critical"


# =============================================================================
# PERFORMANCE OPTIMIZED RESPONSE BUILDERS - PHASE 3
# Enhanced for <10ms standardization overhead requirement
# =============================================================================

class OptimizedAPIResponseBuilder(APIResponseBuilder):
    """
    Performance-optimized base response builder.
    
    Implements caching and pre-computation strategies to minimize
    response building overhead and meet <10ms standardization target.
    """
    
    def __init__(self):
        """Initialize optimized response builder with caching."""
        super().__init__()
        self._cached_base_metadata = {}
        self._cached_error_responses = {}
        self._iso_timestamp_cache = None
        self._iso_timestamp_cache_time = None
    
    def _get_cached_timestamp(self) -> str:
        """Get cached ISO timestamp to avoid repeated formatting."""
        current_time = time.time()
        # Cache timestamp for up to 1 second to reduce datetime.isoformat() calls
        if (self._iso_timestamp_cache_time is None or 
            current_time - self._iso_timestamp_cache_time > 1.0):
            self._iso_timestamp_cache = self._timestamp.isoformat()
            self._iso_timestamp_cache_time = current_time
        return self._iso_timestamp_cache
    
    def success(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimized successful response creation.
        
        Performance improvements:
        - Pre-computed base structure
        - Cached timestamp formatting
        - Minimal dictionary operations
        """
        # Use pre-computed base structure when possible
        if not metadata and not self._metadata:
            return {
                "success": True,
                "data": data,
                "timestamp": self._get_cached_timestamp()
            }
        
        # Build metadata efficiently
        combined_metadata = self._metadata.copy() if self._metadata else {}
        if metadata:
            combined_metadata.update(metadata)
        
        return {
            "success": True,
            "data": data,
            "metadata": combined_metadata if combined_metadata else None,
            "timestamp": self._get_cached_timestamp()
        }
    
    def error(self, error: 'StandardAPIError') -> Dict[str, Any]:
        """
        Optimized error response creation with caching.
        
        Caches common error response structures to avoid repeated
        model creation and serialization overhead.
        """
        # Create cache key based on error type and code
        cache_key = f"{type(error).__name__}:{getattr(error, 'error_code', 'unknown')}"
        
        if cache_key in self._cached_error_responses:
            # Use cached structure but update timestamp and details
            cached_response = self._cached_error_responses[cache_key].copy()
            cached_response["timestamp"] = self._get_cached_timestamp()
            if hasattr(error, 'details') and error.details:
                cached_response["error"]["details"] = error.details
            return cached_response
        
        # Create new error response and cache the structure
        error_response = {
            "success": False,
            "error": {
                "error_code": getattr(error, 'error_code', 'UNKNOWN_ERROR'),
                "error_category": getattr(error, 'error_category', 'system'),
                "message": str(error),
                "details": getattr(error, 'details', None),
                "request_path": getattr(error, 'request_path', None),
                "correlation_id": getattr(error, 'correlation_id', None)
            },
            "timestamp": self._get_cached_timestamp()
        }
        
        # Cache the structure (without timestamp and details for reuse)
        cache_structure = {
            "success": False,
            "error": {
                "error_code": getattr(error, 'error_code', 'UNKNOWN_ERROR'),
                "error_category": getattr(error, 'error_category', 'system'),
                "message": str(error),
                "details": None,  # Will be updated per request
                "request_path": getattr(error, 'request_path', None),
                "correlation_id": getattr(error, 'correlation_id', None)
            },
            "timestamp": None  # Will be updated per request
        }
        
        # Only cache if we have space (limit to 100 cached error types)
        if len(self._cached_error_responses) < 100:
            self._cached_error_responses[cache_key] = cache_structure
        
        return error_response
    
    def paginated(
        self, 
        items: List[Any], 
        pagination: 'PaginationInfo',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimized paginated response creation.
        
        Performance improvements:
        - Pre-computed pagination metadata structure
        - Efficient dictionary construction
        """
        # Pre-compute pagination metadata
        pagination_metadata = {
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
        
        # Combine metadata efficiently
        if metadata:
            pagination_metadata.update(metadata)
        if self._metadata:
            pagination_metadata.update(self._metadata)
        
        return {
            "success": True,
            "data": items,
            "metadata": pagination_metadata,
            "timestamp": self._get_cached_timestamp()
        }


class OptimizedAnalyticsResponseBuilder(OptimizedAPIResponseBuilder):
    """
    Performance-optimized analytics response builder.
    
    Specialized for analytics endpoints with pre-computed common
    metadata structures and efficient numeric data handling.
    """
    
    def __init__(self):
        """Initialize with analytics-specific optimizations."""
        super().__init__()
        self._analytics_metadata_template = {
            "processing_time_ms": 0.0,
            "data_points": 0,
            "confidence_score": None,
            "model_type": None,
            "model_version": None,
            "cache_hit": False
        }
    
    def with_performance_metrics(
        self, 
        calculation_time: float, 
        data_points: int, 
        cache_hit: bool = False
    ) -> 'OptimizedAnalyticsResponseBuilder':
        """
        Add performance metrics with pre-computed template.
        
        Performance optimization: Uses template copying instead of
        repeated dictionary construction.
        """
        perf_metadata = self._analytics_metadata_template.copy()
        perf_metadata.update({
            "processing_time_ms": round(calculation_time * 1000, 2),
            "data_points": data_points,
            "cache_hit": cache_hit
        })
        
        self._metadata.update(perf_metadata)
        return self
    
    def with_confidence_score(self, confidence: float) -> 'OptimizedAnalyticsResponseBuilder':
        """Add confidence score with validation."""
        if "confidence_score" not in self._metadata:
            self._metadata.update(self._analytics_metadata_template)
        self._metadata["confidence_score"] = round(confidence, 4)
        return self
    
    def with_model_metadata(
        self, 
        model_type: str, 
        version: str
    ) -> 'OptimizedAnalyticsResponseBuilder':
        """Add model metadata efficiently."""
        if "model_type" not in self._metadata:
            self._metadata.update(self._analytics_metadata_template)
        self._metadata.update({
            "model_type": model_type,
            "model_version": version
        })
        return self


class OptimizedInstrumentResponseBuilder(OptimizedAPIResponseBuilder):
    """
    Performance-optimized instrument response builder.
    
    Optimized for instrument data with cached market status
    and efficient timestamp handling.
    """
    
    def __init__(self):
        """Initialize with instrument-specific caching."""
        super().__init__()
        self._market_status_cache = {}
        self._market_status_cache_time = {}
    
    def with_market_status(self, status: str) -> 'OptimizedInstrumentResponseBuilder':
        """
        Add market status with caching.
        
        Caches market status for up to 30 seconds to avoid
        repeated market status lookups.
        """
        current_time = time.time()
        cache_key = f"market_status_{status}"
        
        # Use cached status if recent
        if (cache_key in self._market_status_cache_time and
            current_time - self._market_status_cache_time[cache_key] < 30):
            self._metadata["market_status"] = self._market_status_cache[cache_key]
        else:
            # Update cache
            self._market_status_cache[cache_key] = status
            self._market_status_cache_time[cache_key] = current_time
            self._metadata["market_status"] = status
        
        return self
    
    def with_last_trade_info(
        self, 
        timestamp: datetime, 
        price: float
    ) -> 'OptimizedInstrumentResponseBuilder':
        """Add last trade info efficiently."""
        self._metadata.update({
            "last_trade": {
                "timestamp": timestamp.isoformat(),
                "price": round(price, 4)
            }
        })
        return self


class OptimizedHealthResponseBuilder(OptimizedAPIResponseBuilder):
    """
    Performance-optimized health response builder.
    
    Optimized for health check endpoints with minimal overhead
    and efficient status aggregation.
    """
    
    def __init__(self):
        """Initialize with health-specific optimizations."""
        super().__init__()
        self._health_status_template = {
            "uptime_seconds": 0,
            "memory_usage_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "active_connections": 0,
            "database_status": "unknown"
        }
    
    def with_operational_metadata(
        self, 
        uptime_seconds: int,
        memory_usage_mb: float,
        cpu_usage_percent: float,
        active_connections: int
    ) -> 'OptimizedHealthResponseBuilder':
        """
        Add operational metadata with template-based construction.
        
        Uses pre-allocated template for consistent performance.
        """
        operational_metadata = self._health_status_template.copy()
        operational_metadata.update({
            "uptime_seconds": uptime_seconds,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "cpu_usage_percent": round(cpu_usage_percent, 2),
            "active_connections": active_connections
        })
        
        self._metadata.update(operational_metadata)
        return self
    
    def with_database_status(self, status: str) -> 'OptimizedHealthResponseBuilder':
        """Add database status efficiently."""
        self._metadata["database_status"] = status
        return self


# Factory function for creating optimized response builders
def create_optimized_response_builder(builder_type: str) -> OptimizedAPIResponseBuilder:
    """
    Factory function for creating performance-optimized response builders.
    
    Args:
        builder_type: Type of builder ('analytics', 'instrument', 'health', 'base')
        
    Returns:
        Optimized response builder instance
        
    Performance: Uses pre-instantiated builders where possible.
    """
    builders = {
        'analytics': OptimizedAnalyticsResponseBuilder,
        'instrument': OptimizedInstrumentResponseBuilder,
        'health': OptimizedHealthResponseBuilder,
        'base': OptimizedAPIResponseBuilder
    }
    
    builder_class = builders.get(builder_type, OptimizedAPIResponseBuilder)
    return builder_class()
