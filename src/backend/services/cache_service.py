"""
Redis Caching Service for Database Optimization
Implements intelligent caching strategies with TTL management and cache invalidation
"""
import json
import hashlib
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta
import redis
from loguru import logger
from functools import wraps
import pickle
import asyncio
from sqlalchemy.orm import Session


class CacheService:
    """
    Intelligent Redis caching service with multiple cache strategies
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis connection with retry logic"""
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # Use bytes for pickle serialization
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
            
            # Cache metrics
            self.cache_hits = 0
            self.cache_misses = 0
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache service disabled.")
            self.redis_client = None
    
    def _is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key from parameters"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return f"ordnungshub:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from Redis"""
        return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_available():
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                self.cache_hits += 1
                return self._deserialize(data)
            else:
                self.cache_misses += 1
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self._is_available():
            return False
        
        try:
            serialized_value = self._serialize(value)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self._is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "is_available": self._is_available()
        }
        
        if self._is_available():
            try:
                info = self.redis_client.info()
                stats.update({
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                })
            except:
                pass
        
        return stats


# Global cache service instance
cache_service = CacheService()


class WorkspaceCacheService:
    """
    Specialized caching for workspace data with 10-minute TTL
    """
    
    TTL = 600  # 10 minutes
    
    @staticmethod
    async def get_workspace(workspace_id: int) -> Optional[Dict]:
        """Get cached workspace data"""
        key = cache_service._generate_key("workspace", workspace_id=workspace_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_workspace(workspace_id: int, workspace_data: Dict) -> bool:
        """Cache workspace data"""
        key = cache_service._generate_key("workspace", workspace_id=workspace_id)
        return await cache_service.set(key, workspace_data, WorkspaceCacheService.TTL)
    
    @staticmethod
    async def get_user_workspaces(user_id: int) -> Optional[List[Dict]]:
        """Get cached user workspaces"""
        key = cache_service._generate_key("user_workspaces", user_id=user_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_user_workspaces(user_id: int, workspaces: List[Dict]) -> bool:
        """Cache user workspaces"""
        key = cache_service._generate_key("user_workspaces", user_id=user_id)
        return await cache_service.set(key, workspaces, WorkspaceCacheService.TTL)
    
    @staticmethod
    async def invalidate_workspace(workspace_id: int) -> None:
        """Invalidate workspace cache"""
        patterns = [
            f"ordnungshub:*workspace_id:{workspace_id}*",
            f"ordnungshub:*workspace:{workspace_id}*"
        ]
        for pattern in patterns:
            await cache_service.delete_pattern(pattern)
    
    @staticmethod
    async def invalidate_user_workspaces(user_id: int) -> None:
        """Invalidate user workspace cache"""
        pattern = f"ordnungshub:*user_workspaces*user_id:{user_id}*"
        await cache_service.delete_pattern(pattern)


class FileMetadataCacheService:
    """
    Specialized caching for file metadata with 5-minute TTL
    """
    
    TTL = 300  # 5 minutes
    
    @staticmethod
    async def get_file_metadata(file_id: int) -> Optional[Dict]:
        """Get cached file metadata"""
        key = cache_service._generate_key("file_metadata", file_id=file_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_file_metadata(file_id: int, file_data: Dict) -> bool:
        """Cache file metadata"""
        key = cache_service._generate_key("file_metadata", file_id=file_id)
        return await cache_service.set(key, file_data, FileMetadataCacheService.TTL)
    
    @staticmethod
    async def get_workspace_files(workspace_id: int, user_id: int) -> Optional[List[Dict]]:
        """Get cached workspace files"""
        key = cache_service._generate_key("workspace_files", workspace_id=workspace_id, user_id=user_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_workspace_files(workspace_id: int, user_id: int, files: List[Dict]) -> bool:
        """Cache workspace files"""
        key = cache_service._generate_key("workspace_files", workspace_id=workspace_id, user_id=user_id)
        return await cache_service.set(key, files, FileMetadataCacheService.TTL)
    
    @staticmethod
    async def invalidate_file(file_id: int) -> None:
        """Invalidate file cache"""
        patterns = [
            f"ordnungshub:*file_id:{file_id}*",
            f"ordnungshub:*file_metadata*file_id:{file_id}*"
        ]
        for pattern in patterns:
            await cache_service.delete_pattern(pattern)
    
    @staticmethod
    async def invalidate_workspace_files(workspace_id: int) -> None:
        """Invalidate workspace files cache"""
        pattern = f"ordnungshub:*workspace_files*workspace_id:{workspace_id}*"
        await cache_service.delete_pattern(pattern)


class UserSessionCacheService:
    """
    Specialized caching for user sessions with 30-minute TTL
    """
    
    TTL = 1800  # 30 minutes
    
    @staticmethod
    async def get_user_session(user_id: int) -> Optional[Dict]:
        """Get cached user session data"""
        key = cache_service._generate_key("user_session", user_id=user_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_user_session(user_id: int, session_data: Dict) -> bool:
        """Cache user session data"""
        key = cache_service._generate_key("user_session", user_id=user_id)
        return await cache_service.set(key, session_data, UserSessionCacheService.TTL)
    
    @staticmethod
    async def get_user_preferences(user_id: int) -> Optional[Dict]:
        """Get cached user preferences"""
        key = cache_service._generate_key("user_preferences", user_id=user_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_user_preferences(user_id: int, preferences: Dict) -> bool:
        """Cache user preferences"""
        key = cache_service._generate_key("user_preferences", user_id=user_id)
        return await cache_service.set(key, preferences, UserSessionCacheService.TTL)
    
    @staticmethod
    async def invalidate_user_session(user_id: int) -> None:
        """Invalidate user session cache"""
        pattern = f"ordnungshub:*user_id:{user_id}*"
        await cache_service.delete_pattern(pattern)


class QueryCacheService:
    """
    Caching for expensive database queries and aggregations
    """
    
    TTL = 900  # 15 minutes for aggregations
    
    @staticmethod
    async def get_workspace_analytics(workspace_id: int) -> Optional[Dict]:
        """Get cached workspace analytics"""
        key = cache_service._generate_key("workspace_analytics", workspace_id=workspace_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_workspace_analytics(workspace_id: int, analytics: Dict) -> bool:
        """Cache workspace analytics"""
        key = cache_service._generate_key("workspace_analytics", workspace_id=workspace_id)
        return await cache_service.set(key, analytics, QueryCacheService.TTL)
    
    @staticmethod
    async def get_user_dashboard_data(user_id: int) -> Optional[Dict]:
        """Get cached user dashboard data"""
        key = cache_service._generate_key("user_dashboard", user_id=user_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def set_user_dashboard_data(user_id: int, dashboard_data: Dict) -> bool:
        """Cache user dashboard data"""
        key = cache_service._generate_key("user_dashboard", user_id=user_id)
        return await cache_service.set(key, dashboard_data, QueryCacheService.TTL)


def cache_result(ttl: int = 300, key_prefix: str = "generic"):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key generation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class CacheInvalidationService:
    """
    Centralized cache invalidation management
    """
    
    @staticmethod
    async def invalidate_workspace_related(workspace_id: int) -> None:
        """Invalidate all workspace-related caches"""
        await WorkspaceCacheService.invalidate_workspace(workspace_id)
        await FileMetadataCacheService.invalidate_workspace_files(workspace_id)
        await cache_service.delete_pattern(f"ordnungshub:*workspace_analytics*workspace_id:{workspace_id}*")
    
    @staticmethod
    async def invalidate_user_related(user_id: int) -> None:
        """Invalidate all user-related caches"""
        await UserSessionCacheService.invalidate_user_session(user_id)
        await WorkspaceCacheService.invalidate_user_workspaces(user_id)
        await cache_service.delete_pattern(f"ordnungshub:*user_dashboard*user_id:{user_id}*")
    
    @staticmethod
    async def invalidate_file_related(file_id: int, workspace_id: int = None) -> None:
        """Invalidate all file-related caches"""
        await FileMetadataCacheService.invalidate_file(file_id)
        if workspace_id:
            await FileMetadataCacheService.invalidate_workspace_files(workspace_id)
    
    @staticmethod
    async def clear_all_cache() -> int:
        """Clear all application caches (use with caution)"""
        return await cache_service.delete_pattern("ordnungshub:*")


# Initialize cache services on module import
logger.info("Database cache services initialized")