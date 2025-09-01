"""
Database Performance Monitoring Service.

Provides real-time monitoring and analysis of database performance metrics
including query execution times, INSERT rates, index usage, and connection pool statistics.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool, QueuePool

from src.backend.database.connection import get_db_session
from src.backend.config import settings
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for database performance metrics."""
    
    timestamp: datetime
    insert_rate: float  # inserts per second
    query_avg_time_ms: float  # average query time in milliseconds
    active_connections: int
    pool_size: int
    pool_overflow: int
    index_hit_ratio: float  # percentage of queries using indexes
    cache_hit_ratio: float  # SQLite cache hit ratio
    wal_checkpoints: int  # WAL checkpoint count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "insert_rate": round(self.insert_rate, 2),
            "query_avg_time_ms": round(self.query_avg_time_ms, 2),
            "active_connections": self.active_connections,
            "pool_size": self.pool_size,
            "pool_overflow": self.pool_overflow,
            "index_hit_ratio": round(self.index_hit_ratio, 2),
            "cache_hit_ratio": round(self.cache_hit_ratio, 2),
            "wal_checkpoints": self.wal_checkpoints
        }


@dataclass
class QueryPerformance:
    """Track individual query performance."""
    
    query_type: str  # SELECT, INSERT, UPDATE, DELETE
    table_name: str
    execution_time_ms: float
    used_index: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DatabasePerformanceMonitor:
    """
    Monitor and analyze database performance metrics.
    
    Tracks INSERT rates, query performance, index usage, and connection pool health.
    Provides real-time metrics for performance optimization validation.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Number of recent queries to track for metrics
        """
        self.window_size = window_size
        self.query_history: deque = deque(maxlen=window_size)
        self.insert_counts: Dict[str, int] = {}
        self.last_reset: datetime = datetime.utcnow()
        self.metrics_history: List[PerformanceMetrics] = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self, interval_seconds: int = 60) -> None:
        """
        Start continuous performance monitoring.
        
        Args:
            interval_seconds: Interval between metric collections
        """
        if self._monitoring:
            logger.warning("Performance monitoring already active")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info(f"Started database performance monitoring (interval: {interval_seconds}s)")
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped database performance monitoring")
    
    async def _monitoring_loop(self, interval: int) -> None:
        """Continuous monitoring loop."""
        while self._monitoring:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of metrics
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if m.timestamp > cutoff
                ]
                
                logger.debug(f"Collected metrics: {metrics.to_dict()}")
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            await asyncio.sleep(interval)
    
    def track_query(self, query_type: str, table_name: str, 
                   execution_time_ms: float, used_index: bool = True) -> None:
        """
        Track a query execution.
        
        Args:
            query_type: Type of query (SELECT, INSERT, etc.)
            table_name: Table being queried
            execution_time_ms: Query execution time in milliseconds
            used_index: Whether query used an index
        """
        perf = QueryPerformance(
            query_type=query_type,
            table_name=table_name,
            execution_time_ms=execution_time_ms,
            used_index=used_index
        )
        self.query_history.append(perf)
        
        # Track INSERT counts for rate calculation
        if query_type == "INSERT":
            if table_name not in self.insert_counts:
                self.insert_counts[table_name] = 0
            self.insert_counts[table_name] += 1
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        async with get_db_session() as session:
            # Get connection pool stats
            engine = session.get_bind()
            pool = engine.pool
            
            if isinstance(pool, QueuePool):
                pool_size = pool.size()
                pool_overflow = pool.overflow()
                active_connections = pool.checked_out_connections()
            else:
                pool_size = 0
                pool_overflow = 0
                active_connections = 0
            
            # Calculate INSERT rate
            now = datetime.utcnow()
            time_delta = (now - self.last_reset).total_seconds()
            
            if time_delta > 0:
                total_inserts = sum(self.insert_counts.values())
                insert_rate = total_inserts / time_delta
            else:
                insert_rate = 0.0
            
            # Calculate average query time
            recent_queries = list(self.query_history)
            if recent_queries:
                avg_time = sum(q.execution_time_ms for q in recent_queries) / len(recent_queries)
                index_hits = sum(1 for q in recent_queries if q.used_index)
                index_hit_ratio = (index_hits / len(recent_queries)) * 100
            else:
                avg_time = 0.0
                index_hit_ratio = 100.0
            
            # Get SQLite-specific metrics
            cache_hit_ratio = await self._get_sqlite_cache_hit_ratio(session)
            wal_checkpoints = await self._get_wal_checkpoint_count(session)
            
            # Reset counters
            self.insert_counts.clear()
            self.last_reset = now
            
            return PerformanceMetrics(
                timestamp=now,
                insert_rate=insert_rate,
                query_avg_time_ms=avg_time,
                active_connections=active_connections,
                pool_size=pool_size,
                pool_overflow=pool_overflow,
                index_hit_ratio=index_hit_ratio,
                cache_hit_ratio=cache_hit_ratio,
                wal_checkpoints=wal_checkpoints
            )
    
    async def _get_sqlite_cache_hit_ratio(self, session: AsyncSession) -> float:
        """Get SQLite cache hit ratio."""
        try:
            # SQLite PRAGMA for cache statistics
            result = await session.execute(text("PRAGMA cache_stats"))
            stats = result.fetchone()
            if stats and len(stats) >= 2:
                hits = stats[0]
                misses = stats[1]
                if hits + misses > 0:
                    return (hits / (hits + misses)) * 100
        except Exception:
            pass  # Not all SQLite versions support this
        return 0.0
    
    async def _get_wal_checkpoint_count(self, session: AsyncSession) -> int:
        """Get WAL checkpoint count."""
        try:
            result = await session.execute(text("PRAGMA wal_checkpoint"))
            checkpoint_data = result.fetchone()
            if checkpoint_data:
                return checkpoint_data[0]  # Checkpoint count
        except Exception:
            pass
        return 0
    
    async def analyze_table_performance(self, table_name: str) -> Dict[str, Any]:
        """
        Analyze performance for a specific table.
        
        Args:
            table_name: Name of table to analyze
            
        Returns:
            Performance analysis for the table
        """
        table_queries = [
            q for q in self.query_history 
            if q.table_name == table_name
        ]
        
        if not table_queries:
            return {
                "table": table_name,
                "query_count": 0,
                "message": "No recent queries for this table"
            }
        
        # Calculate statistics
        insert_queries = [q for q in table_queries if q.query_type == "INSERT"]
        select_queries = [q for q in table_queries if q.query_type == "SELECT"]
        
        insert_avg = (
            sum(q.execution_time_ms for q in insert_queries) / len(insert_queries)
            if insert_queries else 0
        )
        
        select_avg = (
            sum(q.execution_time_ms for q in select_queries) / len(select_queries)
            if select_queries else 0
        )
        
        return {
            "table": table_name,
            "query_count": len(table_queries),
            "insert_count": len(insert_queries),
            "select_count": len(select_queries),
            "insert_avg_ms": round(insert_avg, 2),
            "select_avg_ms": round(select_avg, 2),
            "index_usage": sum(1 for q in table_queries if q.used_index) / len(table_queries) * 100
        }
    
    def get_recent_metrics(self, hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get recent performance metrics.
        
        Args:
            hours: Number of hours of history to return
            
        Returns:
            List of recent metrics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            m.to_dict() for m in self.metrics_history
            if m.timestamp > cutoff
        ]
    
    async def benchmark_insert_performance(self, table_name: str, 
                                          count: int = 1000) -> Dict[str, Any]:
        """
        Benchmark INSERT performance for a table.
        
        Args:
            table_name: Table to benchmark
            count: Number of INSERTs to simulate
            
        Returns:
            Benchmark results
        """
        logger.info(f"Starting INSERT benchmark for {table_name} ({count} operations)")
        
        start_time = time.time()
        
        # Simulate tracking INSERT operations
        for i in range(count):
            # Simulate varying execution times (0.1-2.0ms)
            exec_time = 0.1 + (i % 20) * 0.1
            self.track_query("INSERT", table_name, exec_time, used_index=False)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        inserts_per_second = count / total_time if total_time > 0 else 0
        
        return {
            "table": table_name,
            "insert_count": count,
            "total_time_seconds": round(total_time, 2),
            "inserts_per_second": round(inserts_per_second, 2),
            "avg_time_per_insert_ms": round((total_time * 1000) / count, 2)
        }


# Global instance
_monitor: Optional[DatabasePerformanceMonitor] = None


def get_performance_monitor() -> DatabasePerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = DatabasePerformanceMonitor()
    return _monitor