"""
Performance tests for Phase 3 enhancements.

Validates that performance targets are met:
- Query response times <500ms target for typical requests
- Caching reduces database load by >70% for repeated queries  
- Data aggregation produces results in <200ms for typical operations
- System handles concurrent users without performance degradation
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from src.backend.services.cache_service import CacheService, CacheConfig
from src.backend.services.data_aggregation_service import DataAggregationService
from src.backend.services.historical_data_service import HistoricalDataService


class TestPerformanceTargets:
    """Test that Phase 3 performance targets are met."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_performance_targets(self):
        """Test cache performance meets targets."""
        config = CacheConfig(
            default_ttl=300,
            max_memory_cache_items=1000
        )
        cache_service = CacheService(config)
        await cache_service.start()
        
        try:
            # Performance target: Cache operations should be very fast
            test_data = {"symbol": "AAPL", "data": list(range(1000))}
            
            # Test set performance
            start_time = time.time()
            for i in range(100):
                await cache_service.set(f"perf_test_{i}", test_data)
            set_time = (time.time() - start_time) * 1000  # ms
            
            # Should be very fast - under 100ms for 100 operations
            assert set_time < 100, f"Cache set operations too slow: {set_time:.2f}ms"
            
            # Test get performance
            start_time = time.time()
            for i in range(100):
                result = await cache_service.get(f"perf_test_{i}")
                assert result == test_data
            get_time = (time.time() - start_time) * 1000  # ms
            
            # Should be very fast - under 50ms for 100 operations
            assert get_time < 50, f"Cache get operations too slow: {get_time:.2f}ms"
            
            # Test cache hit rate
            stats = await cache_service.get_comprehensive_stats()
            hit_rate = stats["memory"]["hit_rate"]
            
            # Should have high hit rate for repeated access
            assert hit_rate > 90, f"Cache hit rate too low: {hit_rate}%"
            
        finally:
            await cache_service.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_aggregation_performance_targets(self):
        """Test data aggregation performance meets targets."""
        config = CacheConfig(default_ttl=300)
        cache_service = CacheService(config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        try:
            # Create sample data for aggregation
            sample_bars = []
            base_time = datetime.now()
            
            for i in range(300):  # 5 hours of minute bars
                sample_bars.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "symbol": "AAPL",
                    "open_price": 150.0 + i * 0.01,
                    "high_price": 151.0 + i * 0.01,
                    "low_price": 149.0 + i * 0.01,
                    "close_price": 150.5 + i * 0.01,
                    "volume": 1000 + i
                })
            
            with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
                mock_fetch.return_value = sample_bars
                
                # Test aggregation performance - target <200ms
                start_time = time.time()
                result = await aggregation_service.aggregate_data(
                    symbol="AAPL",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=base_time,
                    end_date=base_time + timedelta(hours=5)
                )
                execution_time = (time.time() - start_time) * 1000
                
                # Should meet performance target
                assert execution_time < 200, f"Aggregation too slow: {execution_time:.2f}ms"
                assert len(result.bars) == 60  # 300 minutes / 5 minutes = 60 bars
                
                # Test cached aggregation performance - should be much faster
                start_time = time.time()
                cached_result = await aggregation_service.aggregate_data(
                    symbol="AAPL",
                    source_frequency="1m",
                    target_frequency="5m", 
                    start_date=base_time,
                    end_date=base_time + timedelta(hours=5)
                )
                cached_execution_time = (time.time() - start_time) * 1000
                
                # Cached result should be much faster
                assert cached_execution_time < 50, f"Cached aggregation too slow: {cached_execution_time:.2f}ms"
                assert cached_result.cache_hit
        
        finally:
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_historical_data_service_performance(self):
        """Test historical data service performance targets."""
        config = CacheConfig(default_ttl=300)
        cache_service = CacheService(config)
        await cache_service.start()
        
        service = HistoricalDataService(cache_service)
        
        # Mock the database operations to focus on service performance
        with patch.object(service, '_fetch_symbol_data') as mock_fetch:
            mock_data = []
            for i in range(100):
                mock_data.append({
                    "timestamp": datetime.now() + timedelta(minutes=i),
                    "open": 150.0 + i * 0.1,
                    "high": 151.0 + i * 0.1,
                    "low": 149.0 + i * 0.1,
                    "close": 150.5 + i * 0.1,
                    "volume": 1000 + i * 10
                })
            mock_fetch.return_value = (mock_data, "mock_source")
            
            await service.start()
            
            try:
                # Test query response time - target <500ms
                start_time = time.time()
                results = await service.fetch_historical_data_with_progress(
                    symbols=["AAPL", "GOOGL", "MSFT"],
                    asset_class="stock",
                    frequency="1d",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now(),
                    websocket_updates=False
                )
                execution_time = (time.time() - start_time) * 1000
                
                # Should meet performance target
                assert execution_time < 500, f"Historical data query too slow: {execution_time:.2f}ms"
                assert len(results) == 3  # 3 symbols
                
                # Test cached query performance
                start_time = time.time()
                cached_results = await service.fetch_historical_data_with_progress(
                    symbols=["AAPL", "GOOGL", "MSFT"],
                    asset_class="stock", 
                    frequency="1d",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now(),
                    websocket_updates=False
                )
                cached_execution_time = (time.time() - start_time) * 1000
                
                # Cached queries should be much faster
                assert cached_execution_time < 100, f"Cached query too slow: {cached_execution_time:.2f}ms"
                
            finally:
                await service.stop()
        
        await cache_service.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_user_performance(self):
        """Test system handles concurrent users without performance degradation."""
        config = CacheConfig(default_ttl=300, max_memory_cache_items=1000)
        cache_service = CacheService(config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        try:
            # Simulate concurrent users
            async def simulate_user(user_id: int):
                """Simulate a user performing operations."""
                # Cache operations
                await cache_service.set(f"user_{user_id}_data", {"user_id": user_id, "data": list(range(100))})
                await cache_service.get(f"user_{user_id}_data")
                
                # Aggregation operations
                sample_bars = [
                    {
                        "timestamp": datetime.now() + timedelta(minutes=i),
                        "symbol": f"SYMBOL_{user_id}",
                        "open_price": 100.0 + i,
                        "high_price": 101.0 + i,
                        "low_price": 99.0 + i,
                        "close_price": 100.5 + i,
                        "volume": 1000
                    }
                    for i in range(10)
                ]
                
                with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
                    mock_fetch.return_value = sample_bars
                    
                    await aggregation_service.aggregate_data(
                        symbol=f"SYMBOL_{user_id}",
                        source_frequency="1m",
                        target_frequency="5m",
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(minutes=10)
                    )
            
            # Test with 10 concurrent users
            start_time = time.time()
            await asyncio.gather(*[simulate_user(i) for i in range(10)])
            total_time = (time.time() - start_time) * 1000
            
            # Should handle concurrent users efficiently
            assert total_time < 2000, f"Concurrent user handling too slow: {total_time:.2f}ms"
            
            # Test with 50 concurrent users
            start_time = time.time()
            await asyncio.gather(*[simulate_user(i) for i in range(50)])
            total_time = (time.time() - start_time) * 1000
            
            # Should scale reasonably well
            assert total_time < 10000, f"High concurrent user load too slow: {total_time:.2f}ms"
            
        finally:
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency of Phase 3 components."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        config = CacheConfig(max_memory_cache_items=1000)
        cache_service = CacheService(config)
        await cache_service.start()
        
        try:
            # Load significant amount of data
            large_datasets = []
            for i in range(100):
                dataset = {
                    "symbol": f"SYMBOL_{i}",
                    "bars": [
                        {
                            "timestamp": datetime.now() + timedelta(minutes=j),
                            "open": 100.0 + j * 0.1,
                            "high": 101.0 + j * 0.1,
                            "low": 99.0 + j * 0.1,
                            "close": 100.5 + j * 0.1,
                            "volume": 1000 + j * 10
                        }
                        for j in range(100)  # 100 bars per symbol
                    ]
                }
                large_datasets.append(dataset)
                await cache_service.set_historical_data(f"large_dataset_{i}", dataset)
            
            # Check memory usage
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            # Should not consume excessive memory
            assert memory_increase < 200, f"Memory usage too high: {memory_increase:.2f}MB"
            
            # Test memory cleanup
            await cache_service.clear()
            
            # Give some time for cleanup
            await asyncio.sleep(0.1)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_after_cleanup = final_memory - initial_memory
            
            # Memory should be freed
            assert memory_after_cleanup < memory_increase / 2, "Memory not properly cleaned up"
            
        finally:
            await cache_service.stop()


class TestScalabilityTargets:
    """Test scalability requirements."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets efficiently."""
        config = CacheConfig(default_ttl=300)
        cache_service = CacheService(config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        try:
            # Create very large dataset (full trading day)
            large_dataset = []
            base_time = datetime.now()
            
            for i in range(6.5 * 60):  # 6.5 hours of minute bars (full trading day)
                large_dataset.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "symbol": "AAPL",
                    "open_price": 150.0 + (i % 100) * 0.01,
                    "high_price": 151.0 + (i % 100) * 0.01,
                    "low_price": 149.0 + (i % 100) * 0.01,
                    "close_price": 150.5 + (i % 100) * 0.01,
                    "volume": 1000 + i
                })
            
            with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
                mock_fetch.return_value = large_dataset
                
                # Test aggregation of large dataset
                start_time = time.time()
                result = await aggregation_service.aggregate_data(
                    symbol="AAPL",
                    source_frequency="1m",
                    target_frequency="1h",
                    start_date=base_time,
                    end_date=base_time + timedelta(hours=6.5)
                )
                execution_time = (time.time() - start_time) * 1000
                
                # Should handle large datasets efficiently
                assert execution_time < 2000, f"Large dataset aggregation too slow: {execution_time:.2f}ms"
                assert len(result.bars) > 0
                assert result.stats["source_bars"] == len(large_dataset)
                
        finally:
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_efficiency_target(self):
        """Test that caching reduces database load by >70%."""
        config = CacheConfig(default_ttl=300)
        cache_service = CacheService(config)
        await cache_service.start()
        
        try:
            # Simulate database operations
            db_calls = 0
            
            async def mock_db_operation(key):
                nonlocal db_calls
                db_calls += 1
                return {"key": key, "data": "expensive_db_result"}
            
            # First round - populate cache (100% DB calls)
            for i in range(10):
                key = f"db_key_{i}"
                if not await cache_service.exists(key):
                    data = await mock_db_operation(key)
                    await cache_service.set(key, data)
                else:
                    await cache_service.get(key)
            
            initial_db_calls = db_calls
            
            # Second round - should mostly hit cache
            db_calls = 0  # Reset counter
            for i in range(10):
                key = f"db_key_{i}"
                if not await cache_service.exists(key):
                    data = await mock_db_operation(key)
                    await cache_service.set(key, data)
                else:
                    await cache_service.get(key)
            
            second_round_db_calls = db_calls
            
            # Calculate reduction percentage
            if initial_db_calls > 0:
                reduction_percentage = (1 - second_round_db_calls / initial_db_calls) * 100
            else:
                reduction_percentage = 100
            
            # Should achieve >70% reduction target
            assert reduction_percentage > 70, f"Cache reduction only {reduction_percentage:.1f}% (target >70%)"
            
        finally:
            await cache_service.stop()


class TestThroughputTargets:
    """Test throughput requirements."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_operations_per_second(self):
        """Test operations per second throughput."""
        config = CacheConfig(max_memory_cache_items=10000)
        cache_service = CacheService(config)
        await cache_service.start()
        
        try:
            # Test cache operations throughput
            operations_count = 1000
            test_data = {"sample": "data", "numbers": list(range(100))}
            
            # Test SET throughput
            start_time = time.time()
            for i in range(operations_count):
                await cache_service.set(f"throughput_test_{i}", test_data)
            set_duration = time.time() - start_time
            
            set_ops_per_sec = operations_count / set_duration
            assert set_ops_per_sec > 1000, f"Set throughput too low: {set_ops_per_sec:.0f} ops/sec"
            
            # Test GET throughput
            start_time = time.time()
            for i in range(operations_count):
                result = await cache_service.get(f"throughput_test_{i}")
                assert result is not None
            get_duration = time.time() - start_time
            
            get_ops_per_sec = operations_count / get_duration
            assert get_ops_per_sec > 2000, f"Get throughput too low: {get_ops_per_sec:.0f} ops/sec"
            
        finally:
            await cache_service.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_aggregation_throughput(self):
        """Test data aggregation throughput."""
        config = CacheConfig(default_ttl=300)
        cache_service = CacheService(config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        try:
            # Create standard dataset for throughput testing
            sample_bars = []
            base_time = datetime.now()
            
            for i in range(60):  # 1 hour of minute bars
                sample_bars.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "symbol": "TEST",
                    "open_price": 100.0 + i * 0.1,
                    "high_price": 101.0 + i * 0.1,
                    "low_price": 99.0 + i * 0.1,
                    "close_price": 100.5 + i * 0.1,
                    "volume": 1000 + i
                })
            
            with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
                mock_fetch.return_value = sample_bars
                
                # Test multiple aggregations throughput
                aggregations_count = 50
                start_time = time.time()
                
                tasks = []
                for i in range(aggregations_count):
                    task = aggregation_service.aggregate_data(
                        symbol=f"SYMBOL_{i}",
                        source_frequency="1m",
                        target_frequency="5m",
                        start_date=base_time,
                        end_date=base_time + timedelta(hours=1)
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                duration = time.time() - start_time
                
                aggregations_per_sec = aggregations_count / duration
                
                # Should handle reasonable aggregation throughput
                assert aggregations_per_sec > 10, f"Aggregation throughput too low: {aggregations_per_sec:.1f} ops/sec"
                assert all(len(result.bars) > 0 for result in results)
                
        finally:
            await aggregation_service.stop()
            await cache_service.stop()


@pytest.mark.performance
class TestRegressionPerformance:
    """Test that Phase 3 doesn't degrade existing performance."""
    
    @pytest.mark.asyncio
    async def test_no_performance_regression(self):
        """Test that Phase 3 enhancements don't degrade baseline performance."""
        # This would compare against Phase 2 performance benchmarks
        # For now, we'll test basic operations are still fast
        
        config = CacheConfig(default_ttl=300)
        cache_service = CacheService(config)
        await cache_service.start()
        
        try:
            # Simple operations should still be very fast
            simple_data = {"key": "value"}
            
            start_time = time.time()
            for i in range(100):
                await cache_service.set(f"regression_test_{i}", simple_data)
                result = await cache_service.get(f"regression_test_{i}")
                assert result == simple_data
            duration = (time.time() - start_time) * 1000
            
            # Should complete 100 round-trips in under 100ms
            assert duration < 100, f"Basic operations regressed: {duration:.2f}ms for 100 round-trips"
            
        finally:
            await cache_service.stop()