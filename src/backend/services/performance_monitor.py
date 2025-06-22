"""
Performance Monitoring Service for OrdnungsHub
Tracks response times, database query performance, and system metrics
"""

import time
import asyncio
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    class MockPsutil:
        @staticmethod
        def virtual_memory():
            class Memory:
                percent = 50.0
                total = 8 * 1024**3
                available = 4 * 1024**3
            return Memory()
        
        @staticmethod
        def cpu_percent(interval=None):
            return 25.0
        
        @staticmethod
        def cpu_count():
            return 4
        
        @staticmethod
        def disk_usage(path):
            class Disk:
                total = 100 * 1024**3
                free = 50 * 1024**3
                percent = 50.0
            return Disk()
    
    psutil = MockPsutil()
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from loguru import logger
import json
import os

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    query_count: int = 0
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class PerformanceMonitor:
    """
    Performance monitoring service with baseline tracking
    """
    
    def __init__(self, max_metrics: int = 1000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.query_count = 0
        self.start_time = time.time()
        self.baseline_metrics = {}
        self.alert_thresholds = {
            'response_time': 1.0,  # 1 second
            'memory_usage': 80.0,  # 80% memory usage
            'cpu_usage': 80.0,     # 80% CPU usage
            'query_count': 50      # 50 queries per request
        }
        self._load_baselines()
        logger.info("Performance Monitor initialized")
    
    def _load_baselines(self):
        """Load baseline metrics from file if available"""
        baseline_file = "performance_baselines.json"
        try:
            if os.path.exists(baseline_file):
                with open(baseline_file, 'r') as f:
                    self.baseline_metrics = json.load(f)
                logger.info("Loaded performance baselines from file")
        except Exception as e:
            logger.warning(f"Could not load baseline metrics: {e}")
    
    def _save_baselines(self):
        """Save baseline metrics to file"""
        baseline_file = "performance_baselines.json"
        try:
            with open(baseline_file, 'w') as f:
                json.dump(self.baseline_metrics, f, indent=2, default=str)
            logger.info("Saved performance baselines to file")
        except Exception as e:
            logger.error(f"Could not save baseline metrics: {e}")
    
    def track_request(self, endpoint: str, method: str = "GET"):
        """Decorator to track request performance"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                initial_query_count = self.query_count
                
                try:
                    # Get system metrics before request
                    memory_before = psutil.virtual_memory().percent
                    cpu_before = psutil.cpu_percent(interval=None)
                    
                    result = await func(*args, **kwargs)
                    
                    # Calculate metrics
                    response_time = time.time() - start_time
                    query_count = self.query_count - initial_query_count
                    
                    # Get system metrics after request
                    memory_after = psutil.virtual_memory().percent
                    cpu_after = psutil.cpu_percent(interval=None)
                    
                    # Create metric
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=200,
                        query_count=query_count,
                        memory_usage=max(memory_before, memory_after),
                        cpu_usage=max(cpu_before, cpu_after)
                    )
                    
                    self.add_metric(metric)
                    self._check_performance_alerts(metric)
                    
                    return result
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=500,
                        memory_usage=psutil.virtual_memory().percent,
                        cpu_usage=psutil.cpu_percent(interval=None)
                    )
                    self.add_metric(metric)
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                initial_query_count = self.query_count
                
                try:
                    memory_before = psutil.virtual_memory().percent
                    cpu_before = psutil.cpu_percent(interval=None)
                    
                    result = func(*args, **kwargs)
                    
                    response_time = time.time() - start_time
                    query_count = self.query_count - initial_query_count
                    
                    memory_after = psutil.virtual_memory().percent
                    cpu_after = psutil.cpu_percent(interval=None)
                    
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=200,
                        query_count=query_count,
                        memory_usage=max(memory_before, memory_after),
                        cpu_usage=max(cpu_before, cpu_after)
                    )
                    
                    self.add_metric(metric)
                    self._check_performance_alerts(metric)
                    
                    return result
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=500,
                        memory_usage=psutil.virtual_memory().percent,
                        cpu_usage=psutil.cpu_percent(interval=None)
                    )
                    self.add_metric(metric)
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric"""
        self.metrics.append(metric)
        logger.debug(f"Performance metric: {metric.endpoint} - {metric.response_time:.3f}s")
    
    def increment_query_count(self, count: int = 1):
        """Increment database query count"""
        self.query_count += count
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check if metric exceeds alert thresholds"""
        alerts = []
        
        if metric.response_time > self.alert_thresholds['response_time']:
            alerts.append(f"Slow response time: {metric.response_time:.3f}s")
        
        if metric.memory_usage and metric.memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append(f"High memory usage: {metric.memory_usage:.1f}%")
        
        if metric.cpu_usage and metric.cpu_usage > self.alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {metric.cpu_usage:.1f}%")
        
        if metric.query_count > self.alert_thresholds['query_count']:
            alerts.append(f"High query count: {metric.query_count}")
        
        for alert in alerts:
            logger.warning(f"Performance Alert [{metric.endpoint}]: {alert}")
    
    def get_metrics_summary(self, last_minutes: int = 60) -> Dict[str, Any]:
        """Get performance metrics summary for the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=last_minutes)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"message": "No metrics available for the specified time period"}
        
        # Calculate averages
        response_times = [m.response_time for m in recent_metrics]
        query_counts = [m.query_count for m in recent_metrics]
        memory_usage = [m.memory_usage for m in recent_metrics if m.memory_usage]
        cpu_usage = [m.cpu_usage for m in recent_metrics if m.cpu_usage]
        
        # Group by endpoint
        endpoint_stats = defaultdict(list)
        for metric in recent_metrics:
            endpoint_stats[metric.endpoint].append(metric.response_time)
        
        endpoint_averages = {
            endpoint: {
                "avg_response_time": sum(times) / len(times),
                "max_response_time": max(times),
                "min_response_time": min(times),
                "request_count": len(times)
            }
            for endpoint, times in endpoint_stats.items()
        }
        
        return {
            "period_minutes": last_minutes,
            "total_requests": len(recent_metrics),
            "avg_response_time": sum(response_times) / len(response_times),
            "max_response_time": max(response_times),
            "min_response_time": min(response_times),
            "avg_query_count": sum(query_counts) / len(query_counts) if query_counts else 0,
            "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else None,
            "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage) if cpu_usage else None,
            "endpoint_breakdown": endpoint_averages,
            "uptime_seconds": time.time() - self.start_time
        }
    
    def get_baseline_comparison(self) -> Dict[str, Any]:
        """Compare current performance to baseline"""
        current_summary = self.get_metrics_summary(last_minutes=10)  # Last 10 minutes
        
        comparison = {}
        
        for metric_name in ['avg_response_time', 'avg_memory_usage', 'avg_cpu_usage']:
            current_value = current_summary.get(metric_name)
            baseline_value = self.baseline_metrics.get(metric_name)
            
            if current_value is not None and baseline_value is not None:
                percentage_change = ((current_value - baseline_value) / baseline_value) * 100
                comparison[metric_name] = {
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percent": percentage_change,
                    "status": "improved" if percentage_change < -5 else "degraded" if percentage_change > 10 else "stable"
                }
        
        return {
            "baseline_available": bool(self.baseline_metrics),
            "comparison": comparison,
            "recommendations": self._get_performance_recommendations(comparison)
        }
    
    def _get_performance_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        for metric_name, data in comparison.items():
            if data["status"] == "degraded":
                if metric_name == "avg_response_time":
                    recommendations.append("Consider implementing response caching or database query optimization")
                elif metric_name == "avg_memory_usage":
                    recommendations.append("Review memory usage patterns and consider implementing object pooling")
                elif metric_name == "avg_cpu_usage":
                    recommendations.append("Optimize CPU-intensive operations or consider horizontal scaling")
        
        if not recommendations:
            recommendations.append("Performance is stable or improved compared to baseline")
        
        return recommendations
    
    def set_baseline(self) -> Dict[str, Any]:
        """Set current performance as baseline"""
        current_summary = self.get_metrics_summary(last_minutes=30)  # Use last 30 minutes
        
        self.baseline_metrics = {
            "avg_response_time": current_summary.get("avg_response_time"),
            "avg_memory_usage": current_summary.get("avg_memory_usage"),
            "avg_cpu_usage": current_summary.get("avg_cpu_usage"),
            "created_at": datetime.now().isoformat(),
            "sample_size": current_summary.get("total_requests", 0)
        }
        
        self._save_baselines()
        
        return {
            "message": "Baseline metrics set successfully",
            "baseline": self.baseline_metrics
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        return {
            "cpu_cores": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "percent_used": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                "percent_used": psutil.disk_usage('/').percent
            },
            "uptime_seconds": time.time() - self.start_time
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()