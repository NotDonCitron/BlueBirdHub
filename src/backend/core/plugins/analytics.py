"""
Plugin Analytics and Monitoring System

Tracks plugin usage, performance metrics, and system health
for monitoring and optimization purposes.
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import psutil
from collections import defaultdict, deque
from pathlib import Path

from .base import PluginMetadata, PluginStatus


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    metric_type: MetricType
    plugin_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for a plugin"""
    plugin_id: str
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    active_time: float
    event_count: int
    error_count: int
    api_calls: int
    response_time_ms: float


@dataclass
class Alert:
    """System alert"""
    id: str
    level: AlertLevel
    plugin_id: str
    message: str
    metric_name: str
    threshold_value: float
    actual_value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class UsageStats:
    """Plugin usage statistics"""
    plugin_id: str
    total_activations: int
    total_runtime_hours: float
    avg_session_duration: float
    last_used: datetime
    most_used_features: List[str]
    error_rate: float
    user_count: int


class PluginAnalyticsManager:
    """Analytics and monitoring manager for plugins"""
    
    def __init__(self, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(self.data_dir / "analytics.db")
        
        # Real-time data
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.performance_snapshots: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.active_alerts: Dict[str, Alert] = {}
        
        # Plugin tracking
        self.plugin_sessions: Dict[str, datetime] = {}  # plugin_id -> start_time
        self.plugin_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.plugin_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Thresholds and rules
        self.alert_thresholds: Dict[str, Dict[str, float]] = {
            "memory_mb": {"warning": 256, "error": 512, "critical": 1024},
            "cpu_percent": {"warning": 50, "error": 75, "critical": 90},
            "error_rate": {"warning": 0.05, "error": 0.1, "critical": 0.2},
            "response_time_ms": {"warning": 1000, "error": 5000, "critical": 10000}
        }
        
        # Processing state
        self._collection_active = False
        self._collection_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    plugin_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT,
                    context TEXT
                );
                
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL NOT NULL,
                    memory_mb REAL NOT NULL,
                    active_time REAL NOT NULL,
                    event_count INTEGER NOT NULL,
                    error_count INTEGER NOT NULL,
                    api_calls INTEGER NOT NULL,
                    response_time_ms REAL NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    plugin_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    actual_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS usage_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_id TEXT NOT NULL,
                    user_id TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    features_used TEXT,
                    errors_encountered INTEGER DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_plugin_time ON metrics (plugin_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_performance_plugin_time ON performance_snapshots (plugin_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_plugin ON alerts (plugin_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_plugin ON usage_sessions (plugin_id);
            """)
            conn.commit()
        finally:
            conn.close()
    
    async def start_monitoring(self):
        """Start the analytics monitoring system"""
        if not self._collection_active:
            self._collection_active = True
            self._collection_task = asyncio.create_task(self._collect_metrics())
            self._alert_task = asyncio.create_task(self._monitor_alerts())
            logger.info("Plugin analytics monitoring started")
    
    async def stop_monitoring(self):
        """Stop the analytics monitoring system"""
        if self._collection_active:
            self._collection_active = False
            
            for task in [self._collection_task, self._alert_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Flush remaining metrics
            await self._flush_metrics()
            
            logger.info("Plugin analytics monitoring stopped")
    
    async def track_plugin_start(self, plugin_id: str, user_id: str = None):
        """Track when a plugin starts"""
        self.plugin_sessions[plugin_id] = datetime.utcnow()
        
        # Record session start
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO usage_sessions (plugin_id, user_id, start_time)
                VALUES (?, ?, ?)
            """, (plugin_id, user_id, datetime.utcnow()))
            conn.commit()
        finally:
            conn.close()
        
        await self.record_metric("plugin.start", 1, MetricType.COUNTER, plugin_id)
    
    async def track_plugin_stop(self, plugin_id: str):
        """Track when a plugin stops"""
        if plugin_id in self.plugin_sessions:
            start_time = self.plugin_sessions[plugin_id]
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update session record
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE usage_sessions 
                    SET end_time = ?, duration_seconds = ?
                    WHERE plugin_id = ? AND end_time IS NULL
                    ORDER BY start_time DESC
                    LIMIT 1
                """, (datetime.utcnow(), duration, plugin_id))
                conn.commit()
            finally:
                conn.close()
            
            del self.plugin_sessions[plugin_id]
            await self.record_metric("plugin.duration", duration, MetricType.TIMER, plugin_id)
            await self.record_metric("plugin.stop", 1, MetricType.COUNTER, plugin_id)
    
    async def record_metric(self, name: str, value: float, metric_type: MetricType,
                          plugin_id: str, tags: Dict[str, str] = None,
                          context: Dict[str, Any] = None):
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            plugin_id=plugin_id,
            tags=tags or {},
            context=context or {}
        )
        
        self.metrics_buffer.append(metric)
        
        # Update real-time counters
        if metric_type == MetricType.COUNTER:
            self.plugin_counters[plugin_id][name] += value
        elif metric_type == MetricType.GAUGE:
            self.plugin_metrics[plugin_id][name] = value
    
    async def record_performance_snapshot(self, plugin_id: str, cpu_percent: float,
                                        memory_mb: float, active_time: float,
                                        event_count: int, error_count: int,
                                        api_calls: int, response_time_ms: float):
        """Record a performance snapshot"""
        snapshot = PerformanceSnapshot(
            plugin_id=plugin_id,
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            active_time=active_time,
            event_count=event_count,
            error_count=error_count,
            api_calls=api_calls,
            response_time_ms=response_time_ms
        )
        
        self.performance_snapshots[plugin_id].append(snapshot)
        
        # Store in database periodically
        if len(self.performance_snapshots[plugin_id]) % 10 == 0:
            await self._store_performance_snapshots(plugin_id)
    
    async def track_api_call(self, plugin_id: str, endpoint: str, 
                           response_time_ms: float, success: bool):
        """Track API call metrics"""
        await self.record_metric("api.calls", 1, MetricType.COUNTER, plugin_id,
                                tags={"endpoint": endpoint, "success": str(success)})
        
        await self.record_metric("api.response_time", response_time_ms, 
                               MetricType.TIMER, plugin_id,
                               tags={"endpoint": endpoint})
        
        if not success:
            await self.record_metric("api.errors", 1, MetricType.COUNTER, plugin_id,
                                   tags={"endpoint": endpoint})
    
    async def track_feature_usage(self, plugin_id: str, feature: str, user_id: str = None):
        """Track feature usage"""
        await self.record_metric("feature.usage", 1, MetricType.COUNTER, plugin_id,
                                tags={"feature": feature, "user_id": user_id or "anonymous"})
        
        # Update current session
        conn = sqlite3.connect(self.db_path)
        try:
            # Get current session
            cursor = conn.execute("""
                SELECT id, features_used FROM usage_sessions
                WHERE plugin_id = ? AND end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
            """, (plugin_id,))
            
            session = cursor.fetchone()
            if session:
                session_id, features_used = session
                features = json.loads(features_used or "[]")
                if feature not in features:
                    features.append(feature)
                
                conn.execute("""
                    UPDATE usage_sessions 
                    SET features_used = ?
                    WHERE id = ?
                """, (json.dumps(features), session_id))
                conn.commit()
        finally:
            conn.close()
    
    async def track_error(self, plugin_id: str, error_type: str, error_message: str,
                         context: Dict[str, Any] = None):
        """Track plugin errors"""
        await self.record_metric("errors.count", 1, MetricType.COUNTER, plugin_id,
                                tags={"error_type": error_type},
                                context={"message": error_message, **(context or {})})
        
        # Update current session error count
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE usage_sessions 
                SET errors_encountered = errors_encountered + 1
                WHERE plugin_id = ? AND end_time IS NULL
            """, (plugin_id,))
            conn.commit()
        finally:
            conn.close()
    
    async def get_plugin_stats(self, plugin_id: str, 
                             start_time: datetime = None,
                             end_time: datetime = None) -> Dict[str, Any]:
        """Get comprehensive plugin statistics"""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Get basic usage stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as session_count,
                    AVG(duration_seconds) as avg_duration,
                    SUM(duration_seconds) as total_duration,
                    SUM(errors_encountered) as total_errors
                FROM usage_sessions
                WHERE plugin_id = ? AND start_time BETWEEN ? AND ?
            """, (plugin_id, start_time, end_time))
            
            usage_row = cursor.fetchone()
            
            # Get performance metrics
            cursor = conn.execute("""
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_mb) as avg_memory,
                    MAX(memory_mb) as max_memory,
                    AVG(response_time_ms) as avg_response_time
                FROM performance_snapshots
                WHERE plugin_id = ? AND timestamp BETWEEN ? AND ?
            """, (plugin_id, start_time, end_time))
            
            perf_row = cursor.fetchone()
            
            # Get feature usage
            cursor = conn.execute("""
                SELECT value, tags FROM metrics
                WHERE plugin_id = ? AND name = 'feature.usage'
                AND timestamp BETWEEN ? AND ?
            """, (plugin_id, start_time, end_time))
            
            feature_usage = defaultdict(int)
            for row in cursor.fetchall():
                tags = json.loads(row[1] or "{}")
                feature = tags.get("feature", "unknown")
                feature_usage[feature] += int(row[0])
            
            # Get error breakdown
            cursor = conn.execute("""
                SELECT tags, SUM(value) as error_count FROM metrics
                WHERE plugin_id = ? AND name = 'errors.count'
                AND timestamp BETWEEN ? AND ?
                GROUP BY tags
            """, (plugin_id, start_time, end_time))
            
            error_breakdown = {}
            for row in cursor.fetchall():
                tags = json.loads(row[0] or "{}")
                error_type = tags.get("error_type", "unknown")
                error_breakdown[error_type] = int(row[1])
            
            return {
                "plugin_id": plugin_id,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "usage": {
                    "session_count": usage_row[0] or 0,
                    "avg_session_duration": usage_row[1] or 0,
                    "total_runtime_hours": (usage_row[2] or 0) / 3600,
                    "total_errors": usage_row[3] or 0,
                    "error_rate": (usage_row[3] or 0) / max(usage_row[0] or 1, 1)
                },
                "performance": {
                    "avg_cpu_percent": perf_row[0] or 0,
                    "max_cpu_percent": perf_row[1] or 0,
                    "avg_memory_mb": perf_row[2] or 0,
                    "max_memory_mb": perf_row[3] or 0,
                    "avg_response_time_ms": perf_row[4] or 0
                },
                "features": dict(feature_usage),
                "errors": error_breakdown,
                "current_metrics": self.plugin_metrics.get(plugin_id, {}),
                "current_counters": dict(self.plugin_counters.get(plugin_id, {}))
            }
            
        finally:
            conn.close()
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide analytics overview"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Active plugins
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT plugin_id) FROM usage_sessions
                WHERE end_time IS NULL
            """)
            active_plugins = cursor.fetchone()[0]
            
            # Total sessions today
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM usage_sessions
                WHERE start_time >= ?
            """, (today,))
            sessions_today = cursor.fetchone()[0]
            
            # Top plugins by usage
            cursor = conn.execute("""
                SELECT plugin_id, COUNT(*) as session_count
                FROM usage_sessions
                WHERE start_time >= ?
                GROUP BY plugin_id
                ORDER BY session_count DESC
                LIMIT 10
            """, (datetime.utcnow() - timedelta(days=7),))
            
            top_plugins = [{"plugin_id": row[0], "sessions": row[1]} for row in cursor.fetchall()]
            
            # System alerts
            active_alerts = len([a for a in self.active_alerts.values() if not a.resolved])
            
            # Resource usage
            system_cpu = psutil.cpu_percent()
            system_memory = psutil.virtual_memory().percent
            
            return {
                "active_plugins": active_plugins,
                "sessions_today": sessions_today,
                "top_plugins": top_plugins,
                "active_alerts": active_alerts,
                "system_resources": {
                    "cpu_percent": system_cpu,
                    "memory_percent": system_memory
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            conn.close()
    
    async def get_alerts(self, plugin_id: str = None, resolved: bool = None) -> List[Dict[str, Any]]:
        """Get system alerts"""
        alerts = []
        
        for alert in self.active_alerts.values():
            if plugin_id and alert.plugin_id != plugin_id:
                continue
            if resolved is not None and alert.resolved != resolved:
                continue
            
            alerts.append({
                "id": alert.id,
                "level": alert.level.value,
                "plugin_id": alert.plugin_id,
                "message": alert.message,
                "metric_name": alert.metric_name,
                "threshold_value": alert.threshold_value,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            })
        
        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            # Update in database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE alerts 
                    SET resolved = TRUE, resolved_at = ?
                    WHERE id = ?
                """, (alert.resolved_at, alert_id))
                conn.commit()
            finally:
                conn.close()
            
            return True
        return False
    
    async def _collect_metrics(self):
        """Background task to collect and store metrics"""
        while self._collection_active:
            try:
                # Collect system metrics for active plugins
                for plugin_id in self.plugin_sessions.keys():
                    await self._collect_plugin_metrics(plugin_id)
                
                # Flush metrics buffer periodically
                await self._flush_metrics()
                
                await asyncio.sleep(60)  # Collect every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(10)
    
    async def _collect_plugin_metrics(self, plugin_id: str):
        """Collect metrics for a specific plugin"""
        try:
            # This would integrate with the plugin manager to get actual metrics
            # For now, simulate some metrics
            
            # CPU and memory would come from sandbox monitoring
            cpu_percent = 0.0  # Would get from sandbox
            memory_mb = 0.0    # Would get from sandbox
            
            # Record gauge metrics
            await self.record_metric("cpu.percent", cpu_percent, MetricType.GAUGE, plugin_id)
            await self.record_metric("memory.mb", memory_mb, MetricType.GAUGE, plugin_id)
            
            # Calculate active time
            if plugin_id in self.plugin_sessions:
                active_time = (datetime.utcnow() - self.plugin_sessions[plugin_id]).total_seconds()
                await self.record_metric("active_time", active_time, MetricType.GAUGE, plugin_id)
            
        except Exception as e:
            logger.error(f"Error collecting metrics for plugin {plugin_id}: {e}")
    
    async def _flush_metrics(self):
        """Flush metrics buffer to database"""
        if not self.metrics_buffer:
            return
        
        metrics_to_store = list(self.metrics_buffer)
        self.metrics_buffer.clear()
        
        conn = sqlite3.connect(self.db_path)
        try:
            for metric in metrics_to_store:
                conn.execute("""
                    INSERT INTO metrics 
                    (name, value, metric_type, plugin_id, timestamp, tags, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.name, metric.value, metric.metric_type.value,
                    metric.plugin_id, metric.timestamp,
                    json.dumps(metric.tags), json.dumps(metric.context)
                ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error flushing metrics to database: {e}")
        finally:
            conn.close()
    
    async def _store_performance_snapshots(self, plugin_id: str):
        """Store performance snapshots to database"""
        snapshots = list(self.performance_snapshots[plugin_id])
        
        conn = sqlite3.connect(self.db_path)
        try:
            for snapshot in snapshots:
                conn.execute("""
                    INSERT INTO performance_snapshots 
                    (plugin_id, timestamp, cpu_percent, memory_mb, active_time, 
                     event_count, error_count, api_calls, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.plugin_id, snapshot.timestamp, snapshot.cpu_percent,
                    snapshot.memory_mb, snapshot.active_time, snapshot.event_count,
                    snapshot.error_count, snapshot.api_calls, snapshot.response_time_ms
                ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error storing performance snapshots: {e}")
        finally:
            conn.close()
    
    async def _monitor_alerts(self):
        """Background task to monitor for alert conditions"""
        while self._collection_active:
            try:
                for plugin_id, metrics in self.plugin_metrics.items():
                    await self._check_alert_conditions(plugin_id, metrics)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _check_alert_conditions(self, plugin_id: str, metrics: Dict[str, Any]):
        """Check if any alert conditions are met"""
        for metric_name, value in metrics.items():
            if metric_name in self.alert_thresholds:
                thresholds = self.alert_thresholds[metric_name]
                
                # Check each threshold level
                for level_name, threshold in thresholds.items():
                    if value >= threshold:
                        alert_level = AlertLevel(level_name.upper())
                        await self._create_alert(plugin_id, metric_name, alert_level, 
                                               threshold, value)
                        break  # Only create alert for highest exceeded threshold
    
    async def _create_alert(self, plugin_id: str, metric_name: str, 
                          level: AlertLevel, threshold: float, actual_value: float):
        """Create a new alert"""
        alert_id = f"{plugin_id}:{metric_name}:{level.value}"
        
        # Don't create duplicate alerts
        if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
            return
        
        alert = Alert(
            id=alert_id,
            level=level,
            plugin_id=plugin_id,
            message=f"Plugin {plugin_id} {metric_name} {level.value}: {actual_value} >= {threshold}",
            metric_name=metric_name,
            threshold_value=threshold,
            actual_value=actual_value
        )
        
        self.active_alerts[alert_id] = alert
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO alerts 
                (id, level, plugin_id, message, metric_name, threshold_value, actual_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id, alert.level.value, alert.plugin_id, alert.message,
                alert.metric_name, alert.threshold_value, alert.actual_value
            ))
            conn.commit()
        finally:
            conn.close()
        
        logger.warning(f"Created {level.value} alert: {alert.message}")