"""
Cache Service for OrdnungsHub
Implements in-memory caching with TTL support for API optimization
"""
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps
from loguru import logger

class CacheService:
    """
    Simple in-memory cache service with TTL support
    Can be extended to use Redis in production
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments"""
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry["expires_at"]:
                self._stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key}")
                return entry["value"]
            else:
                # Expired, remove from cache
                del self._cache[key]
                self._stats["evictions"] += 1
        
        self._stats["misses"] += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        logger.debug(f"Cache set for key: {key}, TTL: {ttl_seconds}s")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": f"{hit_rate:.2f}%",
            "memory_entries": len(self._cache)
        }
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now >= entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats["evictions"] += 1
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
cache_service = CacheService()


def cache_result(ttl_seconds: int = 300, prefix: str = "api"):
    """
    Decorator to cache function results
    
    Usage:
        @cache_result(ttl_seconds=600, prefix="files")
        async def get_user_files(user_id: int):
            # Expensive operation
            return files
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # Check cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call original function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, ttl_seconds)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # Check cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, ttl_seconds)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(prefix: str = None):
    """
    Invalidate cache entries by prefix
    
    Usage:
        invalidate_cache("files")  # Invalidate all file-related cache
        invalidate_cache()  # Clear entire cache
    """
    if prefix is None:
        cache_service.clear()
    else:
        keys_to_delete = [
            key for key in cache_service._cache.keys()
            if key.startswith(f"{prefix}:")
        ]
        for key in keys_to_delete:
            cache_service.delete(key)
        
        if keys_to_delete:
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries with prefix '{prefix}'")