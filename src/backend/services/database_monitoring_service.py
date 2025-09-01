"""
Database Monitoring Service for Connection Pool Health and Performance Tracking.

Provides comprehensive monitoring of database connection pool health, query performance,
and high-frequency trading operation metrics with real-time alerting capabilities.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
import psutil
import threading

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import Pool

import structlog

from ..database.connection import get_db_session, engine
from ..config import settings
from .database_performance import get_performance_monitor, PerformanceMetrics

logger = structlog.get_logger(__name__)


@dataclass
class PartitionMetrics:
    """Metrics for a single partition."""
    
    partition_name: str
    table_name: str
    partition_type: str  # 'monthly' or 'quarterly'
    start_date: str
    end_date: str
    row_count: int = 0
    size_mb: float = 0.0
    last_insert: Optional[datetime] = None
    last_query: Optional[datetime] = None
    query_count_24h: int = 0
    insert_count_24h: int = 0
    health_status: str = "healthy"  # healthy, warning, critical
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PartitionHealthMetrics:
    """Overall partition health metrics."""
    
    total_partitions: int = 0
    active_partitions: int = 0
    partitions_by_table: Dict[str, int] = field(default_factory=dict)
    partition_metrics: List[PartitionMetrics] = field(default_factory=list)
    
    # Aggregated statistics
    total_partitioned_rows: int = 0
    total_partitioned_size_mb: float = 0.0
    oldest_partition_date: Optional[str] = None
    newest_partition_date: Optional[str] = None
    
    # Health indicators
    partitions_needing_attention: List[str] = field(default_factory=list)
    partition_alerts: List[str] = field(default_factory=list)
    
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConnectionPoolMetrics:
    """Connection pool health metrics."""
    
    # Pool size metrics
    pool_size: int = 0
    checked_in_connections: int = 0
    checked_out_connections: int = 0
    overflow_connections: int = 0
    
    # Pool configuration
    max_pool_size: int = 0
    max_overflow: int = 0
    
    # Health indicators
    pool_utilization_percent: float = 0.0
    connection_errors: int = 0
    connection_timeouts: int = 0
    
    # Performance metrics
    avg_connection_acquire_time_ms: float = 0.0
    connection_acquire_rate: float = 0.0
    
    # Timestamp
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DatabaseHealthMetrics:
    """Overall database health metrics."""
    
    # Connection metrics
    connection_pool_metrics: ConnectionPoolMetrics
    
    # Query performance
    performance_metrics: PerformanceMetrics
    
    # Partition health (Phase 3)
    partition_health_metrics: Optional[PartitionHealthMetrics] = None
    
    # System resources
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_read_mb_per_sec: float = 0.0
    disk_io_write_mb_per_sec: float = 0.0
    
    # Database-specific metrics
    database_size_mb: float = 0.0
    active_connections: int = 0
    
    # Health status
    overall_status: str = "unknown"  # healthy, warning, critical
    alerts: List[str] = field(default_factory=list)
    
    # Timestamp
    collected_at: datetime = field(default_factory=datetime.utcnow)


class DatabaseMonitoringService:
    """
    Comprehensive database monitoring service.
    
    Monitors connection pool health, query performance, and system resources
    for high-frequency trading operations with configurable alerting.
    
    Features:
    - Real-time connection pool monitoring
    - Query performance tracking
    - System resource monitoring
    - Configurable alert thresholds
    - Background monitoring loop
    - Historical metrics collection
    """
    
    def __init__(self):
        """Initialize monitoring service."""
        self.is_running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self._performance_monitor = get_performance_monitor()
        
        # Configurable thresholds
        self.thresholds = {
            "pool_utilization_warning": 70.0,  # %
            "pool_utilization_critical": 85.0,  # %
            "avg_query_time_warning": 100.0,  # ms
            "avg_query_time_critical": 500.0,  # ms
            "connection_acquire_time_warning": 50.0,  # ms
            "connection_acquire_time_critical": 200.0,  # ms
            "cpu_usage_warning": 70.0,  # %
            "cpu_usage_critical": 85.0,  # %
            "memory_usage_warning": 1024.0,  # MB
            "memory_usage_critical": 2048.0,  # MB
        }
        
        # Metrics collection
        self._connection_acquire_times: deque = deque(maxlen=100)
        self._connection_acquire_count = 0
        self._last_acquire_time = time.time()
        
        # Alert callbacks
        self._alert_callbacks: List[Callable[[str, str], None]] = []
        
        logger.info("DatabaseMonitoringService initialized")
    
    async def start_monitoring(self, interval_seconds: int = 30) -> None:
        """
        Start background monitoring loop.
        
        Args:
            interval_seconds: Monitoring interval in seconds
        """
        if self.is_running:
            logger.warning("Monitoring service already running")
            return
        
        self.is_running = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        
        logger.info(
            "Database monitoring started",
            interval_seconds=interval_seconds
        )
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring loop."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Database monitoring stopped")
    
    async def collect_health_metrics(self) -> DatabaseHealthMetrics:
        """
        Collect comprehensive database health metrics.
        
        Returns:
            DatabaseHealthMetrics with current system status
        """
        start_time = time.time()
        
        try:
            # Collect connection pool metrics
            pool_metrics = await self._collect_connection_pool_metrics()
            
            # Collect performance metrics
            performance_metrics = await self._performance_monitor.collect_metrics()
            
            # Collect system resource metrics
            system_metrics = self._collect_system_metrics()
            
            # Collect database-specific metrics
            db_metrics = await self._collect_database_metrics()
            
            # Collect partition health metrics (Phase 3)
            partition_metrics = await self.collect_partition_health_metrics()
            
            # Combine all metrics
            health_metrics = DatabaseHealthMetrics(
                connection_pool_metrics=pool_metrics,
                performance_metrics=performance_metrics,
                partition_health_metrics=partition_metrics,
                cpu_usage_percent=system_metrics["cpu_usage_percent"],
                memory_usage_mb=system_metrics["memory_usage_mb"],
                disk_io_read_mb_per_sec=system_metrics["disk_io_read_mb_per_sec"],
                disk_io_write_mb_per_sec=system_metrics["disk_io_write_mb_per_sec"],
                database_size_mb=db_metrics["database_size_mb"],
                active_connections=db_metrics["active_connections"]
            )
            
            # Analyze health status and generate alerts
            health_metrics.overall_status, health_metrics.alerts = self._analyze_health_status(health_metrics)
            
            # Store in history
            self._metrics_history.append(health_metrics)
            
            collection_time_ms = (time.time() - start_time) * 1000
            
            logger.debug(
                "Health metrics collected",
                collection_time_ms=collection_time_ms,
                overall_status=health_metrics.overall_status,
                alert_count=len(health_metrics.alerts)
            )
            
            return health_metrics
            
        except Exception as e:
            logger.error(
                "Failed to collect health metrics",
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Return minimal metrics on error
            return DatabaseHealthMetrics(
                connection_pool_metrics=ConnectionPoolMetrics(),
                performance_metrics=PerformanceMetrics(),
                overall_status="critical",
                alerts=[f"Metrics collection failed: {str(e)}"]
            )
    
    async def _collect_connection_pool_metrics(self) -> ConnectionPoolMetrics:
        """Collect connection pool health metrics."""
        try:
            # Get pool from engine
            pool = engine.pool
            
            # Collect basic pool metrics
            metrics = ConnectionPoolMetrics(
                pool_size=pool.size(),
                checked_in_connections=pool.checkedin(),
                checked_out_connections=pool.checkedout(),
                overflow_connections=pool.overflow(),
                max_pool_size=getattr(pool, '_pool_size', 0),
                max_overflow=getattr(pool, '_max_overflow', 0)
            )
            
            # Calculate utilization
            total_capacity = metrics.max_pool_size + metrics.max_overflow
            if total_capacity > 0:
                used_connections = metrics.checked_out_connections + metrics.overflow_connections
                metrics.pool_utilization_percent = (used_connections / total_capacity) * 100
            
            # Calculate connection acquire metrics
            if self._connection_acquire_times:
                metrics.avg_connection_acquire_time_ms = sum(self._connection_acquire_times) / len(self._connection_acquire_times)
            
            # Calculate acquire rate
            current_time = time.time()
            time_diff = current_time - self._last_acquire_time
            if time_diff > 0:
                metrics.connection_acquire_rate = self._connection_acquire_count / time_diff
                # Reset counters
                self._connection_acquire_count = 0
                self._last_acquire_time = current_time
            
            return metrics
            
        except Exception as e:
            logger.error(
                "Failed to collect connection pool metrics",
                error=str(e),
                error_type=type(e).__name__
            )
            return ConnectionPoolMetrics()
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_mb = (memory.total - memory.available) / (1024 * 1024)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            # Calculate per-second rates (simplified)
            disk_read_mb_per_sec = (disk_io.read_bytes if disk_io else 0) / (1024 * 1024) / 60  # Rough estimate
            disk_write_mb_per_sec = (disk_io.write_bytes if disk_io else 0) / (1024 * 1024) / 60
            
            return {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_mb": memory_usage_mb,
                "disk_io_read_mb_per_sec": disk_read_mb_per_sec,
                "disk_io_write_mb_per_sec": disk_write_mb_per_sec
            }
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            return {
                "cpu_usage_percent": 0.0,
                "memory_usage_mb": 0.0,
                "disk_io_read_mb_per_sec": 0.0,
                "disk_io_write_mb_per_sec": 0.0
            }
    
    async def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database-specific metrics."""
        try:
            async with get_db_session() as session:
                # Get database size (SQLite-specific)
                result = await session.execute(
                    text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                )
                db_size_bytes = result.scalar() or 0
                db_size_mb = db_size_bytes / (1024 * 1024)
                
                # Get connection count (approximate for SQLite)
                # SQLite doesn't have true concurrent connections like PostgreSQL
                active_connections = 1  # SQLite is single-writer
                
                return {
                    "database_size_mb": db_size_mb,
                    "active_connections": active_connections
                }
                
        except Exception as e:
            logger.error("Failed to collect database metrics", error=str(e))
            return {
                "database_size_mb": 0.0,
                "active_connections": 0
            }
    
    def _analyze_health_status(self, metrics: DatabaseHealthMetrics) -> tuple[str, List[str]]:
        """
        Analyze health metrics and determine status with alerts.
        
        Returns:
            Tuple of (status, alerts)
        """
        alerts = []
        critical_count = 0
        warning_count = 0
        
        # Check pool utilization
        pool_util = metrics.connection_pool_metrics.pool_utilization_percent
        if pool_util >= self.thresholds["pool_utilization_critical"]:
            alerts.append(f"CRITICAL: Connection pool utilization at {pool_util:.1f}%")
            critical_count += 1
        elif pool_util >= self.thresholds["pool_utilization_warning"]:
            alerts.append(f"WARNING: Connection pool utilization at {pool_util:.1f}%")
            warning_count += 1
        
        # Check query performance
        avg_query_time = metrics.performance_metrics.query_avg_time_ms
        if avg_query_time >= self.thresholds["avg_query_time_critical"]:
            alerts.append(f"CRITICAL: Average query time at {avg_query_time:.1f}ms")
            critical_count += 1
        elif avg_query_time >= self.thresholds["avg_query_time_warning"]:
            alerts.append(f"WARNING: Average query time at {avg_query_time:.1f}ms")
            warning_count += 1
        
        # Check connection acquire time
        acquire_time = metrics.connection_pool_metrics.avg_connection_acquire_time_ms
        if acquire_time >= self.thresholds["connection_acquire_time_critical"]:
            alerts.append(f"CRITICAL: Connection acquire time at {acquire_time:.1f}ms")
            critical_count += 1
        elif acquire_time >= self.thresholds["connection_acquire_time_warning"]:
            alerts.append(f"WARNING: Connection acquire time at {acquire_time:.1f}ms")
            warning_count += 1
        
        # Check system resources
        cpu_usage = metrics.cpu_usage_percent
        if cpu_usage >= self.thresholds["cpu_usage_critical"]:
            alerts.append(f"CRITICAL: CPU usage at {cpu_usage:.1f}%")
            critical_count += 1
        elif cpu_usage >= self.thresholds["cpu_usage_warning"]:
            alerts.append(f"WARNING: CPU usage at {cpu_usage:.1f}%")
            warning_count += 1
        
        memory_usage = metrics.memory_usage_mb
        if memory_usage >= self.thresholds["memory_usage_critical"]:
            alerts.append(f"CRITICAL: Memory usage at {memory_usage:.1f}MB")
            critical_count += 1
        elif memory_usage >= self.thresholds["memory_usage_warning"]:
            alerts.append(f"WARNING: Memory usage at {memory_usage:.1f}MB")
            warning_count += 1
        
        # Determine overall status
        if critical_count > 0:
            status = "critical"
        elif warning_count > 0:
            status = "warning"
        else:
            status = "healthy"
        
        return status, alerts
    
    async def collect_partition_health_metrics(self) -> PartitionHealthMetrics:
        """
        Collect partition health metrics.
        
        Returns:
            PartitionHealthMetrics containing current partition status
        """
        try:
            partition_metrics = []
            partitions_by_table = {}
            total_rows = 0
            total_size = 0.0
            oldest_date = None
            newest_date = None
            needing_attention = []
            alerts = []
            
            async with get_db_session() as session:
                # Find all partition tables
                partition_tables = await self._discover_partition_tables(session)
                
                for table_info in partition_tables:
                    partition_name = table_info['name']
                    base_table = table_info['base_table']
                    partition_type = table_info['type']
                    
                    # Collect metrics for this partition
                    metrics = await self._collect_single_partition_metrics(
                        session, partition_name, base_table, partition_type
                    )
                    
                    if metrics:
                        partition_metrics.append(metrics)
                        
                        # Update aggregates
                        total_rows += metrics.row_count
                        total_size += metrics.size_mb
                        
                        # Track by table
                        if base_table not in partitions_by_table:
                            partitions_by_table[base_table] = 0
                        partitions_by_table[base_table] += 1
                        
                        # Track date ranges
                        if oldest_date is None or metrics.start_date < oldest_date:
                            oldest_date = metrics.start_date
                        if newest_date is None or metrics.end_date > newest_date:
                            newest_date = metrics.end_date
                        
                        # Check for issues
                        if metrics.health_status != "healthy":
                            needing_attention.append(partition_name)
                            alerts.append(f"Partition {partition_name} status: {metrics.health_status}")
            
            return PartitionHealthMetrics(
                total_partitions=len(partition_metrics),
                active_partitions=len([m for m in partition_metrics if m.health_status == "healthy"]),
                partitions_by_table=partitions_by_table,
                partition_metrics=partition_metrics,
                total_partitioned_rows=total_rows,
                total_partitioned_size_mb=total_size,
                oldest_partition_date=oldest_date,
                newest_partition_date=newest_date,
                partitions_needing_attention=needing_attention,
                partition_alerts=alerts
            )
            
        except Exception as e:
            logger.error("Failed to collect partition health metrics", error=str(e))
            # Return empty metrics on error
            return PartitionHealthMetrics()
    
    async def _discover_partition_tables(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Discover all partition tables in the database."""
        partition_tables = []
        
        try:
            # Find market_data partitions
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'market_data_%'")
            )
            
            for row in result:
                table_name = row[0]
                if table_name != 'market_data':  # Skip main table
                    partition_tables.append({
                        'name': table_name,
                        'base_table': 'market_data',
                        'type': 'monthly'
                    })
            
            # Find alert_logs partitions
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'alert_logs_%'")
            )
            
            for row in result:
                table_name = row[0]
                if table_name != 'alert_logs':  # Skip main table
                    partition_tables.append({
                        'name': table_name,
                        'base_table': 'alert_logs',
                        'type': 'quarterly'
                    })
            
        except Exception as e:
            logger.warning("Failed to discover partition tables", error=str(e))
        
        return partition_tables
    
    async def _collect_single_partition_metrics(
        self, 
        session: AsyncSession, 
        partition_name: str, 
        base_table: str, 
        partition_type: str
    ) -> Optional[PartitionMetrics]:
        """Collect metrics for a single partition."""
        try:
            # Extract date range from partition name
            start_date, end_date = self._extract_partition_dates(partition_name, partition_type)
            
            # Get row count
            result = await session.execute(text(f"SELECT COUNT(*) FROM {partition_name}"))
            row_count = result.scalar() or 0
            
            # Estimate size (rough calculation for SQLite)
            size_mb = row_count * 0.001  # Rough estimate
            
            # Get last insert time (approximate)
            last_insert = None
            try:
                result = await session.execute(
                    text(f"SELECT MAX(timestamp) FROM {partition_name}")
                )
                last_insert_raw = result.scalar()
                if last_insert_raw:
                    last_insert = last_insert_raw if isinstance(last_insert_raw, datetime) else None
            except:
                pass
            
            # Determine health status
            health_status = "healthy"
            current_date = datetime.now().date()
            
            if partition_type == 'monthly':
                # Check if partition is current month and has no recent data
                if start_date.replace(day=1) == current_date.replace(day=1):
                    if not last_insert or (datetime.now() - last_insert).days > 1:
                        health_status = "warning"
            elif partition_type == 'quarterly':
                # Check if partition is current quarter and has no recent data
                current_quarter = ((current_date.month - 1) // 3) + 1
                partition_quarter = ((start_date.month - 1) // 3) + 1
                if start_date.year == current_date.year and partition_quarter == current_quarter:
                    if not last_insert or (datetime.now() - last_insert).days > 7:
                        health_status = "warning"
            
            return PartitionMetrics(
                partition_name=partition_name,
                table_name=base_table,
                partition_type=partition_type,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                row_count=row_count,
                size_mb=size_mb,
                last_insert=last_insert,
                health_status=health_status
            )
            
        except Exception as e:
            logger.warning("Failed to collect partition metrics", 
                         partition=partition_name, error=str(e))
            return None
    
    def _extract_partition_dates(self, partition_name: str, partition_type: str) -> tuple:
        """Extract start and end dates from partition name."""
        from datetime import date
        
        try:
            if partition_type == 'monthly':
                # Format: market_data_YYYY_MM
                parts = partition_name.split('_')
                year, month = int(parts[2]), int(parts[3])
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month + 1, 1)
                end_date = end_date - timedelta(days=1)
                
            else:  # quarterly
                # Format: alert_logs_YYYY_qN
                parts = partition_name.split('_')
                year, quarter = int(parts[2]), int(parts[3][1:])  # Remove 'q' prefix
                quarter_start_month = (quarter - 1) * 3 + 1
                start_date = date(year, quarter_start_month, 1)
                
                if quarter == 4:
                    end_date = date(year + 1, 1, 1)
                else:
                    next_quarter_month = quarter * 3 + 1
                    end_date = date(year, next_quarter_month, 1)
                end_date = end_date - timedelta(days=1)
            
            return start_date, end_date
            
        except Exception:
            # Fallback to current date
            current_date = date.today()
            return current_date, current_date
    
    async def _monitoring_loop(self, interval_seconds: int) -> None:
        """Background monitoring loop."""
        logger.info("Database monitoring loop started")
        
        while self.is_running:
            try:
                # Collect metrics
                metrics = await self.collect_health_metrics()
                
                # Trigger alerts if configured
                if metrics.alerts:
                    for callback in self._alert_callbacks:
                        try:
                            for alert in metrics.alerts:
                                callback(metrics.overall_status, alert)
                        except Exception as e:
                            logger.error("Alert callback failed", error=str(e))
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in monitoring loop",
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Continue monitoring despite errors
                await asyncio.sleep(interval_seconds)
        
        logger.info("Database monitoring loop stopped")
    
    def add_alert_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Add alert callback function.
        
        Args:
            callback: Function that takes (status, message) parameters
        """
        self._alert_callbacks.append(callback)
        logger.info("Alert callback added", callback_count=len(self._alert_callbacks))
    
    def get_metrics_history(self, limit: int = 100) -> List[DatabaseHealthMetrics]:
        """
        Get historical metrics.
        
        Args:
            limit: Maximum number of historical records to return
            
        Returns:
            List of historical DatabaseHealthMetrics
        """
        return list(self._metrics_history)[-limit:]
    
    def track_connection_acquire(self, acquire_time_ms: float) -> None:
        """
        Track connection acquisition time.
        
        Args:
            acquire_time_ms: Time taken to acquire connection in milliseconds
        """
        self._connection_acquire_times.append(acquire_time_ms)
        self._connection_acquire_count += 1
    
    async def get_connection_pool_status(self) -> Dict[str, Any]:
        """
        Get current connection pool status.
        
        Returns:
            Dictionary containing connection pool status
        """
        metrics = await self._collect_connection_pool_metrics()
        
        return {
            "pool_size": metrics.pool_size,
            "checked_out": metrics.checked_out_connections,
            "checked_in": metrics.checked_in_connections,
            "overflow": metrics.overflow_connections,
            "utilization_percent": metrics.pool_utilization_percent,
            "max_capacity": metrics.max_pool_size + metrics.max_overflow,
            "health_status": "healthy" if metrics.pool_utilization_percent < 70 else "warning"
        }


# Global monitoring service instance
_database_monitoring_service: Optional[DatabaseMonitoringService] = None


def get_database_monitoring_service() -> DatabaseMonitoringService:
    """
    Get global DatabaseMonitoringService instance.
    
    Returns:
        Singleton DatabaseMonitoringService instance
    """
    global _database_monitoring_service
    
    if _database_monitoring_service is None:
        _database_monitoring_service = DatabaseMonitoringService()
    
    return _database_monitoring_service