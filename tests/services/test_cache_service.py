"""
Comprehensive tests for the CacheService - Phase 3 Enhancement
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.services.cache_service import (
    CacheService, CacheConfig, MemoryCacheBackend, 
    RedisCacheBackend, CacheBackend
)


@pytest.fixture
def cache_config():
    """Cache configuration for testing."""
    return CacheConfig(
        redis_url="redis://localhost:6379",
        redis_db=1,  # Use different DB for testing
        default_ttl=300,
        historical_data_ttl=3600,
        market_data_ttl=60,
        max_memory_cache_items=100
    )


@pytest.fixture
def memory_cache():
    """Memory cache backend for testing."""
    return MemoryCacheBackend(max_items=10)


@pytest.fixture
async def cache_service(cache_config):
    """Cache service fixture."""
    service = CacheService(cache_config)
    # Don't start Redis for unit tests - use memory only
    service.redis_backend = None
    await service.start()
    yield service
    await service.stop()


class TestMemoryCacheBackend:
    """Test memory cache backend functionality."""
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, memory_cache):
        """Test basic set and get operations."""
        # Test successful set and get
        assert await memory_cache.set("test_key", "test_value")
        result = await memory_cache.get("test_key")
        assert result == "test_value"
        
        # Test non-existent key
        result = await memory_cache.get("non_existent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, memory_cache):
        """Test TTL expiration functionality."""
        # Set with TTL
        await memory_cache.set("ttl_key", "ttl_value", ttl=1)  # 1 second
        
        # Should be available immediately
        result = await memory_cache.get("ttl_key")
        assert result == "ttl_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await memory_cache.get("ttl_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_capacity_eviction(self):
        """Test capacity-based eviction."""
        cache = MemoryCacheBackend(max_items=3)
        
        # Fill to capacity
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Add one more - should evict oldest
        await cache.set("key4", "value4")
        
        # key1 should be evicted
        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
        assert await cache.get("key4") == "value4"
    
    @pytest.mark.asyncio
    async def test_delete(self, memory_cache):
        """Test delete functionality."""
        await memory_cache.set("delete_key", "delete_value")
        
        # Verify it exists
        assert await memory_cache.exists("delete_key")
        
        # Delete it
        assert await memory_cache.delete("delete_key")
        
        # Verify it's gone
        assert not await memory_cache.exists("delete_key")
        assert await memory_cache.get("delete_key") is None
    
    @pytest.mark.asyncio
    async def test_clear(self, memory_cache):
        """Test clear functionality."""
        # Add multiple keys
        await memory_cache.set("clear1", "value1")
        await memory_cache.set("clear2", "value2") 
        await memory_cache.set("other", "value3")
        
        # Clear with pattern
        cleared = await memory_cache.clear("clear*")
        assert cleared == 2
        
        # Verify pattern matching
        assert await memory_cache.get("clear1") is None
        assert await memory_cache.get("clear2") is None
        assert await memory_cache.get("other") == "value3"
    
    @pytest.mark.asyncio
    async def test_stats(self, memory_cache):
        """Test statistics functionality."""
        # Generate some operations
        await memory_cache.set("stats_key", "stats_value")
        await memory_cache.get("stats_key")  # Hit
        await memory_cache.get("nonexistent")  # Miss
        
        stats = await memory_cache.get_stats()
        
        assert stats["backend"] == "memory"
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["sets"] >= 1
        assert "hit_rate" in stats


class TestCacheService:
    """Test cache service integration."""
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, cache_config):
        """Test service start and stop."""
        service = CacheService(cache_config)
        
        # Service should not be running initially
        assert not service.is_running if hasattr(service, 'is_running') else True
        
        await service.start()
        # Test that it started successfully (no Redis needed for memory fallback)
        
        await service.stop()
        # Should stop cleanly
    
    @pytest.mark.asyncio 
    async def test_basic_operations(self, cache_service):
        """Test basic cache operations through service."""
        # Set and get
        assert await cache_service.set("service_key", {"data": "value"})
        result = await cache_service.get("service_key")
        assert result == {"data": "value"}
        
        # Delete
        assert await cache_service.delete("service_key")
        assert await cache_service.get("service_key") is None
    
    @pytest.mark.asyncio
    async def test_specialized_cache_methods(self, cache_service):
        """Test specialized cache methods."""
        # Historical data caching
        historical_data = {"bars": [1, 2, 3], "symbol": "AAPL"}
        assert await cache_service.set_historical_data("hist_key", historical_data)
        result = await cache_service.get_historical_data("hist_key")
        assert result == historical_data
        
        # Market data caching  
        market_data = {"price": 150.0, "volume": 1000}
        assert await cache_service.set_market_data("market_key", market_data)
        result = await cache_service.get_market_data("market_key")
        assert result == market_data
        
        # Query results caching
        query_results = {"results": [1, 2, 3], "count": 3}
        assert await cache_service.set_query_results("query_key", query_results)
        result = await cache_service.get_query_results("query_key")
        assert result == query_results
    
    @pytest.mark.asyncio
    async def test_cache_warming(self, cache_service):
        """Test cache warming functionality."""
        warm_data = {
            "key1": "value1",
            "key2": "value2", 
            "key3": "value3"
        }
        
        # Warm cache
        success_count = await cache_service.warm_cache(warm_data)
        assert success_count == 3
        
        # Verify data is cached
        for key, value in warm_data.items():
            cached_value = await cache_service.get(key)
            assert cached_value == value
    
    @pytest.mark.asyncio
    async def test_comprehensive_stats(self, cache_service):
        """Test comprehensive statistics."""
        # Generate some activity
        await cache_service.set("stats_test", "value")
        await cache_service.get("stats_test")
        
        stats = await cache_service.get_comprehensive_stats()
        
        assert "service" in stats
        assert "memory" in stats
        assert stats["service"]["total_gets"] >= 1
        assert stats["service"]["total_sets"] >= 1
        assert stats["memory"]["backend"] == "memory"
    
    @pytest.mark.asyncio
    async def test_redis_fallback_behavior(self, cache_config):
        """Test behavior when Redis is not available."""
        service = CacheService(cache_config)
        
        # Mock Redis backend to fail connection
        with patch('src.backend.services.cache_service.RedisCacheBackend') as mock_redis:
            mock_redis.return_value.connect = AsyncMock(side_effect=Exception("Redis unavailable"))
            
            await service.start()
            
            # Should fall back to memory cache
            assert service.redis_backend is None
            
            # Operations should still work with memory cache
            assert await service.set("fallback_key", "fallback_value")
            assert await service.get("fallback_key") == "fallback_value"
            
            await service.stop()


class TestRedisCacheBackend:
    """Test Redis cache backend (mocked)."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.setex.return_value = True  
        redis_mock.delete.return_value = 1
        redis_mock.exists.return_value = 1
        redis_mock.keys.return_value = []
        redis_mock.info.return_value = {
            "used_memory_human": "1M",
            "connected_clients": 1,
            "total_commands_processed": 100,
            "keyspace_hits": 80,
            "keyspace_misses": 20
        }
        return redis_mock
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, cache_config, mock_redis):
        """Test Redis connection establishment."""
        backend = RedisCacheBackend(cache_config)
        
        with patch('aioredis.ConnectionPool.from_url'), \
             patch('aioredis.Redis') as mock_redis_class:
            
            mock_redis_class.return_value = mock_redis
            
            await backend.connect()
            
            # Should have connected successfully
            assert backend.redis == mock_redis
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_serialization(self, cache_config, mock_redis):
        """Test Redis serialization and deserialization."""
        backend = RedisCacheBackend(cache_config)
        
        # Test JSON serialization
        simple_data = {"key": "value", "number": 123}
        serialized = backend._serialize(simple_data)
        deserialized = backend._deserialize(serialized)
        assert deserialized == simple_data
        
        # Test pickle serialization for complex objects
        complex_data = datetime.now()
        serialized = backend._serialize(complex_data)
        deserialized = backend._deserialize(serialized)
        assert deserialized == complex_data
    
    @pytest.mark.asyncio
    async def test_redis_compression(self, cache_config):
        """Test Redis compression for large data."""
        # Enable compression
        cache_config.compression_enabled = True
        cache_config.compression_threshold = 10  # Low threshold for testing
        
        backend = RedisCacheBackend(cache_config)
        
        # Large data that should be compressed
        large_data = "x" * 100
        serialized = backend._serialize(large_data)
        
        # Should have compression prefix
        assert serialized.startswith(b'comp:')
        
        # Should deserialize correctly
        deserialized = backend._deserialize(serialized)
        assert deserialized == large_data
    
    @pytest.mark.asyncio
    async def test_redis_operations(self, cache_config, mock_redis):
        """Test Redis operations through backend."""
        backend = RedisCacheBackend(cache_config)
        backend.redis = mock_redis
        
        # Test set operation
        result = await backend.set("test_key", "test_value", ttl=300)
        assert result is True
        mock_redis.setex.assert_called()
        
        # Test get operation
        mock_redis.get.return_value = backend._serialize("test_value")
        result = await backend.get("test_key")
        assert result == "test_value"
        
        # Test delete operation
        result = await backend.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called()
        
        # Test exists operation
        result = await backend.exists("test_key")
        assert result is True
        mock_redis.exists.assert_called()
    
    @pytest.mark.asyncio
    async def test_redis_stats(self, cache_config, mock_redis):
        """Test Redis statistics collection."""
        backend = RedisCacheBackend(cache_config)
        backend.redis = mock_redis
        
        stats = await backend.get_stats()
        
        assert stats["backend"] == "redis"
        assert stats["connected"] is True
        assert "used_memory" in stats
        assert "keyspace_hits" in stats
        assert "hit_rate" in stats
        assert stats["hit_rate"] == 80.0  # Based on mock data


class TestPerformanceScenarios:
    """Test performance-related scenarios."""
    
    @pytest.mark.asyncio
    async def test_high_volume_operations(self, cache_service):
        """Test high-volume cache operations."""
        # Generate high volume of operations
        operations = []
        for i in range(100):
            operations.append(cache_service.set(f"key_{i}", f"value_{i}"))
        
        # Execute all sets concurrently
        results = await asyncio.gather(*operations)
        assert all(results)
        
        # Verify all can be retrieved
        get_operations = []
        for i in range(100):
            get_operations.append(cache_service.get(f"key_{i}"))
        
        values = await asyncio.gather(*get_operations)
        for i, value in enumerate(values):
            assert value == f"value_{i}"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, cache_service):
        """Test memory efficiency with large datasets."""
        # Create large data structure
        large_data = {
            "bars": [
                {
                    "timestamp": datetime.now(),
                    "open": 100.0 + i,
                    "high": 105.0 + i,
                    "low": 95.0 + i,
                    "close": 102.0 + i,
                    "volume": 1000 + i
                }
                for i in range(1000)
            ],
            "metadata": {
                "symbol": "AAPL",
                "frequency": "1m",
                "total_bars": 1000
            }
        }
        
        # Should handle large data efficiently
        assert await cache_service.set_historical_data("large_dataset", large_data)
        retrieved_data = await cache_service.get_historical_data("large_dataset")
        
        # Verify data integrity
        assert len(retrieved_data["bars"]) == 1000
        assert retrieved_data["metadata"]["symbol"] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache_service):
        """Test concurrent access to cache."""
        async def worker(worker_id: int):
            """Worker function for concurrent testing."""
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                
                await cache_service.set(key, value)
                retrieved = await cache_service.get(key)
                assert retrieved == value
        
        # Run multiple workers concurrently
        workers = [worker(i) for i in range(5)]
        await asyncio.gather(*workers)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_operations(self, memory_cache):
        """Test handling of invalid operations."""
        # Delete non-existent key should return False
        assert not await memory_cache.delete("non_existent_key")
        
        # Get from empty cache should return None
        empty_cache = MemoryCacheBackend()
        assert await empty_cache.get("any_key") is None
    
    @pytest.mark.asyncio
    async def test_serialization_errors(self, cache_config):
        """Test handling of serialization errors."""
        backend = RedisCacheBackend(cache_config)
        
        # Test with non-serializable object (mock)
        class NonSerializable:
            def __reduce__(self):
                raise TypeError("Cannot serialize this object")
        
        with pytest.raises(Exception):
            backend._serialize(NonSerializable())
    
    @pytest.mark.asyncio
    async def test_cache_service_resilience(self, cache_config):
        """Test cache service resilience to backend failures."""
        service = CacheService(cache_config)
        
        # Mock memory backend to fail
        service.memory_backend = AsyncMock()
        service.memory_backend.get.side_effect = Exception("Memory backend failed")
        service.memory_backend.set.return_value = False
        
        await service.start()
        
        # Operations should handle failures gracefully
        result = await service.get("test_key")
        assert result is None  # Should return None on failure
        
        # Set should return False on failure
        result = await service.set("test_key", "test_value")
        assert result is False
        
        await service.stop()


@pytest.mark.integration
class TestCacheIntegration:
    """Integration tests for cache service."""
    
    @pytest.mark.asyncio
    async def test_cache_with_historical_data_service(self, cache_service):
        """Test cache integration with historical data patterns."""
        # Simulate historical data service patterns
        symbols = ["AAPL", "GOOGL", "MSFT"]
        frequencies = ["1m", "5m", "1h", "1d"]
        
        for symbol in symbols:
            for frequency in frequencies:
                cache_key = f"historical_data:{symbol}:{frequency}:2023-01-01:2023-12-31"
                data = {
                    "symbol": symbol,
                    "frequency": frequency,
                    "bars": [{"timestamp": datetime.now(), "close": 100.0}],
                    "metadata": {"source": "test"}
                }
                
                # Cache the data
                await cache_service.set_historical_data(cache_key, data)
                
                # Retrieve and verify
                cached_data = await cache_service.get_historical_data(cache_key)
                assert cached_data["symbol"] == symbol
                assert cached_data["frequency"] == frequency
    
    @pytest.mark.asyncio
    async def test_cache_performance_monitoring(self, cache_service):
        """Test cache performance monitoring capabilities."""
        # Generate mixed cache operations
        hit_keys = []
        for i in range(10):
            key = f"hit_key_{i}"
            await cache_service.set(key, f"value_{i}")
            hit_keys.append(key)
        
        # Generate cache hits
        for key in hit_keys:
            await cache_service.get(key)
        
        # Generate cache misses
        for i in range(5):
            await cache_service.get(f"miss_key_{i}")
        
        # Check statistics
        stats = await cache_service.get_comprehensive_stats()
        
        # Should have recorded operations
        assert stats["service"]["total_gets"] >= 15  # 10 hits + 5 misses
        assert stats["service"]["total_sets"] >= 10
        
        # Memory backend should show hits and misses
        memory_stats = stats["memory"]
        assert memory_stats["hits"] >= 10
        assert memory_stats["misses"] >= 5