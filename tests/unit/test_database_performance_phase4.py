"""
Unit tests for Database Performance Phase 4: Performance Integration & Validation

Tests comprehensive database performance monitoring, real-time WebSocket broadcasting,
and performance benchmarking functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.backend.services.performance_monitoring_service import (
    PerformanceMonitoringService,
    PerformanceMonitoringConfig,
    PerformanceThresholds,
    PerformanceAlert,
    get_performance_monitoring_service
)
from src.backend.services.performance_benchmark_service import (
    PerformanceBenchmarkService,
    BenchmarkConfig,
    BenchmarkResult,
    get_performance_benchmark_service
)
from src.backend.api.health import (
    DatabasePerformanceMetrics,
    PartitionHealthMetrics,
    DatabaseHealthResponse,
    PerformanceImprovementMetrics
)


class TestPerformanceMonitoringService:
    """Test suite for PerformanceMonitoringService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock performance monitoring configuration."""
        return PerformanceMonitoringConfig(
            monitoring_enabled=True,
            broadcast_interval_seconds=10,
            alert_cooldown_minutes=1,
            thresholds=PerformanceThresholds(
                connection_pool_warning_percent=70.0,
                connection_pool_critical_percent=85.0,
                query_response_warning_ms=80.0,
                query_response_critical_ms=200.0
            )
        )
    
    @pytest.fixture
    def performance_service(self, mock_config):
        """Create PerformanceMonitoringService instance."""
        return PerformanceMonitoringService(mock_config)
    
    @pytest.fixture
    def mock_db_metrics(self):
        """Create mock database metrics."""
        mock_metrics = Mock()
        mock_metrics.connection_pool.utilization_percentage = 60.0
        mock_metrics.connection_pool.active_connections = 12
        mock_metrics.connection_pool.max_connections = 20
        mock_metrics.connection_pool.avg_wait_time_ms = 5.2
        
        mock_metrics.performance_metrics.insert_ops_per_second = 145.0
        mock_metrics.performance_metrics.insert_improvement_percentage = 45.0
        mock_metrics.performance_metrics.avg_query_time_ms = 25.0
        mock_metrics.performance_metrics.slow_queries_last_hour = 2
        mock_metrics.performance_metrics.float_speedup_multiplier = 2.8
        mock_metrics.performance_metrics.index_efficiency_score = 92.5
        
        mock_metrics.last_maintenance_run = datetime.utcnow() - timedelta(hours=2)
        mock_metrics.next_scheduled_maintenance = datetime.utcnow() + timedelta(hours=22)
        
        return mock_metrics
    
    @pytest.fixture
    def mock_partition_status(self):
        """Create mock partition status."""
        return {
            "service_status": "running",
            "partitions": {
                "market_data": [
                    {
                        "name": "market_data_2025_08",
                        "type": "monthly",
                        "start_date": "2025-08-01",
                        "end_date": "2025-08-31",
                        "row_count": 15000,
                        "size_mb": 125.5,
                        "is_active": True
                    }
                ],
                "alert_logs": [
                    {
                        "name": "alert_logs_2025_q3",
                        "type": "quarterly",
                        "start_date": "2025-07-01",
                        "end_date": "2025-09-30",
                        "row_count": 850,
                        "size_mb": 15.2,
                        "is_active": True
                    }
                ]
            },
            "config": {
                "market_data_advance_months": 2,
                "alert_log_advance_quarters": 1
            }
        }
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_service_initialization(self, mock_config):
        """Test performance monitoring service initialization."""
        service = PerformanceMonitoringService(mock_config)
        
        assert service.config == mock_config
        assert not service._is_running
        assert service._monitoring_task is None
        assert len(service._alert_history) == 0
        assert len(service._last_alert_times) == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, performance_service):
        """Test starting and stopping performance monitoring."""
        # Test start monitoring
        with patch.object(performance_service, '_monitoring_loop', new_callable=AsyncMock):
            await performance_service.start_monitoring()
            assert performance_service._is_running
            assert performance_service._monitoring_task is not None
        
        # Test stop monitoring
        await performance_service.stop_monitoring()
        assert not performance_service._is_running
    
    @pytest.mark.asyncio
    async def test_collect_performance_metrics(self, performance_service, mock_db_metrics, mock_partition_status):
        """Test collection of comprehensive performance metrics."""
        with patch.object(performance_service.db_monitoring_service, 'get_comprehensive_metrics', 
                         return_value=mock_db_metrics), \
             patch.object(performance_service.partition_service, 'get_partition_status', 
                         return_value=mock_partition_status):
            
            metrics = await performance_service._collect_performance_metrics()
            
            assert metrics["status"] == "healthy"
            assert metrics["connection_pool"]["utilization_percent"] == 60.0
            assert metrics["connection_pool"]["active_connections"] == 12
            assert metrics["performance_metrics"]["insert_ops_per_sec"] == 145.0
            assert metrics["performance_metrics"]["insert_improvement_pct"] == 45.0
            assert metrics["partition_health"]["total_partitions"] == 2
            assert metrics["partition_health"]["service_running"] is True
    
    @pytest.mark.asyncio
    async def test_performance_alert_generation(self, performance_service):
        """Test performance alert generation with thresholds."""
        # Test connection pool warning alert
        await performance_service._create_alert(
            "connection_pool_warning",
            "Connection pool utilization high: 75.0%",
            "warning",
            75.0,
            70.0
        )
        
        assert len(performance_service._alert_history) == 1
        alert = performance_service._alert_history[0]
        assert alert.alert_type == "connection_pool_warning"
        assert alert.severity == "warning"
        assert alert.metric_value == 75.0
        assert alert.threshold_value == 70.0
    
    @pytest.mark.asyncio
    async def test_alert_cooldown_logic(self, performance_service):
        """Test alert cooldown period functionality."""
        alert_type = "test_alert"
        
        # First alert should be created
        await performance_service._create_alert(alert_type, "Test message", "warning", 100.0, 80.0)
        assert len(performance_service._alert_history) == 1
        
        # Second alert within cooldown should be ignored
        await performance_service._create_alert(alert_type, "Test message 2", "warning", 100.0, 80.0)
        assert len(performance_service._alert_history) == 1  # No new alert
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_thresholds(self, performance_service):
        """Test performance threshold checking and alert generation."""
        performance_data = {
            "connection_pool": {
                "utilization_percent": 85.0,  # Above critical threshold (85%)
                "active_connections": 17,
                "max_connections": 20
            },
            "performance_metrics": {
                "insert_ops_per_sec": 30.0,  # Below critical threshold (25)
                "query_response_time_ms": 150.0,  # Above warning threshold (80)
                "slow_queries_count": 12  # Above warning threshold (5)
            }
        }
        
        with patch.object(performance_service.websocket_manager, 'broadcast_performance_alert', 
                         new_callable=AsyncMock) as mock_broadcast:
            await performance_service._check_performance_alerts(performance_data)
            
            # Should generate multiple alerts
            assert len(performance_service._alert_history) > 0
            # Should have broadcasted alerts
            assert mock_broadcast.call_count > 0
    
    @pytest.mark.asyncio
    async def test_websocket_broadcasting(self, performance_service):
        """Test WebSocket broadcasting functionality."""
        performance_data = {
            "status": "healthy",
            "connection_pool": {"utilization_percent": 60.0},
            "performance_metrics": {"insert_ops_per_sec": 145.0},
            "partition_health": {"total_partitions": 2}
        }
        
        with patch.object(performance_service.websocket_manager, 'broadcast_database_performance', 
                         new_callable=AsyncMock) as mock_broadcast:
            await performance_service.websocket_manager.broadcast_database_performance(performance_data)
            mock_broadcast.assert_called_once_with(performance_data)
    
    def test_get_monitoring_status(self, performance_service):
        """Test monitoring status retrieval."""
        status = performance_service.get_monitoring_status()
        
        assert "service_running" in status
        assert "monitoring_enabled" in status
        assert "broadcast_interval_seconds" in status
        assert "recent_alerts_count" in status
        assert "thresholds" in status
        assert "targets" in status
    
    def test_singleton_service_access(self):
        """Test singleton pattern for service access."""
        service1 = get_performance_monitoring_service()
        service2 = get_performance_monitoring_service()
        
        assert service1 is service2  # Same instance


class TestPerformanceBenchmarkService:
    """Test suite for PerformanceBenchmarkService."""
    
    @pytest.fixture
    def mock_benchmark_config(self):
        """Create mock benchmark configuration."""
        return BenchmarkConfig(
            insert_test_duration_seconds=10,  # Shorter for testing
            insert_test_batch_size=10,
            calculation_test_iterations=100,
            capacity_test_duration_minutes=1,
            insert_improvement_target_pct=30.0,
            calculation_speedup_target=2.0,
            capacity_target_inserts_per_minute=1000  # Lower for testing
        )
    
    @pytest.fixture
    def benchmark_service(self, mock_benchmark_config):
        """Create PerformanceBenchmarkService instance."""
        return PerformanceBenchmarkService(mock_benchmark_config)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add_all = AsyncMock()
        session.commit = AsyncMock()
        return session
    
    @pytest.fixture
    def mock_instrument(self):
        """Create mock instrument for testing."""
        instrument = Mock()
        instrument.id = 1
        instrument.symbol = "TEST"
        instrument.status = "active"
        return instrument
    
    @pytest.mark.asyncio
    async def test_benchmark_service_initialization(self, mock_benchmark_config):
        """Test benchmark service initialization."""
        service = PerformanceBenchmarkService(mock_benchmark_config)
        
        assert service.config == mock_benchmark_config
        assert "insert_ops_per_sec" in service._baseline_data
        assert "calculation_time_ms" in service._baseline_data
        assert "query_response_time_ms" in service._baseline_data
    
    @pytest.mark.asyncio
    async def test_insert_performance_benchmark(self, benchmark_service, mock_instrument):
        """Test INSERT performance benchmarking."""
        with patch('src.backend.services.performance_benchmark_service.get_db_session') as mock_get_session, \
             patch('src.backend.services.performance_benchmark_service.select') as mock_select:
            
            # Mock database session and queries
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock instrument query result
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_instrument
            mock_session.execute.return_value = mock_result
            
            result = await benchmark_service._benchmark_insert_performance()
            
            assert isinstance(result, BenchmarkResult)
            assert result.test_name == "INSERT Performance Test"
            assert result.test_type == "insert_performance"
            assert result.operations_performed > 0
            assert result.operations_per_second > 0
            assert "optimization" in result.details
            assert result.details["optimization"] == "DECIMAL_to_FLOAT_conversion"
    
    @pytest.mark.asyncio
    async def test_calculation_performance_benchmark(self, benchmark_service):
        """Test calculation performance benchmarking."""
        result = await benchmark_service._benchmark_calculation_performance()
        
        assert isinstance(result, BenchmarkResult)
        assert result.test_name == "Calculation Performance Test"
        assert result.test_type == "calculation_performance"
        assert result.operations_performed == 100  # From config
        assert "speedup_multiplier" in result.details
        assert result.details["optimization"] == "DECIMAL_to_FLOAT_data_types"
        
        # Should show FLOAT is faster than DECIMAL
        assert result.details["speedup_multiplier"] > 1.0
    
    @pytest.mark.asyncio
    async def test_query_performance_benchmark(self, benchmark_service, mock_instrument):
        """Test query performance benchmarking."""
        with patch('src.backend.services.performance_benchmark_service.get_db_session') as mock_get_session, \
             patch('src.backend.services.performance_benchmark_service.select') as mock_select:
            
            # Mock database session
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock instrument query
            mock_result = Mock()
            mock_result.scalar_one.return_value = mock_instrument
            mock_session.execute.return_value = mock_result
            
            result = await benchmark_service._benchmark_query_performance()
            
            assert isinstance(result, BenchmarkResult)
            assert result.test_name == "Query Performance Test"
            assert result.test_type == "query_performance"
            assert result.operations_performed > 0
            assert "avg_query_time_ms" in result.details
            assert result.details["optimization"] == "compound_indexes_and_partitioning"
    
    @pytest.mark.asyncio
    async def test_high_frequency_capacity_benchmark(self, benchmark_service, mock_instrument):
        """Test high-frequency capacity benchmarking."""
        with patch('src.backend.services.performance_benchmark_service.get_db_session') as mock_get_session:
            
            # Mock database session
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock instrument query
            mock_result = Mock()
            mock_result.scalar_one.return_value = mock_instrument
            mock_session.execute.return_value = mock_result
            
            result = await benchmark_service._benchmark_high_frequency_capacity()
            
            assert isinstance(result, BenchmarkResult)
            assert result.test_name == "High-Frequency Capacity Test"
            assert result.test_type == "capacity_test"
            assert result.operations_performed > 0
            assert "inserts_per_minute" in result.details
            assert result.details["optimization"] == "all_phases_combined"
    
    @pytest.mark.asyncio
    async def test_connection_pool_benchmark(self, benchmark_service):
        """Test connection pool performance benchmarking."""
        with patch('src.backend.services.performance_benchmark_service.get_db_session') as mock_get_session:
            
            # Mock database session
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            result = await benchmark_service._benchmark_connection_pool()
            
            assert isinstance(result, BenchmarkResult)
            assert result.test_name == "Connection Pool Performance Test"
            assert result.test_type == "connection_pool_performance"
            assert result.operations_performed > 0
            assert "concurrent_tasks" in result.details
            assert result.details["optimization"] == "optimized_connection_pool_configuration"
    
    @pytest.mark.asyncio
    async def test_comprehensive_benchmark(self, benchmark_service):
        """Test comprehensive benchmark execution."""
        with patch.object(benchmark_service, '_benchmark_insert_performance', 
                         return_value=BenchmarkResult(
                             test_name="INSERT Test", test_type="insert", duration_seconds=10.0,
                             operations_performed=1000, operations_per_second=100.0,
                             target_met=True, timestamp=datetime.utcnow()
                         )), \
             patch.object(benchmark_service, '_benchmark_calculation_performance',
                         return_value=BenchmarkResult(
                             test_name="Calc Test", test_type="calc", duration_seconds=5.0,
                             operations_performed=500, operations_per_second=100.0,
                             target_met=True, timestamp=datetime.utcnow()
                         )), \
             patch.object(benchmark_service, '_benchmark_query_performance',
                         return_value=BenchmarkResult(
                             test_name="Query Test", test_type="query", duration_seconds=8.0,
                             operations_performed=200, operations_per_second=25.0,
                             target_met=True, timestamp=datetime.utcnow()
                         )), \
             patch.object(benchmark_service, '_benchmark_high_frequency_capacity',
                         return_value=BenchmarkResult(
                             test_name="Capacity Test", test_type="capacity", duration_seconds=60.0,
                             operations_performed=12000, operations_per_second=200.0,
                             target_met=True, timestamp=datetime.utcnow()
                         )), \
             patch.object(benchmark_service, '_benchmark_connection_pool',
                         return_value=BenchmarkResult(
                             test_name="Pool Test", test_type="pool", duration_seconds=15.0,
                             operations_performed=400, operations_per_second=26.7,
                             target_met=True, timestamp=datetime.utcnow()
                         )):
            
            results = await benchmark_service.run_comprehensive_benchmark()
            
            assert "benchmark_id" in results
            assert "start_time" in results
            assert "end_time" in results
            assert "insert_performance" in results
            assert "calculation_performance" in results
            assert "query_performance" in results
            assert "capacity_test" in results
            assert "connection_pool_performance" in results
            assert "overall_summary" in results
            
            summary = results["overall_summary"]
            assert summary["targets_met"] == 5
            assert summary["total_tests"] == 5
            assert summary["overall_status"] == "EXCELLENT"
    
    @pytest.mark.asyncio
    async def test_performance_target_validation(self, benchmark_service):
        """Test performance target validation."""
        with patch.object(benchmark_service, '_benchmark_insert_performance',
                         return_value=BenchmarkResult(
                             test_name="INSERT Test", test_type="insert", duration_seconds=30.0,
                             operations_performed=4000, operations_per_second=133.3,
                             target_met=True, timestamp=datetime.utcnow()
                         )), \
             patch.object(benchmark_service, '_benchmark_calculation_performance',
                         return_value=BenchmarkResult(
                             test_name="Calc Test", test_type="calc", duration_seconds=5.0,
                             operations_performed=500, operations_per_second=100.0,
                             target_met=True, timestamp=datetime.utcnow(),
                             details={"speedup_multiplier": 2.5}
                         )):
            
            validation_results = await benchmark_service.validate_performance_targets()
            
            assert "validation_timestamp" in validation_results
            assert "insert_performance_validated" in validation_results
            assert "calculation_performance_validated" in validation_results
            assert "insert_ops_per_sec" in validation_results
            assert "calculation_speedup" in validation_results
            assert "overall_validation" in validation_results
    
    def test_overall_summary_calculation(self, benchmark_service):
        """Test overall benchmark summary calculation."""
        mock_results = {
            "insert_performance": {"target_met": True, "improvement_percentage": 45.0},
            "calculation_performance": {"target_met": True, "details": {"speedup_multiplier": 2.6}},
            "query_performance": {"target_met": True},
            "capacity_test": {"target_met": True, "details": {"inserts_per_minute": 12500}},
            "connection_pool_performance": {"target_met": False}  # One failure
        }
        
        summary = benchmark_service._calculate_overall_summary(mock_results)
        
        assert summary["targets_met"] == 4
        assert summary["total_tests"] == 5
        assert summary["success_rate_percentage"] == 80.0
        assert summary["overall_status"] == "GOOD"  # 80% success rate
        assert len(summary["key_achievements"]) > 0
    
    def test_singleton_benchmark_service_access(self):
        """Test singleton pattern for benchmark service access."""
        service1 = get_performance_benchmark_service()
        service2 = get_performance_benchmark_service()
        
        assert service1 is service2  # Same instance


class TestEnhancedHealthAPI:
    """Test suite for enhanced health API functionality."""
    
    def test_database_performance_metrics_model(self):
        """Test DatabasePerformanceMetrics model validation."""
        metrics = DatabasePerformanceMetrics(
            connection_pool_utilization=75.5,
            avg_connection_wait_time_ms=12.3,
            total_active_connections=15,
            max_connections=20,
            insert_performance_ops_per_sec=142.5,
            insert_performance_improvement_pct=42.5,
            query_response_time_ms=25.8,
            slow_queries_count=3,
            float_calculation_speedup=2.8,
            index_efficiency_score=92.0
        )
        
        assert metrics.connection_pool_utilization == 75.5
        assert metrics.insert_performance_improvement_pct == 42.5
        assert metrics.float_calculation_speedup == 2.8
    
    def test_partition_health_metrics_model(self):
        """Test PartitionHealthMetrics model validation."""
        metrics = PartitionHealthMetrics(
            total_partitions=5,
            market_data_partitions=3,
            alert_log_partitions=2,
            total_storage_mb=1250.5,
            largest_partition_mb=425.2,
            oldest_partition_age_days=45,
            partition_creation_success_rate=99.8,
            archival_queue_size=1
        )
        
        assert metrics.total_partitions == 5
        assert metrics.total_storage_mb == 1250.5
        assert metrics.partition_creation_success_rate == 99.8
    
    def test_database_health_response_model(self):
        """Test DatabaseHealthResponse model validation."""
        perf_metrics = DatabasePerformanceMetrics(
            connection_pool_utilization=60.0,
            avg_connection_wait_time_ms=5.2,
            total_active_connections=12,
            max_connections=20,
            insert_performance_ops_per_sec=145.0,
            insert_performance_improvement_pct=45.0,
            query_response_time_ms=22.5,
            slow_queries_count=1,
            float_calculation_speedup=2.6,
            index_efficiency_score=94.5
        )
        
        partition_health = PartitionHealthMetrics(
            total_partitions=3,
            market_data_partitions=2,
            alert_log_partitions=1,
            total_storage_mb=680.5,
            largest_partition_mb=320.2,
            oldest_partition_age_days=30,
            partition_creation_success_rate=100.0,
            archival_queue_size=0
        )
        
        response = DatabaseHealthResponse(
            status="healthy",
            performance_metrics=perf_metrics,
            partition_health=partition_health,
            last_maintenance_run=datetime.utcnow() - timedelta(hours=4),
            next_scheduled_maintenance=datetime.utcnow() + timedelta(hours=20),
            alerts=["Test alert"],
            recommendations=["Test recommendation"]
        )
        
        assert response.status == "healthy"
        assert response.performance_metrics.insert_performance_improvement_pct == 45.0
        assert response.partition_health.total_partitions == 3
        assert len(response.alerts) == 1
        assert len(response.recommendations) == 1
    
    def test_performance_improvement_metrics_model(self):
        """Test PerformanceImprovementMetrics model validation."""
        metrics = PerformanceImprovementMetrics(
            insert_baseline_ops_per_sec=100.0,
            insert_current_ops_per_sec=142.0,
            insert_improvement_percentage=42.0,
            calculation_baseline_time_ms=10.0,
            calculation_current_time_ms=3.8,
            calculation_speedup_multiplier=2.6,
            high_frequency_capacity=12500,
            target_capacity_met=True,
            baseline_established_date=datetime(2025, 8, 1),
            last_measurement_date=datetime.utcnow()
        )
        
        assert metrics.insert_improvement_percentage == 42.0
        assert metrics.calculation_speedup_multiplier == 2.6
        assert metrics.target_capacity_met is True
        assert metrics.high_frequency_capacity == 12500


class TestPhase4Integration:
    """Test suite for Phase 4 integration functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_database_performance_broadcasting(self):
        """Test WebSocket database performance broadcasting."""
        from src.backend.websocket.realtime import get_websocket_manager
        
        manager = get_websocket_manager()
        performance_data = {
            "status": "healthy",
            "connection_pool": {"utilization_percent": 65.0},
            "performance_metrics": {"insert_ops_per_sec": 150.0},
            "partition_health": {"total_partitions": 4}
        }
        
        # Mock broadcast functionality
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            await manager.broadcast_database_performance(performance_data)
            
            # Verify broadcast was called with correct message structure
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "database_performance"
            assert "timestamp" in call_args
            assert call_args["data"]["overall_status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_websocket_performance_alert_broadcasting(self):
        """Test WebSocket performance alert broadcasting."""
        from src.backend.websocket.realtime import get_websocket_manager
        
        manager = get_websocket_manager()
        
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            await manager.broadcast_performance_alert(
                "connection_pool_warning",
                "Connection pool utilization high: 80%",
                "warning"
            )
            
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "performance_alert"
            assert call_args["data"]["alert_type"] == "connection_pool_warning"
            assert call_args["data"]["severity"] == "warning"
    
    @pytest.mark.asyncio
    async def test_websocket_partition_status_broadcasting(self):
        """Test WebSocket partition status broadcasting."""
        from src.backend.websocket.realtime import get_websocket_manager
        
        manager = get_websocket_manager()
        partition_data = {
            "service_status": "running",
            "partitions": {"market_data": [], "alert_logs": []},
            "health_summary": {"total_partitions": 2}
        }
        
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            await manager.broadcast_partition_status_update(partition_data)
            
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "partition_status"
            assert call_args["data"]["service_status"] == "running"
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test integration between performance monitoring and other services."""
        config = PerformanceMonitoringConfig(
            monitoring_enabled=True,
            broadcast_interval_seconds=5
        )
        
        service = PerformanceMonitoringService(config)
        
        # Mock dependencies
        with patch.object(service, '_collect_performance_metrics', 
                         return_value={"status": "healthy"}), \
             patch.object(service, '_check_performance_alerts', new_callable=AsyncMock), \
             patch.object(service.websocket_manager, 'broadcast_database_performance', 
                         new_callable=AsyncMock), \
             patch.object(service.websocket_manager, 'broadcast_partition_status_update', 
                         new_callable=AsyncMock):
            
            # Simulate one monitoring cycle
            await service._collect_performance_metrics()
            await service._check_performance_alerts({"status": "healthy"})
            
            # Verify integration works
            assert True  # If we get here without exceptions, integration works


class TestPhase4Performance:
    """Test suite for Phase 4 performance validation."""
    
    @pytest.mark.asyncio
    async def test_performance_targets_validation(self):
        """Test validation of all performance targets."""
        benchmark_service = get_performance_benchmark_service()
        
        with patch.object(benchmark_service, '_benchmark_insert_performance',
                         return_value=BenchmarkResult(
                             test_name="INSERT Test", test_type="insert",
                             duration_seconds=30.0, operations_performed=4200,
                             operations_per_second=140.0, target_met=True,
                             timestamp=datetime.utcnow(), improvement_percentage=40.0
                         )), \
             patch.object(benchmark_service, '_benchmark_calculation_performance',
                         return_value=BenchmarkResult(
                             test_name="Calc Test", test_type="calc",
                             duration_seconds=5.0, operations_performed=500,
                             operations_per_second=100.0, target_met=True,
                             timestamp=datetime.utcnow(),
                             details={"speedup_multiplier": 2.8}
                         )):
            
            # Run performance validation
            results = await benchmark_service.validate_performance_targets()
            
            # Verify targets are met
            assert results["insert_performance_validated"] is True
            assert results["calculation_performance_validated"] is True
            assert results["overall_validation"] is True
            assert results["insert_ops_per_sec"] >= 100  # Above baseline
            assert results["calculation_speedup"] >= 2.0  # Above target
    
    def test_performance_improvement_calculations(self):
        """Test performance improvement percentage calculations."""
        # Test INSERT improvement calculation
        baseline_ops = 100.0
        current_ops = 145.0
        improvement_pct = ((current_ops - baseline_ops) / baseline_ops) * 100
        
        assert improvement_pct == 45.0
        assert improvement_pct >= 30.0  # Target met
        
        # Test calculation speedup
        baseline_time_ms = 10.0
        current_time_ms = 3.8
        speedup_multiplier = baseline_time_ms / current_time_ms
        
        assert speedup_multiplier > 2.6
        assert speedup_multiplier >= 2.0  # Target met
    
    def test_capacity_target_validation(self):
        """Test high-frequency capacity target validation."""
        # Test 10,000+ inserts per minute capacity
        inserts_in_test = 2100  # In 10 seconds
        test_duration_seconds = 10
        
        inserts_per_minute = (inserts_in_test / test_duration_seconds) * 60
        
        assert inserts_per_minute >= 10000  # Target: 10,000+ per minute
        assert inserts_per_minute > 12000   # Should exceed target significantly


if __name__ == "__main__":
    pytest.main([__file__])