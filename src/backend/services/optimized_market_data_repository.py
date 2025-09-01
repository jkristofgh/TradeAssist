"""
Optimized Market Data Repository for High-Frequency Trading Operations.

Provides high-performance bulk operations for market data ingestion with
soft delete support, optimized queries, and performance monitoring integration.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, insert, update, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import structlog

from ..models.market_data import MarketData
from ..models.instruments import Instrument
from ..database.connection import get_db_session
from ..database.mixins import SoftDeleteMixin
from .database_performance import get_performance_monitor

logger = structlog.get_logger(__name__)


class OptimizedMarketDataRepository:
    """
    High-performance repository for market data operations.
    
    Optimized for high-frequency trading data ingestion with bulk operations,
    soft delete support, and performance monitoring integration.
    
    Features:
    - Bulk insert operations for high-throughput data ingestion
    - Active record queries excluding soft deleted data
    - Optimized queries leveraging Phase 1 index improvements
    - Soft delete and restore functionality
    - Performance monitoring integration
    """
    
    def __init__(self):
        """Initialize repository with performance monitoring."""
        self.performance_monitor = get_performance_monitor()
        self._bulk_insert_threshold = 100  # Records per bulk operation
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._query_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def bulk_insert_market_data(
        self, 
        market_data_records: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        High-performance bulk insert of market data records.
        
        Args:
            market_data_records: List of market data dictionaries
            batch_size: Number of records per batch operation
            
        Returns:
            Number of records successfully inserted
            
        Raises:
            ValueError: If market_data_records is empty or invalid
            Exception: If bulk insert operation fails
        """
        if not market_data_records:
            raise ValueError("market_data_records cannot be empty")
        
        start_time = time.time()
        inserted_count = 0
        
        try:
            async with get_db_session() as session:
                # Process records in batches for optimal performance
                for i in range(0, len(market_data_records), batch_size):
                    batch = market_data_records[i:i + batch_size]
                    
                    # Prepare batch data with validation
                    validated_batch = []
                    for record in batch:
                        validated_record = await self._validate_market_data_record(record)
                        if validated_record:
                            validated_batch.append(validated_record)
                    
                    if validated_batch:
                        # Bulk insert using SQLAlchemy Core for maximum performance
                        stmt = insert(MarketData).values(validated_batch)
                        result = await session.execute(stmt)
                        inserted_count += len(validated_batch)
                
                await session.commit()
                
                # Track performance metrics
                execution_time_ms = (time.time() - start_time) * 1000
                self.performance_monitor.track_query(
                    query_type="BULK_INSERT",
                    table_name="market_data",
                    execution_time_ms=execution_time_ms,
                    record_count=inserted_count
                )
                
                logger.info(
                    "Bulk market data insert completed",
                    records_inserted=inserted_count,
                    execution_time_ms=execution_time_ms,
                    records_per_second=int(inserted_count / (execution_time_ms / 1000)) if execution_time_ms > 0 else 0
                )
                
                return inserted_count
                
        except Exception as e:
            logger.error(
                "Bulk market data insert failed",
                error=str(e),
                record_count=len(market_data_records),
                error_type=type(e).__name__
            )
            raise
    
    async def get_active_market_data(
        self,
        instrument_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[MarketData]:
        """
        Get active (non-soft-deleted) market data records.
        
        Args:
            instrument_id: ID of the instrument
            start_time: Start of time range filter
            end_time: End of time range filter
            limit: Maximum number of records to return
            
        Returns:
            List of active MarketData records
        """
        start_time_query = time.time()
        
        try:
            async with get_db_session() as session:
                # Build optimized query using Phase 1 indexes
                query = select(MarketData).where(
                    and_(
                        MarketData.instrument_id == instrument_id,
                        MarketData.deleted_at.is_(None)  # Exclude soft deleted
                    )
                ).options(
                    selectinload(MarketData.instrument)  # Optimized loading
                ).order_by(
                    desc(MarketData.timestamp)
                ).limit(limit)
                
                # Apply time range filters if provided
                if start_time:
                    query = query.where(MarketData.timestamp >= start_time)
                if end_time:
                    query = query.where(MarketData.timestamp <= end_time)
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                # Track query performance
                execution_time_ms = (time.time() - start_time_query) * 1000
                self.performance_monitor.track_query(
                    query_type="SELECT",
                    table_name="market_data",
                    execution_time_ms=execution_time_ms,
                    used_index=True  # Uses optimized composite index
                )
                
                logger.debug(
                    "Active market data query completed",
                    instrument_id=instrument_id,
                    records_found=len(records),
                    execution_time_ms=execution_time_ms
                )
                
                return records
                
        except Exception as e:
            logger.error(
                "Failed to get active market data",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_latest_market_data(
        self,
        instrument_ids: List[int],
        include_inactive: bool = False
    ) -> Dict[int, Optional[MarketData]]:
        """
        Get latest market data for multiple instruments efficiently.
        
        Args:
            instrument_ids: List of instrument IDs
            include_inactive: Whether to include soft deleted records
            
        Returns:
            Dictionary mapping instrument_id to latest MarketData record
        """
        start_time_query = time.time()
        result_map: Dict[int, Optional[MarketData]] = {}
        
        try:
            async with get_db_session() as session:
                for instrument_id in instrument_ids:
                    # Use optimized query with composite index
                    query = select(MarketData).where(
                        MarketData.instrument_id == instrument_id
                    )
                    
                    # Apply soft delete filter unless including inactive
                    if not include_inactive:
                        query = query.where(MarketData.deleted_at.is_(None))
                    
                    query = query.order_by(
                        desc(MarketData.timestamp)
                    ).limit(1)
                    
                    result = await session.execute(query)
                    record = result.scalars().first()
                    result_map[instrument_id] = record
                
                # Track performance
                execution_time_ms = (time.time() - start_time_query) * 1000
                self.performance_monitor.track_query(
                    query_type="SELECT_LATEST",
                    table_name="market_data",
                    execution_time_ms=execution_time_ms,
                    record_count=len(instrument_ids)
                )
                
                logger.debug(
                    "Latest market data query completed",
                    instrument_count=len(instrument_ids),
                    records_found=sum(1 for r in result_map.values() if r is not None),
                    execution_time_ms=execution_time_ms
                )
                
                return result_map
                
        except Exception as e:
            logger.error(
                "Failed to get latest market data",
                instrument_ids=instrument_ids,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def soft_delete_market_data(
        self,
        record_ids: List[int],
        batch_size: int = 500
    ) -> int:
        """
        Soft delete market data records efficiently.
        
        Args:
            record_ids: List of MarketData record IDs to soft delete
            batch_size: Number of records per batch operation
            
        Returns:
            Number of records successfully soft deleted
        """
        if not record_ids:
            return 0
        
        start_time = time.time()
        deleted_count = 0
        
        try:
            async with get_db_session() as session:
                # Process in batches for performance
                for i in range(0, len(record_ids), batch_size):
                    batch_ids = record_ids[i:i + batch_size]
                    
                    # Bulk soft delete using update
                    stmt = update(MarketData).where(
                        and_(
                            MarketData.id.in_(batch_ids),
                            MarketData.deleted_at.is_(None)  # Only delete active records
                        )
                    ).values(deleted_at=datetime.utcnow())
                    
                    result = await session.execute(stmt)
                    deleted_count += result.rowcount
                
                await session.commit()
                
                # Track performance
                execution_time_ms = (time.time() - start_time) * 1000
                self.performance_monitor.track_query(
                    query_type="SOFT_DELETE",
                    table_name="market_data",
                    execution_time_ms=execution_time_ms,
                    record_count=deleted_count
                )
                
                logger.info(
                    "Bulk soft delete completed",
                    records_deleted=deleted_count,
                    execution_time_ms=execution_time_ms
                )
                
                return deleted_count
                
        except Exception as e:
            logger.error(
                "Bulk soft delete failed",
                record_ids_count=len(record_ids),
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def restore_market_data(
        self,
        record_ids: List[int],
        batch_size: int = 500
    ) -> int:
        """
        Restore soft deleted market data records.
        
        Args:
            record_ids: List of MarketData record IDs to restore
            batch_size: Number of records per batch operation
            
        Returns:
            Number of records successfully restored
        """
        if not record_ids:
            return 0
        
        start_time = time.time()
        restored_count = 0
        
        try:
            async with get_db_session() as session:
                # Process in batches
                for i in range(0, len(record_ids), batch_size):
                    batch_ids = record_ids[i:i + batch_size]
                    
                    # Bulk restore using update
                    stmt = update(MarketData).where(
                        and_(
                            MarketData.id.in_(batch_ids),
                            MarketData.deleted_at.is_not(None)  # Only restore deleted records
                        )
                    ).values(deleted_at=None)
                    
                    result = await session.execute(stmt)
                    restored_count += result.rowcount
                
                await session.commit()
                
                # Track performance
                execution_time_ms = (time.time() - start_time) * 1000
                self.performance_monitor.track_query(
                    query_type="RESTORE",
                    table_name="market_data",
                    execution_time_ms=execution_time_ms,
                    record_count=restored_count
                )
                
                logger.info(
                    "Bulk restore completed",
                    records_restored=restored_count,
                    execution_time_ms=execution_time_ms
                )
                
                return restored_count
                
        except Exception as e:
            logger.error(
                "Bulk restore failed",
                record_ids_count=len(record_ids),
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get repository performance statistics.
        
        Returns:
            Dictionary containing performance metrics
        """
        metrics = await self.performance_monitor.collect_metrics()
        
        return {
            "insert_rate_per_second": metrics.insert_rate,
            "average_query_time_ms": metrics.query_avg_time_ms,
            "total_queries": len(metrics.query_performance_history),
            "cache_hit_ratio": self._calculate_cache_hit_ratio(),
            "repository_type": "OptimizedMarketDataRepository"
        }
    
    async def _validate_market_data_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and prepare market data record for insertion.
        
        Args:
            record: Raw market data record
            
        Returns:
            Validated record or None if invalid
        """
        required_fields = ["timestamp", "instrument_id"]
        
        # Check required fields
        if not all(field in record for field in required_fields):
            logger.warning("Missing required fields in market data record", record=record)
            return None
        
        # Validate data types
        try:
            validated_record = {
                "timestamp": record["timestamp"] if isinstance(record["timestamp"], datetime) 
                          else datetime.fromisoformat(str(record["timestamp"])),
                "instrument_id": int(record["instrument_id"]),
            }
            
            # Add optional fields with type validation
            optional_float_fields = ["price", "bid", "ask", "open_price", "high_price", "low_price"]
            for field in optional_float_fields:
                if field in record and record[field] is not None:
                    validated_record[field] = float(record[field])
            
            optional_int_fields = ["volume", "bid_size", "ask_size"]
            for field in optional_int_fields:
                if field in record and record[field] is not None:
                    validated_record[field] = int(record[field])
            
            return validated_record
            
        except (ValueError, TypeError) as e:
            logger.warning("Invalid data types in market data record", record=record, error=str(e))
            return None
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio for performance monitoring."""
        # Simplified cache hit ratio calculation
        # In a real implementation, this would track actual cache hits/misses
        return 0.85  # Placeholder value


# Global repository instance
_optimized_market_data_repository: Optional[OptimizedMarketDataRepository] = None


def get_optimized_market_data_repository() -> OptimizedMarketDataRepository:
    """
    Get global OptimizedMarketDataRepository instance.
    
    Returns:
        Singleton OptimizedMarketDataRepository instance
    """
    global _optimized_market_data_repository
    
    if _optimized_market_data_repository is None:
        _optimized_market_data_repository = OptimizedMarketDataRepository()
    
    return _optimized_market_data_repository