"""
Redis Cache Service for OrdnungsHub

Provides caching functionality for API responses, database queries,
and other performance-critical operations.
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import redis
import os
from loguru import logger

class CacheService:
    """Redis-based caching service with automatic serialization"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL")
            redis_password = os.getenv("REDIS_PASSWORD")
            
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
            elif redis_password:
                self.redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    password=redis_password,
                    decode_responses=False  # We handle serialization ourselves
                )
            else:
                logger.warning("Redis not configured - caching disabled")
                return
                
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - caching disabled")
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
            
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
                
            # Try JSON first (for simple data), then pickle
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Union[int, timedelta] = 300) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds or timedelta
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # Try JSON first (faster), fall back to pickle
            try:
                data = json.dumps(value, default=str)
            except TypeError:
                data = pickle.dumps(value)
            
            return self.redis_client.setex(key, ttl, data)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Redis pattern (e.g., "user:*", "api:workspaces:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled:
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for key"""
        if not self.enabled:
            return -1
            
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    def health_check(self) -> dict:
        """Check cache service health"""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Redis not configured"
            }
        
        try:
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# Global cache instance
cache = CacheService()

def cache_key(*args) -> str:
    """Generate cache key from arguments"""
    return ":".join(str(arg) for arg in args)

def cached_response(key_prefix: str, ttl: int = 300):
    """
    Decorator for caching function responses
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key = cache_key(key_prefix, func.__name__, str(args), str(sorted(kwargs.items())))
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            logger.debug(f"Cache miss - stored result for {key}")
            
            return result
        return wrapper
    return decorator