"""
Production logging configuration for TradeAssist.

Provides structured logging with file rotation, performance tracking,
and audit logging for historical data operations.
"""

import logging
import logging.handlers
import os
import sys
from typing import Dict, Any

import structlog
from structlog.stdlib import LoggerFactory

from .config import settings


def configure_production_logging() -> None:
    """
    Configure production logging with structured logs and file rotation.
    
    Sets up:
    - Structured logging with JSON format for production
    - File rotation with configurable size and retention
    - Performance metrics logging
    - Audit logging for historical data access
    - Error tracking and alerting
    """
    
    # Ensure log directory exists
    if settings.LOG_TO_FILE:
        log_dir = os.path.dirname(settings.LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.value.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.value.upper()))
    
    if settings.DEBUG:
        # Pretty format for development
        console_format = logging.Formatter(
            fmt='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # JSON format for production
        console_format = logging.Formatter(settings.LOG_FORMAT)
    
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (if enabled)
    if settings.LOG_TO_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            maxBytes=settings.LOG_FILE_MAX_SIZE,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)  # Always log INFO+ to files
        
        # JSON format for file logs
        file_format = logging.Formatter(
            fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    
    # Configure structlog
    configure_structlog()
    
    # Set specific logger levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("schwab").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    

def configure_structlog() -> None:
    """Configure structlog for structured logging."""
    
    # Determine processors based on environment
    if settings.DEBUG:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def create_performance_logger() -> structlog.BoundLogger:
    """
    Create a dedicated logger for performance metrics.
    
    Returns:
        BoundLogger: Configured logger for performance tracking
    """
    return structlog.get_logger("tradeassist.performance")


def create_audit_logger() -> structlog.BoundLogger:
    """
    Create a dedicated logger for audit events.
    
    Returns:
        BoundLogger: Configured logger for audit tracking
    """
    return structlog.get_logger("tradeassist.audit")


def create_historical_data_logger() -> structlog.BoundLogger:
    """
    Create a dedicated logger for historical data operations.
    
    Returns:
        BoundLogger: Configured logger for historical data tracking
    """
    return structlog.get_logger("tradeassist.historical_data")


def log_historical_data_request(
    logger: structlog.BoundLogger,
    symbols: list,
    frequency: str,
    start_date: str = None,
    end_date: str = None,
    user_id: str = None,
    **kwargs
) -> None:
    """
    Log historical data request for audit purposes.
    
    Args:
        logger: Logger instance
        symbols: List of requested symbols
        frequency: Data frequency requested
        start_date: Start date for data range
        end_date: End date for data range
        user_id: User making the request
        **kwargs: Additional context
    """
    logger.info(
        "Historical data request",
        event_type="historical_data_request",
        symbols=symbols,
        symbol_count=len(symbols),
        frequency=frequency,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        **kwargs
    )


def log_historical_data_response(
    logger: structlog.BoundLogger,
    symbols: list,
    total_bars: int,
    cache_hit: bool,
    response_time_ms: float,
    data_source: str = None,
    **kwargs
) -> None:
    """
    Log historical data response for performance tracking.
    
    Args:
        logger: Logger instance
        symbols: List of symbols returned
        total_bars: Total number of data bars returned
        cache_hit: Whether response was served from cache
        response_time_ms: Response time in milliseconds
        data_source: Source of the data (e.g., 'schwab', 'cache')
        **kwargs: Additional context
    """
    logger.info(
        "Historical data response",
        event_type="historical_data_response",
        symbols=symbols,
        symbol_count=len(symbols),
        total_bars=total_bars,
        cache_hit=cache_hit,
        response_time_ms=response_time_ms,
        data_source=data_source,
        **kwargs
    )


def log_performance_metric(
    logger: structlog.BoundLogger,
    metric_name: str,
    metric_value: float,
    metric_unit: str = "ms",
    **context
) -> None:
    """
    Log performance metric.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        metric_value: Metric value
        metric_unit: Unit of measurement
        **context: Additional context
    """
    logger.info(
        f"Performance metric: {metric_name}",
        event_type="performance_metric",
        metric_name=metric_name,
        metric_value=metric_value,
        metric_unit=metric_unit,
        **context
    )


def log_error_with_context(
    logger: structlog.BoundLogger,
    error: Exception,
    operation: str,
    **context
) -> None:
    """
    Log error with full context for troubleshooting.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Operation being performed when error occurred
        **context: Additional context
    """
    logger.error(
        f"Error in {operation}",
        event_type="error",
        operation=operation,
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
        exc_info=True
    )


class HistoricalDataLoggerMixin:
    """
    Mixin class to add structured logging to historical data services.
    
    Provides consistent logging methods for historical data operations.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._audit_logger = create_audit_logger()
        self._performance_logger = create_performance_logger()
        self._data_logger = create_historical_data_logger()
    
    def log_request(self, symbols: list, frequency: str, **kwargs) -> None:
        """Log historical data request."""
        log_historical_data_request(
            self._audit_logger,
            symbols=symbols,
            frequency=frequency,
            **kwargs
        )
    
    def log_response(
        self, 
        symbols: list, 
        total_bars: int, 
        cache_hit: bool,
        response_time_ms: float,
        **kwargs
    ) -> None:
        """Log historical data response."""
        log_historical_data_response(
            self._performance_logger,
            symbols=symbols,
            total_bars=total_bars,
            cache_hit=cache_hit,
            response_time_ms=response_time_ms,
            **kwargs
        )
    
    def log_error(self, error: Exception, operation: str, **kwargs) -> None:
        """Log error with context."""
        log_error_with_context(
            self._data_logger,
            error=error,
            operation=operation,
            **kwargs
        )
    
    def log_performance(self, metric_name: str, value: float, unit: str = "ms") -> None:
        """Log performance metric."""
        log_performance_metric(
            self._performance_logger,
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit
        )