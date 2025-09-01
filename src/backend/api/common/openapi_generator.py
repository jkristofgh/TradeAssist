"""
OpenAPI Documentation Generator - Phase 3 Integration.

This module provides enhanced OpenAPI documentation generation with
automatic schema extraction from standardized response models and
error formats.
"""

from typing import Dict, Any, List, Optional, Type
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from .exceptions import StandardAPIError, ValidationError, AuthenticationError, BusinessLogicError, SystemError
from .responses import (
    StandardResponse, 
    StandardErrorResponse, 
    PaginatedResponse,
    APIResponseBuilder,
    AnalyticsResponseBuilder,
    InstrumentResponseBuilder,
    HealthResponseBuilder
)
from .configuration import config_manager


class OpenAPIEnhancer:
    """
    Enhanced OpenAPI documentation generator.
    
    Automatically generates comprehensive API documentation with
    standardized error schemas, response formats, and configuration
    examples.
    """
    
    def __init__(self, app: FastAPI):
        """
        Initialize OpenAPI enhancer.
        
        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.custom_schemas = {}
        self._setup_standard_schemas()
    
    def _setup_standard_schemas(self):
        """Set up standardized schemas for documentation."""
        
        # Standard response schemas
        self.custom_schemas.update({
            "StandardSuccessResponse": {
                "title": "Standard Success Response",
                "description": "Standardized successful API response format",
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True,
                        "description": "Indicates request was processed successfully"
                    },
                    "data": {
                        "description": "Response payload data",
                        "example": {"message": "Operation completed successfully"}
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Response metadata including performance metrics",
                        "properties": {
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "example": "2025-09-01T10:30:00Z"
                            },
                            "correlation_id": {
                                "type": "string",
                                "example": "req_123456789"
                            },
                            "processing_time_ms": {
                                "type": "number",
                                "example": 45.2
                            },
                            "data_points": {
                                "type": "integer",
                                "example": 100
                            },
                            "cache_hit": {
                                "type": "boolean",
                                "example": True
                            }
                        }
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2025-09-01T10:30:00Z"
                    }
                },
                "required": ["success", "data", "timestamp"]
            },
            
            "StandardErrorResponse": {
                "title": "Standard Error Response",
                "description": "Standardized error response format with categorization",
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False,
                        "description": "Always false for error responses"
                    },
                    "error": {
                        "type": "object",
                        "properties": {
                            "error_code": {
                                "type": "string",
                                "example": "VALIDATION_001",
                                "description": "Structured error code for programmatic handling"
                            },
                            "error_category": {
                                "type": "string",
                                "enum": ["validation", "authentication", "business", "system"],
                                "example": "validation",
                                "description": "Error category for classification"
                            },
                            "message": {
                                "type": "string",
                                "example": "Invalid parameter value provided",
                                "description": "Human-readable error message"
                            },
                            "details": {
                                "type": "object",
                                "example": {"field": "instrument_id", "value": "999"},
                                "description": "Additional error context and details"
                            },
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "example": "2025-09-01T10:30:00Z"
                            },
                            "correlation_id": {
                                "type": "string",
                                "example": "req_123456789",
                                "description": "Request correlation ID for debugging"
                            },
                            "request_path": {
                                "type": "string",
                                "example": "/api/analytics/market-analysis",
                                "description": "API endpoint that generated the error"
                            }
                        },
                        "required": ["error_code", "error_category", "message", "timestamp"]
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2025-09-01T10:30:00Z"
                    }
                },
                "required": ["success", "error", "timestamp"]
            },
            
            "PaginatedResponse": {
                "title": "Paginated Response",
                "description": "Standardized paginated response format",
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "data": {
                        "type": "array",
                        "description": "Array of paginated items"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "pagination": {
                                "type": "object",
                                "properties": {
                                    "page": {"type": "integer", "example": 1},
                                    "per_page": {"type": "integer", "example": 25},
                                    "total": {"type": "integer", "example": 150},
                                    "pages": {"type": "integer", "example": 6},
                                    "has_next": {"type": "boolean", "example": True},
                                    "has_prev": {"type": "boolean", "example": False}
                                }
                            }
                        }
                    }
                },
                "required": ["success", "data", "metadata"]
            }
        })
        
        # Add error category schemas
        self._add_error_category_schemas()
        
        # Add configuration schemas  
        self._add_configuration_schemas()
        
        # Add performance monitoring schemas
        self._add_performance_monitoring_schemas()
    
    def _add_error_category_schemas(self):
        """Add error category specific schemas."""
        
        error_categories = {
            "ValidationError": {
                "title": "Validation Error",
                "description": "Parameter validation failure",
                "allOf": [
                    {"$ref": "#/components/schemas/StandardErrorResponse"}
                ],
                "example": {
                    "success": False,
                    "error": {
                        "error_code": "VALIDATION_001",
                        "error_category": "validation",
                        "message": "Instrument not found",
                        "details": {"instrument_id": 999},
                        "timestamp": "2025-09-01T10:30:00Z",
                        "correlation_id": "req_123456789",
                        "request_path": "/api/analytics/market-analysis"
                    },
                    "timestamp": "2025-09-01T10:30:00Z"
                }
            },
            
            "AuthenticationError": {
                "title": "Authentication Error", 
                "description": "Authentication or authorization failure",
                "allOf": [
                    {"$ref": "#/components/schemas/StandardErrorResponse"}
                ],
                "example": {
                    "success": False,
                    "error": {
                        "error_code": "AUTH_001",
                        "error_category": "authentication",
                        "message": "Invalid or expired authentication token",
                        "details": {"token_type": "bearer"},
                        "timestamp": "2025-09-01T10:30:00Z",
                        "correlation_id": "req_123456789"
                    },
                    "timestamp": "2025-09-01T10:30:00Z"
                }
            },
            
            "BusinessLogicError": {
                "title": "Business Logic Error",
                "description": "Business rule validation failure", 
                "allOf": [
                    {"$ref": "#/components/schemas/StandardErrorResponse"}
                ],
                "example": {
                    "success": False,
                    "error": {
                        "error_code": "BUSINESS_001",
                        "error_category": "business",
                        "message": "Alert rule limit exceeded",
                        "details": {"current_count": 100, "max_allowed": 50},
                        "timestamp": "2025-09-01T10:30:00Z",
                        "correlation_id": "req_123456789"
                    },
                    "timestamp": "2025-09-01T10:30:00Z"
                }
            },
            
            "SystemError": {
                "title": "System Error",
                "description": "System or infrastructure failure",
                "allOf": [
                    {"$ref": "#/components/schemas/StandardErrorResponse"}
                ],
                "example": {
                    "success": False,
                    "error": {
                        "error_code": "SYSTEM_001",
                        "error_category": "system",
                        "message": "Database connection timeout",
                        "details": {"component": "database", "timeout_ms": 15000},
                        "timestamp": "2025-09-01T10:30:00Z",
                        "correlation_id": "req_123456789"
                    },
                    "timestamp": "2025-09-01T10:30:00Z"
                }
            }
        }
        
        self.custom_schemas.update(error_categories)
    
    def _add_configuration_schemas(self):
        """Add configuration management schemas."""
        
        config_schemas = {
            "ConfigurationValidationResponse": {
                "title": "Configuration Validation Response",
                "description": "Response from configuration validation endpoint",
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "validation_summary": {
                        "type": "object",
                        "properties": {
                            "total_sections": {"type": "integer", "example": 5},
                            "valid_sections": {"type": "integer", "example": 5},
                            "invalid_sections": {"type": "integer", "example": 0},
                            "warnings": {"type": "integer", "example": 0}
                        }
                    },
                    "section_details": {
                        "type": "object",
                        "description": "Validation details for each configuration section"
                    },
                    "cross_section_validation": {
                        "type": "object",
                        "properties": {
                            "valid": {"type": "boolean", "example": True},
                            "errors": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            },
            
            "ConfigurationResponse": {
                "title": "Current Configuration Response",
                "description": "Response containing current configuration settings",
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "configuration": {
                        "type": "object",
                        "description": "Configuration sections and their current values"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "sections_included": {"type": "integer", "example": 5},
                            "sensitive_data_included": {"type": "boolean", "example": False}
                        }
                    }
                }
            }
        }
        
        self.custom_schemas.update(config_schemas)
    
    def _add_performance_monitoring_schemas(self):
        """Add performance monitoring schemas."""
        
        perf_schemas = {
            "PerformanceStatisticsResponse": {
                "title": "Performance Statistics Response",
                "description": "Response containing API performance statistics",
                "type": "object", 
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "performance_data": {
                        "type": "object",
                        "properties": {
                            "global_statistics": {
                                "type": "object",
                                "properties": {
                                    "total_requests": {"type": "integer", "example": 1500},
                                    "error_count": {"type": "integer", "example": 12},
                                    "error_rate": {"type": "number", "example": 0.008},
                                    "response_times": {
                                        "type": "object",
                                        "properties": {
                                            "mean": {"type": "number", "example": 85.5},
                                            "median": {"type": "number", "example": 75.0},
                                            "p95": {"type": "number", "example": 150.0},
                                            "p99": {"type": "number", "example": 280.0},
                                            "min": {"type": "number", "example": 15.0},
                                            "max": {"type": "number", "example": 450.0}
                                        }
                                    },
                                    "cache_statistics": {
                                        "type": "object", 
                                        "properties": {
                                            "hits": {"type": "integer", "example": 850},
                                            "misses": {"type": "integer", "example": 150},
                                            "hit_rate": {"type": "number", "example": 0.85}
                                        }
                                    }
                                }
                            },
                            "endpoint_statistics": {
                                "type": "object",
                                "description": "Per-endpoint performance statistics"
                            }
                        }
                    },
                    "monitoring_config": {
                        "type": "object",
                        "description": "Current monitoring configuration settings"
                    }
                }
            },
            
            "PerformanceAlertsResponse": {
                "title": "Performance Alerts Response", 
                "description": "Response containing performance alert status",
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "alerting_status": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean", "example": True},
                            "error_rate_threshold": {"type": "number", "example": 0.05},
                            "response_time_threshold_ms": {"type": "number", "example": 5000.0},
                            "cooldown_minutes": {"type": "integer", "example": 15}
                        }
                    },
                    "recent_alerts": {
                        "type": "object",
                        "description": "Recent performance alerts (last 24 hours)"
                    },
                    "monitoring_health": {
                        "type": "object",
                        "properties": {
                            "performance_tracking": {"type": "boolean", "example": True},
                            "error_tracking": {"type": "boolean", "example": True},
                            "resource_monitoring": {"type": "boolean", "example": True}
                        }
                    }
                }
            }
        }
        
        self.custom_schemas.update(perf_schemas)
    
    def generate_enhanced_openapi(self) -> Dict[str, Any]:
        """
        Generate enhanced OpenAPI documentation.
        
        Returns:
            Enhanced OpenAPI specification dictionary
        """
        # Get base OpenAPI spec from FastAPI
        openapi_spec = get_openapi(
            title="TradeAssist API - Enhanced with Standardization",
            version="1.0.0",
            description=self._get_enhanced_description(),
            routes=self.app.routes,
        )
        
        # Add custom schemas
        if "components" not in openapi_spec:
            openapi_spec["components"] = {}
        
        if "schemas" not in openapi_spec["components"]:
            openapi_spec["components"]["schemas"] = {}
        
        openapi_spec["components"]["schemas"].update(self.custom_schemas)
        
        # Add standardized headers
        self._add_standardized_headers(openapi_spec)
        
        # Add configuration examples
        self._add_configuration_examples(openapi_spec)
        
        # Add error code documentation
        self._add_error_code_documentation(openapi_spec)
        
        # Add performance optimization notes
        self._add_performance_documentation(openapi_spec)
        
        return openapi_spec
    
    def _get_enhanced_description(self) -> str:
        """Get enhanced API description."""
        return """
## TradeAssist API - Phase 3 Enhanced Documentation

A comprehensive real-time trading alerts and market data streaming API with 
**standardized error handling**, **consistent response formats**, and 
**advanced performance monitoring**.

### Key Features

- **Standardized Response Formats**: All endpoints use consistent success/error response structures
- **Comprehensive Error Handling**: Categorized errors with structured error codes and correlation IDs  
- **Performance Monitoring**: Real-time performance metrics and alerting
- **Configuration Management**: Runtime configuration validation and management
- **Backward Compatibility**: Maintains compatibility with existing API consumers

### Response Format Standards

All API endpoints follow standardized response formats:

- **Success Responses**: Include `success: true`, `data`, optional `metadata`, and `timestamp`
- **Error Responses**: Include `success: false`, structured `error` object with categorization, and `timestamp`
- **Paginated Responses**: Include standard pagination metadata with `page`, `per_page`, `total`, etc.

### Error Categories

Errors are categorized for better handling:

- **validation**: Parameter validation failures
- **authentication**: Authentication and authorization errors  
- **business**: Business rule violations
- **system**: Infrastructure and system errors

### Performance Features

- **Response Time Tracking**: <10ms standardization overhead target
- **Cache Hit Rate Monitoring**: Cache performance metrics
- **Error Rate Alerting**: Configurable error rate thresholds
- **Resource Usage Monitoring**: CPU and memory usage tracking

### Configuration Management

Runtime configuration management with:

- **Validation API**: Validate configuration consistency
- **Live Reload**: Update configuration without restart
- **Environment Override**: Environment variable configuration
- **Audit Logging**: Configuration change tracking
        """.strip()
    
    def _add_standardized_headers(self, openapi_spec: Dict[str, Any]):
        """Add documentation for standardized headers."""
        
        # Add common response headers
        if "components" not in openapi_spec:
            openapi_spec["components"] = {}
        
        if "headers" not in openapi_spec["components"]:
            openapi_spec["components"]["headers"] = {}
        
        standardized_headers = {
            "X-Correlation-ID": {
                "description": "Unique request correlation ID for debugging and tracing",
                "schema": {"type": "string", "example": "req_123456789"}
            },
            "X-Response-Time": {
                "description": "Response processing time in seconds",
                "schema": {"type": "string", "example": "0.045s"}
            },
            "X-Response-Time-MS": {
                "description": "Response processing time in milliseconds",
                "schema": {"type": "string", "example": "45"}
            },
            "X-API-Version": {
                "description": "API version identifier",
                "schema": {"type": "string", "example": "1.0"}
            },
            "X-Request-Path": {
                "description": "Original request path for debugging",
                "schema": {"type": "string", "example": "/api/analytics/market-analysis"}
            }
        }
        
        openapi_spec["components"]["headers"].update(standardized_headers)
    
    def _add_configuration_examples(self, openapi_spec: Dict[str, Any]):
        """Add configuration examples to the documentation."""
        
        # Add examples section
        if "info" not in openapi_spec:
            openapi_spec["info"] = {}
        
        config_examples = {
            "x-configuration-examples": {
                "monitoring": {
                    "enable_performance_tracking": True,
                    "enable_error_tracking": True,
                    "slow_request_threshold_ms": 2000.0,
                    "error_rate_alert_threshold": 0.05
                },
                "api_limits": {
                    "max_page_size": 100,
                    "max_requests_per_minute": 100,
                    "request_timeout_seconds": 30.0
                },
                "validation": {
                    "max_lookback_hours": 8760,
                    "allowed_confidence_levels": [0.90, 0.95, 0.99, 0.999]
                }
            }
        }
        
        openapi_spec["info"].update(config_examples)
    
    def _add_error_code_documentation(self, openapi_spec: Dict[str, Any]):
        """Add error code documentation."""
        
        error_codes = {
            "x-error-codes": {
                "VALIDATION_001": "Instrument not found",
                "VALIDATION_002": "Invalid lookback hours parameter",
                "VALIDATION_003": "Invalid confidence level", 
                "VALIDATION_004": "Invalid date range",
                "VALIDATION_005": "Invalid pagination parameters",
                "AUTH_001": "Authentication token missing",
                "AUTH_002": "Invalid authentication token", 
                "AUTH_003": "Authentication token expired",
                "AUTH_004": "Insufficient permissions",
                "BUSINESS_001": "Alert rule limit exceeded",
                "BUSINESS_002": "Duplicate alert rule",
                "BUSINESS_003": "Invalid instrument configuration",
                "SYSTEM_001": "Database connection timeout",
                "SYSTEM_002": "External API unavailable",
                "SYSTEM_003": "Internal server error",
                "SYSTEM_004": "Service temporarily unavailable"
            }
        }
        
        if "info" not in openapi_spec:
            openapi_spec["info"] = {}
        
        openapi_spec["info"].update(error_codes)
    
    def _add_performance_documentation(self, openapi_spec: Dict[str, Any]):
        """Add performance optimization documentation."""
        
        performance_info = {
            "x-performance-targets": {
                "standardization_overhead": "<10ms per request",
                "response_time_p95": "<500ms for analytics endpoints",
                "response_time_p99": "<1000ms for analytics endpoints",
                "error_rate": "<1% under normal load",
                "cache_hit_rate": ">80% for historical data",
                "concurrent_requests": "100+ requests/second"
            },
            "x-optimization-features": [
                "Optimized response builders with caching",
                "Efficient timestamp formatting",
                "Pre-computed metadata templates", 
                "Response compression for large payloads",
                "Database query optimization",
                "Intelligent cache warming"
            ]
        }
        
        if "info" not in openapi_spec:
            openapi_spec["info"] = {}
        
        openapi_spec["info"].update(performance_info)


def setup_enhanced_openapi(app: FastAPI) -> None:
    """
    Set up enhanced OpenAPI documentation for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    enhancer = OpenAPIEnhancer(app)
    
    # Override the default OpenAPI function
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = enhancer.generate_enhanced_openapi()
        app.openapi_schema = openapi_schema
        return openapi_schema
    
    app.openapi = custom_openapi


# Convenience function for easy integration
def generate_api_documentation(app: FastAPI) -> Dict[str, Any]:
    """
    Generate comprehensive API documentation.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Enhanced OpenAPI specification
    """
    enhancer = OpenAPIEnhancer(app)
    return enhancer.generate_enhanced_openapi()