"""
Standardized response builder framework for API endpoints.

This module provides consistent response formatting across all API endpoints,
with specialized builders for different domain contexts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
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