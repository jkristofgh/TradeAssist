"""
Unit tests for Phase 2 Database Performance & Integrity Extension.

Tests the enhanced service layer components including optimized repository patterns,
database monitoring service, and updated models with soft delete functionality.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

# Import Phase 2 components
from src.backend.services.optimized_market_data_repository import (
    OptimizedMarketDataRepository,
    get_optimized_market_data_repository
)
from src.backend.services.database_monitoring_service import (
    DatabaseMonitoringService,
    get_database_monitoring_service,
    ConnectionPoolMetrics,
    DatabaseHealthMetrics
)
from src.backend.database.database_config import DatabaseConfig
from src.backend.models.market_data import MarketData
from src.backend.models.alert_logs import AlertLog
from src.backend.database.mixins import SoftDeleteMixin


class TestOptimizedMarketDataRepository:
    """Test suite for OptimizedMarketDataRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance for testing."""
        return OptimizedMarketDataRepository()
    
    @pytest.fixture
    def sample_market_data_records(self):
        """Sample market data records for testing."""
        base_time = datetime.utcnow()
        return [
            {
                "timestamp": base_time - timedelta(seconds=i),
                "instrument_id": 1,
                "price": 100.0 + i * 0.5,
                "bid": 99.5 + i * 0.5,
                "ask": 100.5 + i * 0.5,
                "volume": 1000 + i * 10
            }
            for i in range(10)
        ]
    
    @pytest.mark.asyncio
    async def test_repository_initialization(self, repository):
        """Test repository initializes correctly."""
        assert repository is not None
        assert repository.performance_monitor is not None
        assert repository._bulk_insert_threshold == 100
        assert repository._cache_ttl == 300
        assert isinstance(repository._query_cache, dict)
        assert isinstance(repository._cache_timestamps, dict)
    
    @pytest.mark.asyncio
    async def test_bulk_insert_market_data_empty_records(self, repository):
        """Test bulk insert with empty records raises ValueError."""
        with pytest.raises(ValueError, match="market_data_records cannot be empty"):
            await repository.bulk_insert_market_data([])
    
    @pytest.mark.asyncio
    @patch('src.backend.services.optimized_market_data_repository.get_db_session')
    async def test_bulk_insert_market_data_success(self, mock_get_session, repository, sample_market_data_records):
        """Test successful bulk insert operation."""
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.rowcount = len(sample_market_data_records)
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor
        repository.performance_monitor = Mock()
        repository.performance_monitor.track_query = Mock()
        
        # Execute bulk insert
        result = await repository.bulk_insert_market_data(sample_market_data_records)
        
        # Assertions
        assert result == len(sample_market_data_records)
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        repository.performance_monitor.track_query.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.backend.services.optimized_market_data_repository.get_db_session')
    async def test_get_active_market_data(self, mock_get_session, repository):
        """Test getting active market data records."""
        # Mock database session and results
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_records = [Mock(spec=MarketData) for _ in range(5)]
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor
        repository.performance_monitor = Mock()
        repository.performance_monitor.track_query = Mock()
        
        # Execute query
        result = await repository.get_active_market_data(
            instrument_id=1,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            limit=100
        )
        
        # Assertions
        assert result == mock_records
        mock_session.execute.assert_called_once()
        repository.performance_monitor.track_query.assert_called_once()
        
        # Verify query includes soft delete filter
        call_args = mock_session.execute.call_args[0][0]
        # Query should include deleted_at.is_(None) condition
        assert "deleted_at" in str(call_args).lower()
    
    @pytest.mark.asyncio
    @patch('src.backend.services.optimized_market_data_repository.get_db_session')
    async def test_get_latest_market_data(self, mock_get_session, repository):
        """Test getting latest market data for multiple instruments."""
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_record = Mock(spec=MarketData)
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor
        repository.performance_monitor = Mock()
        repository.performance_monitor.track_query = Mock()
        
        # Execute query
        instrument_ids = [1, 2, 3]
        result = await repository.get_latest_market_data(instrument_ids)
        
        # Assertions
        assert isinstance(result, dict)
        assert len(result) == len(instrument_ids)
        for instrument_id in instrument_ids:
            assert instrument_id in result
        
        # Should execute one query per instrument
        assert mock_session.execute.call_count == len(instrument_ids)
        repository.performance_monitor.track_query.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.backend.services.optimized_market_data_repository.get_db_session')
    async def test_soft_delete_market_data(self, mock_get_session, repository):
        """Test soft delete operation."""
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor
        repository.performance_monitor = Mock()
        repository.performance_monitor.track_query = Mock()
        
        # Execute soft delete
        record_ids = [1, 2, 3, 4, 5]
        result = await repository.soft_delete_market_data(record_ids)
        
        # Assertions
        assert result == 5
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        repository.performance_monitor.track_query.assert_called_once()
        
        # Verify update statement includes deleted_at
        call_args = mock_session.execute.call_args[0][0]
        assert "deleted_at" in str(call_args).lower()
    
    @pytest.mark.asyncio
    @patch('src.backend.services.optimized_market_data_repository.get_db_session')
    async def test_restore_market_data(self, mock_get_session, repository):
        """Test restore operation."""
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor
        repository.performance_monitor = Mock()
        repository.performance_monitor.track_query = Mock()
        
        # Execute restore
        record_ids = [1, 2, 3]
        result = await repository.restore_market_data(record_ids)
        
        # Assertions
        assert result == 3
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        repository.performance_monitor.track_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_market_data_record_valid(self, repository):
        """Test validation of valid market data record."""
        valid_record = {
            "timestamp": datetime.utcnow(),
            "instrument_id": 1,
            "price": 100.50,
            "bid": 100.25,
            "ask": 100.75,
            "volume": 1000
        }
        
        result = await repository._validate_market_data_record(valid_record)
        
        assert result is not None
        assert result["timestamp"] == valid_record["timestamp"]
        assert result["instrument_id"] == 1
        assert result["price"] == 100.50
        assert result["volume"] == 1000
    
    @pytest.mark.asyncio
    async def test_validate_market_data_record_missing_required(self, repository):
        """Test validation with missing required fields."""
        invalid_record = {
            "price": 100.50,
            # Missing timestamp and instrument_id
        }
        
        result = await repository._validate_market_data_record(invalid_record)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_market_data_record_invalid_types(self, repository):
        """Test validation with invalid data types."""
        invalid_record = {
            "timestamp": datetime.utcnow(),
            "instrument_id": "not_an_int",  # Invalid type
            "price": "not_a_float",  # Invalid type
        }
        
        result = await repository._validate_market_data_record(invalid_record)
        assert result is None
    
    def test_get_optimized_market_data_repository_singleton(self):
        """Test singleton pattern for repository."""
        repo1 = get_optimized_market_data_repository()
        repo2 = get_optimized_market_data_repository()
        assert repo1 is repo2


class TestDatabaseMonitoringService:
    """Test suite for DatabaseMonitoringService."""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance for testing."""
        return DatabaseMonitoringService()
    
    def test_monitoring_service_initialization(self, monitoring_service):
        """Test monitoring service initializes correctly."""
        assert monitoring_service is not None
        assert not monitoring_service.is_running
        assert monitoring_service._monitoring_task is None
        assert len(monitoring_service._metrics_history) == 0
        assert monitoring_service.thresholds["pool_utilization_warning"] == 70.0
        assert monitoring_service.thresholds["pool_utilization_critical"] == 85.0
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitoring_service):
        """Test starting monitoring service."""
        # Start monitoring
        await monitoring_service.start_monitoring(interval_seconds=1)
        
        # Verify service started
        assert monitoring_service.is_running
        assert monitoring_service._monitoring_task is not None
        
        # Stop monitoring to cleanup
        await monitoring_service.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitoring_service):
        """Test stopping monitoring service."""
        # Start then stop monitoring
        await monitoring_service.start_monitoring(interval_seconds=1)
        await monitoring_service.stop_monitoring()
        
        # Verify service stopped
        assert not monitoring_service.is_running
    
    @pytest.mark.asyncio
    @patch('src.backend.services.database_monitoring_service.engine')
    @patch('src.backend.services.database_monitoring_service.get_db_session')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_io_counters')
    async def test_collect_health_metrics(
        self, 
        mock_disk_io,
        mock_memory,
        mock_cpu,
        mock_get_session,
        mock_engine,
        monitoring_service
    ):
        """Test health metrics collection."""
        # Mock system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB available
        mock_disk_io.return_value.read_bytes = 1024 * 1024  # 1MB
        mock_disk_io.return_value.write_bytes = 2 * 1024 * 1024  # 2MB
        
        # Mock database engine and pool
        mock_pool = Mock()
        mock_pool.size.return_value = 20
        mock_pool.checkedin.return_value = 15
        mock_pool.checkedout.return_value = 5
        mock_pool.overflow.return_value = 0
        mock_pool._pool_size = 20
        mock_pool._max_overflow = 50
        mock_engine.pool = mock_pool
        
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 100 * 1024 * 1024  # 100MB database
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor
        monitoring_service._performance_monitor = Mock()
        mock_metrics = Mock()
        mock_metrics.insert_rate = 1000.0
        mock_metrics.query_avg_time_ms = 5.5
        mock_metrics.query_performance_history = [1, 2, 3]
        monitoring_service._performance_monitor.collect_metrics.return_value = mock_metrics
        
        # Collect metrics
        metrics = await monitoring_service.collect_health_metrics()
        
        # Assertions
        assert isinstance(metrics, DatabaseHealthMetrics)
        assert metrics.overall_status in ["healthy", "warning", "critical"]
        assert metrics.cpu_usage_percent == 45.5
        assert metrics.memory_usage_mb == 4096.0  # 4GB in MB
        assert metrics.connection_pool_metrics.pool_size == 20
        assert metrics.connection_pool_metrics.checked_out_connections == 5
        assert metrics.performance_metrics.insert_rate == 1000.0
    
    def test_analyze_health_status_healthy(self, monitoring_service):
        """Test health status analysis for healthy system."""
        # Create healthy metrics
        pool_metrics = ConnectionPoolMetrics(
            pool_utilization_percent=50.0,
            avg_connection_acquire_time_ms=10.0
        )
        
        from src.backend.services.database_performance import PerformanceMetrics
        perf_metrics = PerformanceMetrics(
            insert_rate=5000.0,
            query_avg_time_ms=15.0
        )
        
        health_metrics = DatabaseHealthMetrics(
            connection_pool_metrics=pool_metrics,
            performance_metrics=perf_metrics,
            cpu_usage_percent=45.0,
            memory_usage_mb=512.0
        )
        
        status, alerts = monitoring_service._analyze_health_status(health_metrics)
        
        assert status == "healthy"
        assert len(alerts) == 0
    
    def test_analyze_health_status_warning(self, monitoring_service):
        """Test health status analysis for system with warnings."""
        # Create warning-level metrics
        pool_metrics = ConnectionPoolMetrics(
            pool_utilization_percent=75.0,  # Above warning threshold
            avg_connection_acquire_time_ms=60.0  # Above warning threshold
        )
        
        from src.backend.services.database_performance import PerformanceMetrics
        perf_metrics = PerformanceMetrics(
            insert_rate=5000.0,
            query_avg_time_ms=150.0  # Above warning threshold
        )
        
        health_metrics = DatabaseHealthMetrics(
            connection_pool_metrics=pool_metrics,
            performance_metrics=perf_metrics,
            cpu_usage_percent=75.0,  # Above warning threshold
            memory_usage_mb=1500.0  # Above warning threshold
        )
        
        status, alerts = monitoring_service._analyze_health_status(health_metrics)
        
        assert status == "warning"
        assert len(alerts) > 0
        assert any("WARNING" in alert for alert in alerts)
    
    def test_analyze_health_status_critical(self, monitoring_service):
        """Test health status analysis for critical system."""
        # Create critical-level metrics
        pool_metrics = ConnectionPoolMetrics(
            pool_utilization_percent=90.0,  # Above critical threshold
            avg_connection_acquire_time_ms=250.0  # Above critical threshold
        )
        
        from src.backend.services.database_performance import PerformanceMetrics
        perf_metrics = PerformanceMetrics(
            insert_rate=5000.0,
            query_avg_time_ms=600.0  # Above critical threshold
        )
        
        health_metrics = DatabaseHealthMetrics(
            connection_pool_metrics=pool_metrics,
            performance_metrics=perf_metrics,
            cpu_usage_percent=90.0,  # Above critical threshold
            memory_usage_mb=2500.0  # Above critical threshold
        )
        
        status, alerts = monitoring_service._analyze_health_status(health_metrics)
        
        assert status == "critical"
        assert len(alerts) > 0
        assert any("CRITICAL" in alert for alert in alerts)
    
    def test_add_alert_callback(self, monitoring_service):
        """Test adding alert callback."""
        def test_callback(status: str, message: str):
            pass
        
        monitoring_service.add_alert_callback(test_callback)
        
        assert len(monitoring_service._alert_callbacks) == 1
        assert test_callback in monitoring_service._alert_callbacks
    
    def test_track_connection_acquire(self, monitoring_service):
        """Test tracking connection acquisition time."""
        monitoring_service.track_connection_acquire(25.5)
        monitoring_service.track_connection_acquire(30.2)
        
        assert len(monitoring_service._connection_acquire_times) == 2
        assert monitoring_service._connection_acquire_count == 2
        assert 25.5 in monitoring_service._connection_acquire_times
        assert 30.2 in monitoring_service._connection_acquire_times
    
    def test_get_database_monitoring_service_singleton(self):
        """Test singleton pattern for monitoring service."""
        service1 = get_database_monitoring_service()
        service2 = get_database_monitoring_service()
        assert service1 is service2


class TestDatabaseConfig:
    """Test suite for DatabaseConfig."""
    
    def test_get_connection_pool_config(self):
        """Test connection pool configuration."""
        config = DatabaseConfig.get_connection_pool_config()
        
        assert config["pool_size"] == 20
        assert config["max_overflow"] == 50
        assert config["pool_timeout"] == 30
        assert config["pool_recycle"] == 3600
        assert config["pool_pre_ping"] is True
    
    def test_get_sqlite_performance_config(self):
        """Test SQLite performance configuration."""
        config = DatabaseConfig.get_sqlite_performance_config()
        
        assert config["journal_mode"] == "WAL"
        assert config["synchronous"] == "NORMAL"
        assert config["cache_size"] == "10000"
        assert config["temp_store"] == "MEMORY"
        assert config["busy_timeout"] == "30000"
    
    def test_get_performance_monitoring_config(self):
        """Test performance monitoring configuration."""
        config = DatabaseConfig.get_performance_monitoring_config()
        
        assert config["health_check_interval_seconds"] == 30
        assert config["pool_utilization_warning_percent"] == 70.0
        assert config["pool_utilization_critical_percent"] == 85.0
        assert config["target_insert_rate_per_second"] == 10000
        assert config["target_query_response_time_ms"] == 10
    
    def test_create_connection_string_sqlite(self):
        """Test SQLite connection string creation."""
        connection_string = DatabaseConfig.create_connection_string(
            database_type="sqlite",
            database_path="./test.db"
        )
        
        assert connection_string == "sqlite+aiosqlite:///./test.db"
    
    def test_create_connection_string_postgresql(self):
        """Test PostgreSQL connection string creation."""
        connection_string = DatabaseConfig.create_connection_string(
            database_type="postgresql",
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )
        
        assert connection_string == "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
    
    def test_create_connection_string_unsupported(self):
        """Test unsupported database type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseConfig.create_connection_string(database_type="mysql")


class TestUpdatedModels:
    """Test suite for updated models with SoftDeleteMixin."""
    
    def test_market_data_inherits_soft_delete_mixin(self):
        """Test MarketData inherits from SoftDeleteMixin."""
        assert issubclass(MarketData, SoftDeleteMixin)
        
        # Check that soft delete methods are available
        market_data = MarketData(
            timestamp=datetime.utcnow(),
            instrument_id=1,
            price=100.0
        )
        
        # Should have soft delete methods
        assert hasattr(market_data, 'soft_delete')
        assert hasattr(market_data, 'restore')
        assert hasattr(market_data, 'is_deleted')
        assert hasattr(market_data, 'is_active')
    
    def test_alert_log_inherits_soft_delete_mixin(self):
        """Test AlertLog inherits from SoftDeleteMixin."""
        assert issubclass(AlertLog, SoftDeleteMixin)
        
        # Check that soft delete methods are available
        alert_log = AlertLog(
            timestamp=datetime.utcnow(),
            rule_id=1,
            instrument_id=1,
            trigger_value=100.5,
            threshold_value=100.0,
            rule_condition="GREATER_THAN"
        )
        
        # Should have soft delete methods
        assert hasattr(alert_log, 'soft_delete')
        assert hasattr(alert_log, 'restore')
        assert hasattr(alert_log, 'is_deleted')
        assert hasattr(alert_log, 'is_active')
    
    def test_market_data_float_types(self):
        """Test MarketData uses Float types for price fields."""
        # Create instance to check field types
        market_data = MarketData(
            timestamp=datetime.utcnow(),
            instrument_id=1,
            price=100.50,
            bid=100.25,
            ask=100.75
        )
        
        # Check that float values are properly handled
        assert market_data.price == 100.50
        assert market_data.bid == 100.25
        assert market_data.ask == 100.75
        
        # Values should be Python floats, not Decimal
        assert isinstance(market_data.price, (float, type(None)))
        assert isinstance(market_data.bid, (float, type(None)))
        assert isinstance(market_data.ask, (float, type(None)))
    
    def test_alert_log_float_types(self):
        """Test AlertLog uses Float types for value fields."""
        # Create instance to check field types
        alert_log = AlertLog(
            timestamp=datetime.utcnow(),
            rule_id=1,
            instrument_id=1,
            trigger_value=100.75,
            threshold_value=100.50,
            rule_condition="GREATER_THAN"
        )
        
        # Check that float values are properly handled
        assert alert_log.trigger_value == 100.75
        assert alert_log.threshold_value == 100.50
        
        # Values should be Python floats
        assert isinstance(alert_log.trigger_value, float)
        assert isinstance(alert_log.threshold_value, float)


class TestPhase2Integration:
    """Integration tests for Phase 2 components."""
    
    @pytest.mark.asyncio
    @patch('src.backend.services.optimized_market_data_repository.get_db_session')
    async def test_repository_and_monitoring_integration(self, mock_get_session):
        """Test integration between repository and monitoring service."""
        # Create instances
        repository = OptimizedMarketDataRepository()
        monitoring_service = DatabaseMonitoringService()
        
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.rowcount = 10
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock performance monitor to verify integration
        mock_perf_monitor = Mock()
        repository.performance_monitor = mock_perf_monitor
        monitoring_service._performance_monitor = mock_perf_monitor
        
        # Execute repository operation
        sample_records = [
            {
                "timestamp": datetime.utcnow(),
                "instrument_id": 1,
                "price": 100.0
            }
            for _ in range(10)
        ]
        
        result = await repository.bulk_insert_market_data(sample_records)
        
        # Verify integration
        assert result == 10
        mock_perf_monitor.track_query.assert_called_once_with(
            query_type="BULK_INSERT",
            table_name="market_data",
            execution_time_ms=pytest.approx(0, abs=1000),  # Allow some execution time variance
            record_count=10
        )
    
    def test_phase2_component_availability(self):
        """Test that all Phase 2 components are available and importable."""
        # Test repository
        repo = get_optimized_market_data_repository()
        assert repo is not None
        assert isinstance(repo, OptimizedMarketDataRepository)
        
        # Test monitoring service
        monitor = get_database_monitoring_service()
        assert monitor is not None
        assert isinstance(monitor, DatabaseMonitoringService)
        
        # Test database config
        config = DatabaseConfig.get_connection_pool_config()
        assert config is not None
        assert isinstance(config, dict)
        
        # Test model updates
        assert issubclass(MarketData, SoftDeleteMixin)
        assert issubclass(AlertLog, SoftDeleteMixin)


if __name__ == "__main__":
    pytest.main([__file__])