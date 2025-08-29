"""
Data Retention and Cleanup Automation.

Automated cleanup of old market data, logs, and other temporary data
with configurable retention policies and performance optimization.
"""

import asyncio
import os
import shutil
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.connection import get_db_session

logger = structlog.get_logger()


class RetentionPolicy(str, Enum):
    """Data retention policy types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


@dataclass
class DataCategory:
    """Configuration for a data category to be managed."""
    name: str
    description: str
    retention_days: int
    table_name: Optional[str] = None
    file_pattern: Optional[str] = None
    directory_path: Optional[Path] = None
    cleanup_function: Optional[Callable] = None
    size_limit_mb: Optional[int] = None
    priority: int = 1  # Lower numbers = higher priority
    enabled: bool = True


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    category: str
    records_deleted: int = 0
    files_deleted: int = 0
    bytes_freed: int = 0
    execution_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    success: bool = True


@dataclass
class RetentionStats:
    """Statistics for the data retention system."""
    last_run: Optional[datetime] = None
    total_runs: int = 0
    total_records_cleaned: int = 0
    total_files_cleaned: int = 0
    total_bytes_freed: int = 0
    categories_managed: int = 0
    average_execution_time: float = 0.0
    last_error: Optional[str] = None


class DataRetentionService:
    """
    Automated data retention and cleanup service.
    
    Manages cleanup of old data based on configurable retention policies
    with performance monitoring, error handling, and scheduling.
    """
    
    def __init__(self):
        self.categories: List[DataCategory] = []
        self.stats = RetentionStats()
        self.running = False
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize default data categories
        self._initialize_default_categories()
        
        logger.info("Data retention service initialized")
    
    def _initialize_default_categories(self) -> None:
        """Initialize default data categories for cleanup."""
        
        # Market data retention
        self.categories.append(DataCategory(
            name="market_data",
            description="Historical market data older than retention period",
            retention_days=settings.MARKET_DATA_RETENTION_DAYS,
            table_name="market_data",
            priority=1
        ))
        
        # Alert history retention
        self.categories.append(DataCategory(
            name="alert_history",
            description="Alert execution history and logs",
            retention_days=90,
            table_name="alert_history",
            priority=2
        ))
        
        # Log files cleanup
        self.categories.append(DataCategory(
            name="log_files",
            description="Application log files",
            retention_days=30,
            file_pattern="*.log",
            directory_path=Path("logs"),
            size_limit_mb=500,
            priority=3
        ))
        
        # Cache files cleanup
        self.categories.append(DataCategory(
            name="cache_files",
            description="Temporary cache files",
            retention_days=7,
            file_pattern="*.cache",
            directory_path=Path(".cache"),
            priority=4
        ))
        
        # Temporary files
        self.categories.append(DataCategory(
            name="temp_files",
            description="Temporary processing files",
            retention_days=1,
            file_pattern="temp_*",
            directory_path=Path("tmp"),
            priority=5
        ))
        
        # Secret manager cache
        self.categories.append(DataCategory(
            name="secrets_cache",
            description="Encrypted secrets cache files",
            retention_days=1,
            file_pattern="cache_*.enc",
            directory_path=Path(".secrets_cache"),
            priority=6
        ))
    
    def add_category(self, category: DataCategory) -> None:
        """
        Add a custom data category for cleanup.
        
        Args:
            category: Data category configuration.
        """
        self.categories.append(category)
        self.stats.categories_managed = len([c for c in self.categories if c.enabled])
        logger.info(f"Added data category: {category.name}")
    
    async def cleanup_database_category(self, category: DataCategory) -> CleanupResult:
        """
        Clean up database records for a category.
        
        Args:
            category: Category configuration.
            
        Returns:
            CleanupResult with operation details.
        """
        start_time = time.time()
        result = CleanupResult(category=category.name)
        
        if not category.table_name:
            result.success = False
            result.errors.append("No table name specified")
            return result
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=category.retention_days)
            
            async with get_db_session() as session:
                # Count records to be deleted
                count_query = text(f"""
                    SELECT COUNT(*) as count 
                    FROM {category.table_name} 
                    WHERE created_at < :cutoff_date
                """)
                count_result = await session.execute(count_query, {"cutoff_date": cutoff_date})
                records_to_delete = count_result.fetchone().count
                
                if records_to_delete > 0:
                    # Delete old records
                    delete_query = text(f"""
                        DELETE FROM {category.table_name} 
                        WHERE created_at < :cutoff_date
                    """)
                    await session.execute(delete_query, {"cutoff_date": cutoff_date})
                    await session.commit()
                    
                    result.records_deleted = records_to_delete
                    logger.info(
                        f"Cleaned up {records_to_delete} records from {category.table_name}",
                        category=category.name,
                        cutoff_date=cutoff_date.isoformat()
                    )
                
        except Exception as e:
            result.success = False
            result.errors.append(f"Database cleanup failed: {e}")
            logger.error(f"Database cleanup failed for {category.name}: {e}")
        
        result.execution_time_seconds = time.time() - start_time
        return result
    
    async def cleanup_file_category(self, category: DataCategory) -> CleanupResult:
        """
        Clean up files for a category.
        
        Args:
            category: Category configuration.
            
        Returns:
            CleanupResult with operation details.
        """
        start_time = time.time()
        result = CleanupResult(category=category.name)
        
        if not category.directory_path or not category.file_pattern:
            result.success = False
            result.errors.append("Directory path or file pattern not specified")
            return result
        
        try:
            if not category.directory_path.exists():
                logger.debug(f"Directory {category.directory_path} does not exist, skipping")
                result.execution_time_seconds = time.time() - start_time
                return result
            
            cutoff_time = time.time() - (category.retention_days * 24 * 60 * 60)
            files_deleted = 0
            bytes_freed = 0
            
            # Find matching files
            for file_path in category.directory_path.rglob(category.file_pattern):
                try:
                    if file_path.is_file():
                        file_mtime = file_path.stat().st_mtime
                        
                        # Check if file is old enough for deletion
                        if file_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            
                            files_deleted += 1
                            bytes_freed += file_size
                            
                            logger.debug(
                                f"Deleted file: {file_path}",
                                size_bytes=file_size,
                                age_days=(time.time() - file_mtime) / (24 * 60 * 60)
                            )
                            
                except Exception as e:
                    result.errors.append(f"Failed to delete {file_path}: {e}")
                    logger.warning(f"Failed to delete {file_path}: {e}")
            
            # Check directory size limit
            if category.size_limit_mb and files_deleted == 0:
                await self._enforce_size_limit(category, result)
            
            result.files_deleted = files_deleted
            result.bytes_freed = bytes_freed
            
            if files_deleted > 0:
                logger.info(
                    f"Cleaned up {files_deleted} files ({bytes_freed / (1024*1024):.1f} MB)",
                    category=category.name,
                    retention_days=category.retention_days
                )
        
        except Exception as e:
            result.success = False
            result.errors.append(f"File cleanup failed: {e}")
            logger.error(f"File cleanup failed for {category.name}: {e}")
        
        result.execution_time_seconds = time.time() - start_time
        return result
    
    async def _enforce_size_limit(self, category: DataCategory, result: CleanupResult) -> None:
        """
        Enforce size limit by deleting oldest files if necessary.
        
        Args:
            category: Category configuration.
            result: Result object to update.
        """
        try:
            total_size = 0
            file_list = []
            
            # Calculate total size and collect file info
            for file_path in category.directory_path.rglob(category.file_pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    total_size += stat.st_size
                    file_list.append((file_path, stat.st_mtime, stat.st_size))
            
            size_limit_bytes = category.size_limit_mb * 1024 * 1024
            
            if total_size > size_limit_bytes:
                # Sort by modification time (oldest first)
                file_list.sort(key=lambda x: x[1])
                
                bytes_to_free = total_size - size_limit_bytes
                bytes_freed = 0
                
                for file_path, mtime, size in file_list:
                    if bytes_freed >= bytes_to_free:
                        break
                    
                    try:
                        file_path.unlink()
                        bytes_freed += size
                        result.files_deleted += 1
                        result.bytes_freed += size
                        
                        logger.debug(f"Deleted file for size limit: {file_path}")
                        
                    except Exception as e:
                        result.errors.append(f"Failed to delete {file_path} for size limit: {e}")
                
                logger.info(
                    f"Enforced size limit for {category.name}",
                    size_limit_mb=category.size_limit_mb,
                    files_deleted=result.files_deleted,
                    bytes_freed=bytes_freed
                )
        
        except Exception as e:
            result.errors.append(f"Size limit enforcement failed: {e}")
            logger.error(f"Size limit enforcement failed for {category.name}: {e}")
    
    async def cleanup_category(self, category: DataCategory) -> CleanupResult:
        """
        Clean up a single data category.
        
        Args:
            category: Category to clean up.
            
        Returns:
            CleanupResult with operation details.
        """
        if not category.enabled:
            logger.debug(f"Category {category.name} is disabled, skipping")
            return CleanupResult(category=category.name, success=True)
        
        logger.info(f"Starting cleanup for category: {category.name}")
        
        # Use custom cleanup function if provided
        if category.cleanup_function:
            try:
                return await category.cleanup_function(category)
            except Exception as e:
                logger.error(f"Custom cleanup function failed for {category.name}: {e}")
                return CleanupResult(
                    category=category.name,
                    success=False,
                    errors=[f"Custom cleanup failed: {e}"]
                )
        
        # Use built-in cleanup methods
        if category.table_name:
            return await self.cleanup_database_category(category)
        elif category.directory_path and category.file_pattern:
            return await self.cleanup_file_category(category)
        else:
            return CleanupResult(
                category=category.name,
                success=False,
                errors=["No cleanup method configured"]
            )
    
    async def run_cleanup(self, category_names: Optional[List[str]] = None) -> Dict[str, CleanupResult]:
        """
        Run cleanup for all or specified categories.
        
        Args:
            category_names: Optional list of category names to clean (all if None).
            
        Returns:
            Dict mapping category names to their cleanup results.
        """
        start_time = datetime.now(timezone.utc)
        results = {}
        
        # Filter categories
        categories_to_clean = [
            c for c in self.categories
            if (category_names is None or c.name in category_names) and c.enabled
        ]
        
        # Sort by priority (lower number = higher priority)
        categories_to_clean.sort(key=lambda x: x.priority)
        
        logger.info(f"Starting cleanup for {len(categories_to_clean)} categories")
        
        for category in categories_to_clean:
            try:
                result = await self.cleanup_category(category)
                results[category.name] = result
                
                # Update statistics
                if result.success:
                    self.stats.total_records_cleaned += result.records_deleted
                    self.stats.total_files_cleaned += result.files_deleted
                    self.stats.total_bytes_freed += result.bytes_freed
                else:
                    self.stats.last_error = f"{category.name}: {'; '.join(result.errors)}"
                
            except Exception as e:
                logger.error(f"Unexpected error cleaning category {category.name}: {e}")
                results[category.name] = CleanupResult(
                    category=category.name,
                    success=False,
                    errors=[f"Unexpected error: {e}"]
                )
        
        # Update overall statistics
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        self.stats.last_run = start_time
        self.stats.total_runs += 1
        self.stats.average_execution_time = (
            (self.stats.average_execution_time * (self.stats.total_runs - 1) + execution_time)
            / self.stats.total_runs
        )
        
        successful_cleanups = sum(1 for r in results.values() if r.success)
        total_cleaned = sum(r.records_deleted + r.files_deleted for r in results.values())
        
        logger.info(
            f"Cleanup completed: {successful_cleanups}/{len(results)} categories successful, "
            f"{total_cleaned} items cleaned in {execution_time:.1f}s"
        )
        
        return results
    
    async def start_scheduled_cleanup(
        self,
        interval_hours: int = 24,
        initial_delay_minutes: int = 5
    ) -> None:
        """
        Start scheduled cleanup process.
        
        Args:
            interval_hours: Hours between cleanup runs.
            initial_delay_minutes: Minutes to wait before first run.
        """
        if self.running:
            logger.warning("Scheduled cleanup is already running")
            return
        
        self.running = True
        
        async def cleanup_loop():
            # Initial delay
            await asyncio.sleep(initial_delay_minutes * 60)
            
            while self.running:
                try:
                    await self.run_cleanup()
                except Exception as e:
                    logger.error(f"Scheduled cleanup failed: {e}")
                    self.stats.last_error = f"Scheduled cleanup error: {e}"
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
        
        self.cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started scheduled cleanup (interval: {interval_hours}h)")
    
    async def stop_scheduled_cleanup(self) -> None:
        """Stop the scheduled cleanup process."""
        if not self.running:
            return
        
        self.running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped scheduled cleanup")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get data retention service statistics.
        
        Returns:
            Dict with comprehensive statistics.
        """
        return {
            "service_status": {
                "running": self.running,
                "categories_managed": len([c for c in self.categories if c.enabled]),
                "total_categories": len(self.categories),
            },
            "execution_stats": {
                "last_run": self.stats.last_run.isoformat() if self.stats.last_run else None,
                "total_runs": self.stats.total_runs,
                "average_execution_time_seconds": self.stats.average_execution_time,
                "last_error": self.stats.last_error,
            },
            "cleanup_totals": {
                "records_cleaned": self.stats.total_records_cleaned,
                "files_cleaned": self.stats.total_files_cleaned,
                "bytes_freed": self.stats.total_bytes_freed,
                "megabytes_freed": self.stats.total_bytes_freed / (1024 * 1024),
            },
            "categories": [
                {
                    "name": c.name,
                    "description": c.description,
                    "retention_days": c.retention_days,
                    "enabled": c.enabled,
                    "priority": c.priority,
                    "type": "database" if c.table_name else "filesystem"
                }
                for c in sorted(self.categories, key=lambda x: x.priority)
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_disk_usage(self) -> Dict[str, Any]:
        """
        Get disk usage information for managed directories.
        
        Returns:
            Dict with disk usage statistics.
        """
        usage_info = {}
        
        for category in self.categories:
            if category.directory_path and category.directory_path.exists():
                try:
                    total_size = 0
                    file_count = 0
                    
                    for file_path in category.directory_path.rglob(category.file_pattern or "*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
                    
                    usage_info[category.name] = {
                        "directory": str(category.directory_path),
                        "total_size_bytes": total_size,
                        "total_size_mb": total_size / (1024 * 1024),
                        "file_count": file_count,
                        "size_limit_mb": category.size_limit_mb,
                        "size_limit_exceeded": (
                            category.size_limit_mb and 
                            total_size > (category.size_limit_mb * 1024 * 1024)
                        )
                    }
                    
                except Exception as e:
                    usage_info[category.name] = {"error": str(e)}
        
        # Add system disk usage
        try:
            disk_usage = shutil.disk_usage(".")
            usage_info["system"] = {
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "used_percentage": (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            usage_info["system"] = {"error": str(e)}
        
        return usage_info


# Global data retention service instance
data_retention_service = DataRetentionService()