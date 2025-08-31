# Database Performance & Integrity Extension - Comprehensive PRP

**Generated:** 2025-08-31 12:21:30  
**Extension Name:** Database Performance & Integrity  
**Target Project:** TradeAssist  
**Extension Type:** Infrastructure/Performance Optimization  
**Version:** 1.0  
**Base Project Version:** Phase 3 Complete

## Extension Context

This comprehensive Product Requirements Prompt (PRP) provides complete implementation guidance for the Database Performance & Integrity extension. The extension optimizes TradeAssist's database layer for high-frequency trading operations while implementing critical data safety mechanisms to prevent accidental data loss.

### Primary Objectives
- Eliminate performance bottlenecks in database operations with 30-50% INSERT improvement
- Protect against accidental data loss through CASCADE DELETE safety measures
- Optimize database for high-frequency market data ingestion (10,000+ inserts/minute)
- Establish production-ready database architecture for long-term scalability

## Existing System Understanding

### Current Architecture Analysis
TradeAssist is a production-ready, single-user trading application with the following database characteristics:

**Database Technologies:**
- SQLite with WAL mode for persistence
- SQLAlchemy 2.0+ async ORM with connection pooling
- Alembic migration system for schema evolution
- Structured logging with performance monitoring

**Current Performance Bottlenecks:**
- **MarketData Table**: 5 indexes causing INSERT performance degradation
- **AlertLog Table**: 11 indexes significantly impacting write performance
- **DECIMAL Data Types**: CPU-intensive calculations for price arithmetic
- **CASCADE DELETE**: Risk of accidental historical data loss

**Database Schema Structure:**
```python
# Current MarketData model (performance bottlenecks identified)
class MarketData(Base):
    price: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4))  # CPU-intensive
    bid: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4))    # CPU-intensive
    ask: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4))    # CPU-intensive
    
    # 5 indexes causing INSERT performance issues:
    __table_args__ = (
        Index("ix_market_data_timestamp_instrument", "timestamp", "instrument_id"),
        Index("ix_market_data_timestamp", "timestamp"),
        Index("ix_market_data_instrument", "instrument_id"),
        Index("ix_market_data_price", "price"),
        Index("ix_market_data_latest", "instrument_id", "timestamp", "price"),
    )

# Current AlertLog model (11 indexes causing performance issues)
class AlertLog(Base):
    trigger_value: Mapped[float] = mapped_column(DECIMAL(12, 4))     # CPU-intensive
    threshold_value: Mapped[float] = mapped_column(DECIMAL(12, 4))   # CPU-intensive
    
    # 11 indexes causing INSERT performance degradation
```

### Available Integration Points

**Database Integration Opportunities:**
- **Model Extension**: Base class and TimestampMixin patterns for consistency
- **Migration System**: Alembic integration for zero-downtime schema changes
- **Connection Management**: Async SQLAlchemy with connection pooling
- **Service Layer**: Existing services can be updated to handle new data types

**Performance Monitoring Integration:**
- **Health API**: `/api/health` can report database performance metrics
- **Structured Logging**: Performance metrics integration with existing logging
- **WebSocket**: Real-time performance monitoring via existing WebSocket infrastructure

## Complete Technical Architecture

### 1. Index Optimization Strategy

**MarketData Table Index Reduction:**
```python
# BEFORE: 5 indexes causing INSERT bottlenecks
__table_args__ = (
    Index("ix_market_data_timestamp_instrument", "timestamp", "instrument_id"),
    Index("ix_market_data_timestamp", "timestamp"),
    Index("ix_market_data_instrument", "instrument_id"),
    Index("ix_market_data_price", "price"),
    Index("ix_market_data_latest", "instrument_id", "timestamp", "price"),
)

# AFTER: 2 essential indexes for optimal INSERT performance
__table_args__ = (
    # Primary composite index for most common queries
    Index("ix_market_data_timestamp_instrument", "timestamp", "instrument_id"),
    # Secondary index for price-based alert queries
    Index("ix_market_data_instrument_price", "instrument_id", "price"),
)
```

**AlertLog Table Index Reduction:**
```python
# BEFORE: 11 indexes causing severe INSERT performance issues
__table_args__ = (
    Index("ix_alert_logs_timestamp", "timestamp"),
    Index("ix_alert_logs_rule", "rule_id"),
    Index("ix_alert_logs_instrument", "instrument_id"),
    Index("ix_alert_logs_timestamp_instrument", "timestamp", "instrument_id"),
    Index("ix_alert_logs_timestamp_rule", "timestamp", "rule_id"),
    Index("ix_alert_logs_rule_timestamp", "rule_id", "timestamp"),
    Index("ix_alert_logs_fired_status", "fired_status"),
    Index("ix_alert_logs_delivery_status", "delivery_status"),
    Index("ix_alert_logs_evaluation_time", "evaluation_time_ms"),
    Index("ix_alert_logs_recent", "timestamp", "fired_status", "instrument_id"),
)

# AFTER: 4 essential indexes optimized for query patterns
__table_args__ = (
    # Primary time-series index
    Index("ix_alert_logs_timestamp", "timestamp"),
    # Rule performance index
    Index("ix_alert_logs_rule_timestamp", "rule_id", "timestamp"),
    # Instrument alerts index
    Index("ix_alert_logs_instrument", "instrument_id"),
    # Status monitoring index
    Index("ix_alert_logs_status", "fired_status", "delivery_status"),
)
```

### 2. Data Type Optimization Architecture

**DECIMAL to FLOAT Conversion Strategy:**
```python
# BEFORE: CPU-intensive DECIMAL arithmetic
price: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4))
bid: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4))
ask: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4))

# AFTER: High-performance FLOAT arithmetic
price: Mapped[Optional[float]] = mapped_column(Float)
bid: Mapped[Optional[float]] = mapped_column(Float)
ask: Mapped[Optional[float]] = mapped_column(Float)

# Note: Keep DECIMAL for accounting operations where precision is critical
settlement_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))  # Kept for precision
```

**Backward Compatibility Response Format:**
```python
class MarketDataResponse(BaseModel):
    """API response model ensuring backward compatibility."""
    
    price: Optional[float] = Field(None, description="Current price")
    bid: Optional[float] = Field(None, description="Best bid price")  
    ask: Optional[float] = Field(None, description="Best ask price")
    
    class Config:
        from_attributes = True
        
    @field_validator('price', 'bid', 'ask', mode='before')
    @classmethod
    def round_float_precision(cls, v):
        """Ensure API compatibility by rounding to 4 decimal places."""
        if v is not None:
            return round(float(v), 4)
        return v
```

### 3. Referential Integrity Safety Architecture

**CASCADE DELETE to RESTRICT Conversion:**
```python
# BEFORE: Dangerous CASCADE DELETE (risk of data loss)
instrument_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("instruments.id", ondelete="CASCADE"),  # DANGEROUS
    nullable=False
)

# AFTER: Safe RESTRICT with soft delete capability
instrument_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("instruments.id", ondelete="RESTRICT"),  # SAFE
    nullable=False
)

# Add soft delete capability
deleted_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime,
    nullable=True,
    index=True,
    doc="Timestamp for soft deletion (NULL = active)"
)
```

**Soft Delete Mixin Pattern:**
```python
class SoftDeleteMixin:
    """Mixin for soft delete functionality across models."""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        doc="Soft delete timestamp"
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
```

### 4. Time-Series Partitioning Architecture

**MarketData Monthly Partitioning:**
```sql
-- Monthly partitioning strategy for high-volume market data
CREATE TABLE market_data_2025_01 (
    CHECK (timestamp >= '2025-01-01' AND timestamp < '2025-02-01')
) INHERITS (market_data);

CREATE TABLE market_data_2025_02 (
    CHECK (timestamp >= '2025-02-01' AND timestamp < '2025-03-01')
) INHERITS (market_data);

-- Automated partition creation function
CREATE OR REPLACE FUNCTION create_market_data_partition(
    partition_date DATE
) RETURNS VOID AS $$
DECLARE
    table_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Calculate partition boundaries
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    table_name := 'market_data_' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Create partition table
    EXECUTE format('CREATE TABLE %I (
        CHECK (timestamp >= %L AND timestamp < %L)
    ) INHERITS (market_data)', table_name, start_date, end_date);
    
    -- Create indexes on partition
    EXECUTE format('CREATE INDEX %I ON %I (timestamp, instrument_id)', 
        'ix_' || table_name || '_timestamp_instrument', table_name);
    EXECUTE format('CREATE INDEX %I ON %I (instrument_id, price)', 
        'ix_' || table_name || '_instrument_price', table_name);
END;
$$ LANGUAGE plpgsql;
```

**AlertLog Quarterly Partitioning:**
```sql
-- Quarterly partitioning for alert logs (lower volume, longer retention)
CREATE TABLE alert_logs_2025_q1 (
    CHECK (timestamp >= '2025-01-01' AND timestamp < '2025-04-01')
) INHERITS (alert_logs);

-- Automated partition management
CREATE OR REPLACE FUNCTION create_alert_log_partition(
    partition_quarter INTEGER,
    partition_year INTEGER
) RETURNS VOID AS $$
-- Implementation for quarterly partition creation
$$;
```

### 5. Connection Pool Optimization Architecture

**High-Frequency Trading Connection Pool:**
```python
# src/backend/database/connection.py - Enhanced for high-frequency operations
class DatabaseConfig:
    """Database configuration optimized for high-frequency trading."""
    
    # Connection pool sizing for high throughput
    POOL_SIZE: int = 20  # Base connections
    MAX_OVERFLOW: int = 50  # Burst capacity
    POOL_TIMEOUT: int = 30  # Connection timeout
    POOL_RECYCLE: int = 3600  # Connection recycling
    
    # SQLite optimizations for high-frequency writes
    SQLITE_PRAGMA = {
        "journal_mode": "WAL",  # Write-Ahead Logging
        "synchronous": "NORMAL",  # Balanced safety/performance
        "cache_size": 10000,  # 10MB cache
        "temp_store": "MEMORY",  # Memory temp storage
        "mmap_size": 134217728,  # 128MB memory mapping
    }
    
    # Connection health monitoring
    POOL_PRE_PING: bool = True  # Validate connections
    POOL_RESET_ON_RETURN: str = "commit"  # Reset connection state

async def create_optimized_engine() -> AsyncEngine:
    """Create database engine optimized for high-frequency trading."""
    
    # Build connection URL with optimizations
    sqlite_url = f"sqlite+aiosqlite:///{settings.DATABASE_PATH}"
    
    # Pragma parameters for performance
    pragma_params = "&".join([
        f"pragma_{key}={value}" 
        for key, value in DatabaseConfig.SQLITE_PRAGMA.items()
    ])
    
    full_url = f"{sqlite_url}?{pragma_params}"
    
    # Create engine with optimized pool
    engine = create_async_engine(
        full_url,
        poolclass=StaticPool,
        pool_size=DatabaseConfig.POOL_SIZE,
        max_overflow=DatabaseConfig.MAX_OVERFLOW,
        pool_timeout=DatabaseConfig.POOL_TIMEOUT,
        pool_recycle=DatabaseConfig.POOL_RECYCLE,
        pool_pre_ping=DatabaseConfig.POOL_PRE_PING,
        pool_reset_on_return=DatabaseConfig.POOL_RESET_ON_RETURN,
        echo=settings.DATABASE_ECHO_QUERIES,
    )
    
    return engine
```

## Complete Implementation Roadmap

### Phase 1: Database Schema Optimization (Days 1-3)

**1.1 Index Analysis and Removal**
```bash
# Migration: Remove non-essential indexes
alembic revision --autogenerate -m "Optimize MarketData indexes for INSERT performance"
alembic revision --autogenerate -m "Optimize AlertLog indexes for INSERT performance"
```

**Migration Implementation:**
```python
# alembic/versions/xxx_optimize_market_data_indexes.py
def upgrade():
    # Remove non-essential MarketData indexes
    op.drop_index('ix_market_data_timestamp')
    op.drop_index('ix_market_data_instrument')  
    op.drop_index('ix_market_data_price')
    op.drop_index('ix_market_data_latest')
    
    # Keep only essential composite index
    # ix_market_data_timestamp_instrument already exists
    
    # Add optimized secondary index
    op.create_index(
        'ix_market_data_instrument_price',
        'market_data',
        ['instrument_id', 'price']
    )

def downgrade():
    # Restore all original indexes if needed
    op.create_index('ix_market_data_timestamp', 'market_data', ['timestamp'])
    op.create_index('ix_market_data_instrument', 'market_data', ['instrument_id'])
    op.create_index('ix_market_data_price', 'market_data', ['price'])
    op.create_index('ix_market_data_latest', 'market_data', ['instrument_id', 'timestamp', 'price'])
    op.drop_index('ix_market_data_instrument_price')
```

**1.2 Data Type Optimization Migration**
```python
# alembic/versions/xxx_convert_decimal_to_float.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Convert DECIMAL fields to FLOAT for performance."""
    
    # MarketData table conversions
    with op.batch_alter_table('market_data') as batch_op:
        batch_op.alter_column('price', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
        batch_op.alter_column('bid', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
        batch_op.alter_column('ask', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
        batch_op.alter_column('open_price', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
        batch_op.alter_column('high_price', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
        batch_op.alter_column('low_price', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
    
    # AlertLog table conversions
    with op.batch_alter_table('alert_logs') as batch_op:
        batch_op.alter_column('trigger_value', type_=sa.Float, existing_type=sa.DECIMAL(12,4))
        batch_op.alter_column('threshold_value', type_=sa.Float, existing_type=sa.DECIMAL(12,4))

def downgrade():
    """Revert FLOAT fields back to DECIMAL."""
    # Implementation for rollback if needed
    pass
```

**1.3 Referential Integrity Safety Migration**
```python
# alembic/versions/xxx_add_soft_delete_safety.py
def upgrade():
    """Add soft delete capability and convert CASCADE to RESTRICT."""
    
    # Add soft delete columns
    with op.batch_alter_table('market_data') as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_market_data_deleted_at', ['deleted_at'])
    
    with op.batch_alter_table('alert_logs') as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_alert_logs_deleted_at', ['deleted_at'])
    
    # Convert CASCADE DELETE to RESTRICT
    # Note: SQLite doesn't support changing foreign key constraints directly
    # This would require table recreation in production
    pass

def downgrade():
    # Remove soft delete capability
    op.drop_column('market_data', 'deleted_at')
    op.drop_column('alert_logs', 'deleted_at')
```

### Phase 2: Service Layer Updates (Days 4-6)

**2.1 Updated Model Classes**
```python
# src/backend/models/market_data.py - Optimized version
from .mixins import SoftDeleteMixin

class MarketData(Base, SoftDeleteMixin):
    """Optimized MarketData model for high-frequency trading."""
    
    __tablename__ = "market_data"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("instruments.id", ondelete="RESTRICT"),  # SAFE
        nullable=False
    )
    
    # Optimized FLOAT fields for performance
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True) 
    ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Volume fields remain integer
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bid_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ask_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Optimized indexes (only 2 essential indexes)
    __table_args__ = (
        Index("ix_market_data_timestamp_instrument", "timestamp", "instrument_id"),
        Index("ix_market_data_instrument_price", "instrument_id", "price"),
    )
```

**2.2 Enhanced Repository Pattern**
```python
# src/backend/repositories/market_data_repository.py
class OptimizedMarketDataRepository:
    """Optimized repository for high-frequency market data operations."""
    
    async def bulk_insert_market_data(
        self, 
        market_data_list: List[MarketData]
    ) -> int:
        """
        Optimized bulk insert for high-frequency data ingestion.
        
        Targets: 30-50% performance improvement over individual inserts.
        """
        async with get_db_session() as session:
            try:
                # Use bulk insert for maximum performance
                session.add_all(market_data_list)
                await session.commit()
                
                logger.info(f"Bulk inserted {len(market_data_list)} market data records")
                return len(market_data_list)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Bulk insert failed: {e}")
                raise
    
    async def get_active_market_data(
        self,
        instrument_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[MarketData]:
        """Query active (non-deleted) market data with optimized indexes."""
        async with get_db_session() as session:
            result = await session.execute(
                select(MarketData)
                .where(
                    MarketData.instrument_id == instrument_id,
                    MarketData.timestamp >= start_time,
                    MarketData.timestamp <= end_time,
                    MarketData.deleted_at.is_(None)  # Only active records
                )
                .order_by(MarketData.timestamp.asc())
                .options(selectinload(MarketData.instrument))
            )
            return result.scalars().all()
    
    async def soft_delete_market_data(
        self, 
        market_data_id: int
    ) -> bool:
        """Safely soft delete market data record."""
        async with get_db_session() as session:
            try:
                market_data = await session.get(MarketData, market_data_id)
                if not market_data:
                    return False
                
                market_data.soft_delete()
                await session.commit()
                
                logger.info(f"Soft deleted MarketData {market_data_id}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Soft delete failed for MarketData {market_data_id}: {e}")
                return False
```

**2.3 Connection Pool Monitoring Service**
```python
# src/backend/services/database_monitor.py
import asyncio
import structlog
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = structlog.get_logger()

class DatabaseMonitoringService:
    """
    Database performance monitoring service.
    
    Tracks connection pool health, query performance, and database metrics
    for high-frequency trading operations optimization.
    """
    
    def __init__(self):
        self.is_running = False
        self._metrics: Dict[str, Any] = {}
        self._background_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start database monitoring service."""
        if self.is_running:
            logger.warning("Database monitoring service already running")
            return
        
        logger.info("Starting database monitoring service")
        self.is_running = True
        
        # Initialize metrics
        self._metrics = {
            "connection_pool": {
                "size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
            },
            "performance": {
                "avg_query_time": 0.0,
                "slow_queries": 0,
                "total_queries": 0,
                "insert_rate": 0.0,
            },
            "health": {
                "last_check": None,
                "status": "unknown",
            }
        }
        
        # Start background monitoring
        self._background_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Database monitoring service started")
    
    async def stop(self) -> None:
        """Stop database monitoring service gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping database monitoring service")
        self.is_running = False
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Database monitoring service stopped")
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.is_running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(10.0)  # Collect metrics every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in database monitoring loop: {e}")
                await asyncio.sleep(30.0)  # Error backoff
    
    async def _collect_metrics(self) -> None:
        """Collect database performance metrics."""
        try:
            # Collect connection pool metrics
            from src.backend.database.connection import engine
            
            pool = engine.pool
            self._metrics["connection_pool"].update({
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            })
            
            # Update health status
            self._metrics["health"].update({
                "last_check": datetime.utcnow(),
                "status": "healthy" if pool.checkedout() < pool.size() else "degraded"
            })
            
            # Log metrics periodically
            if datetime.utcnow().second % 60 == 0:  # Every minute
                logger.info("Database metrics", **self._metrics)
        
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            self._metrics["health"]["status"] = "error"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current database metrics."""
        return self._metrics.copy()
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            # Simple query to test database connectivity
            from src.backend.database.connection import get_db_session
            
            async with get_db_session() as session:
                start_time = datetime.utcnow()
                await session.execute(text("SELECT 1"))
                query_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "query_time": query_time,
                "timestamp": datetime.utcnow(),
            }
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow(),
            }
```

### Phase 3: Time-Series Partitioning Implementation (Days 7-9)

**3.1 Partition Management Service**
```python
# src/backend/services/partition_manager.py
import asyncio
import structlog
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Optional

logger = structlog.get_logger()

class PartitionManagerService:
    """
    Automated database partition management service.
    
    Handles creation, maintenance, and archival of time-series partitions
    for MarketData (monthly) and AlertLog (quarterly) tables.
    """
    
    def __init__(self):
        self.is_running = False
        self._background_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start partition management service."""
        if self.is_running:
            logger.warning("Partition manager already running")
            return
        
        logger.info("Starting partition management service")
        self.is_running = True
        
        # Create initial partitions
        await self._create_initial_partitions()
        
        # Start background management
        self._background_task = asyncio.create_task(self._management_loop())
        logger.info("Partition management service started")
    
    async def _create_initial_partitions(self) -> None:
        """Create initial partitions for current and future periods."""
        current_date = datetime.utcnow().date()
        
        # Create MarketData partitions (current + 2 months ahead)
        for i in range(3):
            target_date = current_date + relativedelta(months=i)
            await self._create_market_data_partition(target_date)
        
        # Create AlertLog partitions (current + 1 quarter ahead)
        for i in range(2):
            target_date = current_date + relativedelta(months=i*3)
            await self._create_alert_log_partition(target_date)
    
    async def _create_market_data_partition(self, partition_date: date) -> bool:
        """Create monthly MarketData partition."""
        try:
            from src.backend.database.connection import get_db_session
            
            # Calculate partition boundaries
            start_date = partition_date.replace(day=1)
            end_date = start_date + relativedelta(months=1)
            
            table_name = f"market_data_{start_date.strftime('%Y_%m')}"
            
            async with get_db_session() as session:
                # Check if partition already exists
                result = await session.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                ), {"table_name": table_name})
                
                if result.fetchone():
                    logger.debug(f"Partition {table_name} already exists")
                    return True
                
                # Create partition table
                await session.execute(text(f"""
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        instrument_id INTEGER NOT NULL,
                        price REAL,
                        volume INTEGER,
                        bid REAL,
                        ask REAL,
                        bid_size INTEGER,
                        ask_size INTEGER,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        deleted_at DATETIME,
                        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE RESTRICT,
                        CHECK (timestamp >= '{start_date}' AND timestamp < '{end_date}')
                    )
                """))
                
                # Create indexes on partition
                await session.execute(text(f"""
                    CREATE INDEX ix_{table_name}_timestamp_instrument 
                    ON {table_name} (timestamp, instrument_id)
                """))
                
                await session.execute(text(f"""
                    CREATE INDEX ix_{table_name}_instrument_price 
                    ON {table_name} (instrument_id, price)
                """))
                
                await session.commit()
                logger.info(f"Created MarketData partition: {table_name}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to create MarketData partition for {partition_date}: {e}")
            return False
    
    async def _management_loop(self) -> None:
        """Background partition management loop."""
        while self.is_running:
            try:
                # Check daily for new partitions needed
                await self._ensure_future_partitions()
                await self._cleanup_old_partitions()
                
                # Sleep for 24 hours
                await asyncio.sleep(86400)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in partition management loop: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _ensure_future_partitions(self) -> None:
        """Ensure future partitions exist."""
        current_date = datetime.utcnow().date()
        future_date = current_date + relativedelta(months=2)
        
        # Ensure MarketData partitions exist for next 2 months
        await self._create_market_data_partition(current_date + relativedelta(months=1))
        await self._create_market_data_partition(future_date)
        
        # Ensure AlertLog partitions exist for next quarter
        future_quarter = current_date + relativedelta(months=3)
        await self._create_alert_log_partition(future_quarter)
    
    async def get_partition_info(self) -> List[Dict[str, Any]]:
        """Get information about existing partitions."""
        try:
            from src.backend.database.connection import get_db_session
            
            async with get_db_session() as session:
                result = await session.execute(text("""
                    SELECT name, sql 
                    FROM sqlite_master 
                    WHERE type='table' 
                    AND (name LIKE 'market_data_%' OR name LIKE 'alert_logs_%')
                    ORDER BY name
                """))
                
                partitions = []
                for row in result:
                    partitions.append({
                        "name": row.name,
                        "type": "MarketData" if "market_data" in row.name else "AlertLog",
                        "sql": row.sql
                    })
                
                return partitions
        
        except Exception as e:
            logger.error(f"Failed to get partition info: {e}")
            return []
```

### Phase 4: Performance Monitoring Integration (Days 10-12)

**4.1 Enhanced Health API**
```python
# src/backend/api/health.py - Enhanced with database performance metrics
from src.backend.services.database_monitor import DatabaseMonitoringService

@router.get("/database", response_model=DatabaseHealthResponse)
async def get_database_health(
    db_monitor: DatabaseMonitoringService = Depends(get_database_monitor)
) -> DatabaseHealthResponse:
    """Get comprehensive database health and performance metrics."""
    
    # Get current metrics from monitoring service
    metrics = db_monitor.get_metrics()
    health_check = await db_monitor.check_health()
    
    # Calculate performance indicators
    insert_performance = await _calculate_insert_performance()
    query_performance = await _calculate_query_performance()
    
    return DatabaseHealthResponse(
        status=health_check["status"],
        timestamp=datetime.utcnow(),
        connection_pool={
            "size": metrics["connection_pool"]["size"],
            "active": metrics["connection_pool"]["checked_out"],
            "idle": metrics["connection_pool"]["checked_in"],
            "overflow": metrics["connection_pool"]["overflow"],
        },
        performance={
            "insert_rate": insert_performance["rate"],
            "avg_query_time": query_performance["avg_time"],
            "slow_queries": query_performance["slow_count"],
            "index_efficiency": await _calculate_index_efficiency(),
        },
        partitions=await _get_partition_status(),
        optimization_impact={
            "insert_improvement": insert_performance["improvement_pct"],
            "calculation_speedup": await _calculate_arithmetic_speedup(),
            "index_reduction": await _get_index_reduction_stats(),
        }
    )

async def _calculate_insert_performance() -> Dict[str, float]:
    """Calculate INSERT performance metrics."""
    try:
        # Measure actual INSERT performance
        test_data = [
            MarketData(
                timestamp=datetime.utcnow(),
                instrument_id=1,
                price=100.0 + i,
                volume=1000
            ) for i in range(100)
        ]
        
        start_time = datetime.utcnow()
        # Perform bulk insert test
        async with get_db_session() as session:
            session.add_all(test_data)
            await session.commit()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        rate = len(test_data) / duration  # Records per second
        
        # Compare to baseline (stored in configuration)
        baseline_rate = settings.BASELINE_INSERT_RATE or 1000
        improvement_pct = ((rate - baseline_rate) / baseline_rate) * 100
        
        return {
            "rate": rate,
            "improvement_pct": improvement_pct,
            "duration": duration,
        }
    
    except Exception as e:
        logger.error(f"Failed to calculate insert performance: {e}")
        return {"rate": 0.0, "improvement_pct": 0.0, "duration": 0.0}
```

**4.2 Real-time Performance WebSocket**
```python
# src/backend/websocket/database_realtime.py
async def broadcast_database_metrics():
    """Broadcast real-time database performance metrics via WebSocket."""
    
    db_monitor = get_database_monitor()
    metrics = db_monitor.get_metrics()
    
    # Format for frontend consumption
    realtime_data = {
        "message_type": "database_performance",
        "data": {
            "timestamp": datetime.utcnow().isoformat(),
            "connection_pool": metrics["connection_pool"],
            "performance": metrics["performance"],
            "health_status": metrics["health"]["status"],
            "alerts": await _check_performance_alerts(metrics),
        },
        "performance_indicators": {
            "insert_rate_status": _get_insert_rate_status(metrics),
            "connection_health": _get_connection_health_status(metrics),
            "query_performance": _get_query_performance_status(metrics),
        }
    }
    
    # Broadcast to all connected clients
    await websocket_manager.broadcast_message(realtime_data)

async def _check_performance_alerts(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Check for performance alerts based on current metrics."""
    alerts = []
    
    # High connection pool usage alert
    pool_usage = metrics["connection_pool"]["checked_out"] / metrics["connection_pool"]["size"]
    if pool_usage > 0.8:
        alerts.append({
            "type": "warning",
            "message": f"High connection pool usage: {pool_usage:.1%}",
            "recommendation": "Consider increasing pool size or optimizing queries"
        })
    
    # Slow query alert
    if metrics["performance"]["avg_query_time"] > 1.0:
        alerts.append({
            "type": "error", 
            "message": f"Slow queries detected: {metrics['performance']['avg_query_time']:.2f}s avg",
            "recommendation": "Review query performance and index usage"
        })
    
    return alerts
```

### Phase 5: Testing and Validation (Days 13-15)

**5.1 Performance Test Suite**
```python
# tests/performance/test_database_optimization.py
import pytest
import asyncio
import time
from typing import List
from datetime import datetime, timedelta

class TestDatabaseOptimization:
    """Comprehensive performance tests for database optimizations."""
    
    @pytest.mark.asyncio
    async def test_insert_performance_improvement(self):
        """Verify 30-50% INSERT performance improvement."""
        
        # Generate test data
        test_data = self._generate_market_data(1000)
        
        # Measure INSERT performance
        start_time = time.time()
        await self._bulk_insert_market_data(test_data)
        duration = time.time() - start_time
        
        # Calculate inserts per second
        insert_rate = len(test_data) / duration
        
        # Verify performance target (10,000+ inserts/minute = 166+ inserts/second)
        assert insert_rate >= 166, f"INSERT rate {insert_rate:.1f}/sec below target of 166/sec"
        
        # Compare to baseline (if available)
        baseline_rate = 100  # Example baseline
        improvement = ((insert_rate - baseline_rate) / baseline_rate) * 100
        assert improvement >= 30, f"INSERT improvement {improvement:.1f}% below 30% target"
    
    @pytest.mark.asyncio
    async def test_float_calculation_performance(self):
        """Verify 2-3x faster price calculations with FLOAT."""
        
        # Test data with FLOAT values
        prices = [100.25 + i * 0.01 for i in range(10000)]
        
        # Measure calculation performance
        start_time = time.time()
        results = []
        for i in range(len(prices) - 1):
            # Simulate price change calculation
            change = prices[i+1] - prices[i]
            pct_change = (change / prices[i]) * 100
            results.append(pct_change)
        
        calculation_time = time.time() - start_time
        calculations_per_second = len(results) / calculation_time
        
        # Verify performance target (should be significantly faster than DECIMAL)
        expected_baseline = 5000  # Calculations per second baseline
        assert calculations_per_second >= expected_baseline * 2, \
            f"Calculation rate {calculations_per_second:.0f}/sec below 2x improvement target"
    
    @pytest.mark.asyncio
    async def test_index_optimization_effectiveness(self):
        """Test that reduced indexes don't hurt query performance."""
        
        # Test common query patterns with optimized indexes
        instrument_id = 1
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        # Time-series query (uses ix_market_data_timestamp_instrument)
        query_start = time.time()
        time_series_data = await self._query_time_series(instrument_id, start_time, end_time)
        time_series_duration = time.time() - query_start
        
        # Price-based query (uses ix_market_data_instrument_price)
        query_start = time.time()
        price_data = await self._query_price_range(instrument_id, 100.0, 200.0)
        price_query_duration = time.time() - query_start
        
        # Verify query performance maintained
        assert time_series_duration < 0.1, f"Time-series query too slow: {time_series_duration:.3f}s"
        assert price_query_duration < 0.1, f"Price query too slow: {price_query_duration:.3f}s"
        
        # Verify data integrity
        assert len(time_series_data) > 0, "Time-series query returned no data"
        assert len(price_data) >= 0, "Price query failed"
    
    @pytest.mark.asyncio
    async def test_soft_delete_safety(self):
        """Test soft delete mechanism prevents data loss."""
        
        # Create test market data
        test_record = await self._create_test_market_data()
        
        # Perform soft delete
        await self._soft_delete_market_data(test_record.id)
        
        # Verify record is marked as deleted but still exists
        deleted_record = await self._get_market_data_by_id(test_record.id, include_deleted=True)
        assert deleted_record is not None, "Soft deleted record not found"
        assert deleted_record.deleted_at is not None, "Deleted timestamp not set"
        
        # Verify record excluded from normal queries
        active_record = await self._get_market_data_by_id(test_record.id, include_deleted=False)
        assert active_record is None, "Soft deleted record still appears in active queries"
        
        # Test restore functionality
        await self._restore_market_data(test_record.id)
        restored_record = await self._get_market_data_by_id(test_record.id, include_deleted=False)
        assert restored_record is not None, "Restored record not found in active queries"
        assert restored_record.deleted_at is None, "Restored record still has deleted timestamp"
    
    @pytest.mark.asyncio
    async def test_connection_pool_optimization(self):
        """Test optimized connection pool handles high concurrency."""
        
        # Simulate concurrent database operations
        async def concurrent_operation():
            async with get_db_session() as session:
                await session.execute(select(MarketData).limit(10))
                await asyncio.sleep(0.1)  # Simulate processing time
        
        # Run many concurrent operations
        tasks = [concurrent_operation() for _ in range(50)]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify operations complete within reasonable time
        assert total_time < 5.0, f"Concurrent operations too slow: {total_time:.2f}s"
        
        # Check connection pool health
        db_monitor = get_database_monitor()
        metrics = db_monitor.get_metrics()
        
        # Verify no connection pool overflow
        assert metrics["connection_pool"]["overflow"] == 0, \
            f"Connection pool overflow detected: {metrics['connection_pool']['overflow']}"
```

**5.2 Data Migration Validation Tests**
```python
# tests/integration/test_data_migration.py
class TestDataMigration:
    """Tests for safe data migration from DECIMAL to FLOAT."""
    
    @pytest.mark.asyncio
    async def test_decimal_to_float_migration_accuracy(self):
        """Verify DECIMAL to FLOAT migration maintains accuracy."""
        
        # Test precision retention for typical price values
        test_prices = [
            Decimal('123.4567'),  # 4 decimal places
            Decimal('0.0001'),    # Small value
            Decimal('9999.9999'), # Large value
            Decimal('100.25'),    # Typical stock price
        ]
        
        for decimal_price in test_prices:
            # Convert to float and back to verify accuracy
            float_price = float(decimal_price)
            rounded_float = round(float_price, 4)
            
            # Verify accuracy within acceptable tolerance
            difference = abs(float(decimal_price) - rounded_float)
            assert difference < 0.0001, f"Precision loss too high: {difference} for {decimal_price}"
    
    @pytest.mark.asyncio 
    async def test_api_backward_compatibility(self):
        """Test API responses maintain 4-decimal precision."""
        
        # Create test market data with float values
        market_data = MarketData(
            timestamp=datetime.utcnow(),
            instrument_id=1,
            price=123.456789,  # More precision than needed
            bid=123.4567,
            ask=123.4568
        )
        
        # Convert to API response model
        response = MarketDataResponse.model_validate(market_data)
        
        # Verify precision is limited to 4 decimal places
        assert response.price == 123.4568, f"Price precision not rounded: {response.price}"
        assert response.bid == 123.4567, f"Bid precision not rounded: {response.bid}"  
        assert response.ask == 123.4568, f"Ask precision not rounded: {response.ask}"
        
        # Verify JSON serialization maintains precision
        json_data = response.model_dump()
        assert json_data["price"] == 123.4568
        assert json_data["bid"] == 123.4567
        assert json_data["ask"] == 123.4568
```

## Success Criteria and Validation

### Performance Improvements (Target: 30-50% INSERT performance)
- [ ] MarketData INSERT operations show 30-50% performance improvement over baseline
- [ ] Price calculations show 2-3x speed improvement with FLOAT arithmetic
- [ ] Database can handle 10,000+ market data inserts per minute
- [ ] Query response times maintained or improved after index optimization
- [ ] Connection pool optimization shows improved utilization and stability

### Data Safety & Integrity (Zero tolerance for data loss)
- [ ] All CASCADE DELETE relationships replaced with RESTRICT for safety
- [ ] Soft delete mechanism implemented with `deleted_at` columns
- [ ] Zero data loss during DECIMAL to FLOAT migration
- [ ] All existing data accessible and queryable after migration
- [ ] Data validation confirms integrity throughout migration process

### Scalability & Architecture (10x capacity improvement)
- [ ] Time-series partitioning implemented for MarketData and AlertLog tables
- [ ] Automated partition management procedures created and tested
- [ ] Database supports 10x current data volume without performance degradation
- [ ] Long-term data retention strategy established and documented

### Migration & Deployment (Zero downtime requirement)
- [ ] Zero-downtime migration plan executed successfully in production
- [ ] Rollback procedures tested and documented for all changes
- [ ] All database migrations are reversible through migration scripts
- [ ] Production deployment completed without service interruption
- [ ] Post-migration validation confirms all systems operating normally

### Monitoring & Operations (Production readiness)
- [ ] Database performance metrics integrated with existing monitoring system
- [ ] Connection pool health monitoring and alerting configured
- [ ] Query performance baselines established and tracked over time
- [ ] Data integrity monitoring implemented for ongoing validation
- [ ] Documentation updated with new operational procedures

## Implementation Guidelines

### Follow Existing TradeAssist Patterns
- **Code Organization**: Place new files following `src/backend/` structure
- **Naming Conventions**: Use existing patterns for classes, functions, and variables  
- **Error Handling**: Use structured logging with `structlog` for all database operations
- **Testing**: Maintain test coverage with pytest for all new functionality
- **Documentation**: Include Google-style docstrings for all new functions and classes

### Database-Specific Guidelines
- **Migration Safety**: All schema changes must be reversible via migration scripts
- **Transaction Management**: Use async context managers for database sessions
- **Query Optimization**: Leverage SQLAlchemy's `selectinload` for relationship queries
- **Connection Pooling**: Use existing connection pool configuration patterns
- **Monitoring Integration**: Integrate performance metrics with existing health API

### Backward Compatibility Requirements
- **API Responses**: Maintain 4-decimal precision in all API responses
- **Query Patterns**: Existing query logic must continue to work after optimization
- **Service Integration**: All existing services must work with optimized database layer
- **Configuration**: New settings must have sensible defaults

## Completion Checklist

### Pre-Implementation Validation
- [ ] Understanding of current database bottlenecks confirmed through analysis
- [ ] Performance baseline measurements taken for comparison
- [ ] Migration strategy validated in staging environment
- [ ] Rollback procedures documented and tested

### Development Phase Completion
- [ ] All database schema optimizations implemented via migrations
- [ ] Service layer updated to handle FLOAT data types and soft delete
- [ ] Connection pool configuration optimized for high-frequency operations
- [ ] Time-series partitioning system implemented and automated
- [ ] Performance monitoring service integrated with existing health API

### Testing and Validation Complete
- [ ] Performance tests confirm 30-50% INSERT improvement achieved
- [ ] Data migration tests verify zero data loss and accuracy
- [ ] Integration tests confirm all existing functionality preserved
- [ ] Load tests verify system can handle 10,000+ inserts/minute
- [ ] Regression tests confirm no breaking changes introduced

### Production Deployment Ready
- [ ] Zero-downtime migration plan tested and approved
- [ ] Database backup and recovery procedures updated
- [ ] Monitoring dashboards updated with new performance metrics
- [ ] Documentation updated with new operational procedures
- [ ] Performance baselines established for ongoing monitoring

This comprehensive Database Performance & Integrity extension PRP provides complete implementation guidance for optimizing TradeAssist's database layer while maintaining data safety and system reliability. The extension addresses critical performance bottlenecks while establishing a foundation for future scalability and production readiness.