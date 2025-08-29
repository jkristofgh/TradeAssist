"""
Unit tests for Data Retention service.
"""

import asyncio
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.backend.services.data_retention import (
    DataRetentionService,
    DataCategory,
    CleanupResult,
    RetentionStats,
    RetentionPolicy
)


class TestDataCategory:
    """Test cases for DataCategory."""
    
    def test_database_category_creation(self):
        """Test creating a database cleanup category."""
        category = DataCategory(
            name="test_table",
            description="Test table cleanup",
            retention_days=30,
            table_name="test_data",
            priority=1
        )
        
        assert category.name == "test_table"
        assert category.retention_days == 30
        assert category.table_name == "test_data"
        assert category.enabled is True
        assert category.priority == 1
    
    def test_file_category_creation(self):
        """Test creating a file cleanup category."""
        category = DataCategory(
            name="log_files",
            description="Application log files",
            retention_days=7,
            file_pattern="*.log",
            directory_path=Path("logs"),
            size_limit_mb=100
        )
        
        assert category.file_pattern == "*.log"
        assert category.directory_path == Path("logs")
        assert category.size_limit_mb == 100


class TestCleanupResult:
    """Test cases for CleanupResult."""
    
    def test_cleanup_result_creation(self):
        """Test creating cleanup results."""
        result = CleanupResult(
            category="test",
            records_deleted=10,
            files_deleted=5,
            bytes_freed=1024,
            execution_time_seconds=1.5,
            success=True
        )
        
        assert result.category == "test"
        assert result.records_deleted == 10
        assert result.files_deleted == 5
        assert result.bytes_freed == 1024
        assert result.execution_time_seconds == 1.5
        assert result.success is True
        assert result.errors == []


class TestDataRetentionService:
    """Test cases for DataRetentionService."""
    
    def setup_method(self):
        """Setup test data retention service."""
        self.service = DataRetentionService()
        # Clear default categories for testing
        self.service.categories = []
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = DataRetentionService()
        
        # Should have default categories
        assert len(service.categories) > 0
        assert isinstance(service.stats, RetentionStats)
        assert service.running is False
    
    def test_add_category(self):
        """Test adding custom categories."""
        category = DataCategory(
            name="custom_test",
            description="Custom test category",
            retention_days=15,
            table_name="custom_table"
        )
        
        initial_count = len(self.service.categories)
        self.service.add_category(category)
        
        assert len(self.service.categories) == initial_count + 1
        assert self.service.categories[-1] == category
    
    @pytest.mark.asyncio
    async def test_cleanup_database_category_success(self):
        """Test successful database category cleanup."""
        category = DataCategory(
            name="test_db",
            description="Test database",
            retention_days=30,
            table_name="test_table"
        )
        
        # Mock database session and query results
        mock_result = Mock()
        mock_result.fetchone.return_value = Mock(count=5)
        
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        
        with patch('src.backend.services.data_retention.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            result = await self.service.cleanup_database_category(category)
        
        assert result.success is True
        assert result.records_deleted == 5
        assert result.category == "test_db"
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_cleanup_database_category_no_table(self):
        """Test database cleanup with no table name."""
        category = DataCategory(
            name="invalid_db",
            description="Invalid database category",
            retention_days=30
            # No table_name specified
        )
        
        result = await self.service.cleanup_database_category(category)
        
        assert result.success is False
        assert "No table name specified" in result.errors
        assert result.records_deleted == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_file_category_success(self):
        """Test successful file category cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files with different ages
            old_file = temp_path / "old.log"
            recent_file = temp_path / "recent.log"
            
            old_file.write_text("old log data")
            recent_file.write_text("recent log data")
            
            # Make old file appear old
            old_time = (datetime.now() - timedelta(days=10)).timestamp()
            old_file.touch(times=(old_time, old_time))
            
            category = DataCategory(
                name="test_files",
                description="Test log files",
                retention_days=7,
                file_pattern="*.log",
                directory_path=temp_path
            )
            
            result = await self.service.cleanup_file_category(category)
            
            assert result.success is True
            assert result.files_deleted == 1  # Only old file should be deleted
            assert result.bytes_freed > 0
            assert not old_file.exists()
            assert recent_file.exists()  # Recent file should remain
    
    @pytest.mark.asyncio
    async def test_cleanup_file_category_nonexistent_directory(self):
        """Test file cleanup with nonexistent directory."""
        category = DataCategory(
            name="missing_dir",
            description="Missing directory",
            retention_days=7,
            file_pattern="*.log",
            directory_path=Path("/nonexistent/directory")
        )
        
        result = await self.service.cleanup_file_category(category)
        
        assert result.success is True  # Should succeed gracefully
        assert result.files_deleted == 0
        assert result.bytes_freed == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_file_category_no_pattern(self):
        """Test file cleanup with missing pattern."""
        category = DataCategory(
            name="no_pattern",
            description="No file pattern",
            retention_days=7,
            directory_path=Path("/tmp")
            # No file_pattern specified
        )
        
        result = await self.service.cleanup_file_category(category)
        
        assert result.success is False
        assert "Directory path or file pattern not specified" in result.errors
    
    @pytest.mark.asyncio
    async def test_enforce_size_limit(self):
        """Test size limit enforcement."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files exceeding size limit
            for i in range(5):
                file_path = temp_path / f"file_{i}.log"
                file_path.write_text("x" * 1024)  # 1KB each
            
            category = DataCategory(
                name="size_limit_test",
                description="Size limit test",
                retention_days=365,  # Don't delete by age
                file_pattern="*.log",
                directory_path=temp_path,
                size_limit_mb=0.003  # ~3KB limit (should delete 2 files)
            )
            
            result = await self.service.cleanup_file_category(category)
            
            assert result.success is True
            assert result.files_deleted >= 2  # Should delete oldest files
            assert result.bytes_freed >= 2048  # At least 2KB freed
    
    @pytest.mark.asyncio
    async def test_cleanup_category_with_custom_function(self):
        """Test cleanup with custom cleanup function."""
        async def custom_cleanup(category):
            return CleanupResult(
                category=category.name,
                records_deleted=10,
                success=True
            )
        
        category = DataCategory(
            name="custom_cleanup",
            description="Custom cleanup function",
            retention_days=30,
            cleanup_function=custom_cleanup
        )
        
        result = await self.service.cleanup_category(category)
        
        assert result.success is True
        assert result.records_deleted == 10
        assert result.category == "custom_cleanup"
    
    @pytest.mark.asyncio
    async def test_cleanup_category_disabled(self):
        """Test cleanup skips disabled categories."""
        category = DataCategory(
            name="disabled_category",
            description="Disabled category",
            retention_days=30,
            table_name="test_table",
            enabled=False
        )
        
        result = await self.service.cleanup_category(category)
        
        assert result.success is True
        assert result.records_deleted == 0
        assert result.files_deleted == 0
    
    @pytest.mark.asyncio
    async def test_run_cleanup_all_categories(self):
        """Test running cleanup for all categories."""
        # Add test categories
        db_category = DataCategory(
            name="test_db",
            description="Test database",
            retention_days=30,
            table_name="test_table",
            priority=1
        )
        
        file_category = DataCategory(
            name="test_files",
            description="Test files",
            retention_days=7,
            file_pattern="*.tmp",
            directory_path=Path("/tmp/nonexistent"),
            priority=2
        )
        
        self.service.add_category(db_category)
        self.service.add_category(file_category)
        
        # Mock cleanup methods
        with patch.object(self.service, 'cleanup_database_category') as mock_db_cleanup, \
             patch.object(self.service, 'cleanup_file_category') as mock_file_cleanup:
            
            mock_db_cleanup.return_value = CleanupResult("test_db", records_deleted=5, success=True)
            mock_file_cleanup.return_value = CleanupResult("test_files", files_deleted=3, success=True)
            
            results = await self.service.run_cleanup()
        
        assert len(results) == 2
        assert "test_db" in results
        assert "test_files" in results
        assert results["test_db"].records_deleted == 5
        assert results["test_files"].files_deleted == 3
        
        # Check statistics were updated
        assert self.service.stats.total_runs == 1
        assert self.service.stats.total_records_cleaned == 5
        assert self.service.stats.total_files_cleaned == 3
    
    @pytest.mark.asyncio
    async def test_run_cleanup_specific_categories(self):
        """Test running cleanup for specific categories only."""
        # Add test categories
        category1 = DataCategory("cat1", "Category 1", 30, table_name="table1")
        category2 = DataCategory("cat2", "Category 2", 30, table_name="table2")
        category3 = DataCategory("cat3", "Category 3", 30, table_name="table3")
        
        self.service.add_category(category1)
        self.service.add_category(category2)
        self.service.add_category(category3)
        
        # Mock cleanup method
        with patch.object(self.service, 'cleanup_database_category') as mock_cleanup:
            mock_cleanup.return_value = CleanupResult("test", success=True)
            
            results = await self.service.run_cleanup(category_names=["cat1", "cat3"])
        
        assert len(results) == 2
        assert "cat1" in results
        assert "cat3" in results
        assert "cat2" not in results
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduled_cleanup(self):
        """Test starting and stopping scheduled cleanup."""
        assert self.service.running is False
        assert self.service.cleanup_task is None
        
        # Start scheduled cleanup with short interval for testing
        await self.service.start_scheduled_cleanup(
            interval_hours=0.01,  # Very short interval
            initial_delay_minutes=0.001  # Very short delay
        )
        
        assert self.service.running is True
        assert self.service.cleanup_task is not None
        
        # Wait a bit to let the task start
        await asyncio.sleep(0.01)
        
        # Stop scheduled cleanup
        await self.service.stop_scheduled_cleanup()
        
        assert self.service.running is False
    
    def test_get_statistics(self):
        """Test getting service statistics."""
        # Add some test data to stats
        self.service.stats.total_runs = 5
        self.service.stats.total_records_cleaned = 100
        self.service.stats.total_files_cleaned = 50
        self.service.stats.total_bytes_freed = 1024 * 1024  # 1MB
        
        # Add test category
        category = DataCategory("test", "Test", 30, table_name="test_table")
        self.service.add_category(category)
        
        stats = self.service.get_statistics()
        
        assert stats["service_status"]["running"] is False
        assert stats["service_status"]["categories_managed"] == 1
        assert stats["execution_stats"]["total_runs"] == 5
        assert stats["cleanup_totals"]["records_cleaned"] == 100
        assert stats["cleanup_totals"]["files_cleaned"] == 50
        assert stats["cleanup_totals"]["megabytes_freed"] == 1.0
        assert len(stats["categories"]) == 1
        assert "timestamp" in stats
    
    @pytest.mark.asyncio
    async def test_get_disk_usage(self):
        """Test getting disk usage information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            test_file = temp_path / "test.log"
            test_file.write_text("test data" * 100)  # Some data
            
            category = DataCategory(
                name="disk_test",
                description="Disk usage test",
                retention_days=30,
                file_pattern="*.log",
                directory_path=temp_path
            )
            
            self.service.add_category(category)
            
            usage_info = await self.service.get_disk_usage()
            
            assert "disk_test" in usage_info
            assert usage_info["disk_test"]["directory"] == str(temp_path)
            assert usage_info["disk_test"]["file_count"] == 1
            assert usage_info["disk_test"]["total_size_bytes"] > 0
            assert usage_info["disk_test"]["total_size_mb"] > 0
            assert "system" in usage_info
    
    def test_default_categories_initialization(self):
        """Test that default categories are properly initialized."""
        service = DataRetentionService()
        
        # Should have several default categories
        assert len(service.categories) >= 5
        
        category_names = {cat.name for cat in service.categories}
        expected_categories = {
            "market_data",
            "alert_history", 
            "log_files",
            "cache_files",
            "temp_files",
            "secrets_cache"
        }
        
        assert expected_categories.issubset(category_names)
        
        # Verify configuration of key categories
        market_data_category = next(cat for cat in service.categories if cat.name == "market_data")
        assert market_data_category.table_name == "market_data"
        assert market_data_category.priority == 1
        
        log_files_category = next(cat for cat in service.categories if cat.name == "log_files")
        assert log_files_category.file_pattern == "*.log"
        assert log_files_category.size_limit_mb == 500


@pytest.mark.integration
class TestDataRetentionIntegration:
    """Integration tests for data retention service."""
    
    @pytest.mark.asyncio
    async def test_complete_cleanup_cycle(self):
        """Test complete cleanup cycle with real files and directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create directory structure
            logs_dir = base_path / "logs"
            cache_dir = base_path / "cache"
            logs_dir.mkdir()
            cache_dir.mkdir()
            
            # Create old and new files
            old_log = logs_dir / "old.log"
            new_log = logs_dir / "new.log"
            old_cache = cache_dir / "old.cache"
            new_cache = cache_dir / "new.cache"
            
            # Write files
            for file_path in [old_log, new_log, old_cache, new_cache]:
                file_path.write_text("test data")
            
            # Make some files old
            old_time = (datetime.now() - timedelta(days=10)).timestamp()
            old_log.touch(times=(old_time, old_time))
            old_cache.touch(times=(old_time, old_time))
            
            # Setup service with test categories
            service = DataRetentionService()
            service.categories = []  # Clear defaults
            
            service.add_category(DataCategory(
                name="test_logs",
                description="Test log files",
                retention_days=5,
                file_pattern="*.log",
                directory_path=logs_dir,
                priority=1
            ))
            
            service.add_category(DataCategory(
                name="test_cache",
                description="Test cache files", 
                retention_days=5,
                file_pattern="*.cache",
                directory_path=cache_dir,
                priority=2
            ))
            
            # Run cleanup
            results = await service.run_cleanup()
            
            # Verify results
            assert len(results) == 2
            assert all(result.success for result in results.values())
            assert results["test_logs"].files_deleted == 1
            assert results["test_cache"].files_deleted == 1
            
            # Verify files
            assert not old_log.exists()
            assert new_log.exists()
            assert not old_cache.exists()
            assert new_cache.exists()
            
            # Verify statistics
            assert service.stats.total_runs == 1
            assert service.stats.total_files_cleaned == 2
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires actual database setup")
    async def test_database_cleanup_integration(self):
        """Test database cleanup with real database (manual test)."""
        # This test would require:
        # 1. Actual database connection
        # 2. Test table with timestamped data
        # 3. Proper cleanup verification
        
        service = DataRetentionService()
        
        # Add database category for testing
        category = DataCategory(
            name="test_integration_table",
            description="Integration test table",
            retention_days=30,
            table_name="test_data"
        )
        
        service.add_category(category)
        
        # This would test with real database
        # results = await service.run_cleanup(category_names=["test_integration_table"])
        # assert results["test_integration_table"].success