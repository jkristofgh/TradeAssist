"""
Unit tests for HistoricalDataCache component.
Tests Phase 3 decomposition: cache management and optimization functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from typing import Dict, List, Any

from src.backend.services.historical_data.cache import HistoricalDataCache


class TestHistoricalDataCache:
    """Test suite for HistoricalDataCache component."""

    @pytest.fixture
    def cache(self):
        """Create cache instance with test settings."""
        return HistoricalDataCache(ttl_minutes=5, max_cache_size_mb=10)

    @pytest.fixture
    def sample_data(self):
        """Sample market data for testing."""
        return [
            {
                "timestamp": datetime(2024, 1, 1, 9, 30),
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 101.0,
                "volume": 1000000
            },
            {
                "timestamp": datetime(2024, 1, 1, 10, 30),
                "open": 101.0,
                "high": 106.0,
                "low": 100.0,
                "close": 102.0,
                "volume": 1100000
            }
        ]

    # Test initialization

    def test_init_default_values(self):
        """Test cache initialization with default values."""
        cache = HistoricalDataCache()
        
        assert cache._cache_ttl_minutes == 30
        assert cache._max_cache_size_mb == 100
        assert cache._cache_hits == 0
        assert cache._cache_misses == 0
        assert len(cache._cache) == 0

    def test_init_custom_values(self):
        """Test cache initialization with custom values."""
        cache = HistoricalDataCache(ttl_minutes=15, max_cache_size_mb=50)
        
        assert cache._cache_ttl_minutes == 15
        assert cache._max_cache_size_mb == 50
        assert cache._max_cache_size_bytes == 50 * 1024 * 1024

    # Test service lifecycle

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, cache):
        """Test cache service start/stop lifecycle."""
        # Start the cache
        await cache.start()
        assert cache._cleanup_task is not None
        
        # Stop the cache
        await cache.stop()
        assert len(cache._cache) == 0

    # Test cache key generation

    def test_build_cache_key_single_symbol(self, cache):
        """Test cache key generation for single symbol."""
        key = cache.build_cache_key(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            frequency="daily"
        )
        
        assert key.startswith("historical_data:")
        assert len(key) > 20  # Should be reasonably long hash

    def test_build_cache_key_multiple_symbols(self, cache):
        """Test cache key generation for multiple symbols."""
        key = cache.build_cache_key(
            symbols=["AAPL", "MSFT", "GOOGL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            frequency="daily"
        )
        
        assert key.startswith("historical_data:")
        
        # Same symbols in different order should produce same key
        key2 = cache.build_cache_key(
            symbols=["GOOGL", "AAPL", "MSFT"],  # Different order
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            frequency="daily"
        )
        
        assert key == key2

    def test_build_cache_key_with_optional_params(self, cache):
        """Test cache key generation with optional parameters."""
        key1 = cache.build_cache_key(
            symbol="AAPL",
            frequency="daily",
            include_extended_hours=True,
            max_records=1000
        )
        
        key2 = cache.build_cache_key(
            symbol="AAPL", 
            frequency="daily",
            include_extended_hours=False,
            max_records=1000
        )
        
        # Different extended hours setting should produce different keys
        assert key1 != key2

    def test_build_cache_key_with_kwargs(self, cache):
        """Test cache key generation with additional kwargs."""
        key1 = cache.build_cache_key(symbol="AAPL", frequency="daily")
        key2 = cache.build_cache_key(
            symbol="AAPL", 
            frequency="daily", 
            custom_param="value"
        )
        
        # Additional parameters should change the key
        assert key1 != key2

    # Test basic cache operations

    @pytest.mark.asyncio
    async def test_cache_and_retrieve_data(self, cache, sample_data):
        """Test basic cache storage and retrieval."""
        key = "test_key"
        
        # Store data
        await cache.cache_data(key, sample_data)
        
        # Retrieve data
        retrieved = await cache.get_cached_data(key)
        
        assert retrieved == sample_data
        assert cache._cache_hits == 1

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss scenario."""
        result = await cache.get_cached_data("nonexistent_key")
        
        assert result is None
        assert cache._cache_misses == 1

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache, sample_data):
        """Test TTL expiration functionality."""
        key = "test_key"
        
        # Store data
        await cache.cache_data(key, sample_data)
        
        # Manually set timestamp to simulate expiration
        cache._cache_timestamps[key] = datetime.utcnow() - timedelta(minutes=10)
        
        # Try to retrieve expired data
        result = await cache.get_cached_data(key)
        
        assert result is None
        assert cache._cache_misses == 1
        assert key not in cache._cache  # Should be cleaned up

    @pytest.mark.asyncio
    async def test_cache_access_pattern_tracking(self, cache, sample_data):
        """Test access pattern tracking."""
        key = "test_key"
        await cache.cache_data(key, sample_data)
        
        # Access the data multiple times
        for i in range(3):
            await cache.get_cached_data(key)
        
        # Check access count
        assert cache._cache_access_counts[key] == 3
        assert len(cache._access_patterns[key]) == 3

    # Test cache size management

    @pytest.mark.asyncio
    async def test_cache_data_too_large(self, cache):
        """Test rejection of data that's too large."""
        # Create very large data that exceeds cache limit
        large_data = [{"large_field": "x" * 1000000} for _ in range(20)]  # ~20MB
        
        with pytest.raises(ValueError, match="Data too large to cache"):
            await cache.cache_data("large_key", large_data)

    @pytest.mark.asyncio
    async def test_cache_size_eviction(self, cache):
        """Test LRU eviction when cache size limit is exceeded."""
        # Fill cache with data
        data_items = []
        for i in range(5):
            data = [{"field": f"data_{i}" * 10000} for _ in range(100)]  # ~1MB each
            key = f"key_{i}"
            await cache.cache_data(key, data)
            data_items.append((key, data))
        
        # Access first few items to make them more recent
        await cache.get_cached_data("key_0")
        await cache.get_cached_data("key_1")
        
        # Add one more large item to trigger eviction
        large_data = [{"field": "large" * 10000} for _ in range(200)]  # ~2MB
        await cache.cache_data("key_large", large_data)
        
        # Check that some items were evicted
        stats = cache.get_cache_statistics()
        assert stats["evictions"] > 0

    # Test cache invalidation

    @pytest.mark.asyncio
    async def test_invalidate_cache_all(self, cache, sample_data):
        """Test clearing entire cache."""
        # Add multiple items
        await cache.cache_data("key1", sample_data)
        await cache.cache_data("key2", sample_data)
        await cache.cache_data("key3", sample_data)
        
        # Invalidate all
        count = await cache.invalidate_cache()
        
        assert count == 3
        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_invalidate_cache_pattern(self, cache, sample_data):
        """Test pattern-based cache invalidation."""
        # Add items with different patterns
        await cache.cache_data("user_123_data", sample_data)
        await cache.cache_data("user_456_data", sample_data)
        await cache.cache_data("admin_data", sample_data)
        
        # Invalidate only user items
        count = await cache.invalidate_cache("user_.*")
        
        assert count == 2
        assert len(cache._cache) == 1  # admin_data should remain
        assert await cache.get_cached_data("admin_data") is not None

    @pytest.mark.asyncio
    async def test_invalidate_cache_invalid_pattern(self, cache):
        """Test invalidation with invalid regex pattern."""
        count = await cache.invalidate_cache("[invalid")
        assert count == 0

    # Test cache statistics

    @pytest.mark.asyncio
    async def test_get_cache_statistics(self, cache, sample_data):
        """Test cache statistics generation."""
        # Generate some activity
        await cache.cache_data("key1", sample_data)
        await cache.cache_data("key2", sample_data)
        await cache.get_cached_data("key1")  # Hit
        await cache.get_cached_data("nonexistent")  # Miss
        
        stats = cache.get_cache_statistics()
        
        assert stats["cache_size"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate_percent"] == 50.0
        assert stats["memory_usage_mb"] > 0
        assert stats["ttl_minutes"] == 5
        assert "most_accessed_keys" in stats

    @pytest.mark.asyncio
    async def test_get_cache_usage_by_pattern(self, cache, sample_data):
        """Test cache usage analysis by pattern."""
        # Add items with patterns
        await cache.cache_data("api_endpoint_1", sample_data)
        await cache.cache_data("api_endpoint_2", sample_data)
        await cache.cache_data("user_data", sample_data)
        
        # Access API endpoints
        await cache.get_cached_data("api_endpoint_1")
        await cache.get_cached_data("api_endpoint_2")
        
        usage = await cache.get_cache_usage_by_pattern("api_.*")
        
        assert usage["matching_keys"] == 2
        assert usage["total_accesses"] == 2
        assert usage["memory_usage_mb"] > 0

    # Test cache warming

    @pytest.mark.asyncio
    async def test_warm_cache(self, cache):
        """Test cache warming functionality."""
        warm_data = {"warmed": True, "data": "test"}
        
        async def warm_callback(key: str):
            if key == "warmable_key":
                return warm_data
            return None
        
        count = await cache.warm_cache(["warmable_key", "invalid_key"], warm_callback)
        
        assert count == 1  # Only one key was successfully warmed
        assert await cache.get_cached_data("warmable_key") == warm_data

    @pytest.mark.asyncio
    async def test_warm_cache_skip_existing(self, cache, sample_data):
        """Test that cache warming skips existing entries."""
        key = "existing_key"
        await cache.cache_data(key, sample_data)
        
        warm_data = {"different": "data"}
        
        async def warm_callback(key: str):
            return warm_data
        
        count = await cache.warm_cache([key], warm_callback)
        
        assert count == 0  # Should skip existing key
        assert await cache.get_cached_data(key) == sample_data  # Original data unchanged

    # Test cleanup operations

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, cache, sample_data):
        """Test cleanup of expired entries."""
        # Add some data
        await cache.cache_data("key1", sample_data)
        await cache.cache_data("key2", sample_data)
        
        # Manually expire one entry
        cache._cache_timestamps["key1"] = datetime.utcnow() - timedelta(minutes=10)
        
        # Run cleanup
        cleaned = await cache._cleanup_expired_entries()
        
        assert cleaned == 1
        assert "key1" not in cache._cache
        assert "key2" in cache._cache

    @pytest.mark.asyncio
    async def test_clear_all(self, cache, sample_data):
        """Test clearing all cache data."""
        await cache.cache_data("key1", sample_data)
        await cache.cache_data("key2", sample_data)
        
        await cache.clear_all()
        
        assert len(cache._cache) == 0
        assert len(cache._cache_timestamps) == 0
        assert len(cache._cache_access_counts) == 0

    # Test data size calculation

    def test_calculate_data_size_dict(self, cache):
        """Test data size calculation for dictionary."""
        data = {"key": "value", "number": 123}
        size = cache._calculate_data_size(data)
        assert size > 0
        assert isinstance(size, int)

    def test_calculate_data_size_list(self, cache):
        """Test data size calculation for list."""
        data = ["item1", "item2", 123, {"nested": "data"}]
        size = cache._calculate_data_size(data)
        assert size > 0

    def test_calculate_data_size_string(self, cache):
        """Test data size calculation for string."""
        data = "test string"
        size = cache._calculate_data_size(data)
        assert size == len(data.encode('utf-8'))

    def test_calculate_data_size_numeric(self, cache):
        """Test data size calculation for numeric types."""
        int_size = cache._calculate_data_size(123)
        float_size = cache._calculate_data_size(123.45)
        
        assert int_size > 0
        assert float_size > 0

    # Test memory management

    @pytest.mark.asyncio
    async def test_ensure_cache_space_sufficient(self, cache, sample_data):
        """Test space management when sufficient space available."""
        await cache.cache_data("key1", sample_data)
        
        # Calculate size of sample data
        data_size = cache._calculate_data_size(sample_data)
        
        # Should not evict anything if space is available
        await cache._ensure_cache_space(data_size)
        
        # Original data should still be there
        assert await cache.get_cached_data("key1") is not None

    @pytest.mark.asyncio
    async def test_lru_eviction_strategy(self, cache):
        """Test LRU eviction strategy implementation."""
        # Add multiple small items
        items = {}
        for i in range(3):
            key = f"key_{i}"
            data = {"item": i, "data": "x" * 1000}
            await cache.cache_data(key, data)
            items[key] = data
        
        # Access key_0 and key_1 to make them more recent
        await cache.get_cached_data("key_0")
        await cache.get_cached_data("key_1")
        
        # Force eviction by adding large data
        large_data = {"large": "x" * 100000}
        await cache.cache_data("large_key", large_data)
        
        # key_2 should be evicted (least recently used)
        assert await cache.get_cached_data("key_2") is None
        assert await cache.get_cached_data("key_0") is not None
        assert await cache.get_cached_data("key_1") is not None

    # Test concurrent operations

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self, cache):
        """Test thread safety of cache operations."""
        async def cache_worker(worker_id: int):
            data = {"worker": worker_id, "data": [i for i in range(100)]}
            key = f"worker_{worker_id}"
            await cache.cache_data(key, data)
            retrieved = await cache.get_cached_data(key)
            assert retrieved == data
        
        # Run multiple workers concurrently
        tasks = [cache_worker(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # All workers should have succeeded
        assert len(cache._cache) == 5

    # Test edge cases

    @pytest.mark.asyncio
    async def test_cache_none_values(self, cache):
        """Test caching None values."""
        await cache.cache_data("none_key", None)
        result = await cache.get_cached_data("none_key")
        assert result is None
        assert cache._cache_hits == 1  # Should still count as hit

    @pytest.mark.asyncio
    async def test_cache_empty_structures(self, cache):
        """Test caching empty data structures."""
        await cache.cache_data("empty_list", [])
        await cache.cache_data("empty_dict", {})
        
        assert await cache.get_cached_data("empty_list") == []
        assert await cache.get_cached_data("empty_dict") == {}

    @pytest.mark.asyncio
    async def test_access_patterns_cleanup(self, cache, sample_data):
        """Test that access patterns are cleaned up over time."""
        key = "test_key"
        await cache.cache_data(key, sample_data)
        
        # Add old access pattern
        old_time = datetime.utcnow() - timedelta(hours=25)
        cache._access_patterns[key].append(old_time)
        
        # Access the data (should clean up old patterns)
        await cache.get_cached_data(key)
        
        # Old access should be removed
        assert all(
            access_time > datetime.utcnow() - timedelta(hours=24)
            for access_time in cache._access_patterns[key]
        )