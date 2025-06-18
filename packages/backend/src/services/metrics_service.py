"""
Prometheus Metrics Service for OrdnungsHub

Collects and exposes application metrics for monitoring and alerting.
"""

import time
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from loguru import logger
import os

class MetricsService:
    """Prometheus metrics collection service"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_METRICS", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("Metrics collection disabled")
            return
            
        # HTTP Request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections'
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation']
        )
        
        self.db_errors_total = Counter(
            'db_errors_total',
            'Total database errors',
            ['operation', 'error_type']
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result']
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio (0-1)'
        )
        
        # Application metrics
        self.active_users = Gauge(
            'active_users_total',
            'Number of active users'
        )
        
        self.workspaces_total = Gauge(
            'workspaces_total',
            'Total number of workspaces'
        )
        
        self.tasks_total = Gauge(
            'tasks_total',
            'Total number of tasks',
            ['status']
        )
        
        self.ai_requests_total = Counter(
            'ai_requests_total',
            'Total AI service requests',
            ['service', 'status']
        )
        
        self.ai_request_duration = Histogram(
            'ai_request_duration_seconds',
            'AI request duration in seconds',
            ['service']
        )
        
        # Error tracking
        self.errors_total = Counter(
            'application_errors_total',
            'Total application errors',
            ['error_type', 'component']
        )
        
        logger.info("Prometheus metrics service initialized")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not self.enabled:
            return
            
        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record HTTP metrics: {e}")
    
    def record_db_operation(self, operation: str, duration: float, success: bool = True, error_type: str = None):
        """Record database operation metrics"""
        if not self.enabled:
            return
            
        try:
            self.db_query_duration.labels(operation=operation).observe(duration)
            
            if not success and error_type:
                self.db_errors_total.labels(
                    operation=operation,
                    error_type=error_type
                ).inc()
        except Exception as e:
            logger.error(f"Failed to record DB metrics: {e}")
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics"""
        if not self.enabled:
            return
            
        try:
            result = "hit" if hit else "miss"
            self.cache_operations_total.labels(
                operation=operation,
                result=result
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record cache metrics: {e}")
    
    def record_ai_request(self, service: str, duration: float, success: bool = True):
        """Record AI service request metrics"""
        if not self.enabled:
            return
            
        try:
            status = "success" if success else "error"
            self.ai_requests_total.labels(
                service=service,
                status=status
            ).inc()
            
            self.ai_request_duration.labels(service=service).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record AI metrics: {e}")
    
    def record_error(self, error_type: str, component: str):
        """Record application error"""
        if not self.enabled:
            return
            
        try:
            self.errors_total.labels(
                error_type=error_type,
                component=component
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")
    
    def update_application_metrics(self, active_users: int = None, workspaces: int = None, 
                                 tasks_by_status: Dict[str, int] = None):
        """Update application-level metrics"""
        if not self.enabled:
            return
            
        try:
            if active_users is not None:
                self.active_users.set(active_users)
            
            if workspaces is not None:
                self.workspaces_total.set(workspaces)
            
            if tasks_by_status:
                for status, count in tasks_by_status.items():
                    self.tasks_total.labels(status=status).set(count)
        except Exception as e:
            logger.error(f"Failed to update application metrics: {e}")
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        if not self.enabled:
            return ""
        
        try:
            return generate_latest().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return ""

# Global metrics instance
metrics = MetricsService()

class MetricsMiddleware:
    """FastAPI middleware for automatic HTTP metrics collection"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not metrics.enabled:
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Extract request info
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        # Simplify path for metrics (remove IDs, etc.)
        endpoint = self._simplify_path(path)
        
        # Track response
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        # Record metrics
        duration = time.time() - start_time
        metrics.record_http_request(method, endpoint, status_code, duration)
    
    def _simplify_path(self, path: str) -> str:
        """Simplify path for metrics grouping"""
        # Replace common ID patterns
        import re
        
        # Replace UUIDs and numeric IDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path or "/"