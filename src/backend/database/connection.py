"""
Database connection and session management.

Provides SQLite database setup with WAL mode for optimal time-series
performance and async session management for the FastAPI application.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.engine import Engine

from ..config import settings, ensure_data_directory
from ..models.base import Base

logger = structlog.get_logger()

# Global engine and session maker
engine = None
async_session_maker = None


def configure_sqlite_wal(dbapi_connection, connection_record) -> None:
    """
    Configure SQLite for optimal performance with WAL mode.
    
    Args:
        dbapi_connection: Database connection.
        connection_record: Connection record.
    """
    cursor = dbapi_connection.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # Optimize for time-series workload
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed
    cursor.execute("PRAGMA cache_size=10000")    # 10MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")   # Temp tables in memory
    cursor.execute("PRAGMA mmap_size=268435456") # 256MB memory map
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Optimize checkpoint behavior
    cursor.execute("PRAGMA wal_autocheckpoint=1000")
    
    cursor.close()


async def init_database() -> None:
    """
    Initialize database connection and create tables.
    
    Sets up the SQLite database with WAL mode and creates all tables
    according to the defined models.
    """
    global engine, async_session_maker
    
    logger.info("Initializing database connection")
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Create async engine with SQLite optimizations
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={
            "check_same_thread": False,  # Required for async SQLite
        },
        pool_pre_ping=True,  # Verify connections before use
    )
    
    # Configure SQLite WAL mode
    event.listen(engine.sync_engine, "connect", configure_sqlite_wal)
    
    # Create session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,  # Manual control for performance
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize default instruments
    await _initialize_default_instruments()
    
    logger.info("Database initialized successfully")


async def close_database() -> None:
    """
    Close database connections and cleanup.
    """
    global engine
    
    if engine:
        logger.info("Closing database connections")
        await engine.dispose()
        logger.info("Database connections closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with automatic cleanup.
    
    Yields:
        AsyncSession: Database session for operations.
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _initialize_default_instruments() -> None:
    """
    Initialize default instruments in the database.
    
    Creates instrument records for all target futures, indices,
    and market internals as specified in configuration.
    """
    from ..models.instruments import Instrument, InstrumentType
    
    # Define instrument metadata
    instrument_definitions = [
        # Futures
        ("ES", "E-mini S&P 500", InstrumentType.FUTURE),
        ("NQ", "E-mini Nasdaq-100", InstrumentType.FUTURE),
        ("YM", "E-mini Dow Jones", InstrumentType.FUTURE),
        ("CL", "Crude Oil", InstrumentType.FUTURE),
        ("GC", "Gold", InstrumentType.FUTURE),
        
        # Indices
        ("SPX", "S&P 500 Index", InstrumentType.INDEX),
        ("NDX", "Nasdaq-100 Index", InstrumentType.INDEX),
        ("RUT", "Russell 2000 Index", InstrumentType.INDEX),
        
        # Market Internals
        ("VIX", "CBOE Volatility Index", InstrumentType.INTERNAL),
        ("TICK", "NYSE TICK", InstrumentType.INTERNAL),
        ("ADD", "NYSE Advancing-Declining Issues", InstrumentType.INTERNAL),
        ("TRIN", "Arms Index (TRIN)", InstrumentType.INTERNAL),
    ]
    
    async with get_db_session() as session:
        # Check if instruments already exist
        from sqlalchemy import select
        result = await session.execute(select(Instrument))
        existing_instruments = result.scalars().all()
        
        if existing_instruments:
            logger.info(f"Found {len(existing_instruments)} existing instruments, skipping initialization")
            return
        
        # Create instrument records
        instruments = []
        for symbol, name, instrument_type in instrument_definitions:
            instrument = Instrument(
                symbol=symbol,
                name=name,
                type=instrument_type,
            )
            instruments.append(instrument)
            session.add(instrument)
        
        await session.commit()
        logger.info(f"Initialized {len(instruments)} default instruments")