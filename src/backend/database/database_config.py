"""
Database Configuration and Optimization Settings
Mercury-DB optimized configuration for maximum performance
"""
import os
from typing import Dict, Any
from pathlib import Path

class DatabaseConfig:
    """
    Centralized database configuration with optimization settings
    """
    
    # SQLite Performance Settings
    SQLITE_PRAGMAS = {
        # WAL mode for better concurrency
        'journal_mode': 'WAL',
        
        # Balanced durability vs performance
        'synchronous': 'NORMAL',
        
        # Large cache for better performance (64MB)
        'cache_size': -64000,
        
        # Store temporary tables in memory
        'temp_store': 'MEMORY',
        
        # Memory-mapped I/O (256MB)
        'mmap_size': 268435456,
        
        # Enable foreign key constraints
        'foreign_keys': 'ON',
        
        # Incremental vacuum for maintenance
        'auto_vacuum': 'INCREMENTAL',
        
        # Optimize query planner
        'optimize': True,
        
        # WAL checkpoint settings
        'wal_autocheckpoint': 1000,
        'wal_checkpoint': 'TRUNCATE'
    }
    
    # Connection Pool Settings
    CONNECTION_POOL = {
        'pool_size': 20,          # Number of persistent connections
        'max_overflow': 30,       # Additional connections under load
        'pool_timeout': 30,       # Timeout for getting connection
        'pool_recycle': 3600,     # Recycle connections every hour
        'pool_pre_ping': True,    # Verify connections before use
        'pool_reset_on_return': 'commit'  # Reset connections on return
    }
    
    # Query Performance Thresholds
    PERFORMANCE_THRESHOLDS = {
        'slow_query_threshold': 0.050,      # 50ms
        'very_slow_query_threshold': 0.200, # 200ms
        'connection_timeout': 30,           # 30 seconds
        'query_timeout': 60,                # 60 seconds
        'max_connections': 50,              # Maximum concurrent connections
    }
    
    # Cache Configuration
    CACHE_CONFIG = {
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'redis_db': int(os.getenv('REDIS_DB', '0')),
        'redis_timeout': 5,
        'redis_retry_on_timeout': True,
        'redis_health_check_interval': 30,
        
        # TTL Settings (in seconds)
        'workspace_ttl': 600,      # 10 minutes
        'file_metadata_ttl': 300,  # 5 minutes
        'user_session_ttl': 1800,  # 30 minutes
        'query_cache_ttl': 900,    # 15 minutes
        'search_cache_ttl': 180,   # 3 minutes
        
        # Cache size limits
        'max_cache_size': '256mb',
        'max_memory_policy': 'allkeys-lru'
    }
    
    # Monitoring and Alerting
    MONITORING_CONFIG = {
        'enable_query_logging': True,
        'log_slow_queries': True,
        'enable_performance_metrics': True,
        'metrics_retention_hours': 24,
        'alert_slow_query_threshold': 0.100,  # 100ms
        'alert_connection_errors': 5,
        'health_check_interval': 300,  # 5 minutes
    }
    
    # Index Optimization Settings
    INDEX_CONFIG = {
        'auto_analyze': True,
        'analyze_threshold': 1000,  # Auto-analyze after 1000 changes
        'vacuum_threshold': 0.1,    # Vacuum when 10% of pages are free
        'incremental_vacuum_pages': 100,
    }

    @classmethod
    def get_database_url(cls) -> str:
        """Get optimized database URL"""
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Add connection parameters for optimization
        base_url = f"sqlite:///{data_dir}/ordnungshub.db"
        
        # SQLite doesn't support URL parameters, these are applied via pragmas
        return base_url
    
    @classmethod
    def get_engine_config(cls) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration"""
        return {
            'pool_pre_ping': cls.CONNECTION_POOL['pool_pre_ping'],
            'pool_recycle': cls.CONNECTION_POOL['pool_recycle'],
            'echo': cls.MONITORING_CONFIG['enable_query_logging'],
            'echo_pool': False,  # Enable for connection pool debugging
            'future': True,      # Use SQLAlchemy 2.0 style
            'connect_args': {
                'check_same_thread': False,
                'timeout': cls.PERFORMANCE_THRESHOLDS['connection_timeout'],
                'isolation_level': None,  # Enable autocommit mode
            }
        }
    
    @classmethod
    def get_session_config(cls) -> Dict[str, Any]:
        """Get SQLAlchemy session configuration"""
        return {
            'autocommit': False,
            'autoflush': False,      # Manual flush control
            'expire_on_commit': False,  # Keep objects accessible after commit
        }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            'url': cls.CACHE_CONFIG['redis_url'],
            'db': cls.CACHE_CONFIG['redis_db'],
            'socket_timeout': cls.CACHE_CONFIG['redis_timeout'],
            'socket_connect_timeout': cls.CACHE_CONFIG['redis_timeout'],
            'socket_keepalive': True,
            'socket_keepalive_options': {},
            'retry_on_timeout': cls.CACHE_CONFIG['redis_retry_on_timeout'],
            'health_check_interval': cls.CACHE_CONFIG['redis_health_check_interval'],
            'decode_responses': False,  # Use bytes for pickle serialization
        }
    
    @classmethod
    def get_performance_config(cls) -> Dict[str, Any]:
        """Get performance monitoring configuration"""
        return cls.PERFORMANCE_THRESHOLDS.copy()
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check data directory
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
        if not data_dir.exists():
            validation_results['warnings'].append(f"Data directory does not exist: {data_dir}")
        
        # Check Redis connection if configured
        try:
            import redis
            redis_client = redis.from_url(cls.CACHE_CONFIG['redis_url'])
            redis_client.ping()
            validation_results['redis_available'] = True
        except Exception as e:
            validation_results['warnings'].append(f"Redis not available: {e}")
            validation_results['redis_available'] = False
        
        # Validate thresholds
        if cls.PERFORMANCE_THRESHOLDS['slow_query_threshold'] > 1.0:
            validation_results['warnings'].append("Slow query threshold is very high (>1s)")
        
        return validation_results


# Database optimization constants
DB_OPTIMIZATION_QUERIES = {
    'analyze_database': 'ANALYZE;',
    'vacuum_database': 'VACUUM;',
    'incremental_vacuum': 'PRAGMA incremental_vacuum(100);',
    'optimize_database': 'PRAGMA optimize;',
    'integrity_check': 'PRAGMA integrity_check;',
    'foreign_key_check': 'PRAGMA foreign_key_check;',
}

# Index creation queries for optimization
INDEX_CREATION_QUERIES = [
    # Workspace optimizations
    'CREATE INDEX IF NOT EXISTS idx_workspaces_owner_created ON workspaces(owner_id, created_at DESC);',
    'CREATE INDEX IF NOT EXISTS idx_workspaces_name_search ON workspaces(name COLLATE NOCASE);',
    
    # File metadata optimizations
    'CREATE INDEX IF NOT EXISTS idx_file_metadata_composite ON file_metadata(workspace_id, user_id, is_archived);',
    'CREATE INDEX IF NOT EXISTS idx_file_metadata_search ON file_metadata(file_name COLLATE NOCASE, ai_description COLLATE NOCASE);',
    'CREATE INDEX IF NOT EXISTS idx_file_metadata_importance ON file_metadata(importance_score DESC, updated_at DESC);',
    'CREATE INDEX IF NOT EXISTS idx_file_metadata_category ON file_metadata(ai_category, user_id);',
    'CREATE INDEX IF NOT EXISTS idx_file_metadata_size ON file_metadata(file_size DESC);',
    
    # Task optimizations
    'CREATE INDEX IF NOT EXISTS idx_tasks_workspace_priority ON tasks(workspace_id, priority, status);',
    'CREATE INDEX IF NOT EXISTS idx_tasks_assignee_due ON tasks(assignee_id, due_date);',
    'CREATE INDEX IF NOT EXISTS idx_tasks_status_updated ON tasks(status, updated_at DESC);',
    
    # User optimizations
    'CREATE INDEX IF NOT EXISTS idx_users_email_unique ON users(LOWER(email)) WHERE email IS NOT NULL;',
    'CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, created_at DESC);',
    
    # File tags optimizations (after migration)
    'CREATE INDEX IF NOT EXISTS idx_file_tags_file_id ON file_tags(file_id);',
    'CREATE INDEX IF NOT EXISTS idx_file_tags_tag_id ON file_tags(tag_id);',
    'CREATE INDEX IF NOT EXISTS idx_file_tags_created ON file_tags(created_at DESC);',
]

# Performance monitoring queries
PERFORMANCE_QUERIES = {
    'table_info': '''
        SELECT 
            name,
            COUNT(*) as row_count,
            AVG(LENGTH(sql)) as avg_row_size
        FROM sqlite_master 
        WHERE type='table' 
        GROUP BY name;
    ''',
    
    'index_usage': '''
        SELECT 
            name,
            tbl_name,
            sql
        FROM sqlite_master 
        WHERE type='index' 
        ORDER BY tbl_name, name;
    ''',
    
    'database_size': '''
        SELECT 
            page_count * page_size as database_size_bytes,
            page_count,
            page_size,
            freelist_count
        FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count();
    ''',
    
    'cache_stats': '''
        SELECT * FROM pragma_cache_size(), pragma_temp_store();
    '''
}