"""
API standardization middleware for consistent request/response handling.

This module provides middleware components for correlation ID tracking,
request timing, error standardization, and response formatting across
all API endpoints.
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
import structlog

from .exceptions import StandardAPIError, SystemError, CommonErrors
from .responses import APIResponseBuilder


# Configure structured logger
logger = structlog.get_logger(__name__)


class APIStandardizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for consistent request/response handling across all API endpoints.
    
    Provides correlation ID generation, request timing, standardized error responses,
    and consistent header injection for debugging and monitoring.
    """
    
    def __init__(self, app, enable_timing: bool = True, enable_cors_headers: bool = True):
        """
        Initialize API standardization middleware.
        
        Args:
            app: FastAPI application instance
            enable_timing: Whether to add response time headers
            enable_cors_headers: Whether to add CORS headers
        """
        super().__init__(app)
        self.enable_timing = enable_timing
        self.enable_cors_headers = enable_cors_headers
        self.response_builder = APIResponseBuilder()
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request and response with standardization logic.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Processed HTTP response with standardized headers and formatting
        """
        # Generate or extract correlation ID
        correlation_id = self._get_or_create_correlation_id(request)
        
        # Start request timing
        start_time = time.time() if self.enable_timing else None
        
        # Add correlation ID to request state for use in endpoints
        request.state.correlation_id = correlation_id
        request.state.request_start_time = start_time
        
        # Log request start
        await self._log_request_start(request, correlation_id)
        
        try:
            # Process request through application
            response = await call_next(request)
            
            # Add standardized headers to response
            response = await self._add_response_headers(
                response, correlation_id, start_time, request
            )
            
            # Log successful response
            await self._log_response_success(request, response, correlation_id, start_time)
            
            return response
            
        except Exception as error:
            # Handle uncaught exceptions with standardized error response
            error_response = await self._handle_uncaught_exception(
                error, request, correlation_id, start_time
            )
            
            # Log error response
            await self._log_response_error(request, error, correlation_id, start_time)
            
            return error_response
    
    def _get_or_create_correlation_id(self, request: Request) -> str:
        """
        Get existing correlation ID from headers or create a new one.
        
        Args:
            request: HTTP request
            
        Returns:
            Correlation ID string
        """
        # Check for existing correlation ID in headers
        correlation_id = request.headers.get("x-correlation-id")
        
        if not correlation_id:
            correlation_id = request.headers.get("x-request-id")
        
        if not correlation_id:
            # Generate new correlation ID
            correlation_id = str(uuid.uuid4())
        
        return correlation_id
    
    async def _add_response_headers(
        self, 
        response: Response, 
        correlation_id: str, 
        start_time: Optional[float],
        request: Request
    ) -> Response:
        """
        Add standardized headers to response.
        
        Args:
            response: HTTP response
            correlation_id: Request correlation ID
            start_time: Request start time
            request: Original HTTP request
            
        Returns:
            Response with added headers
        """
        # Always add correlation ID
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Add response timing if enabled
        if self.enable_timing and start_time is not None:
            response_time = time.time() - start_time
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Response-Time-MS"] = f"{response_time * 1000:.0f}"
        
        # Add API version header
        response.headers["X-API-Version"] = "1.0"
        
        # Add CORS headers if enabled
        if self.enable_cors_headers:
            response.headers["Access-Control-Expose-Headers"] = (
                "X-Correlation-ID, X-Response-Time, X-API-Version"
            )
        
        # Add request path for debugging
        response.headers["X-Request-Path"] = str(request.url.path)
        
        return response
    
    async def _handle_uncaught_exception(
        self, 
        error: Exception, 
        request: Request,
        correlation_id: str,
        start_time: Optional[float]
    ) -> JSONResponse:
        """
        Handle uncaught exceptions with standardized error response.
        
        Args:
            error: Exception that was raised
            request: HTTP request that caused the error
            correlation_id: Request correlation ID
            start_time: Request start time
            
        Returns:
            Standardized error JSON response
        """
        # Check if this is already a StandardAPIError
        if isinstance(error, StandardAPIError):
            # Update correlation ID and request path
            error.correlation_id = correlation_id
            error.request_path = str(request.url.path)
            
            error_response = error.detail
            status_code = error.status_code
        
        else:
            # Convert unhandled exception to SystemError
            system_error = SystemError(
                error_code=CommonErrors.INTERNAL_SERVER_ERROR[0],
                message="An unexpected error occurred",
                system_component="application",
                upstream_error=str(error),
                correlation_id=correlation_id,
                request_path=str(request.url.path)
            )
            
            error_response = system_error.detail
            status_code = system_error.status_code
        
        # Create JSON response with standardized error format
        json_response = JSONResponse(
            status_code=status_code,
            content=error_response
        )
        
        # Add standardized headers
        json_response.headers["X-Correlation-ID"] = correlation_id
        
        if self.enable_timing and start_time is not None:
            response_time = time.time() - start_time
            json_response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        
        json_response.headers["X-API-Version"] = "1.0"
        json_response.headers["X-Request-Path"] = str(request.url.path)
        
        return json_response
    
    async def _log_request_start(self, request: Request, correlation_id: str):
        """
        Log request start with structured logging.
        
        Args:
            request: HTTP request
            correlation_id: Request correlation ID
        """
        logger.info(
            "API request started",
            correlation_id=correlation_id,
            method=request.method,
            path=str(request.url.path),
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    async def _log_response_success(
        self, 
        request: Request, 
        response: Response, 
        correlation_id: str,
        start_time: Optional[float]
    ):
        """
        Log successful response with structured logging.
        
        Args:
            request: HTTP request
            response: HTTP response
            correlation_id: Request correlation ID
            start_time: Request start time
        """
        response_time = time.time() - start_time if start_time else None
        
        logger.info(
            "API request completed successfully",
            correlation_id=correlation_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            response_time_seconds=response_time
        )
    
    async def _log_response_error(
        self, 
        request: Request, 
        error: Exception, 
        correlation_id: str,
        start_time: Optional[float]
    ):
        """
        Log error response with structured logging.
        
        Args:
            request: HTTP request
            error: Exception that occurred
            correlation_id: Request correlation ID
            start_time: Request start time
        """
        response_time = time.time() - start_time if start_time else None
        
        # Determine log level based on error type
        if isinstance(error, StandardAPIError):
            if error.status_code >= 500:
                log_level = "error"
            elif error.status_code >= 400:
                log_level = "warning"
            else:
                log_level = "info"
        else:
            log_level = "error"
        
        log_data = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": str(request.url.path),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "response_time_seconds": response_time
        }
        
        if isinstance(error, StandardAPIError):
            log_data.update({
                "error_code": error.error_code,
                "error_category": error.error_category,
                "status_code": error.status_code
            })
        
        # Log with appropriate level
        if log_level == "error":
            logger.error("API request failed with error", **log_data)
        elif log_level == "warning":
            logger.warning("API request completed with warning", **log_data)
        else:
            logger.info("API request completed with info", **log_data)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation and preprocessing.
    
    Provides request size limiting, content type validation,
    and basic security checks.
    """
    
    def __init__(
        self, 
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_content_types: Optional[list] = None
    ):
        """
        Initialize request validation middleware.
        
        Args:
            app: FastAPI application instance
            max_request_size: Maximum request size in bytes
            allowed_content_types: List of allowed content types
        """
        super().__init__(app)
        self.max_request_size = max_request_size
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Validate request before processing.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Processed HTTP response or validation error
        """
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            error = SystemError(
                error_code="VALIDATION_010",
                message=f"Request size exceeds maximum allowed size of {self.max_request_size} bytes",
                system_component="middleware"
            )
            
            return JSONResponse(
                status_code=error.status_code,
                content=error.detail
            )
        
        # Validate content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").split(";")[0]
            
            if content_type and content_type not in self.allowed_content_types:
                error = SystemError(
                    error_code="VALIDATION_011",
                    message=f"Unsupported content type: {content_type}",
                    system_component="middleware",
                    details={
                        "allowed_content_types": self.allowed_content_types
                    }
                )
                
                return JSONResponse(
                    status_code=error.status_code,
                    content=error.detail
                )
        
        # Process request
        return await call_next(request)


class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for response compression and optimization.
    
    Provides gzip compression for large responses and
    content optimization based on client capabilities.
    """
    
    def __init__(
        self, 
        app,
        minimum_size: int = 1024,  # Compress responses larger than 1KB
        compress_level: int = 6
    ):
        """
        Initialize response compression middleware.
        
        Args:
            app: FastAPI application instance
            minimum_size: Minimum response size to compress
            compress_level: Gzip compression level (1-9)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = compress_level
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process response with compression if applicable.
        
        Args:
            request: HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Potentially compressed HTTP response
        """
        response = await call_next(request)
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        
        if "gzip" in accept_encoding and hasattr(response, "body"):
            # Get response body
            body = response.body
            
            if isinstance(body, bytes) and len(body) >= self.minimum_size:
                # Compress response body
                import gzip
                
                compressed_body = gzip.compress(body, compresslevel=self.compress_level)
                
                # Only use compression if it actually reduces size
                if len(compressed_body) < len(body):
                    response.body = compressed_body
                    response.headers["Content-Encoding"] = "gzip"
                    response.headers["Content-Length"] = str(len(compressed_body))
        
        return response


# Middleware factory functions for easy integration
def create_api_standardization_middleware(
    enable_timing: bool = True,
    enable_cors_headers: bool = True
) -> APIStandardizationMiddleware:
    """
    Create API standardization middleware with specified configuration.
    
    Args:
        enable_timing: Whether to add response time headers
        enable_cors_headers: Whether to add CORS headers
        
    Returns:
        Configured middleware instance
    """
    def middleware_factory(app):
        return APIStandardizationMiddleware(
            app, 
            enable_timing=enable_timing,
            enable_cors_headers=enable_cors_headers
        )
    
    return middleware_factory


def create_request_validation_middleware(
    max_request_size: int = 10 * 1024 * 1024,
    allowed_content_types: Optional[list] = None
) -> RequestValidationMiddleware:
    """
    Create request validation middleware with specified configuration.
    
    Args:
        max_request_size: Maximum request size in bytes
        allowed_content_types: List of allowed content types
        
    Returns:
        Configured middleware instance
    """
    def middleware_factory(app):
        return RequestValidationMiddleware(
            app,
            max_request_size=max_request_size,
            allowed_content_types=allowed_content_types
        )
    
    return middleware_factory


def create_response_compression_middleware(
    minimum_size: int = 1024,
    compress_level: int = 6
) -> ResponseCompressionMiddleware:
    """
    Create response compression middleware with specified configuration.
    
    Args:
        minimum_size: Minimum response size to compress
        compress_level: Gzip compression level (1-9)
        
    Returns:
        Configured middleware instance
    """
    def middleware_factory(app):
        return ResponseCompressionMiddleware(
            app,
            minimum_size=minimum_size,
            compress_level=compress_level
        )
    
    return middleware_factory