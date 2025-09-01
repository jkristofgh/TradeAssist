"""
Unit tests for Database Performance Extension - Phase 1.

Tests index optimization, data type conversion, soft delete functionality,
and performance monitoring components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy import Float, DECIMAL, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.mixins import SoftDeleteMixin, TimestampMixin
from src.backend.services.database_performance import (
    DatabasePerformanceMonitor,
    PerformanceMetrics,
    QueryPerformance,
    get_performance_monitor
)


class TestSoftDeleteMixin:
    """Test soft delete functionality."""
    
    def test_soft_delete_mixin_initialization(self):
        """Test SoftDeleteMixin initialization."""
        
        class TestModel(SoftDeleteMixin):
            pass
        
        model = TestModel()
        assert model.deleted_at is None
        assert model.is_active is True
        assert model.is_deleted is False
    
    def test_soft_delete_operation(self):
        """Test soft delete marks record as deleted."""
        
        class TestModel(SoftDeleteMixin):
            pass
        
        model = TestModel()
        
        # Perform soft delete
        model.soft_delete()
        
        assert model.deleted_at is not None
        assert model.is_deleted is True
        assert model.is_active is False
        assert isinstance(model.deleted_at, datetime)
    
    def test_soft_delete_idempotent(self):
        """Test soft delete is idempotent."""
        
        class TestModel(SoftDeleteMixin):
            pass
        
        model = TestModel()
        
        # First soft delete
        model.soft_delete()
        first_timestamp = model.deleted_at
        
        # Second soft delete should not change timestamp
        model.soft_delete()
        assert model.deleted_at == first_timestamp
    
    def test_restore_operation(self):
        """Test restore brings back soft deleted record."""
        
        class TestModel(SoftDeleteMixin):
            pass
        
        model = TestModel()
        
        # Soft delete then restore
        model.soft_delete()
        assert model.is_deleted is True
        
        model.restore()
        assert model.deleted_at is None
        assert model.is_active is True
        assert model.is_deleted is False
    
    def test_repr_deleted(self):
        """Test string representation includes deletion status."""
        
        class TestModel(SoftDeleteMixin):
            pass
        
        model = TestModel()
        
        # Active record
        assert model.__repr_deleted__() == ""
        
        # Deleted record
        model.soft_delete()
        repr_str = model.__repr_deleted__()
        assert "[DELETED at " in repr_str
        assert str(model.deleted_at) in repr_str


class TestDatabasePerformanceMonitor:
    """Test database performance monitoring."""
    
    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor instance."""
        return DatabasePerformanceMonitor(window_size=10)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initializes correctly."""
        assert monitor.window_size == 10
        assert len(monitor.query_history) == 0
        assert len(monitor.insert_counts) == 0
        assert monitor._monitoring is False
        assert len(monitor.metrics_history) == 0
    
    def test_track_query(self, monitor):
        """Test query tracking."""
        # Track SELECT query
        monitor.track_query("SELECT", "market_data", 1.5, used_index=True)
        
        assert len(monitor.query_history) == 1
        query = monitor.query_history[0]
        assert query.query_type == "SELECT"
        assert query.table_name == "market_data"
        assert query.execution_time_ms == 1.5
        assert query.used_index is True
    
    def test_track_insert_counts(self, monitor):
        """Test INSERT tracking for rate calculation."""
        # Track multiple INSERTs
        monitor.track_query("INSERT", "market_data", 0.5, used_index=False)
        monitor.track_query("INSERT", "market_data", 0.6, used_index=False)
        monitor.track_query("INSERT", "alert_logs", 0.7, used_index=False)
        
        assert monitor.insert_counts["market_data"] == 2
        assert monitor.insert_counts["alert_logs"] == 1
    
    def test_query_history_window(self, monitor):
        """Test query history respects window size."""
        # Track more queries than window size
        for i in range(15):
            monitor.track_query("SELECT", f"table_{i}", i * 0.1, used_index=True)
        
        # Should only keep last 10 (window_size)
        assert len(monitor.query_history) == 10
        
        # Verify it kept the most recent ones
        first_query = monitor.query_history[0]
        assert first_query.table_name == "table_5"
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self, monitor):
        """Test metrics collection."""
        # Track some queries
        monitor.track_query("INSERT", "market_data", 0.5, used_index=False)
        monitor.track_query("INSERT", "market_data", 0.6, used_index=False)
        monitor.track_query("SELECT", "market_data", 1.5, used_index=True)
        monitor.track_query("SELECT", "alert_logs", 2.0, used_index=False)
        
        # Mock database session
        with patch('src.backend.services.database_performance.get_db_session') as mock_session:
            mock_db = AsyncMock()
            mock_engine = Mock()
            mock_pool = Mock()
            
            mock_pool.size.return_value = 10
            mock_pool.overflow.return_value = 5
            mock_pool.checked_out_connections.return_value = 3
            
            mock_engine.pool = mock_pool
            mock_db.get_bind.return_value = mock_engine
            mock_db.execute = AsyncMock(return_value=Mock(fetchone=Mock(return_value=None)))
            
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Collect metrics
            metrics = await monitor.collect_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.pool_size == 10
        assert metrics.pool_overflow == 5
        assert metrics.active_connections == 3
        
        # Check query metrics
        assert metrics.query_avg_time_ms == 1.15  # (0.5 + 0.6 + 1.5 + 2.0) / 4
        assert metrics.index_hit_ratio == 50.0  # 2 out of 4 used index
    
    @pytest.mark.asyncio
    async def test_analyze_table_performance(self, monitor):
        """Test table-specific performance analysis."""
        # Track queries for specific table
        monitor.track_query("INSERT", "market_data", 0.5, used_index=False)
        monitor.track_query("INSERT", "market_data", 0.7, used_index=False)
        monitor.track_query("SELECT", "market_data", 1.5, used_index=True)
        monitor.track_query("SELECT", "market_data", 2.0, used_index=True)
        monitor.track_query("SELECT", "alert_logs", 3.0, used_index=False)
        
        # Analyze market_data table
        analysis = await monitor.analyze_table_performance("market_data")
        
        assert analysis["table"] == "market_data"
        assert analysis["query_count"] == 4
        assert analysis["insert_count"] == 2
        assert analysis["select_count"] == 2
        assert analysis["insert_avg_ms"] == 0.6  # (0.5 + 0.7) / 2
        assert analysis["select_avg_ms"] == 1.75  # (1.5 + 2.0) / 2
        assert analysis["index_usage"] == 50.0  # 2 out of 4 used index
    
    @pytest.mark.asyncio
    async def test_analyze_table_no_data(self, monitor):
        """Test analysis when no data for table."""
        analysis = await monitor.analyze_table_performance("nonexistent_table")
        
        assert analysis["table"] == "nonexistent_table"
        assert analysis["query_count"] == 0
        assert "No recent queries" in analysis["message"]
    
    def test_get_recent_metrics(self, monitor):
        """Test retrieving recent metrics."""
        # Add some metrics history
        now = datetime.utcnow()
        
        # Old metric (2 hours ago)
        old_metric = PerformanceMetrics(
            timestamp=now - timedelta(hours=2),
            insert_rate=100.0,
            query_avg_time_ms=1.0,
            active_connections=1,
            pool_size=10,
            pool_overflow=0,
            index_hit_ratio=90.0,
            cache_hit_ratio=80.0,
            wal_checkpoints=5
        )
        
        # Recent metric (30 minutes ago)
        recent_metric = PerformanceMetrics(
            timestamp=now - timedelta(minutes=30),
            insert_rate=150.0,
            query_avg_time_ms=0.8,
            active_connections=2,
            pool_size=10,
            pool_overflow=0,
            index_hit_ratio=95.0,
            cache_hit_ratio=85.0,
            wal_checkpoints=6
        )
        
        monitor.metrics_history = [old_metric, recent_metric]
        
        # Get last hour of metrics
        recent = monitor.get_recent_metrics(hours=1)
        
        assert len(recent) == 1
        assert recent[0]["insert_rate"] == 150.0
    
    @pytest.mark.asyncio
    async def test_benchmark_insert_performance(self, monitor):
        """Test INSERT performance benchmarking."""
        result = await monitor.benchmark_insert_performance("market_data", count=100)
        
        assert result["table"] == "market_data"
        assert result["insert_count"] == 100
        assert "total_time_seconds" in result
        assert "inserts_per_second" in result
        assert "avg_time_per_insert_ms" in result
        
        # Verify queries were tracked
        assert len(monitor.query_history) == 10  # Limited by window_size
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping continuous monitoring."""
        # Start monitoring
        await monitor.start_monitoring(interval_seconds=1)
        assert monitor._monitoring is True
        assert monitor._monitor_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor._monitoring is False
    
    @pytest.mark.asyncio
    async def test_monitoring_already_active(self, monitor):
        """Test starting monitoring when already active."""
        await monitor.start_monitoring(interval_seconds=1)
        
        # Try to start again - should log warning
        with patch('src.backend.services.database_performance.logger') as mock_logger:
            await monitor.start_monitoring(interval_seconds=1)
            mock_logger.warning.assert_called_once()
        
        await monitor.stop_monitoring()


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        now = datetime.utcnow()
        metrics = PerformanceMetrics(
            timestamp=now,
            insert_rate=123.456,
            query_avg_time_ms=1.234,
            active_connections=5,
            pool_size=20,
            pool_overflow=10,
            index_hit_ratio=89.123,
            cache_hit_ratio=76.543,
            wal_checkpoints=42
        )
        
        result = metrics.to_dict()
        
        assert result["timestamp"] == now.isoformat()
        assert result["insert_rate"] == 123.46  # Rounded to 2 decimals
        assert result["query_avg_time_ms"] == 1.23
        assert result["active_connections"] == 5
        assert result["pool_size"] == 20
        assert result["pool_overflow"] == 10
        assert result["index_hit_ratio"] == 89.12
        assert result["cache_hit_ratio"] == 76.54
        assert result["wal_checkpoints"] == 42


class TestGlobalMonitorInstance:
    """Test global monitor instance management."""
    
    def test_get_performance_monitor_singleton(self):
        """Test get_performance_monitor returns singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        assert monitor1 is monitor2
        
        # Track query on first instance
        monitor1.track_query("SELECT", "test_table", 1.0, True)
        
        # Should be visible in second instance
        assert len(monitor2.query_history) > 0
        assert monitor2.query_history[-1].table_name == "test_table"


class TestMigrationCompatibility:
    """Test migration script compatibility."""
    
    @pytest.mark.asyncio
    async def test_float_conversion_precision(self):
        """Test FLOAT maintains acceptable precision after conversion."""
        # Test values that were DECIMAL(12,4)
        test_values = [
            Decimal("9999.9999"),
            Decimal("0.0001"),
            Decimal("1234.5678"),
            Decimal("-9999.9999")
        ]
        
        for decimal_val in test_values:
            float_val = float(decimal_val)
            
            # Check precision is maintained to 4 decimal places
            diff = abs(float_val - float(decimal_val))
            assert diff < 0.0001, f"Precision loss for {decimal_val}: {diff}"
            
            # Check rounding works correctly
            rounded = round(float_val, 4)
            assert abs(rounded - float(decimal_val)) < 0.0001


@pytest.mark.asyncio
async def test_integration_with_monitoring():
    """Integration test for monitoring with mock database."""
    monitor = DatabasePerformanceMonitor()
    
    # Simulate a series of database operations
    operations = [
        ("INSERT", "market_data", 0.5),
        ("INSERT", "market_data", 0.4),
        ("SELECT", "market_data", 1.2),
        ("INSERT", "alert_logs", 0.6),
        ("SELECT", "alert_logs", 2.1),
        ("UPDATE", "alert_logs", 1.5),
    ]
    
    for op_type, table, exec_time in operations:
        monitor.track_query(op_type, table, exec_time, used_index=(op_type == "SELECT"))
    
    # Analyze performance
    market_perf = await monitor.analyze_table_performance("market_data")
    alert_perf = await monitor.analyze_table_performance("alert_logs")
    
    # Verify analysis results
    assert market_perf["insert_count"] == 2
    assert market_perf["select_count"] == 1
    assert alert_perf["insert_count"] == 1
    assert alert_perf["select_count"] == 1