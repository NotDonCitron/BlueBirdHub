"""
Database Query Optimization Service
Implements query analysis, connection pooling, and performance monitoring
"""
from typing import Any, Dict, List, Optional, Callable
from sqlalchemy import event, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
import time
import statistics
from loguru import logger

class QueryPerformanceMonitor:
    """
    Monitor database query performance and provide optimization insights
    """
    
    def __init__(self):
        self.query_stats: Dict[str, List[Dict[str, Any]]] = {}
        self.slow_query_threshold = 1.0  # seconds
        self.max_stats_entries = 1000
    
    def record_query(self, query: str, duration: float, params: dict = None):
        """Record query execution time and parameters"""
        query_hash = hash(query.strip()[:200])  # Use first 200 chars for grouping
        
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = []
        
        stats_entry = {
            "query": query.strip()[:200],
            "duration": duration,
            "timestamp": datetime.now(),
            "params": params or {},
            "is_slow": duration > self.slow_query_threshold
        }
        
        self.query_stats[query_hash].append(stats_entry)
        
        # Keep only recent entries to prevent memory bloat
        if len(self.query_stats[query_hash]) > self.max_stats_entries:
            self.query_stats[query_hash] = self.query_stats[query_hash][-self.max_stats_entries:]
        
        # Log slow queries
        if duration > self.slow_query_threshold:
            logger.warning(f"Slow query detected ({duration:.3f}s): {query.strip()[:100]}...")
    
    def get_query_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive query statistics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        all_durations = []
        slow_queries = []
        query_counts = {}
        
        for query_hash, entries in self.query_stats.items():
            recent_entries = [e for e in entries if e["timestamp"] > cutoff_time]
            
            if not recent_entries:
                continue
            
            durations = [e["duration"] for e in recent_entries]
            all_durations.extend(durations)
            
            # Count queries
            query_pattern = recent_entries[0]["query"]
            query_counts[query_pattern] = len(recent_entries)
            
            # Track slow queries
            slow_entries = [e for e in recent_entries if e["is_slow"]]
            if slow_entries:
                slow_queries.extend(slow_entries)
        
        stats = {
            "total_queries": len(all_durations),
            "slow_queries": len(slow_queries),
            "query_types": len(query_counts),
            "time_period_hours": hours
        }
        
        if all_durations:
            stats.update({
                "avg_duration": statistics.mean(all_durations),
                "median_duration": statistics.median(all_durations),
                "min_duration": min(all_durations),
                "max_duration": max(all_durations),
                "p95_duration": statistics.quantiles(all_durations, n=20)[18] if len(all_durations) > 20 else max(all_durations)
            })
        
        # Most frequent queries
        stats["top_queries"] = sorted(
            query_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Recent slow queries
        stats["recent_slow_queries"] = sorted(
            slow_queries, 
            key=lambda x: x["duration"], 
            reverse=True
        )[:5]
        
        return stats
    
    def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on query patterns"""
        stats = self.get_query_statistics()
        recommendations = []
        
        if stats.get("slow_queries", 0) > stats.get("total_queries", 1) * 0.1:
            recommendations.append("Consider adding database indexes for frequently queried columns")
        
        if stats.get("avg_duration", 0) > 0.5:
            recommendations.append("Average query time is high - review query complexity and add caching")
        
        # Analyze query patterns
        for query, count in stats.get("top_queries", [])[:5]:
            if "SELECT *" in query.upper():
                recommendations.append(f"Query uses SELECT * - specify needed columns: {query[:50]}...")
            
            if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
                recommendations.append(f"Query has ORDER BY without LIMIT - consider pagination: {query[:50]}...")
        
        if not recommendations:
            recommendations.append("Database performance looks good!")
        
        return recommendations


class DatabaseOptimizer:
    """
    Database optimization service with connection pooling and query monitoring
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.query_monitor = QueryPerformanceMonitor()
        self.engine = None
        self.session_factory = None
        self._setup_optimized_engine()
    
    def _setup_optimized_engine(self):
        """Setup database engine with optimizations"""
        
        # Engine configuration for SQLite optimization
        engine_kwargs = {
            "echo": False,  # Set to True for SQL debugging
            "pool_pre_ping": True,  # Verify connections before use
            "pool_recycle": 3600,  # Recycle connections every hour
        }
        
        # SQLite specific optimizations
        if "sqlite" in self.database_url:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    # SQLite optimizations
                    "timeout": 20,
                }
            })
        
        self.engine = create_engine(self.database_url, **engine_kwargs)
        
        # Setup query monitoring
        self._setup_query_monitoring()
        
        # Apply SQLite pragmas for performance
        if "sqlite" in self.database_url:
            self._apply_sqlite_optimizations()
        
        self.session_factory = sessionmaker(bind=self.engine)
    
    def _setup_query_monitoring(self):
        """Setup automatic query performance monitoring"""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            self.query_monitor.record_query(statement, total, parameters)
    
    def _apply_sqlite_optimizations(self):
        """Apply SQLite-specific performance optimizations"""
        optimizations = [
            "PRAGMA synchronous = NORMAL",  # Faster than FULL, safer than OFF
            "PRAGMA cache_size = 10000",    # 10MB cache
            "PRAGMA temp_store = MEMORY",   # Store temp tables in memory
            "PRAGMA mmap_size = 268435456", # 256MB memory map
            "PRAGMA journal_mode = WAL",    # Write-Ahead Logging for better concurrency
            "PRAGMA foreign_keys = ON",     # Enable foreign key constraints
        ]
        
        with self.engine.connect() as conn:
            for pragma in optimizations:
                try:
                    conn.execute(text(pragma))
                    logger.debug(f"Applied SQLite optimization: {pragma}")
                except Exception as e:
                    logger.warning(f"Failed to apply optimization {pragma}: {e}")
    
    def get_optimized_session(self) -> Session:
        """Get a database session with monitoring"""
        return self.session_factory()
    
    def analyze_query_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive query performance analysis"""
        stats = self.query_monitor.get_query_statistics(hours)
        recommendations = self.query_monitor.get_optimization_recommendations()
        
        return {
            "performance_stats": stats,
            "recommendations": recommendations,
            "monitoring_active": True,
            "optimization_level": "enhanced"
        }
    
    def execute_optimized_query(self, query: str, params: dict = None) -> Any:
        """Execute query with automatic performance monitoring"""
        start_time = time.time()
        
        with self.get_optimized_session() as session:
            try:
                result = session.execute(text(query), params or {})
                duration = time.time() - start_time
                
                # Manual recording for raw queries
                self.query_monitor.record_query(query, duration, params)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Query failed after {duration:.3f}s: {query[:100]}... Error: {e}")
                raise
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get overall database health metrics"""
        try:
            with self.engine.connect() as conn:
                # Test query performance
                start_time = time.time()
                conn.execute(text("SELECT 1"))
                connection_time = time.time() - start_time
                
                health = {
                    "status": "healthy",
                    "connection_time_ms": connection_time * 1000,
                    "engine_info": str(self.engine.url),
                    "pool_status": {
                        "pool_size": getattr(self.engine.pool, 'size', lambda: 'N/A')(),
                        "checked_in": getattr(self.engine.pool, 'checkedin', lambda: 'N/A')(),
                        "checked_out": getattr(self.engine.pool, 'checkedout', lambda: 'N/A')(),
                    }
                }
                
                # Add SQLite specific info
                if "sqlite" in self.database_url:
                    pragma_results = {}
                    pragmas = ["synchronous", "cache_size", "journal_mode", "mmap_size"]
                    
                    for pragma in pragmas:
                        try:
                            result = conn.execute(text(f"PRAGMA {pragma}")).fetchone()
                            pragma_results[pragma] = result[0] if result else "unknown"
                        except:
                            pragma_results[pragma] = "error"
                    
                    health["sqlite_config"] = pragma_results
                
                return health
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_time_ms": None
            }


# Global optimizer instance (to be initialized by the app)
db_optimizer: Optional[DatabaseOptimizer] = None

def initialize_db_optimizer(database_url: str):
    """Initialize the global database optimizer"""
    global db_optimizer
    db_optimizer = DatabaseOptimizer(database_url)
    logger.info("Database optimizer initialized")

def get_db_optimizer() -> Optional[DatabaseOptimizer]:
    """Get the global database optimizer instance"""
    return db_optimizer