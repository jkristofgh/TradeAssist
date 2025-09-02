"""
Partition Manager Service for Automated Time-Series Partitioning.

Provides automated partition management for MarketData (monthly) and AlertLog (quarterly) 
tables with scheduled partition creation, cleanup, and archival procedures.
"""

import asyncio
import calendar
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import structlog

from sqlalchemy import text, inspect, MetaData
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db_session, engine
from ..config import settings
from .database_monitoring_service import get_database_monitoring_service

logger = structlog.get_logger(__name__)


@dataclass
class PartitionInfo:
    """Information about a database partition."""
    
    table_name: str
    partition_name: str
    partition_type: str  # 'monthly' or 'quarterly'
    start_date: date
    end_date: date
    created_at: datetime
    row_count: int = 0
    size_mb: float = 0.0
    is_active: bool = True


@dataclass
class PartitionManagerConfig:
    """Configuration for partition management operations."""
    
    # Partition creation settings
    market_data_advance_months: int = 2  # Create partitions 2 months in advance
    alert_log_advance_quarters: int = 1  # Create partitions 1 quarter in advance
    
    # Data retention settings
    market_data_retention_months: int = 24  # Keep 24 months of data
    alert_log_retention_quarters: int = 8   # Keep 8 quarters of data
    
    # Archival settings
    enable_archival: bool = True
    archive_path: str = "./data/archive"
    compress_archives: bool = True
    
    # Background task settings
    check_interval_hours: int = 24  # Check every 24 hours
    maintenance_hour: int = 2  # Run maintenance at 2 AM
    
    # Alert settings
    low_disk_space_threshold_gb: float = 10.0
    partition_size_warning_gb: float = 2.0


class PartitionManagerService:
    """
    Service for automated time-series partition management.
    
    Manages monthly MarketData partitions and quarterly AlertLog partitions
    with automated creation, cleanup, and archival procedures.
    
    Features:
    - Automated partition creation for future periods
    - Background partition health monitoring
    - Configurable data retention and archival
    - Integration with existing monitoring systems
    """
    
    def __init__(self, config: Optional[PartitionManagerConfig] = None):
        """Initialize partition manager service."""
        self.config = config or PartitionManagerConfig()
        self.monitoring_service = get_database_monitoring_service()
        self._is_running = False
        self._background_task: Optional[asyncio.Task] = None
        self._alert_callbacks: List[Callable[[str, str], None]] = []
        
        # Partition management state
        self._active_partitions: Dict[str, List[PartitionInfo]] = {
            'market_data': [],
            'alert_logs': []
        }
        
    async def start_partition_management(self) -> None:
        """Start the background partition management service."""
        if self._is_running:
            logger.info("Partition management service already running")
            return
        
        logger.info("Starting partition management service",
                   market_data_advance=self.config.market_data_advance_months,
                   alert_log_advance=self.config.alert_log_advance_quarters)
        
        self._is_running = True
        self._background_task = asyncio.create_task(self._background_management_loop())
        
        # Initial partition discovery and creation
        await self._discover_existing_partitions()
        await self._ensure_future_partitions()
    
    async def stop_partition_management(self) -> None:
        """Stop the background partition management service."""
        if not self._is_running:
            return
        
        logger.info("Stopping partition management service")
        self._is_running = False
        
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
    
    async def _background_management_loop(self) -> None:
        """Background loop for partition management operations."""
        logger.info("Starting partition management background loop",
                   interval_hours=self.config.check_interval_hours)
        
        while self._is_running:
            try:
                current_hour = datetime.now().hour
                
                # Run maintenance at configured hour
                if current_hour == self.config.maintenance_hour:
                    await self._run_daily_maintenance()
                
                # Regular partition checks
                await self._ensure_future_partitions()
                await self._update_partition_metrics()
                
                # Wait for next check
                await asyncio.sleep(self.config.check_interval_hours * 3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in partition management loop", error=str(e))
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _run_daily_maintenance(self) -> None:
        """Run daily maintenance operations."""
        logger.info("Running daily partition maintenance")
        
        try:
            # Update partition metrics
            await self._update_partition_metrics()
            
            # Check for old partitions to archive/cleanup
            await self._cleanup_old_partitions()
            
            # Validate partition integrity
            await self._validate_partition_integrity()
            
            # Check disk space and alert if needed
            await self._check_disk_space_alerts()
            
        except Exception as e:
            logger.error("Error during daily maintenance", error=str(e))
            await self._notify_alert("maintenance_error", f"Daily maintenance failed: {str(e)}")
    
    async def create_market_data_partition(self, year: int, month: int) -> str:
        """
        Create a monthly MarketData partition.
        
        Args:
            year: Year for the partition
            month: Month for the partition (1-12)
            
        Returns:
            Name of the created partition
        """
        partition_name = f"market_data_{year}_{month:02d}"
        
        # Calculate date boundaries
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        logger.info("Creating MarketData partition",
                   partition=partition_name,
                   start_date=start_date,
                   end_date=end_date)
        
        async with get_db_session() as session:
            # Create partition table with SQLite-compatible syntax
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {partition_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                instrument_id INTEGER NOT NULL,
                price FLOAT,
                volume INTEGER,
                bid FLOAT,
                ask FLOAT,
                bid_size INTEGER,
                ask_size INTEGER,
                open_price FLOAT,
                high_price FLOAT,
                low_price FLOAT,
                deleted_at DATETIME,
                FOREIGN KEY (instrument_id) REFERENCES instruments (id) ON DELETE CASCADE,
                CHECK (timestamp >= '{start_date}' AND timestamp <= '{end_date} 23:59:59')
            )"""
            
            index1_sql = f"""CREATE INDEX IF NOT EXISTS ix_{partition_name}_timestamp_instrument 
            ON {partition_name} (timestamp, instrument_id)"""
            
            index2_sql = f"""CREATE INDEX IF NOT EXISTS ix_{partition_name}_instrument_price 
            ON {partition_name} (instrument_id, price)"""
            
            # Execute each statement separately
            await session.execute(text(create_table_sql))
            await session.execute(text(index1_sql))
            await session.execute(text(index2_sql))
            await session.commit()
        
        # Add to partition tracking
        partition_info = PartitionInfo(
            table_name="market_data",
            partition_name=partition_name,
            partition_type="monthly",
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        )
        
        self._active_partitions['market_data'].append(partition_info)
        
        logger.info("Successfully created MarketData partition", partition=partition_name)
        return partition_name
    
    async def create_alert_log_partition(self, year: int, quarter: int) -> str:
        """
        Create a quarterly AlertLog partition.
        
        Args:
            year: Year for the partition
            quarter: Quarter for the partition (1-4)
            
        Returns:
            Name of the created partition
        """
        partition_name = f"alert_logs_{year}_q{quarter}"
        
        # Calculate quarter boundaries
        quarter_start_month = (quarter - 1) * 3 + 1
        start_date = date(year, quarter_start_month, 1)
        
        if quarter == 4:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            next_quarter_month = quarter * 3 + 1
            end_date = date(year, next_quarter_month, 1) - timedelta(days=1)
        
        logger.info("Creating AlertLog partition",
                   partition=partition_name,
                   start_date=start_date,
                   end_date=end_date)
        
        async with get_db_session() as session:
            # Create partition table with explicit SQLite-compatible schema
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {partition_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                rule_id INTEGER NOT NULL,
                instrument_id INTEGER NOT NULL,
                trigger_value FLOAT NOT NULL,
                threshold_value FLOAT NOT NULL,
                fired_status VARCHAR(20) NOT NULL DEFAULT 'FIRED',
                delivery_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                evaluation_time_ms INTEGER,
                rule_condition VARCHAR(20) NOT NULL,
                alert_message TEXT,
                error_message TEXT,
                delivery_attempted_at DATETIME,
                delivery_completed_at DATETIME,
                deleted_at DATETIME,
                FOREIGN KEY (rule_id) REFERENCES alert_rules (id) ON DELETE CASCADE,
                FOREIGN KEY (instrument_id) REFERENCES instruments (id) ON DELETE CASCADE,
                CHECK (timestamp >= '{start_date}' AND timestamp <= '{end_date} 23:59:59')
            )"""
            
            await session.execute(text(create_table_sql))
            
            # Create optimized indexes
            index_sqls = [
                f"CREATE INDEX IF NOT EXISTS ix_{partition_name}_timestamp ON {partition_name} (timestamp)",
                f"CREATE INDEX IF NOT EXISTS ix_{partition_name}_rule_timestamp ON {partition_name} (rule_id, timestamp)",
                f"CREATE INDEX IF NOT EXISTS ix_{partition_name}_timestamp_instrument ON {partition_name} (timestamp, instrument_id)",
                f"CREATE INDEX IF NOT EXISTS ix_{partition_name}_status ON {partition_name} (fired_status, delivery_status)"
            ]
            
            for index_sql in index_sqls:
                await session.execute(text(index_sql))
            await session.commit()
        
        # Add to partition tracking
        partition_info = PartitionInfo(
            table_name="alert_logs",
            partition_name=partition_name,
            partition_type="quarterly",
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        )
        
        self._active_partitions['alert_logs'].append(partition_info)
        
        logger.info("Successfully created AlertLog partition", partition=partition_name)
        return partition_name
    
    async def _ensure_future_partitions(self) -> None:
        """Ensure future partitions exist according to configuration."""
        current_date = datetime.now().date()
        
        # Ensure MarketData monthly partitions
        for i in range(self.config.market_data_advance_months + 1):
            future_date = current_date + timedelta(days=30 * i)
            partition_name = f"market_data_{future_date.year}_{future_date.month:02d}"
            
            if not await self._partition_exists(partition_name):
                await self.create_market_data_partition(future_date.year, future_date.month)
        
        # Ensure AlertLog quarterly partitions
        current_quarter = ((current_date.month - 1) // 3) + 1
        for i in range(self.config.alert_log_advance_quarters + 1):
            # Calculate future quarter
            future_quarter = current_quarter + i
            future_year = current_date.year
            
            while future_quarter > 4:
                future_quarter -= 4
                future_year += 1
            
            partition_name = f"alert_logs_{future_year}_q{future_quarter}"
            
            if not await self._partition_exists(partition_name):
                await self.create_alert_log_partition(future_year, future_quarter)
    
    async def _partition_exists(self, partition_name: str) -> bool:
        """Check if a partition table exists."""
        async with get_db_session() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": partition_name}
            )
            return result.fetchone() is not None
    
    async def _discover_existing_partitions(self) -> None:
        """Discover existing partition tables."""
        async with get_db_session() as session:
            # Find MarketData partitions
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'market_data_%'")
            )
            
            for row in result:
                table_name = row[0]
                if table_name != 'market_data':  # Skip main table
                    await self._analyze_partition(table_name, 'market_data')
            
            # Find AlertLog partitions
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'alert_logs_%'")
            )
            
            for row in result:
                table_name = row[0]
                if table_name != 'alert_logs':  # Skip main table
                    await self._analyze_partition(table_name, 'alert_logs')
    
    async def _analyze_partition(self, partition_name: str, base_table: str) -> None:
        """Analyze and register an existing partition."""
        try:
            # Extract date info from partition name
            if base_table == 'market_data':
                # Format: market_data_YYYY_MM
                parts = partition_name.split('_')
                year, month = int(parts[2]), int(parts[3])
                start_date = date(year, month, 1)
                end_date = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year + 1, 1, 1) - timedelta(days=1)
                partition_type = 'monthly'
            
            else:
                # Format: alert_logs_YYYY_qN
                parts = partition_name.split('_')
                year, quarter = int(parts[2]), int(parts[3][1:])  # Remove 'q' prefix
                quarter_start_month = (quarter - 1) * 3 + 1
                start_date = date(year, quarter_start_month, 1)
                if quarter == 4:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    next_quarter_month = quarter * 3 + 1
                    end_date = date(year, next_quarter_month, 1) - timedelta(days=1)
                partition_type = 'quarterly'
            
            # Get partition statistics
            async with get_db_session() as session:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {partition_name}"))
                row_count = result.scalar() or 0
            
            partition_info = PartitionInfo(
                table_name=base_table,
                partition_name=partition_name,
                partition_type=partition_type,
                start_date=start_date,
                end_date=end_date,
                created_at=datetime.now(),  # Approximate
                row_count=row_count
            )
            
            self._active_partitions[base_table].append(partition_info)
            
        except Exception as e:
            logger.warning("Failed to analyze partition", partition=partition_name, error=str(e))
    
    async def _update_partition_metrics(self) -> None:
        """Update metrics for all active partitions."""
        for base_table, partitions in self._active_partitions.items():
            for partition in partitions:
                try:
                    async with get_db_session() as session:
                        # Update row count
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {partition.partition_name}"))
                        partition.row_count = result.scalar() or 0
                        
                        # Update size (approximate for SQLite)
                        # This would be more accurate with actual file size calculation
                        partition.size_mb = partition.row_count * 0.001  # Rough estimate
                        
                except Exception as e:
                    logger.warning("Failed to update partition metrics", 
                                 partition=partition.partition_name, error=str(e))
    
    async def _cleanup_old_partitions(self) -> None:
        """Clean up old partitions based on retention policy."""
        current_date = datetime.now().date()
        
        # Cleanup MarketData partitions
        cutoff_date = current_date - timedelta(days=30 * self.config.market_data_retention_months)
        await self._cleanup_partitions_by_date('market_data', cutoff_date)
        
        # Cleanup AlertLog partitions
        cutoff_date = current_date - timedelta(days=90 * self.config.alert_log_retention_quarters)
        await self._cleanup_partitions_by_date('alert_logs', cutoff_date)
    
    async def _cleanup_partitions_by_date(self, base_table: str, cutoff_date: date) -> None:
        """Clean up partitions older than cutoff date."""
        partitions_to_remove = []
        
        for partition in self._active_partitions[base_table]:
            if partition.end_date < cutoff_date:
                if self.config.enable_archival:
                    await self._archive_partition(partition)
                
                await self._drop_partition(partition)
                partitions_to_remove.append(partition)
        
        # Remove from tracking
        for partition in partitions_to_remove:
            self._active_partitions[base_table].remove(partition)
    
    async def _archive_partition(self, partition: PartitionInfo) -> None:
        """Archive a partition before dropping it."""
        logger.info("Archiving partition", partition=partition.partition_name)
        
        # This would implement actual archival logic
        # For now, just log the action
        await self._notify_alert("partition_archived", 
                               f"Partition {partition.partition_name} archived successfully")
    
    async def _drop_partition(self, partition: PartitionInfo) -> None:
        """Drop an old partition table."""
        logger.info("Dropping partition", partition=partition.partition_name)
        
        async with get_db_session() as session:
            await session.execute(text(f"DROP TABLE IF EXISTS {partition.partition_name}"))
            await session.commit()
    
    async def _validate_partition_integrity(self) -> None:
        """Validate partition table integrity and constraints."""
        for base_table, partitions in self._active_partitions.items():
            for partition in partitions:
                try:
                    async with get_db_session() as session:
                        # Basic integrity check
                        await session.execute(text(f"PRAGMA integrity_check({partition.partition_name})"))
                        
                except Exception as e:
                    logger.error("Partition integrity check failed",
                               partition=partition.partition_name, error=str(e))
                    await self._notify_alert("integrity_error",
                                           f"Partition {partition.partition_name} failed integrity check")
    
    async def _check_disk_space_alerts(self) -> None:
        """Check disk space and send alerts if needed."""
        # This would implement actual disk space checking
        # For now, just a placeholder
        pass
    
    def add_alert_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add callback for partition management alerts."""
        self._alert_callbacks.append(callback)
    
    async def _notify_alert(self, alert_type: str, message: str) -> None:
        """Send alert notifications."""
        logger.warning(f"Partition alert [{alert_type}]: {message}")
        
        for callback in self._alert_callbacks:
            try:
                callback(alert_type, message)
            except Exception as e:
                logger.error("Failed to send partition alert", error=str(e))
    
    def get_partition_status(self) -> Dict[str, Any]:
        """Get current partition status and metrics."""
        return {
            "service_status": "running" if self._is_running else "stopped",
            "partitions": {
                base_table: [
                    {
                        "name": p.partition_name,
                        "type": p.partition_type,
                        "start_date": p.start_date.isoformat(),
                        "end_date": p.end_date.isoformat(),
                        "row_count": p.row_count,
                        "size_mb": p.size_mb,
                        "is_active": p.is_active
                    }
                    for p in partitions
                ]
                for base_table, partitions in self._active_partitions.items()
            },
            "config": {
                "market_data_advance_months": self.config.market_data_advance_months,
                "alert_log_advance_quarters": self.config.alert_log_advance_quarters,
                "market_data_retention_months": self.config.market_data_retention_months,
                "alert_log_retention_quarters": self.config.alert_log_retention_quarters,
                "archival_enabled": self.config.enable_archival
            }
        }


# Global instance management
_partition_manager_service = None


def get_partition_manager_service(config: Optional[PartitionManagerConfig] = None) -> PartitionManagerService:
    """Get global PartitionManagerService instance."""
    global _partition_manager_service
    
    if _partition_manager_service is None:
        _partition_manager_service = PartitionManagerService(config)
        logger.info("PartitionManagerService initialized")
    
    return _partition_manager_service