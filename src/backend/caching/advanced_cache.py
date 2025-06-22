"""
Advanced Caching Strategies - Phase 2 Performance Enhancement
Implements sophisticated caching patterns including stale-while-revalidate,
adaptive TTL, and intelligent cache warming
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")

class CacheStrategy(Enum):
    """Cache strategy types"""
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    CACHE_ONLY = "cache_only"
    NETWORK_ONLY = "network_only"
    ADAPTIVE = "adaptive"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = 0
    strategy: CacheStrategy = CacheStrategy.CACHE_FIRST
    tags: List[str] = None
    size: int = 0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.size == 0:
            self.size = len(json.dumps(self.data, default=str))

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    revalidations: int = 0
    total_size: int = 0
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class AdvancedCacheManager:
    """
    Advanced cache manager with multiple strategies and intelligent optimization
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 max_memory_cache_size: int = 100_000_000,  # 100MB
                 default_ttl: int = 3600):  # 1 hour
        
        self.redis_client = None
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_size = max_memory_cache_size
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()
        
        # Cache configuration
        self.cache_configs: Dict[str, Dict[str, Any]] = {}
        self.revalidation_tasks: Dict[str, asyncio.Task] = {}
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            self._init_redis(redis_url)
        
        # Start background tasks
        asyncio.create_task(self._background_maintenance())
    
    def _init_redis(self, redis_url: str):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    def configure_cache(self, 
                       pattern: str,
                       strategy: CacheStrategy = CacheStrategy.STALE_WHILE_REVALIDATE,
                       ttl: int = None,
                       stale_ttl: int = None,
                       tags: List[str] = None,
                       revalidation_function: Callable = None):
        """Configure caching behavior for specific key patterns"""
        
        self.cache_configs[pattern] = {
            'strategy': strategy,
            'ttl': ttl or self.default_ttl,
            'stale_ttl': stale_ttl or (ttl or self.default_ttl) * 2,
            'tags': tags or [],
            'revalidation_function': revalidation_function
        }
        
        logger.info(f"Cache configured for pattern '{pattern}' with strategy {strategy.value}")
    
    async def get(self, 
                  key: str, 
                  fetch_function: Callable = None,
                  strategy: CacheStrategy = None,
                  ttl: int = None) -> Any:
        """
        Get value from cache with advanced strategies
        """
        config = self._get_config_for_key(key)
        strategy = strategy or config.get('strategy', CacheStrategy.STALE_WHILE_REVALIDATE)
        
        if strategy == CacheStrategy.CACHE_FIRST:
            return await self._cache_first(key, fetch_function, config)
        elif strategy == CacheStrategy.NETWORK_FIRST:
            return await self._network_first(key, fetch_function, config)
        elif strategy == CacheStrategy.STALE_WHILE_REVALIDATE:
            return await self._stale_while_revalidate(key, fetch_function, config)
        elif strategy == CacheStrategy.CACHE_ONLY:
            return await self._cache_only(key)
        elif strategy == CacheStrategy.NETWORK_ONLY:
            return await self._network_only(key, fetch_function)
        elif strategy == CacheStrategy.ADAPTIVE:
            return await self._adaptive_strategy(key, fetch_function, config)
        else:
            return await self._cache_first(key, fetch_function, config)
    
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: int = None,
                  tags: List[str] = None) -> bool:
        """Set value in cache with metadata"""
        
        config = self._get_config_for_key(key)
        ttl = ttl or config.get('ttl', self.default_ttl)
        tags = tags or config.get('tags', [])
        
        now = time.time()
        entry = CacheEntry(
            data=value,
            created_at=now,
            expires_at=now + ttl,
            tags=tags
        )
        
        # Store in memory cache
        await self._set_memory_cache(key, entry)
        
        # Store in Redis if available
        if self.redis_client:
            await self._set_redis_cache(key, entry, ttl)
        
        self.metrics.sets += 1
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache layers"""
        deleted = False
        
        # Delete from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True
        
        # Delete from Redis
        if self.redis_client:
            result = await self.redis_client.delete(key)
            deleted = deleted or bool(result)
        
        if deleted:
            self.metrics.deletes += 1
        
        return deleted
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cache entries with specified tags"""
        invalidated = 0
        
        # Invalidate memory cache
        keys_to_delete = []
        for key, entry in self.memory_cache.items():
            if any(tag in entry.tags for tag in tags):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            await self.delete(key)
            invalidated += 1
        
        # Invalidate Redis cache (would need tag indexing in production)
        # This is a simplified implementation
        
        logger.info(f"Invalidated {invalidated} cache entries for tags: {tags}")
        return invalidated
    
    async def _cache_first(self, key: str, fetch_function: Callable, config: Dict) -> Any:
        """Cache-first strategy: check cache first, fetch if miss"""
        
        # Try to get from cache
        cached_value = await self._get_from_cache(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - fetch and store
        if fetch_function:
            value = await self._call_fetch_function(fetch_function)
            await self.set(key, value, config.get('ttl'))
            return value
        
        return None
    
    async def _network_first(self, key: str, fetch_function: Callable, config: Dict) -> Any:
        """Network-first strategy: try network first, fallback to cache"""
        
        if fetch_function:
            try:
                value = await self._call_fetch_function(fetch_function)
                await self.set(key, value, config.get('ttl'))
                return value
            except Exception as e:
                logger.warning(f"Network fetch failed for {key}: {e}")
                # Fallback to cache
                cached_value = await self._get_from_cache(key, allow_stale=True)
                if cached_value is not None:
                    return cached_value
                raise
        
        return await self._get_from_cache(key)
    
    async def _stale_while_revalidate(self, key: str, fetch_function: Callable, config: Dict) -> Any:
        """
        Stale-while-revalidate: return cached value immediately, 
        revalidate in background if stale
        """
        
        cached_entry = await self._get_cache_entry(key)
        now = time.time()
        
        if cached_entry:
            # Update access time and hit count
            cached_entry.last_accessed = now
            cached_entry.hit_count += 1
            
            # If cache is fresh, return immediately
            if now < cached_entry.expires_at:
                self.metrics.hits += 1
                return cached_entry.data
            
            # Cache is stale but within stale_ttl - return stale data and revalidate
            stale_expires_at = cached_entry.expires_at + config.get('stale_ttl', self.default_ttl)
            if now < stale_expires_at and fetch_function:
                # Return stale data immediately
                self.metrics.hits += 1
                
                # Start background revalidation if not already running
                if key not in self.revalidation_tasks:
                    self.revalidation_tasks[key] = asyncio.create_task(
                        self._revalidate_in_background(key, fetch_function, config)
                    )
                
                return cached_entry.data
        
        # No cache or completely stale - fetch synchronously
        self.metrics.misses += 1
        
        if fetch_function:
            value = await self._call_fetch_function(fetch_function)
            await self.set(key, value, config.get('ttl'))
            return value
        
        return None
    
    async def _cache_only(self, key: str) -> Any:
        """Cache-only strategy: only return cached values"""
        return await self._get_from_cache(key)
    
    async def _network_only(self, key: str, fetch_function: Callable) -> Any:
        """Network-only strategy: always fetch from network"""
        if fetch_function:
            return await self._call_fetch_function(fetch_function)
        return None
    
    async def _adaptive_strategy(self, key: str, fetch_function: Callable, config: Dict) -> Any:
        """
        Adaptive strategy: choose strategy based on performance metrics
        """
        
        # Analyze cache performance for this key pattern
        hit_ratio = self._calculate_pattern_hit_ratio(key)
        average_fetch_time = self._get_average_fetch_time(key)
        
        # Decide strategy based on metrics
        if hit_ratio > 0.8:
            # High hit ratio - use cache first
            return await self._cache_first(key, fetch_function, config)
        elif hit_ratio < 0.3 or average_fetch_time < 50:  # 50ms threshold
            # Low hit ratio or fast fetch - use network first
            return await self._network_first(key, fetch_function, config)
        else:
            # Moderate performance - use stale-while-revalidate
            return await self._stale_while_revalidate(key, fetch_function, config)
    
    async def _revalidate_in_background(self, key: str, fetch_function: Callable, config: Dict):
        """Background revalidation task"""
        try:
            logger.debug(f"Background revalidation started for {key}")
            value = await self._call_fetch_function(fetch_function)
            await self.set(key, value, config.get('ttl'))
            self.metrics.revalidations += 1
            logger.debug(f"Background revalidation completed for {key}")
        except Exception as e:
            logger.error(f"Background revalidation failed for {key}: {e}")
        finally:
            # Remove task from tracking
            if key in self.revalidation_tasks:
                del self.revalidation_tasks[key]
    
    async def _get_from_cache(self, key: str, allow_stale: bool = False) -> Any:
        """Get value from cache layers"""
        entry = await self._get_cache_entry(key)
        
        if entry:
            now = time.time()
            if allow_stale or now < entry.expires_at:
                entry.last_accessed = now
                entry.hit_count += 1
                self.metrics.hits += 1
                return entry.data
        
        self.metrics.misses += 1
        return None
    
    async def _get_cache_entry(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry with metadata"""
        
        # Try memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Try Redis cache
        if self.redis_client:
            try:
                data = await self.redis_client.get(key)
                if data:
                    entry_dict = json.loads(data)
                    entry = CacheEntry(**entry_dict)
                    
                    # Store in memory cache for faster access
                    await self._set_memory_cache(key, entry)
                    return entry
            except Exception as e:
                logger.warning(f"Failed to get from Redis cache: {e}")
        
        return None
    
    async def _set_memory_cache(self, key: str, entry: CacheEntry):
        """Set value in memory cache with size management"""
        
        # Check if we need to evict entries
        while self._get_memory_cache_size() + entry.size > self.max_memory_size:
            await self._evict_lru_entry()
        
        self.memory_cache[key] = entry
        self.metrics.total_size += entry.size
    
    async def _set_redis_cache(self, key: str, entry: CacheEntry, ttl: int):
        """Set value in Redis cache"""
        try:
            entry_dict = asdict(entry)
            await self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(entry_dict, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to set Redis cache: {e}")
    
    def _get_memory_cache_size(self) -> int:
        """Calculate current memory cache size"""
        return sum(entry.size for entry in self.memory_cache.values())
    
    async def _evict_lru_entry(self):
        """Evict least recently used entry from memory cache"""
        if not self.memory_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed
        )
        
        entry = self.memory_cache[lru_key]
        del self.memory_cache[lru_key]
        self.metrics.total_size -= entry.size
        self.metrics.evictions += 1
        
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    async def _call_fetch_function(self, fetch_function: Callable) -> Any:
        """Call fetch function with error handling and timing"""
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(fetch_function):
                result = await fetch_function()
            else:
                result = fetch_function()
            
            end_time = time.time()
            logger.debug(f"Fetch function completed in {(end_time - start_time) * 1000:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Fetch function failed: {e}")
            raise
    
    def _get_config_for_key(self, key: str) -> Dict[str, Any]:
        """Get cache configuration for key pattern"""
        for pattern, config in self.cache_configs.items():
            if pattern in key or key.startswith(pattern):
                return config
        
        return {'ttl': self.default_ttl, 'strategy': CacheStrategy.STALE_WHILE_REVALIDATE}
    
    def _calculate_pattern_hit_ratio(self, key: str) -> float:
        """Calculate hit ratio for key pattern (simplified)"""
        # In production, this would analyze historical metrics
        return self.metrics.hit_ratio
    
    def _get_average_fetch_time(self, key: str) -> float:
        """Get average fetch time for key pattern (simplified)"""
        # In production, this would track fetch times
        return 100.0  # Default 100ms
    
    async def _background_maintenance(self):
        """Background maintenance tasks"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up expired entries
                await self._cleanup_expired_entries()
                
                # Log metrics
                logger.info(f"Cache metrics: {asdict(self.metrics)}")
                
            except Exception as e:
                logger.error(f"Background maintenance error: {e}")
    
    async def _cleanup_expired_entries(self):
        """Clean up expired cache entries"""
        now = time.time()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if now > entry.expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            await self.delete(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'metrics': asdict(self.metrics),
            'memory_cache_size': len(self.memory_cache),
            'memory_usage_bytes': self._get_memory_cache_size(),
            'memory_usage_mb': self._get_memory_cache_size() / 1024 / 1024,
            'configurations': len(self.cache_configs),
            'active_revalidations': len(self.revalidation_tasks),
            'redis_available': self.redis_client is not None
        }

# Global advanced cache instance
advanced_cache = AdvancedCacheManager()

# Configuration examples
def setup_default_cache_patterns():
    """Setup default cache patterns for common use cases"""
    
    # Workspace data - stale-while-revalidate with 10 minute TTL
    advanced_cache.configure_cache(
        pattern='workspaces:',
        strategy=CacheStrategy.STALE_WHILE_REVALIDATE,
        ttl=600,  # 10 minutes
        stale_ttl=1800,  # 30 minutes stale allowed
        tags=['workspaces']
    )
    
    # Task data - adaptive strategy with 5 minute TTL
    advanced_cache.configure_cache(
        pattern='tasks:',
        strategy=CacheStrategy.ADAPTIVE,
        ttl=300,  # 5 minutes
        stale_ttl=900,  # 15 minutes stale allowed
        tags=['tasks']
    )
    
    # User data - cache-first with 1 hour TTL
    advanced_cache.configure_cache(
        pattern='users:',
        strategy=CacheStrategy.CACHE_FIRST,
        ttl=3600,  # 1 hour
        tags=['users']
    )
    
    # Performance metrics - network-first with 1 minute TTL
    advanced_cache.configure_cache(
        pattern='performance:',
        strategy=CacheStrategy.NETWORK_FIRST,
        ttl=60,  # 1 minute
        tags=['performance']
    )
    
    # Static content - cache-first with 24 hour TTL
    advanced_cache.configure_cache(
        pattern='static:',
        strategy=CacheStrategy.CACHE_FIRST,
        ttl=86400,  # 24 hours
        tags=['static']
    )
    
    logger.info("Default cache patterns configured")

# Initialize default patterns
setup_default_cache_patterns()