"""
Historical Data Cache Component

Manages all caching operations for historical market data.
Extracted from HistoricalDataService as part of Phase 3 decomposition.
"""

import asyncio
import json
import re
import structlog
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Pattern
from collections import defaultdict

logger = structlog.get_logger()


class HistoricalDataCache:
    """
    Manages all caching operations for historical market data.
    
    Responsibilities:
    - In-memory cache management with TTL (30 minutes default)
    - Cache key generation with consistent hashing
    - Cache statistics and performance monitoring
    - Cache invalidation strategies (pattern-based)
    - Memory management and cleanup for expired entries
    - Cache warming strategies for frequently accessed data
    """
    
    def __init__(self, ttl_minutes: int = 30, max_cache_size_mb: int = 100):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_access_counts: Dict[str, int] = {}
        self._cache_sizes: Dict[str, int] = {}  # Track memory usage per entry
        
        self._cache_ttl_minutes = ttl_minutes
        self._max_cache_size_mb = max_cache_size_mb
        self._max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        
        # Performance statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_evictions = 0
        self._cache_invalidations = 0
        
        # Access pattern tracking
        self._access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        
        # Background cleanup settings
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval_minutes = 5
        
        logger.debug(
            "HistoricalDataCache initialized",
            ttl_minutes=ttl_minutes,
            max_size_mb=max_cache_size_mb
        )

    async def start(self) -> None:
        """Start the cache service with background cleanup."""
        logger.info("Starting HistoricalDataCache")
        
        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("HistoricalDataCache started successfully")

    async def stop(self) -> None:
        """Stop the cache service and cleanup resources."""
        logger.info("Stopping HistoricalDataCache")
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            
        # Clear all cache data
        await self.clear_all()
        
        logger.info("HistoricalDataCache stopped")

    async def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve data from cache if valid and not expired.
        
        Args:
            cache_key: The cache key to retrieve
            
        Returns:
            Cached data if valid, None otherwise
        """
        # Check if key exists
        if cache_key not in self._cache:
            self._cache_misses += 1
            return None
            
        # Check TTL expiration
        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            self._cache_misses += 1
            await self._remove_cache_entry(cache_key)
            return None
            
        age_minutes = (datetime.utcnow() - cache_time).total_seconds() / 60
        if age_minutes > self._cache_ttl_minutes:
            self._cache_misses += 1
            await self._remove_cache_entry(cache_key)
            logger.debug(f"Cache entry expired: {cache_key}")
            return None
            
        # Update access statistics
        self._cache_hits += 1
        self._cache_access_counts[cache_key] = self._cache_access_counts.get(cache_key, 0) + 1
        self._access_patterns[cache_key].append(datetime.utcnow())
        
        # Keep only recent access times (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self._access_patterns[cache_key] = [
            access_time for access_time in self._access_patterns[cache_key] 
            if access_time > cutoff_time
        ]
        
        logger.debug(f"Cache hit: {cache_key}")
        return self._cache[cache_key]

    async def cache_data(self, cache_key: str, data: Any) -> None:
        """
        Store data in cache with size management.
        
        Args:
            cache_key: The cache key
            data: The data to cache
            
        Raises:
            ValueError: If data is too large to cache
        """
        # Calculate data size
        data_size = self._calculate_data_size(data)
        
        # Check if single item is too large
        if data_size > self._max_cache_size_bytes:
            raise ValueError(
                f"Data too large to cache: {data_size} bytes exceeds "
                f"maximum cache size: {self._max_cache_size_bytes} bytes"
            )
            
        # Ensure cache has space (evict if necessary)
        await self._ensure_cache_space(data_size)
        
        # Store the data
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.utcnow()
        self._cache_sizes[cache_key] = data_size
        self._cache_access_counts[cache_key] = 1
        
        logger.debug(f"Cached data: {cache_key} ({data_size} bytes)")

    def build_cache_key(
        self, 
        symbols: Optional[List[str]] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        frequency: Optional[str] = None,
        include_extended_hours: bool = False,
        max_records: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate consistent cache key for request parameters.
        
        Args:
            symbols: List of symbols (for multi-symbol requests)
            symbol: Single symbol (for single-symbol requests)
            start_date: Start date
            end_date: End date
            frequency: Data frequency
            include_extended_hours: Extended hours flag
            max_records: Maximum records limit
            **kwargs: Additional parameters to include in key
            
        Returns:
            Consistent cache key string
        """
        # Handle both single symbol and multiple symbols
        symbol_str = ""
        if symbols:
            symbol_str = "|".join(sorted(symbols))
        elif symbol:
            symbol_str = symbol
            
        key_parts = [
            symbol_str,
            frequency or "default",
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none",
            str(include_extended_hours),
            str(max_records or "none")
        ]
        
        # Add any additional parameters
        if kwargs:
            # Sort kwargs for consistency
            for key, value in sorted(kwargs.items()):
                key_parts.append(f"{key}:{value}")
                
        # Create hash-like key to keep it shorter
        key_string = "|".join(key_parts)
        return f"historical_data:{hash(key_string) & 0x7FFFFFFF:08x}"

    async def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries matching pattern or all if None.
        
        Args:
            pattern: Regex pattern to match keys, or None to clear all
            
        Returns:
            Number of entries invalidated
        """
        if pattern is None:
            # Clear all cache
            count = len(self._cache)
            await self.clear_all()
            logger.info(f"Cleared entire cache: {count} entries")
            return count
            
        # Compile pattern
        try:
            regex_pattern: Pattern[str] = re.compile(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return 0
            
        # Find matching keys
        matching_keys = [
            key for key in self._cache.keys() 
            if regex_pattern.search(key)
        ]
        
        # Remove matching entries
        for key in matching_keys:
            await self._remove_cache_entry(key)
            
        self._cache_invalidations += len(matching_keys)
        
        logger.info(f"Invalidated {len(matching_keys)} cache entries matching pattern: {pattern}")
        return len(matching_keys)

    async def clear_all(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self._cache_access_counts.clear()
        self._cache_sizes.clear()
        self._access_patterns.clear()

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Comprehensive cache performance statistics.
        
        Returns:
            Dictionary with cache performance metrics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate memory usage
        total_memory_bytes = sum(self._cache_sizes.values())
        memory_usage_mb = total_memory_bytes / (1024 * 1024)
        memory_usage_percent = (total_memory_bytes / self._max_cache_size_bytes * 100)
        
        # Find most accessed keys
        most_accessed = sorted(
            self._cache_access_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5
        
        # Calculate average data age
        now = datetime.utcnow()
        ages = [
            (now - timestamp).total_seconds() / 60  # Age in minutes
            for timestamp in self._cache_timestamps.values()
        ]
        avg_age_minutes = sum(ages) / len(ages) if ages else 0
        
        return {
            "cache_size": len(self._cache),
            "memory_usage_mb": round(memory_usage_mb, 2),
            "memory_usage_percent": round(memory_usage_percent, 2),
            "max_memory_mb": self._max_cache_size_mb,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self._cache_evictions,
            "invalidations": self._cache_invalidations,
            "ttl_minutes": self._cache_ttl_minutes,
            "avg_age_minutes": round(avg_age_minutes, 2),
            "most_accessed_keys": most_accessed,
            "total_requests": total_requests
        }

    async def get_cache_usage_by_pattern(self, pattern: str) -> Dict[str, Any]:
        """
        Get cache usage statistics for entries matching a pattern.
        
        Args:
            pattern: Regex pattern to match cache keys
            
        Returns:
            Dictionary with usage statistics for matching entries
        """
        try:
            regex_pattern: Pattern[str] = re.compile(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return {}
            
        matching_keys = [
            key for key in self._cache.keys() 
            if regex_pattern.search(key)
        ]
        
        if not matching_keys:
            return {
                "pattern": pattern,
                "matching_keys": 0,
                "memory_usage_mb": 0,
                "total_accesses": 0
            }
            
        # Calculate statistics for matching keys
        total_memory = sum(self._cache_sizes.get(key, 0) for key in matching_keys)
        total_accesses = sum(self._cache_access_counts.get(key, 0) for key in matching_keys)
        
        return {
            "pattern": pattern,
            "matching_keys": len(matching_keys),
            "memory_usage_mb": round(total_memory / (1024 * 1024), 2),
            "total_accesses": total_accesses,
            "avg_accesses_per_key": round(total_accesses / len(matching_keys), 2)
        }

    async def warm_cache(self, cache_keys: List[str], warm_callback) -> int:
        """
        Warm cache with frequently accessed data.
        
        Args:
            cache_keys: List of cache keys to warm
            warm_callback: Async function to generate data for a key
            
        Returns:
            Number of keys successfully warmed
        """
        warmed_count = 0
        
        for key in cache_keys:
            try:
                # Skip if already cached and not expired
                if await self.get_cached_data(key) is not None:
                    continue
                    
                # Generate data using callback
                data = await warm_callback(key)
                if data is not None:
                    await self.cache_data(key, data)
                    warmed_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to warm cache key '{key}': {e}")
                
        logger.info(f"Warmed {warmed_count} cache entries")
        return warmed_count

    # Private helper methods
    
    async def _cleanup_loop(self) -> None:
        """Background task for periodic cache cleanup."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval_minutes * 60)
                await self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _cleanup_expired_entries(self) -> int:
        """Remove expired cache entries and return count removed."""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, timestamp in self._cache_timestamps.items():
            age_minutes = (now - timestamp).total_seconds() / 60
            if age_minutes > self._cache_ttl_minutes:
                expired_keys.append(key)
                
        for key in expired_keys:
            await self._remove_cache_entry(key)
            
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        return len(expired_keys)

    async def _ensure_cache_space(self, required_bytes: int) -> None:
        """Ensure cache has enough space by evicting entries if necessary."""
        current_size = sum(self._cache_sizes.values())
        
        # If we have space, no need to evict
        if current_size + required_bytes <= self._max_cache_size_bytes:
            return
            
        # Calculate how much we need to free
        bytes_to_free = current_size + required_bytes - self._max_cache_size_bytes
        
        # Get candidates for eviction (LRU policy based on access count and timestamp)
        eviction_candidates = []
        for key in self._cache.keys():
            access_count = self._cache_access_counts.get(key, 0)
            timestamp = self._cache_timestamps.get(key, datetime.min)
            size = self._cache_sizes.get(key, 0)
            
            # Score based on access count (lower is better for eviction) and age
            score = access_count - ((datetime.utcnow() - timestamp).total_seconds() / 3600)
            eviction_candidates.append((score, key, size))
            
        # Sort by score (lowest first = best candidates for eviction)
        eviction_candidates.sort()
        
        # Evict entries until we have enough space
        freed_bytes = 0
        evicted_count = 0
        
        for score, key, size in eviction_candidates:
            await self._remove_cache_entry(key)
            freed_bytes += size
            evicted_count += 1
            
            if freed_bytes >= bytes_to_free:
                break
                
        self._cache_evictions += evicted_count
        logger.debug(
            f"Evicted {evicted_count} cache entries to free {freed_bytes} bytes"
        )

    async def _remove_cache_entry(self, key: str) -> None:
        """Remove a single cache entry and all associated data."""
        self._cache.pop(key, None)
        self._cache_timestamps.pop(key, None)
        self._cache_access_counts.pop(key, None)
        self._cache_sizes.pop(key, None)
        self._access_patterns.pop(key, None)

    def _calculate_data_size(self, data: Any) -> int:
        """
        Calculate approximate memory size of data in bytes.
        
        Args:
            data: The data to measure
            
        Returns:
            Approximate size in bytes
        """
        try:
            # Try to serialize to get accurate size
            if isinstance(data, (dict, list)):
                return len(json.dumps(data, default=str).encode('utf-8'))
            elif isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (int, float)):
                return sys.getsizeof(data)
            else:
                # Fallback to sys.getsizeof for other types
                return sys.getsizeof(data)
        except Exception:
            # Conservative estimate if calculation fails
            return sys.getsizeof(data)