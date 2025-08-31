"""
Comprehensive tests for DataAggregationService - Phase 3 Enhancement
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.services.data_aggregation_service import (
    DataAggregationService, AggregationMethod, AggregationResult, GapInfo
)
from src.backend.services.cache_service import CacheService, CacheConfig


@pytest.fixture
async def cache_service():
    """Cache service fixture for aggregation testing."""
    config = CacheConfig(default_ttl=300)
    service = CacheService(config)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture
async def aggregation_service(cache_service):
    """Data aggregation service fixture."""
    service = DataAggregationService(cache_service)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture
def sample_bars():
    """Sample bar data for testing."""
    base_time = datetime(2023, 1, 1, 9, 30)  # Market open
    bars = []
    
    for i in range(60):  # 60 minutes of 1-minute bars
        bars.append({
            "timestamp": base_time + timedelta(minutes=i),
            "symbol": "AAPL",
            "open_price": 150.0 + i * 0.1,
            "high_price": 151.0 + i * 0.1,
            "low_price": 149.0 + i * 0.1,
            "close_price": 150.5 + i * 0.1,
            "volume": 1000 + i * 10
        })
    
    return bars


class TestDataAggregationService:
    """Test data aggregation service functionality."""
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, cache_service):
        """Test service start and stop lifecycle."""
        service = DataAggregationService(cache_service)
        
        assert not service.is_running
        
        await service.start()
        assert service.is_running
        
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_frequency_hierarchy_validation(self, aggregation_service):
        """Test frequency hierarchy validation."""
        # Should have proper frequency hierarchy
        hierarchy = aggregation_service.frequency_hierarchy
        
        assert "1m" in hierarchy
        assert "5m" in hierarchy
        assert "1h" in hierarchy
        assert "1d" in hierarchy
        
        # Should be ordered by minutes
        frequencies = list(hierarchy.keys())
        minutes = [hierarchy[f] for f in frequencies]
        assert minutes == sorted(minutes)
    
    @pytest.mark.asyncio
    async def test_aggregate_data_basic(self, aggregation_service):
        """Test basic data aggregation functionality."""
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            # Mock source data - 4 x 1-minute bars to aggregate to 1 x 4-minute bar
            source_bars = [
                {
                    "timestamp": datetime(2023, 1, 1, 9, 30),
                    "symbol": "AAPL",
                    "open_price": 150.0,
                    "high_price": 152.0,
                    "low_price": 149.0,
                    "close_price": 151.0,
                    "volume": 1000
                },
                {
                    "timestamp": datetime(2023, 1, 1, 9, 31),
                    "symbol": "AAPL", 
                    "open_price": 151.0,
                    "high_price": 153.0,
                    "low_price": 150.0,
                    "close_price": 152.0,
                    "volume": 1100
                },
                {
                    "timestamp": datetime(2023, 1, 1, 9, 32),
                    "symbol": "AAPL",
                    "open_price": 152.0,
                    "high_price": 154.0,
                    "low_price": 151.0,
                    "close_price": 153.0,
                    "volume": 900
                },
                {
                    "timestamp": datetime(2023, 1, 1, 9, 33),
                    "symbol": "AAPL",
                    "open_price": 153.0,
                    "high_price": 155.0,
                    "low_price": 152.0,
                    "close_price": 154.0,
                    "volume": 1200
                }
            ]
            mock_fetch.return_value = source_bars
            
            result = await aggregation_service.aggregate_data(
                symbol="AAPL",
                source_frequency="1m",
                target_frequency="5m",  # Should aggregate into 1 bar
                start_date=datetime(2023, 1, 1, 9, 30),
                end_date=datetime(2023, 1, 1, 9, 35)
            )
            
            assert isinstance(result, AggregationResult)
            assert result.symbol == "AAPL"
            assert result.source_frequency == "1m"
            assert result.target_frequency == "5m"
            assert len(result.bars) == 1
            
            # Check aggregated values
            bar = result.bars[0]
            assert bar["open_price"] == 150.0  # First open
            assert bar["close_price"] == 154.0  # Last close
            assert bar["high_price"] == 155.0   # Highest high
            assert bar["low_price"] == 149.0    # Lowest low
            assert bar["volume"] == 4200        # Sum of volumes
    
    @pytest.mark.asyncio
    async def test_aggregate_data_validation(self, aggregation_service):
        """Test aggregation parameter validation."""
        # Test invalid symbol
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            await aggregation_service.aggregate_data("", "1m", "5m", datetime.now(), datetime.now())
        
        # Test unsupported frequencies
        with pytest.raises(ValueError, match="Unsupported source frequency"):
            await aggregation_service.aggregate_data("AAPL", "invalid", "5m", datetime.now(), datetime.now())
        
        with pytest.raises(ValueError, match="Unsupported target frequency"):
            await aggregation_service.aggregate_data("AAPL", "1m", "invalid", datetime.now(), datetime.now())
        
        # Test invalid frequency relationship (target must be higher than source)
        with pytest.raises(ValueError, match="Target frequency .* must be higher than source frequency"):
            await aggregation_service.aggregate_data("AAPL", "5m", "1m", datetime.now(), datetime.now())
        
        # Test invalid date range
        future_date = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="Start date must be before end date"):
            await aggregation_service.aggregate_data("AAPL", "1m", "5m", future_date, datetime.now())
    
    @pytest.mark.asyncio
    async def test_aggregate_empty_data(self, aggregation_service):
        """Test aggregation with no source data."""
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = []
            
            result = await aggregation_service.aggregate_data(
                symbol="AAPL",
                source_frequency="1m", 
                target_frequency="5m",
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 2)
            )
            
            assert len(result.bars) == 0
            assert result.stats["source_bars"] == 0
            assert result.stats["target_bars"] == 0
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, aggregation_service):
        """Test that aggregation results are properly cached."""
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = [
                {
                    "timestamp": datetime(2023, 1, 1, 9, 30),
                    "symbol": "AAPL",
                    "open_price": 150.0,
                    "high_price": 151.0,
                    "low_price": 149.0,
                    "close_price": 150.5,
                    "volume": 1000
                }
            ]
            
            # First call should fetch data
            result1 = await aggregation_service.aggregate_data(
                symbol="AAPL",
                source_frequency="1m",
                target_frequency="5m",
                start_date=datetime(2023, 1, 1, 9, 30),
                end_date=datetime(2023, 1, 1, 9, 35),
                use_cache=True
            )
            
            assert not result1.cache_hit
            assert mock_fetch.call_count == 1
            
            # Second call should use cache
            result2 = await aggregation_service.aggregate_data(
                symbol="AAPL",
                source_frequency="1m", 
                target_frequency="5m",
                start_date=datetime(2023, 1, 1, 9, 30),
                end_date=datetime(2023, 1, 1, 9, 35),
                use_cache=True
            )
            
            assert result2.cache_hit
            assert mock_fetch.call_count == 1  # Should not call again
    
    @pytest.mark.asyncio
    async def test_calculate_vwap(self, aggregation_service, sample_bars):
        """Test VWAP calculation functionality."""
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = sample_bars[:10]  # First 10 bars
            
            vwap_data = await aggregation_service.calculate_vwap(
                symbol="AAPL",
                frequency="1m",
                start_date=datetime(2023, 1, 1, 9, 30),
                end_date=datetime(2023, 1, 1, 9, 40),
                period_minutes=5  # 5-minute VWAP periods
            )
            
            # Should have 2 VWAP periods (10 minutes / 5 minutes per period)
            assert len(vwap_data) == 2
            
            for vwap_bar in vwap_data:
                assert "vwap" in vwap_bar
                assert "volume" in vwap_bar
                assert "bars_count" in vwap_bar
                assert vwap_bar["symbol"] == "AAPL"
                assert vwap_bar["vwap"] > 0
    
    @pytest.mark.asyncio
    async def test_gap_detection(self, aggregation_service):
        """Test gap detection functionality."""
        # Create bars with a gap
        bars_with_gap = [
            {
                "timestamp": datetime(2023, 1, 1, 9, 30),
                "symbol": "AAPL",
                "open_price": 150.0,
                "high_price": 151.0,
                "low_price": 149.0,
                "close_price": 150.5,
                "volume": 1000
            },
            {
                "timestamp": datetime(2023, 1, 1, 9, 31),
                "symbol": "AAPL",
                "open_price": 150.5,
                "high_price": 151.5,
                "low_price": 149.5,
                "close_price": 151.0,
                "volume": 1100
            },
            # Gap here - missing 9:32, 9:33, 9:34
            {
                "timestamp": datetime(2023, 1, 1, 9, 35),
                "symbol": "AAPL",
                "open_price": 151.0,
                "high_price": 152.0,
                "low_price": 150.0,
                "close_price": 151.5,
                "volume": 900
            }
        ]
        
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = bars_with_gap
            
            gaps = await aggregation_service.detect_gaps(
                symbol="AAPL",
                frequency="1m",
                start_date=datetime(2023, 1, 1, 9, 30),
                end_date=datetime(2023, 1, 1, 9, 36)
            )
            
            assert len(gaps) == 1
            gap = gaps[0]
            assert isinstance(gap, GapInfo)
            assert gap.symbol == "AAPL"
            assert gap.frequency == "1m"
            assert gap.expected_bars == 3  # Missing 3 one-minute bars
            assert gap.gap_duration_minutes == 3
    
    @pytest.mark.asyncio
    async def test_aggregation_stats(self, aggregation_service):
        """Test aggregation service statistics."""
        # Initially should have no activity
        stats = await aggregation_service.get_aggregation_stats()
        assert stats["aggregations_performed"] == 0
        assert stats["cache_hits"] == 0
        assert stats["is_running"] == True
        
        # Perform some aggregations
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = [
                {
                    "timestamp": datetime(2023, 1, 1, 9, 30),
                    "symbol": "AAPL",
                    "open_price": 150.0,
                    "high_price": 151.0,
                    "low_price": 149.0,
                    "close_price": 150.5,
                    "volume": 1000
                }
            ]
            
            await aggregation_service.aggregate_data(
                "AAPL", "1m", "5m",
                datetime(2023, 1, 1, 9, 30),
                datetime(2023, 1, 1, 9, 35)
            )
        
        stats = await aggregation_service.get_aggregation_stats()
        assert stats["aggregations_performed"] == 1


class TestAggregationMethods:
    """Test different aggregation methods."""
    
    @pytest.mark.asyncio
    async def test_ohlcv_aggregation(self, aggregation_service):
        """Test OHLCV aggregation method."""
        bars = [
            {
                "timestamp": datetime(2023, 1, 1, 9, 30),
                "open_price": 100.0,
                "high_price": 102.0,
                "low_price": 99.0,
                "close_price": 101.0,
                "volume": 1000,
                "symbol": "TEST"
            },
            {
                "timestamp": datetime(2023, 1, 1, 9, 31),
                "open_price": 101.0,
                "high_price": 103.0,
                "low_price": 100.0,
                "close_price": 102.0,
                "volume": 1500,
                "symbol": "TEST"
            }
        ]
        
        result = await aggregation_service._aggregate_bar_group(bars, AggregationMethod.OHLCV)
        
        assert result["open_price"] == 100.0  # First bar's open
        assert result["close_price"] == 102.0  # Last bar's close
        assert result["high_price"] == 103.0   # Highest high
        assert result["low_price"] == 99.0     # Lowest low
        assert result["volume"] == 2500        # Sum of volumes
        assert result["symbol"] == "TEST"
    
    @pytest.mark.asyncio
    async def test_vwap_aggregation(self, aggregation_service):
        """Test VWAP aggregation method."""
        bars = [
            {
                "timestamp": datetime(2023, 1, 1, 9, 30),
                "high_price": 102.0,
                "low_price": 98.0,
                "close_price": 100.0,
                "volume": 1000,
                "symbol": "TEST"
            },
            {
                "timestamp": datetime(2023, 1, 1, 9, 31),
                "high_price": 104.0,
                "low_price": 100.0,
                "close_price": 102.0,
                "volume": 2000,
                "symbol": "TEST"
            }
        ]
        
        result = await aggregation_service._aggregate_bar_group(bars, AggregationMethod.VWAP)
        
        # VWAP calculation: ((102+98+100)/3 * 1000 + (104+100+102)/3 * 2000) / (1000+2000)
        expected_vwap = ((100.0 * 1000) + (102.0 * 2000)) / 3000
        
        assert result["symbol"] == "TEST"
        assert result["volume"] == 3000
        assert result["bars_count"] == 2
        assert abs(result["vwap"] - expected_vwap) < 0.01  # Allow small floating point error


class TestPerformanceScenarios:
    """Test performance-related scenarios."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_aggregation(self, aggregation_service):
        """Test aggregation with large datasets."""
        # Create 1000 bars (simulating a full trading day of minute bars)
        large_dataset = []
        base_time = datetime(2023, 1, 1, 9, 30)
        
        for i in range(1000):
            large_dataset.append({
                "timestamp": base_time + timedelta(minutes=i),
                "symbol": "AAPL",
                "open_price": 150.0 + (i % 10),
                "high_price": 151.0 + (i % 10),
                "low_price": 149.0 + (i % 10),
                "close_price": 150.5 + (i % 10),
                "volume": 1000 + i
            })
        
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = large_dataset
            
            # Aggregate to hourly bars
            result = await aggregation_service.aggregate_data(
                symbol="AAPL",
                source_frequency="1m",
                target_frequency="1h",
                start_date=base_time,
                end_date=base_time + timedelta(minutes=1000)
            )
            
            # Should handle large dataset efficiently
            assert len(result.bars) > 0
            assert result.execution_time_ms < 5000  # Should complete within 5 seconds
            assert result.stats["source_bars"] == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_aggregations(self, aggregation_service):
        """Test concurrent aggregation operations."""
        sample_bars = [
            {
                "timestamp": datetime(2023, 1, 1, 9, 30),
                "symbol": "AAPL",
                "open_price": 150.0,
                "high_price": 151.0,
                "low_price": 149.0,
                "close_price": 150.5,
                "volume": 1000
            }
        ]
        
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.return_value = sample_bars
            
            # Run multiple aggregations concurrently
            tasks = []
            for i in range(5):
                task = aggregation_service.aggregate_data(
                    symbol=f"SYMBOL_{i}",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=datetime(2023, 1, 1, 9, 30),
                    end_date=datetime(2023, 1, 1, 9, 35)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result.symbol == f"SYMBOL_{i}"
                assert len(result.bars) >= 0


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, aggregation_service):
        """Test handling of database errors."""
        with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
            mock_fetch.side_effect = Exception("Database connection failed")
            
            with pytest.raises(RuntimeError, match="Aggregation failed"):
                await aggregation_service.aggregate_data(
                    symbol="AAPL",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 2)
                )
    
    @pytest.mark.asyncio
    async def test_invalid_aggregation_method(self, aggregation_service):
        """Test handling of invalid aggregation methods."""
        bars = [{"symbol": "TEST"}]
        
        with pytest.raises(ValueError, match="Unsupported aggregation method"):
            await aggregation_service._aggregate_bar_group(bars, "invalid_method")
    
    @pytest.mark.asyncio
    async def test_empty_bars_aggregation(self, aggregation_service):
        """Test aggregation with empty bar groups."""
        result = await aggregation_service._aggregate_bar_group([], AggregationMethod.OHLCV)
        assert result == {}


class TestTimeHandling:
    """Test time and frequency handling."""
    
    @pytest.mark.asyncio
    async def test_daily_aggregation(self, aggregation_service):
        """Test daily bar aggregation."""
        # Create hourly bars throughout a day
        hourly_bars = []
        base_date = datetime(2023, 1, 1, 0, 0)
        
        for hour in range(24):
            hourly_bars.append({
                "timestamp": base_date + timedelta(hours=hour),
                "symbol": "AAPL",
                "open_price": 150.0 + hour,
                "high_price": 151.0 + hour,
                "low_price": 149.0 + hour,
                "close_price": 150.5 + hour,
                "volume": 1000
            })
        
        aggregated = await aggregation_service._perform_aggregation(
            hourly_bars, "1d", AggregationMethod.OHLCV
        )
        
        # Should aggregate into 1 daily bar
        assert len(aggregated) == 1
        daily_bar = aggregated[0]
        
        assert daily_bar["open_price"] == 150.0  # First hour's open
        assert daily_bar["close_price"] == 173.5  # Last hour's close (150.5 + 23)
        assert daily_bar["high_price"] == 174.0   # Highest hour's high (151.0 + 23)
        assert daily_bar["low_price"] == 149.0    # Lowest hour's low
        assert daily_bar["volume"] == 24000       # Sum of all volumes
    
    @pytest.mark.asyncio 
    async def test_weekly_aggregation(self, aggregation_service):
        """Test weekly bar aggregation."""
        # Create daily bars for a week
        daily_bars = []
        base_date = datetime(2023, 1, 2)  # Monday
        
        for day in range(7):  # Full week
            daily_bars.append({
                "timestamp": base_date + timedelta(days=day),
                "symbol": "AAPL",
                "open_price": 150.0 + day,
                "high_price": 155.0 + day,
                "low_price": 145.0 + day,
                "close_price": 152.0 + day,
                "volume": 1000000
            })
        
        aggregated = await aggregation_service._perform_aggregation(
            daily_bars, "1w", AggregationMethod.OHLCV
        )
        
        # Should aggregate into 1 weekly bar
        assert len(aggregated) == 1
        weekly_bar = aggregated[0]
        
        assert weekly_bar["open_price"] == 150.0    # Monday's open
        assert weekly_bar["close_price"] == 158.0   # Sunday's close (152.0 + 6)
        assert weekly_bar["high_price"] == 161.0    # Highest day's high (155.0 + 6)
        assert weekly_bar["low_price"] == 145.0     # Lowest day's low
        assert weekly_bar["volume"] == 7000000      # Sum of all volumes