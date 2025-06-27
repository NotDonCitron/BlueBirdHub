"""
Cache Configuration for BlueBirdHub
Provides environment-specific cache settings
"""
import os
from typing import Dict, Any

class CacheConfig:
    """Cache configuration manager"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration based on environment"""
        
        if self.environment == "production":
            return {
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                "socket_timeout": 10,
                "socket_connect_timeout": 10,
                "socket_keepalive": True,
                "retry_on_timeout": True,
                "health_check_interval": 30,
                "max_connections": 50,
                "decode_responses": False,
                "password": os.getenv("REDIS_PASSWORD"),
                "ssl": os.getenv("REDIS_SSL", "false").lower() == "true",
                "ssl_ca_certs": os.getenv("REDIS_SSL_CA_CERTS"),
            }
        
        elif self.environment == "testing":
            return {
                "redis_url": os.getenv("REDIS_TEST_URL", "redis://localhost:6380"),
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "decode_responses": False,
                "max_connections": 10,
            }
        
        else:  # development
            return {
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "socket_keepalive": True,
                "retry_on_timeout": True,
                "health_check_interval": 30,
                "max_connections": 20,
                "decode_responses": False,
            }
    
    def get_cache_ttl_config(self) -> Dict[str, int]:
        """Get TTL configuration for different cache types"""
        return {
            "user_sessions": 3600,      # 1 hour
            "workspace_data": 1800,     # 30 minutes
            "task_data": 900,           # 15 minutes
            "analytics_data": 300,      # 5 minutes
            "file_metadata": 1800,      # 30 minutes
            "search_results": 600,      # 10 minutes
            "api_responses": 180,       # 3 minutes
            "database_queries": 120,    # 2 minutes
        }
    
    def get_cache_policies(self) -> Dict[str, str]:
        """Get cache eviction policies"""
        return {
            "default": "allkeys-lru",
            "sessions": "volatile-ttl",
            "analytics": "allkeys-lfu",
            "search": "allkeys-lru",
        }

# Global cache config instance
cache_config = CacheConfig()