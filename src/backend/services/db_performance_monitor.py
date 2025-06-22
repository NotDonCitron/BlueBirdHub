"""
Database Performance Monitoring Service
Tracks query performance, connection health, and database metrics
"""
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import contextmanager
import threading
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from loguru import logger
import json
from pathlib import Path


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_text: str
    execution_time: float
    timestamp: datetime
    parameters: Optional[Dict] = None
    rows_affected: Optional[int] = None
    connection_id: Optional[str] = None


@dataclass
class ConnectionMetrics:
    """Database connection metrics"""
    active_connections: int
    total_connections: int
    connection_errors: int
    average_connection_time: float
    pool_size: int
    checked_out: int
    overflow: int
    timestamp: datetime


class DatabasePerformanceMonitor:
    """
    Real-time database performance monitoring
    """
    
    def __init__(self, slow_query_threshold: float = 0.05):  # 50ms threshold
        self.slow_query_threshold = slow_query_threshold
        self.query_metrics: deque = deque(maxlen=1000)  # Keep last 1000 queries
        self.slow_queries: deque = deque(maxlen=100)    # Keep last 100 slow queries
        self.connection_metrics: deque = deque(maxlen=288)  # Keep 24 hours of 5-min intervals
        
        # Performance counters
        self.total_queries = 0
        self.slow_query_count = 0
        self.connection_errors = 0
        self.query_types = defaultdict(int)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Query execution times by type
        self.query_times = defaultdict(list)
        
        logger.info(f"Database performance monitor initialized (slow query threshold: {slow_query_threshold}s)")
    
    def record_query(self, query_text: str, execution_time: float, 
                    parameters: Optional[Dict] = None, rows_affected: Optional[int] = None):
        """Record query execution metrics"""
        with self._lock:
            query_hash = str(hash(query_text.strip()[:200]))
            
            metrics = QueryMetrics(
                query_hash=query_hash,
                query_text=query_text.strip()[:500],  # Truncate long queries
                execution_time=execution_time,
                timestamp=datetime.now(),
                parameters=parameters,
                rows_affected=rows_affected
            )
            
            self.query_metrics.append(metrics)
            self.total_queries += 1
            
            # Track query types
            query_type = self._get_query_type(query_text)
            self.query_types[query_type] += 1
            self.query_times[query_type].append(execution_time)
            
            # Keep only recent times (last 100 per type)
            if len(self.query_times[query_type]) > 100:
                self.query_times[query_type] = self.query_times[query_type][-100:]
            
            # Track slow queries
            if execution_time > self.slow_query_threshold:
                self.slow_queries.append(metrics)
                self.slow_query_count += 1
                logger.warning(f"Slow query detected: {execution_time:.3f}s - {query_text[:100]}...")
    
    def record_connection_metrics(self, pool_status: Dict):
        """Record connection pool metrics"""
        with self._lock:
            metrics = ConnectionMetrics(
                active_connections=pool_status.get('checked_out', 0),
                total_connections=pool_status.get('pool_size', 0),
                connection_errors=self.connection_errors,
                average_connection_time=0.0,  # Would need to track separately
                pool_size=pool_status.get('pool_size', 0),
                checked_out=pool_status.get('checked_out', 0),
                overflow=pool_status.get('overflow', 0),
                timestamp=datetime.now()
            )
            
            self.connection_metrics.append(metrics)
    
    def _get_query_type(self, query_text: str) -> str:
        """Determine query type from SQL statement"""
        query_upper = query_text.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_minute = now - timedelta(minutes=1)
            
            # Recent queries
            recent_queries = [q for q in self.query_metrics if q.timestamp > last_hour]
            recent_slow_queries = [q for q in self.slow_queries if q.timestamp > last_hour]
            
            # Calculate averages
            avg_times = {}
            for query_type, times in self.query_times.items():
                if times:
                    avg_times[query_type] = {
                        'avg_time': sum(times) / len(times),
                        'max_time': max(times),
                        'min_time': min(times),
                        'count': len(times)
                    }
            
            # Connection stats
            latest_connection_metrics = list(self.connection_metrics)[-1] if self.connection_metrics else None
            
            return {
                'summary': {
                    'total_queries': self.total_queries,
                    'slow_queries': self.slow_query_count,
                    'slow_query_percentage': (self.slow_query_count / max(self.total_queries, 1)) * 100,
                    'queries_last_hour': len(recent_queries),
                    'slow_queries_last_hour': len(recent_slow_queries),
                    'connection_errors': self.connection_errors
                },
                'query_types': dict(self.query_types),
                'average_times': avg_times,
                'connection_status': asdict(latest_connection_metrics) if latest_connection_metrics else None,
                'slow_query_threshold': self.slow_query_threshold,
                'timestamp': now.isoformat()
            }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent slow queries"""
        with self._lock:
            slow_queries = sorted(
                self.slow_queries, 
                key=lambda x: x.execution_time, 
                reverse=True
            )[:limit]
            
            return [asdict(q) for q in slow_queries]
    
    def get_query_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get query performance trends"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_queries = [q for q in self.query_metrics if q.timestamp > cutoff_time]
            
            # Group by hour
            hourly_stats = defaultdict(lambda: {'count': 0, 'avg_time': 0, 'slow_count': 0})
            
            for query in recent_queries:
                hour_key = query.timestamp.strftime('%Y-%m-%d %H:00')
                hourly_stats[hour_key]['count'] += 1
                hourly_stats[hour_key]['avg_time'] += query.execution_time
                if query.execution_time > self.slow_query_threshold:
                    hourly_stats[hour_key]['slow_count'] += 1
            
            # Calculate averages
            for hour_data in hourly_stats.values():
                if hour_data['count'] > 0:
                    hour_data['avg_time'] /= hour_data['count']
            
            return dict(hourly_stats)
    
    def reset_metrics(self) -> None:
        """Reset all metrics (use with caution)"""
        with self._lock:
            self.query_metrics.clear()
            self.slow_queries.clear()
            self.connection_metrics.clear()
            self.total_queries = 0
            self.slow_query_count = 0
            self.connection_errors = 0
            self.query_types.clear()
            self.query_times.clear()
            logger.info("Database performance metrics reset")


# Global performance monitor instance
db_monitor = DatabasePerformanceMonitor()


class QueryTimer:
    """Context manager for timing database queries"""
    
    def __init__(self, query_text: str, parameters: Optional[Dict] = None):
        self.query_text = query_text
        self.parameters = parameters
        self.start_time = None
        self.execution_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.execution_time = time.perf_counter() - self.start_time
            db_monitor.record_query(
                self.query_text,
                self.execution_time,
                self.parameters
            )


def setup_sqlalchemy_monitoring(engine: Engine):
    """
    Set up SQLAlchemy event listeners for automatic query monitoring
    """
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.perf_counter()
        context._query_statement = statement
        context._query_parameters = parameters
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if hasattr(context, '_query_start_time'):
            execution_time = time.perf_counter() - context._query_start_time
            
            # Record the query
            db_monitor.record_query(
                query_text=statement,
                execution_time=execution_time,
                parameters=parameters if not executemany else None,
                rows_affected=cursor.rowcount if hasattr(cursor, 'rowcount') else None
            )
    
    @event.listens_for(engine, "connect")
    def on_connect(dbapi_conn, connection_record):
        # Could track connection establishment time here
        pass
    
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        # Track connection pool checkout
        pass
    
    logger.info("SQLAlchemy performance monitoring enabled")


class DatabaseHealthChecker:
    """
    Database health monitoring and alerting
    """
    
    def __init__(self, monitor: DatabasePerformanceMonitor):
        self.monitor = monitor
        self.health_thresholds = {
            'max_slow_query_percentage': 10.0,  # 10% slow queries is concerning
            'max_avg_query_time': 0.1,          # 100ms average is concerning
            'max_connection_errors': 5,          # 5 connection errors per hour
            'min_queries_per_minute': 0.1,      # Very low activity might indicate issues
        }
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        performance = self.monitor.get_performance_summary()
        health_status = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': performance,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check slow query percentage
        slow_query_pct = performance['summary']['slow_query_percentage']
        if slow_query_pct > self.health_thresholds['max_slow_query_percentage']:
            health_status['issues'].append(f"High slow query percentage: {slow_query_pct:.1f}%")
            health_status['status'] = 'unhealthy'
        
        # Check connection errors
        conn_errors = performance['summary']['connection_errors']
        if conn_errors > self.health_thresholds['max_connection_errors']:
            health_status['issues'].append(f"High connection errors: {conn_errors}")
            health_status['status'] = 'unhealthy'
        
        # Check average query times
        for query_type, stats in performance['average_times'].items():
            if stats['avg_time'] > self.health_thresholds['max_avg_query_time']:
                health_status['warnings'].append(f"Slow {query_type} queries: {stats['avg_time']:.3f}s avg")
        
        # Add recommendations
        health_status['recommendations'] = self._generate_recommendations(performance)
        
        return health_status
    
    def _generate_recommendations(self, performance: Dict) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        # Check for slow SELECT queries
        if 'SELECT' in performance['average_times']:
            select_stats = performance['average_times']['SELECT']
            if select_stats['avg_time'] > 0.05:  # 50ms
                recommendations.append("Consider adding indexes for frequently queried columns")
        
        # Check for slow INSERT/UPDATE operations
        for op_type in ['INSERT', 'UPDATE']:
            if op_type in performance['average_times']:
                stats = performance['average_times'][op_type]
                if stats['avg_time'] > 0.1:  # 100ms
                    recommendations.append(f"Consider optimizing {op_type} operations or using batch processing")
        
        # Check connection pool utilization
        if performance['connection_status']:
            checked_out = performance['connection_status']['checked_out']
            pool_size = performance['connection_status']['pool_size']
            if checked_out / max(pool_size, 1) > 0.8:
                recommendations.append("Consider increasing connection pool size")
        
        return recommendations


# Global health checker
db_health_checker = DatabaseHealthChecker(db_monitor)


def get_database_metrics() -> Dict[str, Any]:
    """Get current database performance metrics"""
    return db_monitor.get_performance_summary()


def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    return asyncio.run(db_health_checker.check_database_health())


# Utility function for manual query timing
@contextmanager
def time_query(query_description: str):
    """Context manager for manually timing queries"""
    with QueryTimer(query_description) as timer:
        yield timer