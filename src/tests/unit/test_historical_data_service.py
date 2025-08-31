"""
Unit tests for Historical Data Service.

Tests the historical data service functionality including data retrieval,
caching, query management, and integration with external data sources.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from src.backend.services.historical_data_service import (
    HistoricalDataService,
    HistoricalDataRequest,
    HistoricalDataResult,
    AggregationRequest
)
from src.backend.models.historical_data import DataFrequency, DataSource, MarketDataBar


class TestHistoricalDataService:
    """Test cases for HistoricalDataService class."""
    
    @pytest.fixture
    def service(self):
        """Create a HistoricalDataService instance for testing."""
        return HistoricalDataService()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample historical data request."""
        return HistoricalDataRequest(
            symbols=["AAPL", "SPY"],
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            frequency=DataFrequency.DAILY.value,
            include_extended_hours=False,
            max_records=100
        )
    
    @pytest.fixture
    def sample_bars(self):
        """Create sample bar data."""
        return [
            {
                "timestamp": datetime.utcnow() - timedelta(days=2),
                "open": 150.00,
                "high": 155.00,
                "low": 149.00,
                "close": 154.00,
                "volume": 100000
            },
            {
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "open": 154.00,
                "high": 158.00,
                "low": 153.00,
                "close": 157.00,
                "volume": 120000
            }
        ]
    
    def test_service_initialization(self, service):
        """Test service initialization with default values."""
        assert service.schwab_client is None
        assert not service.is_running
        assert service._requests_served == 0
        assert service._cache_hits == 0
        assert service._api_calls_made == 0
        assert len(service._cache) == 0
        assert service._cache_ttl_minutes == 15
    
    @pytest.mark.asyncio
    async def test_service_start_stop_demo_mode(self, service):
        """Test service startup and shutdown in demo mode."""
        with patch('src.backend.services.historical_data_service.settings.DEMO_MODE', True):
            with patch.object(service, '_initialize_data_sources', new_callable=AsyncMock):
                # Start service
                await service.start()
                assert service.is_running
                assert len(service._background_tasks) > 0
                
                # Stop service
                await service.stop()
                assert not service.is_running
                assert len(service._background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_demo_mode(self, service, sample_request):
        """Test historical data fetch in demo mode."""
        with patch('src.backend.services.historical_data_service.settings.DEMO_MODE', True):
            with patch.object(service, '_initialize_data_sources', new_callable=AsyncMock):
                await service.start()
                
                try:
                    results = await service.fetch_historical_data(sample_request)
                
                # Verify results
                assert len(results) == len(sample_request.symbols)
                assert service._requests_served == 1
                
                for result in results:
                    assert isinstance(result, HistoricalDataResult)
                    assert result.symbol in sample_request.symbols
                    assert result.frequency == sample_request.frequency
                    assert result.data_source == "Demo"
                    assert len(result.bars) > 0
                    
                    # Verify bar structure
                    for bar in result.bars:
                        assert "timestamp" in bar
                        assert "open" in bar
                        assert "high" in bar
                        assert "low" in bar
                        assert "close" in bar
                        assert "volume" in bar
                        assert bar["open"] > 0
                        assert bar["high"] >= bar["open"]
                        assert bar["low"] <= bar["close"]
                        
            finally:
                await service.stop()
    
    @pytest.mark.asyncio
    async def test_fetch_data_caching(self, service, sample_request):
        """Test data caching functionality."""
        with patch('src.backend.services.historical_data_service.settings.DEMO_MODE', True):
            with patch.object(service, '_initialize_data_sources', new_callable=AsyncMock):
                await service.start()
            
            try:
                # First request
                results1 = await service.fetch_historical_data(sample_request)
                assert service._cache_hits == 0
                
                # Second identical request should hit cache
                results2 = await service.fetch_historical_data(sample_request)
                assert service._cache_hits == len(sample_request.symbols)
                
                # Verify cache hit flag
                for result in results2:
                    assert result.cached
                    
            finally:
                await service.stop()
    
    def test_build_cache_key(self, service):
        """Test cache key generation."""
        request = HistoricalDataRequest(
            symbols=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            frequency=DataFrequency.DAILY.value
        )
        
        key = service._build_cache_key("AAPL", request)
        
        expected_parts = [
            "AAPL",
            DataFrequency.DAILY.value,
            "2024-01-01T00:00:00",
            "2024-01-31T00:00:00",
            "False",
            "none"
        ]
        expected_key = "|".join(expected_parts)
        
        assert key == expected_key
    
    def test_generate_mock_data(self, service):
        """Test mock data generation."""
        request = HistoricalDataRequest(
            symbols=["AAPL"],
            start_date=datetime.utcnow() - timedelta(days=5),
            end_date=datetime.utcnow(),
            frequency=DataFrequency.DAILY.value
        )
        
        bars = service._generate_mock_data("AAPL", request)
        
        assert len(bars) > 0
        assert len(bars) <= 6  # 5 days + potential partial day
        
        for bar in bars:
            assert "timestamp" in bar
            assert "open" in bar
            assert "high" in bar
            assert "low" in bar
            assert "close" in bar
            assert "volume" in bar
            
            # Validate OHLC relationships
            assert bar["high"] >= bar["open"]
            assert bar["high"] >= bar["close"]
            assert bar["low"] <= bar["open"]
            assert bar["low"] <= bar["close"]
            assert bar["volume"] > 0
    
    @pytest.mark.asyncio
    async def test_invalid_request_validation(self, service):
        """Test request validation for invalid parameters."""
        with patch.object(service, '_initialize_data_sources', new_callable=AsyncMock):
            await service.start()
        
        try:
            # Empty symbols list
            with pytest.raises(ValueError, match="At least one symbol is required"):
                invalid_request = HistoricalDataRequest(symbols=[])
                await service.fetch_historical_data(invalid_request)
            
            # Invalid frequency
            with pytest.raises(ValueError, match="Unsupported frequency"):
                invalid_request = HistoricalDataRequest(
                    symbols=["AAPL"],
                    frequency="invalid_freq"
                )
                await service.fetch_historical_data(invalid_request)
                
        finally:
            await service.stop()
    
    @pytest.mark.asyncio
    async def test_store_historical_data(self, service, sample_bars):
        """Test storing historical data in database."""
        with patch('src.backend.services.historical_data_service.get_db_session') as mock_session:
            # Mock database session
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.rollback = AsyncMock()
            
            # Mock data source
            mock_data_source = Mock()
            mock_data_source.id = 1
            
            with patch.object(service, '_get_or_create_data_source', return_value=mock_data_source):
                stored_count = await service.store_historical_data(
                    symbol="AAPL",
                    bars=sample_bars,
                    frequency=DataFrequency.DAILY.value,
                    data_source_name="Test"
                )
                
                assert stored_count == len(sample_bars)
                assert mock_session_instance.commit.called
    
    @pytest.mark.asyncio
    async def test_save_and_load_query(self, service):
        """Test query saving and loading functionality."""
        with patch('src.backend.services.historical_data_service.get_db_session') as mock_session:
            # Mock database session for save
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            # Mock query object
            mock_query = Mock()
            mock_query.id = 123
            mock_session_instance.add = Mock()
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()
            
            # Test save query
            query_id = await service.save_query(
                name="Test Query",
                description="Test Description",
                symbols=["AAPL", "SPY"],
                frequency=DataFrequency.DAILY.value,
                is_favorite=True
            )
            
            assert mock_session_instance.commit.called
            
            # Test load query (mock the database response)
            with patch('src.backend.services.historical_data_service.select'):
                mock_result = AsyncMock()
                mock_query_data = Mock()
                mock_query_data.id = 123
                mock_query_data.name = "Test Query"
                mock_query_data.description = "Test Description"
                mock_query_data.symbols = '["AAPL", "SPY"]'
                mock_query_data.frequency = DataFrequency.DAILY.value
                mock_query_data.filters = None
                mock_query_data.is_favorite = True
                mock_query_data.execution_count = 0
                mock_query_data.last_executed = None
                mock_query_data.start_date = None
                mock_query_data.end_date = None
                
                mock_result.scalar_one_or_none.return_value = mock_query_data
                mock_session_instance.execute.return_value = mock_result
                
                loaded_query = await service.load_query(123)
                
                assert loaded_query is not None
                assert loaded_query["name"] == "Test Query"
                assert loaded_query["symbols"] == ["AAPL", "SPY"]
                assert loaded_query["is_favorite"] is True
    
    def test_performance_stats(self, service):
        """Test performance statistics calculation."""
        # Simulate some activity
        service._requests_served = 100
        service._cache_hits = 25
        service._api_calls_made = 75
        service._total_bars_cached = 1000
        service._cache = {"key1": "data1", "key2": "data2"}
        
        stats = service.get_performance_stats()
        
        assert stats["requests_served"] == 100
        assert stats["cache_hits"] == 25
        assert stats["cache_hit_rate_percent"] == 25.0
        assert stats["api_calls_made"] == 75
        assert stats["total_bars_cached"] == 1000
        assert stats["cache_size"] == 2
        assert stats["service_running"] == service.is_running
        assert "schwab_client_connected" in stats
    
    def test_aggregation_frequency_validation(self, service):
        """Test aggregation frequency hierarchy validation."""
        # Valid aggregation (1min to 1h)
        valid_request = AggregationRequest(
            symbol="AAPL",
            source_frequency=DataFrequency.ONE_MINUTE.value,
            target_frequency=DataFrequency.ONE_HOUR.value
        )
        
        # This would be tested in the actual aggregation method
        # For now, just verify the request structure
        assert valid_request.symbol == "AAPL"
        assert valid_request.source_frequency == DataFrequency.ONE_MINUTE.value
        assert valid_request.target_frequency == DataFrequency.ONE_HOUR.value
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, service):
        """Test cache expiration functionality."""
        # Set short TTL for testing
        service._cache_ttl_minutes = 0.01  # ~0.6 seconds
        
        # Add data to cache
        cache_key = "test_key"
        test_data = HistoricalDataResult(
            symbol="AAPL",
            bars=[],
            start_date=None,
            end_date=None,
            frequency=DataFrequency.DAILY.value,
            total_bars=0,
            data_source="Test"
        )
        
        await service._cache_data(cache_key, test_data)
        
        # Immediately should be available
        cached_data = await service._get_cached_data(cache_key)
        assert cached_data is not None
        
        # Wait for expiration
        await asyncio.sleep(1)
        
        # Should be expired
        expired_data = await service._get_cached_data(cache_key)
        assert expired_data is None
        assert cache_key not in service._cache
    
    @pytest.mark.asyncio
    async def test_error_handling_in_fetch(self, service):
        """Test error handling during data fetch."""
        with patch('src.backend.services.historical_data_service.settings.DEMO_MODE', True):
            with patch.object(service, '_initialize_data_sources', new_callable=AsyncMock):
                await service.start()
            
            try:
                # Mock _fetch_symbol_data to raise exception
                with patch.object(service, '_fetch_symbol_data', side_effect=Exception("API Error")):
                    request = HistoricalDataRequest(symbols=["AAPL"])
                    results = await service.fetch_historical_data(request)
                    
                    # Should still return results, but with error indication
                    assert len(results) == 1
                    assert results[0].symbol == "AAPL"
                    assert results[0].total_bars == 0
                    assert results[0].data_source == "error"
                    
            finally:
                await service.stop()


class TestHistoricalDataModels:
    """Test cases for historical data model classes."""
    
    def test_historical_data_request_validation(self):
        """Test HistoricalDataRequest validation."""
        # Valid request
        request = HistoricalDataRequest(
            symbols=["AAPL", "SPY"],
            frequency=DataFrequency.DAILY.value
        )
        
        assert request.symbols == ["AAPL", "SPY"]
        assert request.frequency == DataFrequency.DAILY.value
        assert request.start_date is None
        assert request.end_date is None
        assert not request.include_extended_hours
        assert request.max_records is None
    
    def test_historical_data_result_structure(self):
        """Test HistoricalDataResult structure."""
        bars = [
            {"timestamp": datetime.utcnow(), "open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000}
        ]
        
        result = HistoricalDataResult(
            symbol="AAPL",
            bars=bars,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            frequency=DataFrequency.DAILY.value,
            total_bars=len(bars),
            data_source="Test"
        )
        
        assert result.symbol == "AAPL"
        assert len(result.bars) == 1
        assert result.frequency == DataFrequency.DAILY.value
        assert result.total_bars == 1
        assert result.data_source == "Test"
        assert not result.cached  # Default value
    
    def test_aggregation_request_structure(self):
        """Test AggregationRequest structure."""
        request = AggregationRequest(
            symbol="AAPL",
            source_frequency=DataFrequency.ONE_MINUTE.value,
            target_frequency=DataFrequency.ONE_HOUR.value,
            start_date=datetime.utcnow() - timedelta(days=1)
        )
        
        assert request.symbol == "AAPL"
        assert request.source_frequency == DataFrequency.ONE_MINUTE.value
        assert request.target_frequency == DataFrequency.ONE_HOUR.value
        assert request.start_date is not None
        assert request.end_date is None


class TestDataFrequencyEnum:
    """Test cases for DataFrequency enum."""
    
    def test_all_frequencies_defined(self):
        """Test that all expected frequencies are defined."""
        expected_frequencies = [
            "1min", "5min", "15min", "30min", "1h", "4h", "1d", "1w", "1M"
        ]
        
        actual_frequencies = [f.value for f in DataFrequency]
        
        for freq in expected_frequencies:
            assert freq in actual_frequencies
    
    def test_frequency_enum_values(self):
        """Test specific frequency enum values."""
        assert DataFrequency.ONE_MINUTE.value == "1min"
        assert DataFrequency.FIVE_MINUTE.value == "5min"
        assert DataFrequency.DAILY.value == "1d"
        assert DataFrequency.WEEKLY.value == "1w"
        assert DataFrequency.MONTHLY.value == "1M"