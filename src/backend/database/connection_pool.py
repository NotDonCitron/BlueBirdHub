"""
Advanced Database Connection Pool - Phase 3 Enterprise Performance Enhancement
Implements intelligent connection pooling, query optimization, and performance monitoring
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import sqlite3
import queue
from pathlib import Path
from loguru import logger

try:
    import aiosqlite
    import asyncpg
    ASYNC_DB_AVAILABLE = True
except ImportError:
    ASYNC_DB_AVAILABLE = False
    logger.warning("Async database drivers not available")

@dataclass
class ConnectionMetrics:
    """Connection pool metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    avg_query_time_ms: float = 0.0
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class QueryStats:
    """Individual query statistics"""
    query_hash: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    last_executed: datetime = field(default_factory=datetime.now)
    error_count: int = 0

class DatabaseConnection:
    """Enhanced database connection wrapper"""
    
    def __init__(self, connection, connection_id: str, pool: 'ConnectionPool'):
        self.connection = connection
        self.connection_id = connection_id
        self.pool = pool
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.query_count = 0
        self.is_transaction = False
        self.health_status = "healthy"
    
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query with performance tracking"""
        start_time = time.time()
        query_hash = self._hash_query(query)
        
        try:
            self.last_used = datetime.now()
            self.query_count += 1
            
            # Execute query based on connection type
            if hasattr(self.connection, 'execute'):
                if params:
                    result = await self.connection.execute(query, params)
                else:
                    result = await self.connection.execute(query)
            else:
                cursor = self.connection.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchall()
            
            # Record performance metrics
            execution_time = (time.time() - start_time) * 1000
            self.pool._record_query_stats(query_hash, execution_time, success=True)
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.pool._record_query_stats(query_hash, execution_time, success=False)
            self.health_status = "unhealthy"
            logger.error(f"Query failed on connection {self.connection_id}: {e}")
            raise
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> Any:
        """Execute multiple queries efficiently"""
        start_time = time.time()
        query_hash = self._hash_query(query)
        
        try:
            self.last_used = datetime.now()
            self.query_count += len(params_list)
            
            if hasattr(self.connection, 'executemany'):
                result = await self.connection.executemany(query, params_list)
            else:
                cursor = self.connection.cursor()
                cursor.executemany(query, params_list)
                result = cursor.rowcount
            
            execution_time = (time.time() - start_time) * 1000
            self.pool._record_query_stats(query_hash, execution_time, success=True)
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.pool._record_query_stats(query_hash, execution_time, success=False)
            self.health_status = "unhealthy"
            logger.error(f"Batch query failed on connection {self.connection_id}: {e}")
            raise
    
    async def begin_transaction(self):
        """Begin database transaction"""
        if hasattr(self.connection, 'begin'):
            await self.connection.begin()
        else:
            await self.execute("BEGIN")
        self.is_transaction = True
    
    async def commit(self):
        """Commit transaction"""
        if hasattr(self.connection, 'commit'):
            await self.connection.commit()
        else:
            await self.execute("COMMIT")
        self.is_transaction = False
    
    async def rollback(self):
        """Rollback transaction"""
        if hasattr(self.connection, 'rollback'):
            await self.connection.rollback()
        else:
            await self.execute("ROLLBACK")
        self.is_transaction = False
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query caching"""
        import hashlib
        # Normalize query for consistent hashing
        normalized = ' '.join(query.split()).lower()
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def is_healthy(self) -> bool:
        """Check connection health"""
        if self.health_status != "healthy":
            return False
        
        # Check if connection is too old
        max_age = timedelta(hours=1)
        if datetime.now() - self.created_at > max_age:
            return False
        
        return True
    
    async def close(self):
        """Close connection"""
        try:
            if self.is_transaction:
                await self.rollback()
            
            if hasattr(self.connection, 'close'):
                await self.connection.close()
            else:
                self.connection.close()
                
        except Exception as e:
            logger.warning(f"Error closing connection {self.connection_id}: {e}")

class ConnectionPool:
    """Advanced database connection pool with intelligent management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.database_url = config.get("database_url", "sqlite:///./ordnungshub.db")
        self.min_connections = config.get("min_connections", 5)
        self.max_connections = config.get("max_connections", 20)
        self.connection_timeout = config.get("connection_timeout", 30)
        self.idle_timeout = config.get("idle_timeout", 300)  # 5 minutes
        
        # Connection management
        self.available_connections: queue.Queue = queue.Queue()
        self.active_connections: Dict[str, DatabaseConnection] = {}
        self.all_connections: Dict[str, DatabaseConnection] = {}
        self.connection_counter = 0
        self.pool_lock = threading.Lock()
        
        # Performance tracking
        self.metrics = ConnectionMetrics()
        self.query_stats: Dict[str, QueryStats] = {}
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.metrics_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize connection pool"""
        logger.info(f"Initializing connection pool: {self.min_connections}-{self.max_connections} connections")
        
        # Create minimum connections
        for _ in range(self.min_connections):
            await self._create_connection()
        
        # Start background tasks
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        self.metrics_task = asyncio.create_task(self._metrics_worker())
        
        logger.info("Connection pool initialized successfully")
    
    async def _create_connection(self) -> DatabaseConnection:
        """Create new database connection"""
        try:
            self.connection_counter += 1
            connection_id = f"conn_{self.connection_counter}"
            
            # Create connection based on database type
            if self.database_url.startswith("sqlite"):
                if ASYNC_DB_AVAILABLE:
                    db_path = self.database_url.replace("sqlite:///", "")
                    connection = await aiosqlite.connect(db_path)
                    # Enable WAL mode for better concurrency
                    await connection.execute("PRAGMA journal_mode=WAL")
                    await connection.execute("PRAGMA synchronous=NORMAL")
                    await connection.execute("PRAGMA cache_size=10000")
                    await connection.execute("PRAGMA temp_store=MEMORY")
                else:
                    db_path = self.database_url.replace("sqlite:///", "")
                    connection = sqlite3.connect(db_path, check_same_thread=False)
                    connection.execute("PRAGMA journal_mode=WAL")
                    connection.execute("PRAGMA synchronous=NORMAL")
                    connection.execute("PRAGMA cache_size=10000")
                    connection.execute("PRAGMA temp_store=MEMORY")
            
            elif self.database_url.startswith("postgresql"):
                if ASYNC_DB_AVAILABLE:
                    connection = await asyncpg.connect(self.database_url)
                else:
                    raise RuntimeError("PostgreSQL requires asyncpg")
            
            else:
                raise ValueError(f"Unsupported database URL: {self.database_url}")
            
            # Create connection wrapper
            db_connection = DatabaseConnection(connection, connection_id, self)
            
            with self.pool_lock:
                self.all_connections[connection_id] = db_connection
                self.available_connections.put(db_connection)
                self.metrics.total_connections += 1
                self.metrics.idle_connections += 1
            
            logger.debug(f"Created connection {connection_id}")
            return db_connection
            
        except Exception as e:
            self.metrics.failed_connections += 1
            logger.error(f"Failed to create database connection: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[DatabaseConnection, None]:
        """Get connection from pool with automatic return"""
        connection = await self._acquire_connection()
        try:
            yield connection
        finally:
            await self._release_connection(connection)
    
    async def _acquire_connection(self) -> DatabaseConnection:
        """Acquire connection from pool"""
        start_time = time.time()
        
        while time.time() - start_time < self.connection_timeout:
            try:
                # Try to get available connection
                if not self.available_connections.empty():
                    connection = self.available_connections.get_nowait()
                    
                    # Check connection health
                    if connection.is_healthy():
                        with self.pool_lock:
                            self.active_connections[connection.connection_id] = connection
                            self.metrics.active_connections += 1
                            self.metrics.idle_connections -= 1
                        
                        logger.debug(f"Acquired connection {connection.connection_id}")
                        return connection
                    else:
                        # Connection is unhealthy, close and create new one
                        await connection.close()
                        with self.pool_lock:
                            del self.all_connections[connection.connection_id]
                            self.metrics.total_connections -= 1
                        
                        # Create replacement connection if below max
                        if self.metrics.total_connections < self.max_connections:
                            await self._create_connection()
                
                # No healthy connections available, create new one if possible
                elif self.metrics.total_connections < self.max_connections:
                    connection = await self._create_connection()
                    with self.pool_lock:
                        connection = self.available_connections.get_nowait()
                        self.active_connections[connection.connection_id] = connection
                        self.metrics.active_connections += 1
                        self.metrics.idle_connections -= 1
                    return connection
                
                else:
                    # Pool is at capacity, wait briefly
                    await asyncio.sleep(0.1)
            
            except queue.Empty:
                await asyncio.sleep(0.1)
        
        raise TimeoutError("Failed to acquire database connection within timeout")
    
    async def _release_connection(self, connection: DatabaseConnection):
        """Release connection back to pool"""
        try:
            # Rollback any uncommitted transaction
            if connection.is_transaction:
                await connection.rollback()
            
            with self.pool_lock:
                if connection.connection_id in self.active_connections:
                    del self.active_connections[connection.connection_id]
                    self.metrics.active_connections -= 1
                
                if connection.is_healthy():
                    self.available_connections.put(connection)
                    self.metrics.idle_connections += 1
                    logger.debug(f"Released connection {connection.connection_id}")
                else:
                    # Connection is unhealthy, close it
                    await connection.close()
                    if connection.connection_id in self.all_connections:
                        del self.all_connections[connection.connection_id]
                        self.metrics.total_connections -= 1
                    
                    # Create replacement connection if below minimum
                    if self.metrics.total_connections < self.min_connections:
                        await self._create_connection()
        
        except Exception as e:
            logger.error(f"Error releasing connection: {e}")
    
    def _record_query_stats(self, query_hash: str, execution_time_ms: float, success: bool):
        """Record query performance statistics"""
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = QueryStats(query_hash=query_hash)
        
        stats = self.query_stats[query_hash]
        stats.execution_count += 1
        stats.last_executed = datetime.now()
        
        if success:
            stats.total_time_ms += execution_time_ms
            stats.avg_time_ms = stats.total_time_ms / stats.execution_count
            
            # Update global metrics
            self.metrics.total_queries += 1
            self.metrics.avg_query_time_ms = (
                (self.metrics.avg_query_time_ms * (self.metrics.total_queries - 1) + execution_time_ms) 
                / self.metrics.total_queries
            )
        else:
            stats.error_count += 1
    
    async def _cleanup_worker(self):
        """Background task for connection cleanup"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                current_time = datetime.now()
                connections_to_close = []
                
                # Check for idle connections to close
                with self.pool_lock:
                    for connection in list(self.all_connections.values()):
                        if (connection.connection_id not in self.active_connections and
                            current_time - connection.last_used > timedelta(seconds=self.idle_timeout) and
                            self.metrics.total_connections > self.min_connections):
                            connections_to_close.append(connection)
                
                # Close idle connections
                for connection in connections_to_close:
                    await connection.close()
                    with self.pool_lock:
                        # Remove from available queue (requires draining and rebuilding)
                        temp_connections = []
                        while not self.available_connections.empty():
                            conn = self.available_connections.get_nowait()
                            if conn.connection_id != connection.connection_id:
                                temp_connections.append(conn)
                        
                        for conn in temp_connections:
                            self.available_connections.put(conn)
                        
                        if connection.connection_id in self.all_connections:
                            del self.all_connections[connection.connection_id]
                            self.metrics.total_connections -= 1
                            self.metrics.idle_connections -= 1
                
                if connections_to_close:
                    logger.debug(f"Cleaned up {len(connections_to_close)} idle connections")
                
            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
    
    async def _metrics_worker(self):
        """Background task for metrics collection"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Clean old query stats
                cutoff_time = datetime.now() - timedelta(hours=1)
                old_queries = [
                    query_hash for query_hash, stats in self.query_stats.items()
                    if stats.last_executed < cutoff_time
                ]
                
                for query_hash in old_queries:
                    del self.query_stats[query_hash]
                
                # Log performance summary
                logger.info(
                    f"Pool metrics: {self.metrics.active_connections} active, "
                    f"{self.metrics.idle_connections} idle, "
                    f"{self.metrics.avg_query_time_ms:.2f}ms avg query time"
                )
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pool metrics"""
        return {
            "connection_metrics": {
                "total_connections": self.metrics.total_connections,
                "active_connections": self.metrics.active_connections,
                "idle_connections": self.metrics.idle_connections,
                "failed_connections": self.metrics.failed_connections,
                "min_pool_size": self.min_connections,
                "max_pool_size": self.max_connections
            },
            "performance_metrics": {
                "total_queries": self.metrics.total_queries,
                "avg_query_time_ms": round(self.metrics.avg_query_time_ms, 2),
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_hit_ratio": round(
                    self.metrics.cache_hits / max(self.metrics.cache_hits + self.metrics.cache_misses, 1) * 100, 2
                )
            },
            "slow_queries": [
                {
                    "query_hash": stats.query_hash,
                    "avg_time_ms": round(stats.avg_time_ms, 2),
                    "execution_count": stats.execution_count,
                    "error_count": stats.error_count
                }
                for stats in sorted(self.query_stats.values(), key=lambda s: s.avg_time_ms, reverse=True)[:10]
            ]
        }
    
    async def close(self):
        """Close all connections and cleanup"""
        logger.info("Closing connection pool")
        
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()
        
        # Close all connections
        for connection in self.all_connections.values():
            await connection.close()
        
        # Clear all data structures
        with self.pool_lock:
            self.active_connections.clear()
            self.all_connections.clear()
            while not self.available_connections.empty():
                self.available_connections.get_nowait()
        
        logger.info("Connection pool closed")

# Global connection pool instance
_connection_pool: Optional[ConnectionPool] = None

async def get_connection_pool() -> ConnectionPool:
    """Get global connection pool instance"""
    global _connection_pool
    
    if _connection_pool is None:
        config = {
            "database_url": "sqlite:///./ordnungshub.db",
            "min_connections": 5,
            "max_connections": 20,
            "connection_timeout": 30,
            "idle_timeout": 300,
            "cache_ttl": 300
        }
        
        _connection_pool = ConnectionPool(config)
        await _connection_pool.initialize()
    
    return _connection_pool

async def close_connection_pool():
    """Close global connection pool"""
    global _connection_pool
    
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None