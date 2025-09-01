"""
Unit tests for Phase 3 Database Performance & Integrity Extension.

Tests the advanced architecture features including partition management,
data archival, and enhanced monitoring with partition health tracking.
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from pathlib import Path

# Import Phase 3 components
from src.backend.services.partition_manager_service import (
    PartitionManagerService,
    PartitionManagerConfig,
    PartitionInfo,
    get_partition_manager_service
)
from src.backend.services.data_archival_service import (
    DataArchivalService,
    ArchivalConfig,
    ArchiveRecord,
    get_data_archival_service
)
from src.backend.services.database_monitoring_service import (
    DatabaseMonitoringService,
    PartitionMetrics,
    PartitionHealthMetrics,
    get_database_monitoring_service
)


class TestPartitionManagerService:
    """Test suite for PartitionManagerService."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PartitionManagerConfig(
            market_data_advance_months=1,
            alert_log_advance_quarters=1,
            market_data_retention_months=12,
            alert_log_retention_quarters=4,
            check_interval_hours=1
        )
    
    @pytest.fixture
    def partition_service(self, config):
        """Create partition manager service for testing."""
        return PartitionManagerService(config)
    
    def test_partition_service_initialization(self, partition_service, config):
        """Test partition service initializes correctly."""
        assert partition_service is not None
        assert partition_service.config == config
        assert partition_service._is_running == False
        assert partition_service._active_partitions == {'market_data': [], 'alert_logs': []}
    
    @pytest.mark.asyncio
    async def test_create_market_data_partition(self, partition_service):
        """Test creation of monthly MarketData partition."""
        with patch('src.backend.services.partition_manager_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            partition_name = await partition_service.create_market_data_partition(2025, 8)
            
            assert partition_name == "market_data_2025_08"
            mock_session.execute.assert_called()
            mock_session.commit.assert_called()
            
            # Check partition was added to tracking
            assert len(partition_service._active_partitions['market_data']) == 1
            partition_info = partition_service._active_partitions['market_data'][0]
            assert partition_info.partition_name == "market_data_2025_08"
            assert partition_info.partition_type == "monthly"
    
    @pytest.mark.asyncio
    async def test_create_alert_log_partition(self, partition_service):
        """Test creation of quarterly AlertLog partition."""
        with patch('src.backend.services.partition_manager_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            partition_name = await partition_service.create_alert_log_partition(2025, 3)
            
            assert partition_name == "alert_logs_2025_q3"
            mock_session.execute.assert_called()
            mock_session.commit.assert_called()
            
            # Check partition was added to tracking
            assert len(partition_service._active_partitions['alert_logs']) == 1
            partition_info = partition_service._active_partitions['alert_logs'][0]
            assert partition_info.partition_name == "alert_logs_2025_q3"
            assert partition_info.partition_type == "quarterly"
    
    @pytest.mark.asyncio
    async def test_partition_exists_check(self, partition_service):
        """Test partition existence checking."""
        with patch('src.backend.services.partition_manager_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.fetchone.return_value = ("test_partition",)  # Partition exists
            mock_session.execute.return_value = mock_result
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            exists = await partition_service._partition_exists("test_partition")
            assert exists == True
            
            mock_result.fetchone.return_value = None  # Partition doesn't exist
            exists = await partition_service._partition_exists("nonexistent_partition")
            assert exists == False
    
    @pytest.mark.asyncio
    async def test_start_stop_partition_management(self, partition_service):
        """Test starting and stopping partition management."""
        with patch.object(partition_service, '_discover_existing_partitions') as mock_discover, \
             patch.object(partition_service, '_ensure_future_partitions') as mock_ensure:
            
            mock_discover.return_value = asyncio.Future()
            mock_discover.return_value.set_result(None)
            
            mock_ensure.return_value = asyncio.Future()
            mock_ensure.return_value.set_result(None)
            
            await partition_service.start_partition_management()
            assert partition_service._is_running == True
            assert partition_service._background_task is not None
            
            await partition_service.stop_partition_management()
            assert partition_service._is_running == False
    
    def test_get_partition_status(self, partition_service):
        """Test getting partition status."""
        # Add some test partitions
        partition_service._active_partitions['market_data'].append(
            PartitionInfo(
                table_name="market_data",
                partition_name="market_data_2025_08",
                partition_type="monthly",
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
                created_at=datetime.now(),
                row_count=1000
            )
        )
        
        status = partition_service.get_partition_status()
        
        assert status["service_status"] == "stopped"
        assert status["partitions"]["market_data"][0]["name"] == "market_data_2025_08"
        assert status["partitions"]["market_data"][0]["row_count"] == 1000
        assert status["config"]["market_data_advance_months"] == 1
    
    def test_partition_manager_singleton(self):
        """Test partition manager singleton pattern."""
        service1 = get_partition_manager_service()
        service2 = get_partition_manager_service()
        assert service1 is service2


class TestDataArchivalService:
    """Test suite for DataArchivalService."""
    
    @pytest.fixture
    def temp_archive_path(self):
        """Create temporary archive directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config(self, temp_archive_path):
        """Create test configuration."""
        return ArchivalConfig(
            archive_base_path=temp_archive_path,
            enable_compression=True,
            verify_archives=True
        )
    
    @pytest.fixture
    def archival_service(self, config):
        """Create archival service for testing."""
        return DataArchivalService(config)
    
    def test_archival_service_initialization(self, archival_service, temp_archive_path):
        """Test archival service initializes correctly."""
        assert archival_service is not None
        assert archival_service.config.archive_base_path == temp_archive_path
        assert archival_service._archive_registry == []
        
        # Check directories were created
        base_path = Path(temp_archive_path)
        assert base_path.exists()
        assert (base_path / "market_data").exists()
        assert (base_path / "alert_logs").exists()
        assert (base_path / "registry").exists()
    
    @pytest.mark.asyncio
    async def test_export_partition_data(self, archival_service):
        """Test exporting partition data."""
        with patch('src.backend.services.data_archival_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_result = Mock()
            
            # Mock table data
            mock_result.keys.return_value = ['id', 'timestamp', 'price']
            mock_result.__iter__.return_value = iter([
                (1, datetime(2025, 8, 31, 12, 0), 100.0),
                (2, datetime(2025, 8, 31, 12, 1), 101.0)
            ])
            
            mock_session.execute.return_value = mock_result
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            export_data = await archival_service._export_partition_data("test_partition")
            
            assert export_data['partition_name'] == "test_partition"
            assert len(export_data['rows']) == 2
            assert export_data['rows'][0]['id'] == 1
            assert export_data['rows'][0]['price'] == 100.0
    
    @pytest.mark.asyncio
    async def test_archive_partition(self, archival_service):
        """Test complete partition archival process."""
        test_start_date = date(2025, 8, 1)
        test_end_date = date(2025, 8, 31)
        
        # Mock the export process
        export_data = {
            'partition_name': 'test_partition',
            'rows': [
                {'id': 1, 'timestamp': '2025-08-31T12:00:00', 'price': 100.0},
                {'id': 2, 'timestamp': '2025-08-31T12:01:00', 'price': 101.0}
            ],
            'schema': [],
            'indexes': []
        }
        
        with patch.object(archival_service, '_export_partition_data') as mock_export:
            mock_export.return_value = export_data
            
            archive_record = await archival_service.archive_partition(
                "test_partition", "market_data", test_start_date, test_end_date
            )
            
            assert archive_record.partition_name == "test_partition"
            assert archive_record.table_name == "market_data"
            assert archive_record.archived_row_count == 2
            assert archive_record.compressed == True
            
            # Check archive was registered
            assert len(archival_service._archive_registry) == 1
            assert archival_service._archive_registry[0] == archive_record
    
    def test_create_archive_path(self, archival_service, temp_archive_path):
        """Test archive path creation."""
        test_date = date(2025, 8, 1)
        
        archive_path = archival_service._create_archive_path(
            "market_data", "market_data_2025_08", test_date
        )
        
        expected_path = Path(temp_archive_path) / "market_data" / "2025" / "market_data_2025_08_2025-08-01.json.gz"
        assert archive_path == expected_path
    
    def test_find_archive_by_partition(self, archival_service):
        """Test finding archive by partition name."""
        # Add test archive record
        test_record = ArchiveRecord(
            partition_name="test_partition",
            table_name="market_data",
            archived_at=datetime.now(),
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 31),
            original_row_count=100,
            archived_row_count=100,
            archive_path="/test/path"
        )
        
        archival_service._archive_registry.append(test_record)
        
        found_record = archival_service.find_archive_by_partition("test_partition")
        assert found_record == test_record
        
        not_found = archival_service.find_archive_by_partition("nonexistent")
        assert not_found is None
    
    def test_get_archive_status(self, archival_service):
        """Test getting archive status."""
        # Add test records
        archival_service._archive_registry.extend([
            ArchiveRecord(
                partition_name="market_data_2025_07",
                table_name="market_data",
                archived_at=datetime.now(),
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 31),
                original_row_count=1000,
                archived_row_count=1000,
                archive_path="/test/path1"
            ),
            ArchiveRecord(
                partition_name="alert_logs_2025_q2",
                table_name="alert_logs",
                archived_at=datetime.now(),
                start_date=date(2025, 4, 1),
                end_date=date(2025, 6, 30),
                original_row_count=500,
                archived_row_count=500,
                archive_path="/test/path2"
            )
        ])
        
        status = archival_service.get_archive_status()
        
        assert status["total_archives"] == 2
        assert status["total_archived_rows"] == 1500
        assert len(status["archives_by_table"]["market_data"]) == 1
        assert len(status["archives_by_table"]["alert_logs"]) == 1
    
    def test_archival_service_singleton(self):
        """Test archival service singleton pattern."""
        service1 = get_data_archival_service()
        service2 = get_data_archival_service()
        assert service1 is service2


class TestEnhancedDatabaseMonitoring:
    """Test suite for enhanced database monitoring with partition health."""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service for testing."""
        return DatabaseMonitoringService()
    
    @pytest.mark.asyncio
    async def test_discover_partition_tables(self, monitoring_service):
        """Test discovery of partition tables."""
        with patch('src.backend.services.database_monitoring_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            
            # Mock market_data partitions
            mock_result1 = Mock()
            mock_result1.__iter__.return_value = iter([
                ('market_data_2025_08',),
                ('market_data_2025_09',)
            ])
            
            # Mock alert_logs partitions
            mock_result2 = Mock()
            mock_result2.__iter__.return_value = iter([
                ('alert_logs_2025_q3',),
            ])
            
            mock_session.execute.side_effect = [mock_result1, mock_result2]
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            partition_tables = await monitoring_service._discover_partition_tables(mock_session)
            
            assert len(partition_tables) == 3
            
            market_data_partitions = [p for p in partition_tables if p['base_table'] == 'market_data']
            alert_log_partitions = [p for p in partition_tables if p['base_table'] == 'alert_logs']
            
            assert len(market_data_partitions) == 2
            assert len(alert_log_partitions) == 1
            assert market_data_partitions[0]['type'] == 'monthly'
            assert alert_log_partitions[0]['type'] == 'quarterly'
    
    @pytest.mark.asyncio
    async def test_collect_single_partition_metrics(self, monitoring_service):
        """Test collecting metrics for a single partition."""
        with patch('src.backend.services.database_monitoring_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            
            # Mock row count query
            mock_count_result = Mock()
            mock_count_result.scalar.return_value = 1500
            
            # Mock timestamp query
            mock_timestamp_result = Mock()
            mock_timestamp_result.scalar.return_value = datetime(2025, 8, 31, 12, 0)
            
            mock_session.execute.side_effect = [mock_count_result, mock_timestamp_result]
            
            metrics = await monitoring_service._collect_single_partition_metrics(
                mock_session, "market_data_2025_08", "market_data", "monthly"
            )
            
            assert metrics is not None
            assert metrics.partition_name == "market_data_2025_08"
            assert metrics.table_name == "market_data"
            assert metrics.partition_type == "monthly"
            assert metrics.row_count == 1500
            assert metrics.health_status == "healthy"
    
    def test_extract_partition_dates(self, monitoring_service):
        """Test extracting dates from partition names."""
        # Test monthly partition
        start_date, end_date = monitoring_service._extract_partition_dates(
            "market_data_2025_08", "monthly"
        )
        
        assert start_date == date(2025, 8, 1)
        assert end_date == date(2025, 8, 31)
        
        # Test quarterly partition
        start_date, end_date = monitoring_service._extract_partition_dates(
            "alert_logs_2025_q3", "quarterly"
        )
        
        assert start_date == date(2025, 7, 1)  # Q3 starts in July
        assert end_date == date(2025, 9, 30)   # Q3 ends in September
    
    @pytest.mark.asyncio
    async def test_collect_partition_health_metrics(self, monitoring_service):
        """Test collecting comprehensive partition health metrics."""
        with patch.object(monitoring_service, '_discover_partition_tables') as mock_discover, \
             patch.object(monitoring_service, '_collect_single_partition_metrics') as mock_collect:
            
            # Mock discovered partitions
            mock_discover.return_value = [
                {'name': 'market_data_2025_08', 'base_table': 'market_data', 'type': 'monthly'},
                {'name': 'alert_logs_2025_q3', 'base_table': 'alert_logs', 'type': 'quarterly'}
            ]
            
            # Mock individual metrics
            mock_collect.side_effect = [
                PartitionMetrics(
                    partition_name="market_data_2025_08",
                    table_name="market_data",
                    partition_type="monthly",
                    start_date="2025-08-01",
                    end_date="2025-08-31",
                    row_count=1000,
                    size_mb=1.0,
                    health_status="healthy"
                ),
                PartitionMetrics(
                    partition_name="alert_logs_2025_q3",
                    table_name="alert_logs",
                    partition_type="quarterly",
                    start_date="2025-07-01",
                    end_date="2025-09-30",
                    row_count=500,
                    size_mb=0.5,
                    health_status="warning"
                )
            ]
            
            with patch('src.backend.services.database_monitoring_service.get_db_session') as mock_get_session:
                mock_session = AsyncMock()
                mock_get_session.return_value.__aenter__.return_value = mock_session
                
                health_metrics = await monitoring_service.collect_partition_health_metrics()
                
                assert health_metrics.total_partitions == 2
                assert health_metrics.active_partitions == 1  # Only healthy ones
                assert health_metrics.total_partitioned_rows == 1500
                assert health_metrics.total_partitioned_size_mb == 1.5
                assert health_metrics.partitions_by_table["market_data"] == 1
                assert health_metrics.partitions_by_table["alert_logs"] == 1
                assert len(health_metrics.partitions_needing_attention) == 1
                assert "alert_logs_2025_q3" in health_metrics.partitions_needing_attention


class TestPhase3Integration:
    """Integration tests for Phase 3 components."""
    
    @pytest.mark.asyncio
    async def test_services_initialization(self):
        """Test all Phase 3 services can be initialized."""
        # Test partition manager
        partition_service = get_partition_manager_service()
        assert partition_service is not None
        
        # Test archival service
        archival_service = get_data_archival_service()
        assert archival_service is not None
        
        # Test enhanced monitoring service
        monitoring_service = get_database_monitoring_service()
        assert monitoring_service is not None
    
    @pytest.mark.asyncio
    async def test_partition_manager_archival_integration(self):
        """Test integration between partition manager and archival service."""
        with patch('src.backend.services.partition_manager_service.get_db_session'), \
             patch('src.backend.services.data_archival_service.get_db_session'):
            
            partition_service = get_partition_manager_service()
            archival_service = get_data_archival_service()
            
            # Create a test partition
            await partition_service.create_market_data_partition(2025, 8)
            
            # Mock archival process
            with patch.object(archival_service, '_export_partition_data') as mock_export:
                mock_export.return_value = {
                    'partition_name': 'market_data_2025_08',
                    'rows': [{'id': 1, 'price': 100.0}],
                    'schema': [],
                    'indexes': []
                }
                
                # Archive the partition
                archive_record = await archival_service.archive_partition(
                    "market_data_2025_08", "market_data",
                    date(2025, 8, 1), date(2025, 8, 31)
                )
                
                assert archive_record.partition_name == "market_data_2025_08"
                assert len(archival_service._archive_registry) == 1
    
    @pytest.mark.asyncio
    async def test_monitoring_partition_integration(self):
        """Test integration between monitoring service and partition management."""
        monitoring_service = get_database_monitoring_service()
        
        with patch.object(monitoring_service, '_discover_partition_tables') as mock_discover:
            mock_discover.return_value = [
                {'name': 'market_data_2025_08', 'base_table': 'market_data', 'type': 'monthly'}
            ]
            
            with patch.object(monitoring_service, '_collect_single_partition_metrics') as mock_collect:
                mock_collect.return_value = PartitionMetrics(
                    partition_name="market_data_2025_08",
                    table_name="market_data",
                    partition_type="monthly",
                    start_date="2025-08-01",
                    end_date="2025-08-31",
                    row_count=1000,
                    health_status="healthy"
                )
                
                with patch('src.backend.services.database_monitoring_service.get_db_session') as mock_get_session:
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session
                    
                    partition_health = await monitoring_service.collect_partition_health_metrics()
                    
                    assert partition_health.total_partitions == 1
                    assert partition_health.total_partitioned_rows == 1000


class TestPhase3Performance:
    """Performance tests for Phase 3 components."""
    
    @pytest.mark.asyncio
    async def test_partition_creation_performance(self):
        """Test partition creation performance."""
        partition_service = PartitionManagerService()
        
        with patch('src.backend.services.partition_manager_service.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            start_time = datetime.now()
            
            # Create multiple partitions
            for month in range(1, 13):
                await partition_service.create_market_data_partition(2025, month)
            
            end_time = datetime.now()
            creation_time = (end_time - start_time).total_seconds()
            
            # Should create 12 partitions in reasonable time
            assert creation_time < 5.0  # Less than 5 seconds
            assert len(partition_service._active_partitions['market_data']) == 12
    
    @pytest.mark.asyncio
    async def test_monitoring_collection_performance(self):
        """Test partition monitoring collection performance."""
        monitoring_service = DatabaseMonitoringService()
        
        # Mock large number of partitions
        partition_tables = []
        for year in range(2023, 2026):
            for month in range(1, 13):
                partition_tables.append({
                    'name': f'market_data_{year}_{month:02d}',
                    'base_table': 'market_data',
                    'type': 'monthly'
                })
        
        with patch.object(monitoring_service, '_discover_partition_tables') as mock_discover:
            mock_discover.return_value = partition_tables
            
            with patch.object(monitoring_service, '_collect_single_partition_metrics') as mock_collect:
                mock_collect.return_value = PartitionMetrics(
                    partition_name="test",
                    table_name="market_data",
                    partition_type="monthly",
                    start_date="2025-01-01",
                    end_date="2025-01-31",
                    row_count=1000,
                    health_status="healthy"
                )
                
                with patch('src.backend.services.database_monitoring_service.get_db_session') as mock_get_session:
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session
                    
                    start_time = datetime.now()
                    
                    partition_health = await monitoring_service.collect_partition_health_metrics()
                    
                    end_time = datetime.now()
                    collection_time = (end_time - start_time).total_seconds()
                    
                    # Should collect metrics for 36 partitions in reasonable time
                    assert collection_time < 10.0  # Less than 10 seconds
                    assert partition_health.total_partitions == 36


# Direct testing without pytest for immediate validation
if __name__ == "__main__":
    print("=== Phase 3 Implementation Direct Tests ===")
    
    try:
        # Test imports
        from src.backend.services.partition_manager_service import get_partition_manager_service
        from src.backend.services.data_archival_service import get_data_archival_service
        from src.backend.services.database_monitoring_service import get_database_monitoring_service
        
        print("✓ All Phase 3 services import successfully")
        
        # Test service creation
        partition_service = get_partition_manager_service()
        archival_service = get_data_archival_service()
        monitoring_service = get_database_monitoring_service()
        
        print("✓ All Phase 3 services instantiate successfully")
        
        # Test singleton pattern
        partition_service2 = get_partition_manager_service()
        archival_service2 = get_data_archival_service()
        monitoring_service2 = get_database_monitoring_service()
        
        print(f"✓ PartitionManager singleton works: {partition_service is partition_service2}")
        print(f"✓ DataArchival singleton works: {archival_service is archival_service2}")
        print(f"✓ Monitoring singleton works: {monitoring_service is monitoring_service2}")
        
        # Test configuration
        config = PartitionManagerConfig()
        assert config.market_data_advance_months == 2
        assert config.alert_log_advance_quarters == 1
        print("✓ PartitionManagerConfig works correctly")
        
        # Test basic functionality
        status = partition_service.get_partition_status()
        assert "service_status" in status
        assert "partitions" in status
        print("✓ Partition status reporting works")
        
        archive_status = archival_service.get_archive_status()
        assert "total_archives" in archive_status
        print("✓ Archive status reporting works")
        
        print("=== Phase 3 Direct Tests: ALL PASSED ===")
        
    except Exception as e:
        print(f"✗ Phase 3 test failed: {e}")
        import traceback
        traceback.print_exc()