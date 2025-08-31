"""
Advanced caching service for TradeAssist with Redis support and intelligent cache management.
"""
import asyncio
import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

# Redis backend disabled for this implementation - using memory-only caching
REDIS_AVAILABLE = False
aioredis = None

import structlog
from pydantic_settings import BaseSettings

logger = structlog.get_logger()


class CacheConfig(BaseSettings):
    """Configuration for cache service."""
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_max_connections: int = 20
    redis_encoding: str = "utf-8"
    
    # Cache TTL settings (in seconds)
    default_ttl: int = 300  # 5 minutes
    historical_data_ttl: int = 3600  # 1 hour for historical data
    market_data_ttl: int = 60  # 1 minute for real-time data
    query_results_ttl: int = 1800  # 30 minutes for query results
    
    # Performance settings
    compression_enabled: bool = True
    compression_threshold: int = 1024  # Compress data larger than 1KB
    max_memory_cache_items: int = 1000
    
    # Prefixing for cache keys
    key_prefix: str = "tradeassist:"
    
    class Config:
        env_prefix = "CACHE_"


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend as fallback."""
    
    def __init__(self, max_items: int = 1000):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttls: Dict[str, int] = {}
        self.max_items = max_items
        self._hits = 0
        self._misses = 0
        self._sets = 0
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache with TTL check."""
        if key not in self._cache:
            self._misses += 1
            return None
        
        # Check TTL expiration
        if key in self._ttls:
            age = (datetime.now() - self._timestamps[key]).total_seconds()
            if age > self._ttls[key]:
                await self.delete(key)
                self._misses += 1
                return None
        
        self._hits += 1
        return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache with TTL."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_items and key not in self._cache:
            oldest_key = min(self._timestamps.keys(), 
                           key=lambda k: self._timestamps[k])
            await self.delete(oldest_key)
        
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        if ttl:
            self._ttls[key] = ttl
        elif key in self._ttls:
            del self._ttls[key]
        
        self._sets += 1
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        deleted = key in self._cache
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._ttls.pop(key, None)
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return await self.get(key) is not None
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries."""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            self._ttls.clear()
            return count
        
        # Simple pattern matching for prefix
        keys_to_delete = []
        for key in self._cache.keys():
            if pattern.endswith('*') and key.startswith(pattern[:-1]):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            await self.delete(key)
        
        return len(keys_to_delete)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "backend": "memory",
            "items": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "hit_rate": round(hit_rate, 2),
            "max_items": self.max_items
        }


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for production use."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None
        
    async def connect(self) -> None:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            raise Exception("Redis not available - aioredis import failed")
        
        try:
            self._connection_pool = aioredis.ConnectionPool.from_url(
                self.config.redis_url,
                db=self.config.redis_db,
                max_connections=self.config.redis_max_connections,
                encoding=self.config.redis_encoding
            )
            
            self.redis = aioredis.Redis(
                connection_pool=self._connection_pool,
                decode_responses=False  # We'll handle encoding ourselves
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("Redis cache backend connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        try:
            # Try JSON first for simple types
            if isinstance(value, (str, int, float, bool, dict, list)):
                data = json.dumps(value).encode('utf-8')
                prefix = b'json:'
            else:
                # Use pickle for complex objects
                data = pickle.dumps(value)
                prefix = b'pkl:'
            
            # Compress if enabled and data is large enough
            if (self.config.compression_enabled and 
                len(data) > self.config.compression_threshold):
                import zlib
                data = zlib.compress(data)
                prefix = b'comp:' + prefix
            
            return prefix + data
            
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from Redis storage."""
        try:
            # Check for compression
            if data.startswith(b'comp:'):
                import zlib
                data = data[5:]  # Remove 'comp:' prefix
                if data.startswith(b'json:'):
                    data = zlib.decompress(data[5:])  # Remove 'json:' prefix
                    return json.loads(data.decode('utf-8'))
                elif data.startswith(b'pkl:'):
                    data = zlib.decompress(data[4:])  # Remove 'pkl:' prefix
                    return pickle.loads(data)
            
            # No compression
            if data.startswith(b'json:'):
                return json.loads(data[5:].decode('utf-8'))
            elif data.startswith(b'pkl:'):
                return pickle.loads(data[4:])
            
            # Fallback: try pickle directly
            return pickle.loads(data)
            
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise
    
    def _build_key(self, key: str) -> str:
        """Build full cache key with prefix."""
        return f"{self.config.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis:
            return None
        
        try:
            full_key = self._build_key(key)
            data = await self.redis.get(full_key)
            
            if data is None:
                return None
            
            return self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Redis get failed for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache with TTL."""
        if not self.redis:
            return False
        
        try:
            full_key = self._build_key(key)
            serialized_data = self._serialize(value)
            
            if ttl:
                await self.redis.setex(full_key, ttl, serialized_data)
            else:
                await self.redis.set(full_key, serialized_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set failed for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        if not self.redis:
            return False
        
        try:
            full_key = self._build_key(key)
            result = await self.redis.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete failed for key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self.redis:
            return False
        
        try:
            full_key = self._build_key(key)
            return await self.redis.exists(full_key) > 0
            
        except Exception as e:
            logger.error(f"Redis exists check failed for key '{key}': {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear Redis cache entries matching pattern."""
        if not self.redis:
            return 0
        
        try:
            if pattern is None:
                pattern = "*"
            
            full_pattern = self._build_key(pattern)
            keys = await self.redis.keys(full_pattern)
            
            if keys:
                return await self.redis.delete(*keys)
            
            return 0
            
        except Exception as e:
            logger.error(f"Redis clear failed for pattern '{pattern}': {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self.redis:
            return {"backend": "redis", "connected": False}
        
        try:
            info = await self.redis.info()
            return {
                "backend": "redis",
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Redis stats failed: {e}")
            return {"backend": "redis", "connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


class CacheService:
    """
    Advanced cache service with Redis support and intelligent cache management.
    
    Features:
    - Redis backend with memory fallback
    - Intelligent TTL management
    - Compression for large data
    - Cache warming capabilities
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis_backend: Optional[RedisCacheBackend] = None
        self.memory_backend = MemoryCacheBackend(
            max_items=self.config.max_memory_cache_items
        )
        
        # Performance tracking
        self._total_gets = 0
        self._total_sets = 0
        self._redis_fallbacks = 0
        
        self._warming_tasks: List[asyncio.Task] = []
        
    async def start(self) -> None:
        """Initialize cache service."""
        logger.info("Starting cache service")
        
        # Try to initialize Redis backend
        try:
            self.redis_backend = RedisCacheBackend(self.config)
            await self.redis_backend.connect()
            logger.info("Cache service started with Redis backend")
        except Exception as e:
            logger.warning(f"Redis not available, using memory backend only: {e}")
            self.redis_backend = None
        
        # Start cache warming for common patterns
        await self._start_cache_warming()
    
    async def stop(self) -> None:
        """Stop cache service and cleanup."""
        logger.info("Stopping cache service")
        
        # Cancel warming tasks
        for task in self._warming_tasks:
            task.cancel()
        
        await asyncio.gather(*self._warming_tasks, return_exceptions=True)
        self._warming_tasks.clear()
        
        # Disconnect Redis
        if self.redis_backend:
            await self.redis_backend.disconnect()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Tries Redis first, falls back to memory cache if needed.
        """
        self._total_gets += 1
        
        # Try Redis first
        if self.redis_backend:
            try:
                result = await self.redis_backend.get(key)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Redis get failed, falling back to memory: {e}")
                self._redis_fallbacks += 1
        
        # Fallback to memory cache
        return await self.memory_backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Stores in both Redis and memory cache for redundancy.
        """
        self._total_sets += 1
        
        if ttl is None:
            ttl = self.config.default_ttl
        
        success = True
        
        # Set in Redis
        if self.redis_backend:
            try:
                redis_success = await self.redis_backend.set(key, value, ttl)
                success = success and redis_success
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
                success = False
        
        # Set in memory cache as backup
        try:
            memory_success = await self.memory_backend.set(key, value, ttl)
            success = success or memory_success  # At least one must succeed
        except Exception as e:
            logger.error(f"Memory cache set failed: {e}")
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete value from all cache backends."""
        results = []
        
        # Delete from Redis
        if self.redis_backend:
            try:
                results.append(await self.redis_backend.delete(key))
            except Exception as e:
                logger.error(f"Redis delete failed: {e}")
        
        # Delete from memory
        try:
            results.append(await self.memory_backend.delete(key))
        except Exception as e:
            logger.error(f"Memory cache delete failed: {e}")
        
        return any(results)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any cache backend."""
        # Check Redis first
        if self.redis_backend:
            try:
                if await self.redis_backend.exists(key):
                    return True
            except Exception as e:
                logger.error(f"Redis exists check failed: {e}")
        
        # Check memory cache
        return await self.memory_backend.exists(key)
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern from all backends."""
        total_cleared = 0
        
        # Clear from Redis
        if self.redis_backend:
            try:
                total_cleared += await self.redis_backend.clear(pattern)
            except Exception as e:
                logger.error(f"Redis clear failed: {e}")
        
        # Clear from memory
        try:
            total_cleared += await self.memory_backend.clear(pattern)
        except Exception as e:
            logger.error(f"Memory cache clear failed: {e}")
        
        return total_cleared
    
    async def get_historical_data(self, key: str) -> Optional[Any]:
        """Get historical data with appropriate TTL."""
        return await self.get(key)
    
    async def set_historical_data(self, key: str, value: Any) -> bool:
        """Set historical data with appropriate TTL."""
        return await self.set(key, value, self.config.historical_data_ttl)
    
    async def get_market_data(self, key: str) -> Optional[Any]:
        """Get market data with short TTL for real-time updates."""
        return await self.get(key)
    
    async def set_market_data(self, key: str, value: Any) -> bool:
        """Set market data with short TTL for real-time updates."""
        return await self.set(key, value, self.config.market_data_ttl)
    
    async def get_query_results(self, key: str) -> Optional[Any]:
        """Get cached query results."""
        return await self.get(key)
    
    async def set_query_results(self, key: str, value: Any) -> bool:
        """Set cached query results with medium TTL."""
        return await self.set(key, value, self.config.query_results_ttl)
    
    async def warm_cache(self, keys_and_values: Dict[str, Any]) -> int:
        """
        Warm cache with frequently accessed data.
        
        Args:
            keys_and_values: Dictionary of cache keys and their values
            
        Returns:
            Number of keys successfully cached
        """
        success_count = 0
        
        for key, value in keys_and_values.items():
            try:
                if await self.set(key, value):
                    success_count += 1
            except Exception as e:
                logger.error(f"Cache warming failed for key '{key}': {e}")
        
        logger.info(f"Cache warming completed: {success_count}/{len(keys_and_values)} keys cached")
        return success_count
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all cache backends."""
        stats = {
            "service": {
                "total_gets": self._total_gets,
                "total_sets": self._total_sets,
                "redis_fallbacks": self._redis_fallbacks,
                "redis_available": self.redis_backend is not None
            }
        }
        
        # Get memory cache stats
        try:
            stats["memory"] = await self.memory_backend.get_stats()
        except Exception as e:
            stats["memory"] = {"error": str(e)}
        
        # Get Redis stats if available
        if self.redis_backend:
            try:
                stats["redis"] = await self.redis_backend.get_stats()
            except Exception as e:
                stats["redis"] = {"error": str(e)}
        else:
            stats["redis"] = {"available": False}
        
        return stats
    
    async def _start_cache_warming(self) -> None:
        """Start background cache warming tasks."""
        # This can be extended to warm frequently accessed patterns
        # For now, we'll just log the capability
        logger.info("Cache warming capability initialized")
        
        # Example: Warm cache with common queries
        # warming_task = asyncio.create_task(self._periodic_cache_warming())
        # self._warming_tasks.append(warming_task)
    
    async def _periodic_cache_warming(self) -> None:
        """Periodic cache warming (placeholder for future implementation)."""
        while True:
            try:
                await asyncio.sleep(3600)  # Warm every hour
                # Implement actual warming logic based on usage patterns
                logger.debug("Periodic cache warming executed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic cache warming failed: {e}")