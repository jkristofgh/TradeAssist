"""
Database Configuration for High-Frequency Trading Operations.

Provides optimized database connection configuration, connection pool management,
and SQLite performance optimizations for high-frequency market data ingestion.
"""

from typing import Dict, Any, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.engine import Engine

import structlog

from ..config import settings

logger = structlog.get_logger(__name__)


class DatabaseConfig:
    """
    Database configuration optimized for high-frequency trading operations.
    
    Provides connection pool optimization, SQLite performance tuning,
    and health monitoring configuration for maximum throughput and stability.
    """
    
    @staticmethod
    def create_optimized_engine(
        database_url: Optional[str] = None,
        **engine_kwargs
    ) -> AsyncEngine:
        """
        Create optimized async database engine for high-frequency operations.
        
        Args:
            database_url: Database connection URL (defaults to settings.DATABASE_URL)
            **engine_kwargs: Additional engine configuration options
            
        Returns:
            Configured AsyncEngine with optimal settings
        """
        if database_url is None:
            database_url = settings.DATABASE_URL
        
        # High-frequency trading optimized configuration
        config = {
            # Connection pooling for high-frequency operations
            "poolclass": QueuePool,
            "pool_size": 20,  # Base connections for sustained load
            "max_overflow": 50,  # Additional connections for burst traffic
            "pool_timeout": 30,  # Connection acquire timeout
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Verify connections before use
            
            # Performance optimizations
            "echo": False,  # Disable SQL logging for performance
            "echo_pool": False,  # Disable pool logging
            "future": True,  # Use SQLAlchemy 2.0 style
            
            # Connection options for SQLite optimization
            "connect_args": {
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30,  # Database lock timeout
            }
        }
        
        # Override with provided kwargs
        config.update(engine_kwargs)
        
        # Create async engine
        engine = create_async_engine(database_url, **config)
        
        # Apply SQLite-specific optimizations
        if "sqlite" in database_url.lower():
            DatabaseConfig._configure_sqlite_optimizations(engine)
        
        logger.info(
            "Optimized database engine created",
            database_url=database_url.split("://")[0] + "://***",  # Hide credentials
            pool_size=config.get("pool_size"),
            max_overflow=config.get("max_overflow"),
            pool_timeout=config.get("pool_timeout")
        )
        
        return engine
    
    @staticmethod
    def _configure_sqlite_optimizations(engine: AsyncEngine) -> None:
        """
        Configure SQLite-specific performance optimizations.
        
        Args:
            engine: AsyncEngine to configure
        """
        
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for optimal performance."""
            cursor = dbapi_connection.cursor()
            
            # High-frequency trading optimizations
            pragmas = [
                # WAL mode for better concurrent access
                "PRAGMA journal_mode=WAL;",
                
                # Synchronous mode for performance vs safety balance
                "PRAGMA synchronous=NORMAL;",  # Balance between speed and safety
                
                # Memory optimizations
                "PRAGMA cache_size=10000;",  # 10MB cache (negative value = KB)
                "PRAGMA temp_store=MEMORY;",  # Store temporary data in memory
                
                # Write optimizations for high-frequency inserts
                "PRAGMA wal_autocheckpoint=1000;",  # Checkpoint every 1000 pages
                "PRAGMA journal_size_limit=67108864;",  # 64MB WAL file limit
                
                # Query optimization
                "PRAGMA optimize;",  # Analyze and optimize
                
                # Connection optimizations
                "PRAGMA busy_timeout=30000;",  # 30 second busy timeout
                
                # Performance pragmas for trading workloads
                "PRAGMA threads=4;",  # Use multiple threads if available
                "PRAGMA mmap_size=268435456;",  # 256MB memory-mapped I/O
            ]
            
            for pragma in pragmas:
                try:
                    cursor.execute(pragma)
                    logger.debug("SQLite pragma applied", pragma=pragma.strip())
                except Exception as e:
                    logger.warning("Failed to apply SQLite pragma", pragma=pragma, error=str(e))
            
            cursor.close()
            
            logger.info("SQLite performance optimizations applied")
    
    @staticmethod
    def get_connection_pool_config() -> Dict[str, Any]:
        """
        Get recommended connection pool configuration for high-frequency trading.
        
        Returns:
            Dictionary containing optimal pool configuration
        """
        return {
            # Pool sizing for high-frequency operations
            "pool_size": 20,  # Base pool size for sustained operations
            "max_overflow": 50,  # Overflow for burst traffic (10,000+ inserts/min)
            "pool_timeout": 30,  # Connection acquire timeout
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Health check connections
            
            # Performance settings
            "pool_reset_on_return": "commit",  # Reset connections on return
            "pool_logging_name": "database_pool",  # Pool logging identifier
        }
    
    @staticmethod
    def get_sqlite_performance_config() -> Dict[str, str]:
        """
        Get SQLite-specific performance configuration.
        
        Returns:
            Dictionary of SQLite pragma settings
        """
        return {
            # Write-Ahead Logging for concurrent access
            "journal_mode": "WAL",
            
            # Synchronization mode (NORMAL for trading balance)
            "synchronous": "NORMAL",
            
            # Cache size (10MB for high-frequency operations)
            "cache_size": "10000",
            
            # Memory optimizations
            "temp_store": "MEMORY",
            
            # WAL optimizations
            "wal_autocheckpoint": "1000",
            "journal_size_limit": "67108864",  # 64MB
            
            # Query optimization
            "optimize": "1",
            
            # Timeout for busy database
            "busy_timeout": "30000",  # 30 seconds
            
            # Threading and memory mapping
            "threads": "4",
            "mmap_size": "268435456",  # 256MB
        }
    
    @staticmethod
    def validate_database_configuration(engine: AsyncEngine) -> Dict[str, Any]:
        """
        Validate database configuration for high-frequency trading requirements.
        
        Args:
            engine: Database engine to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        try:
            # Check pool configuration
            pool = engine.pool
            
            # Validate pool size for high-frequency operations
            if hasattr(pool, '_pool_size'):
                pool_size = pool._pool_size
                if pool_size < 10:
                    validation_results["warnings"].append(
                        f"Pool size ({pool_size}) may be too small for high-frequency trading"
                    )
                    validation_results["recommendations"].append(
                        "Consider increasing pool_size to at least 20 for sustained high-frequency operations"
                    )
            
            # Validate overflow capacity
            if hasattr(pool, '_max_overflow'):
                max_overflow = pool._max_overflow
                if max_overflow < 20:
                    validation_results["warnings"].append(
                        f"Pool overflow ({max_overflow}) may be insufficient for burst traffic"
                    )
                    validation_results["recommendations"].append(
                        "Consider increasing max_overflow to at least 50 for handling traffic spikes"
                    )
            
            # Check for SQLite-specific optimizations
            if "sqlite" in str(engine.url).lower():
                validation_results["recommendations"].append(
                    "SQLite detected - ensure WAL mode and performance pragmas are configured"
                )
            
            logger.info(
                "Database configuration validated",
                is_valid=validation_results["is_valid"],
                warning_count=len(validation_results["warnings"]),
                error_count=len(validation_results["errors"])
            )
            
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Validation failed: {str(e)}")
            logger.error("Database configuration validation failed", error=str(e))
        
        return validation_results
    
    @staticmethod
    def get_performance_monitoring_config() -> Dict[str, Any]:
        """
        Get configuration for database performance monitoring.
        
        Returns:
            Dictionary containing monitoring configuration
        """
        return {
            # Monitoring intervals
            "health_check_interval_seconds": 30,
            "metrics_collection_interval_seconds": 60,
            
            # Alert thresholds
            "pool_utilization_warning_percent": 70.0,
            "pool_utilization_critical_percent": 85.0,
            "query_time_warning_ms": 100.0,
            "query_time_critical_ms": 500.0,
            "connection_acquire_warning_ms": 50.0,
            "connection_acquire_critical_ms": 200.0,
            
            # Performance targets for high-frequency trading
            "target_insert_rate_per_second": 10000,  # 10K inserts/second
            "target_query_response_time_ms": 10,  # 10ms average
            "target_connection_acquire_time_ms": 5,  # 5ms connection acquisition
            
            # History retention
            "metrics_history_retention_count": 1000,
            "performance_history_retention_hours": 24,
        }
    
    @staticmethod
    def create_connection_string(
        database_type: str = "sqlite",
        database_path: Optional[str] = None,
        **connection_params
    ) -> str:
        """
        Create optimized database connection string.
        
        Args:
            database_type: Type of database (sqlite, postgresql, etc.)
            database_path: Path to database file (for SQLite)
            **connection_params: Additional connection parameters
            
        Returns:
            Formatted connection string
        """
        if database_type.lower() == "sqlite":
            if database_path is None:
                database_path = "./data/tradeassist_optimized.db"
            
            # SQLite async connection string
            connection_string = f"sqlite+aiosqlite:///{database_path}"
            
        elif database_type.lower() == "postgresql":
            # PostgreSQL connection for production scaling
            host = connection_params.get("host", "localhost")
            port = connection_params.get("port", 5432)
            database = connection_params.get("database", "tradeassist")
            username = connection_params.get("username", "tradeassist")
            password = connection_params.get("password", "")
            
            connection_string = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
            
        else:
            raise ValueError(f"Unsupported database type: {database_type}")
        
        logger.info(
            "Database connection string created",
            database_type=database_type,
            connection_string=connection_string.split("://")[0] + "://***"  # Hide credentials
        )
        
        return connection_string