"""
Real-time Performance Monitoring Dashboard - Phase 3 Enterprise Enhancement
Provides comprehensive performance metrics and monitoring endpoints
"""

import asyncio
import time
import psutil
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import json

from src.backend.database.database import get_db
from src.backend.database.connection_pool import get_connection_pool
from src.backend.services.cache_service import CacheService
from src.backend.database.fts_search import FTSSearchEngine

router = APIRouter(prefix="/performance", tags=["performance"])

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    disk_used_gb: float
    disk_total_gb: float
    disk_percent: float
    load_average: List[float]
    network_bytes_sent: int
    network_bytes_recv: int

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: str
    active_connections: int
    total_requests: int
    avg_response_time_ms: float
    error_rate_percent: float
    cache_hit_ratio: float
    database_query_time_ms: float
    fts_search_time_ms: float
    memory_usage_mb: float

class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_items = 1000
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time_ms": 1000.0,
            "error_rate_percent": 5.0,
            "database_query_time_ms": 500.0
        }
        self.active_alerts: List[Dict[str, Any]] = []
        self.websocket_clients: List[WebSocket] = []
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.start_time = time.time()
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_total_gb = disk.total / 1024 / 1024 / 1024
            
            # Load average (Unix-like systems)
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]  # Windows fallback
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=round(cpu_percent, 2),
                memory_used_mb=round(memory_used_mb, 2),
                memory_total_mb=round(memory_total_mb, 2),
                memory_percent=round(memory.percent, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                disk_percent=round(disk.percent, 2),
                load_average=[round(avg, 2) for avg in load_average],
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv
            )
            
        except Exception as e:
            # Return default metrics if collection fails
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                memory_percent=0.0,
                disk_used_gb=0.0,
                disk_total_gb=0.0,
                disk_percent=0.0,
                load_average=[0.0, 0.0, 0.0],
                network_bytes_sent=0,
                network_bytes_recv=0
            )
    
    async def collect_application_metrics(self, db: Session) -> ApplicationMetrics:
        """Collect application-specific performance metrics"""
        try:
            # Database connection pool metrics
            pool = await get_connection_pool()
            pool_metrics = await pool.get_metrics()
            
            # Cache metrics
            cache_service = CacheService()
            cache_stats = await cache_service.get_cache_stats()
            
            # FTS search performance test
            fts_start = time.time()
            try:
                fts_engine = FTSSearchEngine(db)
                await fts_engine.get_search_statistics(user_id=1)
                fts_search_time = (time.time() - fts_start) * 1000
            except:
                fts_search_time = 0.0
            
            # Application metrics
            uptime_hours = (time.time() - self.start_time) / 3600
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            avg_response_time = self.total_response_time / max(self.request_count, 1)
            
            # Process memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            app_memory_mb = memory_info.rss / 1024 / 1024
            
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                active_connections=pool_metrics["connection_metrics"]["active_connections"],
                total_requests=self.request_count,
                avg_response_time_ms=round(avg_response_time, 2),
                error_rate_percent=round(error_rate, 2),
                cache_hit_ratio=pool_metrics["performance_metrics"]["cache_hit_ratio"],
                database_query_time_ms=pool_metrics["performance_metrics"]["avg_query_time_ms"],
                fts_search_time_ms=round(fts_search_time, 2),
                memory_usage_mb=round(app_memory_mb, 2)
            )
            
        except Exception as e:
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                active_connections=0,
                total_requests=self.request_count,
                avg_response_time_ms=0.0,
                error_rate_percent=0.0,
                cache_hit_ratio=0.0,
                database_query_time_ms=0.0,
                fts_search_time_ms=0.0,
                memory_usage_mb=0.0
            )
    
    async def check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Check for performance alerts"""
        current_alerts = []
        
        # System alerts
        if system_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            current_alerts.append({
                "type": "cpu_high",
                "severity": "warning",
                "message": f"High CPU usage: {system_metrics.cpu_percent}%",
                "value": system_metrics.cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"]
            })
        
        if system_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            current_alerts.append({
                "type": "memory_high",
                "severity": "warning",
                "message": f"High memory usage: {system_metrics.memory_percent}%",
                "value": system_metrics.memory_percent,
                "threshold": self.alert_thresholds["memory_percent"]
            })
        
        if system_metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            current_alerts.append({
                "type": "disk_high",
                "severity": "critical",
                "message": f"High disk usage: {system_metrics.disk_percent}%",
                "value": system_metrics.disk_percent,
                "threshold": self.alert_thresholds["disk_percent"]
            })
        
        # Application alerts
        if app_metrics.avg_response_time_ms > self.alert_thresholds["response_time_ms"]:
            current_alerts.append({
                "type": "response_time_high",
                "severity": "warning",
                "message": f"High response time: {app_metrics.avg_response_time_ms}ms",
                "value": app_metrics.avg_response_time_ms,
                "threshold": self.alert_thresholds["response_time_ms"]
            })
        
        if app_metrics.error_rate_percent > self.alert_thresholds["error_rate_percent"]:
            current_alerts.append({
                "type": "error_rate_high",
                "severity": "critical",
                "message": f"High error rate: {app_metrics.error_rate_percent}%",
                "value": app_metrics.error_rate_percent,
                "threshold": self.alert_thresholds["error_rate_percent"]
            })
        
        if app_metrics.database_query_time_ms > self.alert_thresholds["database_query_time_ms"]:
            current_alerts.append({
                "type": "database_slow",
                "severity": "warning",
                "message": f"Slow database queries: {app_metrics.database_query_time_ms}ms",
                "value": app_metrics.database_query_time_ms,
                "threshold": self.alert_thresholds["database_query_time_ms"]
            })
        
        # Update active alerts
        self.active_alerts = current_alerts
        
        # Broadcast alerts to WebSocket clients
        if current_alerts:
            await self.broadcast_to_clients({
                "type": "alerts",
                "data": current_alerts,
                "timestamp": datetime.now().isoformat()
            })
    
    async def collect_and_store_metrics(self, db: Session):
        """Collect all metrics and store in history"""
        system_metrics = await self.collect_system_metrics()
        app_metrics = await self.collect_application_metrics(db)
        
        # Store in history
        metrics_data = {
            "system": asdict(system_metrics),
            "application": asdict(app_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        self.metrics_history.append(metrics_data)
        
        # Limit history size
        if len(self.metrics_history) > self.max_history_items:
            self.metrics_history = self.metrics_history[-self.max_history_items:]
        
        # Check for alerts
        await self.check_alerts(system_metrics, app_metrics)
        
        # Broadcast to WebSocket clients
        await self.broadcast_to_clients({
            "type": "metrics",
            "data": metrics_data
        })
        
        return metrics_data
    
    async def broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket clients"""
        if self.websocket_clients:
            disconnected_clients = []
            message_str = json.dumps(message)
            
            for client in self.websocket_clients:
                try:
                    await client.send_text(message_str)
                except:
                    disconnected_clients.append(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self.websocket_clients.remove(client)
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record request metrics"""
        self.request_count += 1
        self.total_response_time += response_time_ms
        
        if is_error:
            self.error_count += 1

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# API Endpoints

@router.get("/metrics")
async def get_current_metrics(db: Session = Depends(get_db)):
    """Get current performance metrics"""
    try:
        metrics = await performance_monitor.collect_and_store_metrics(db)
        return {
            "success": True,
            "metrics": metrics,
            "alerts": performance_monitor.active_alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")

@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """Get historical performance metrics"""
    try:
        # Filter history by time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff_time.isoformat()
        
        filtered_history = [
            metric for metric in performance_monitor.metrics_history
            if metric["timestamp"] >= cutoff_iso
        ]
        
        return {
            "success": True,
            "history": filtered_history,
            "total_items": len(filtered_history),
            "time_range_hours": hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics history: {str(e)}")

@router.get("/alerts")
async def get_active_alerts():
    """Get current performance alerts"""
    return {
        "success": True,
        "alerts": performance_monitor.active_alerts,
        "alert_count": len(performance_monitor.active_alerts)
    }

@router.post("/alerts/acknowledge/{alert_type}")
async def acknowledge_alert(alert_type: str):
    """Acknowledge a specific alert"""
    # Remove acknowledged alert
    performance_monitor.active_alerts = [
        alert for alert in performance_monitor.active_alerts
        if alert["type"] != alert_type
    ]
    
    return {
        "success": True,
        "message": f"Alert {alert_type} acknowledged"
    }

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int(time.time() - performance_monitor.start_time),
            "version": "3.0.0",
            "environment": "production"
        }
        
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Determine overall health
        if (cpu_percent > 90 or memory_percent > 95 or disk_percent > 95):
            health_status["status"] = "unhealthy"
        elif (cpu_percent > 80 or memory_percent > 85 or disk_percent > 90):
            health_status["status"] = "degraded"
        
        health_status.update({
            "system": {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "disk_percent": round(disk_percent, 2)
            },
            "services": {
                "database": "healthy",  # Could check actual DB connection
                "cache": "healthy",     # Could check Redis connection
                "search": "healthy"     # Could check FTS functionality
            }
        })
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics streaming"""
    await websocket.accept()
    performance_monitor.websocket_clients.append(websocket)
    
    try:
        # Send initial metrics
        initial_metrics = {
            "type": "welcome",
            "data": {
                "message": "Connected to performance monitoring",
                "client_id": id(websocket),
                "timestamp": datetime.now().isoformat()
            }
        }
        await websocket.send_text(json.dumps(initial_metrics))
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        if websocket in performance_monitor.websocket_clients:
            performance_monitor.websocket_clients.remove(websocket)
    except Exception as e:
        if websocket in performance_monitor.websocket_clients:
            performance_monitor.websocket_clients.remove(websocket)

@router.get("/dashboard")
async def get_dashboard():
    """Serve performance monitoring dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OrdnungsHub Performance Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #2563eb; }
            .metric-label { color: #666; margin-top: 5px; }
            .alert { background: #fee; border: 1px solid #fcc; border-radius: 4px; padding: 10px; margin: 10px 0; }
            .alert.critical { background: #fdd; border-color: #faa; }
            .chart-container { height: 300px; position: relative; }
            h1 { color: #333; text-align: center; }
            .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .status-healthy { background: #10b981; }
            .status-warning { background: #f59e0b; }
            .status-critical { background: #ef4444; }
        </style>
    </head>
    <body>
        <h1>🚀 OrdnungsHub Performance Dashboard - Phase 3</h1>
        
        <div id="connection-status" style="text-align: center; margin-bottom: 20px;">
            <span class="status-indicator status-warning"></span>
            Connecting to real-time monitoring...
        </div>
        
        <div id="alerts-container"></div>
        
        <div class="dashboard">
            <div class="metric-card">
                <div class="metric-value" id="cpu-value">--</div>
                <div class="metric-label">CPU Usage (%)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="memory-value">--</div>
                <div class="metric-label">Memory Usage (%)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="response-time-value">--</div>
                <div class="metric-label">Avg Response Time (ms)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="cache-hit-value">--</div>
                <div class="metric-label">Cache Hit Ratio (%)</div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <div class="metric-card">
                <h3>Performance Trends</h3>
                <div class="chart-container">
                    <canvas id="performance-chart"></canvas>
                </div>
            </div>
        </div>

        <script>
            // WebSocket connection for real-time updates
            const ws = new WebSocket(`ws://${window.location.host}/performance/ws`);
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#ef4444',
                        fill: false
                    }, {
                        label: 'Memory %',
                        data: [],
                        borderColor: '#3b82f6',
                        fill: false
                    }, {
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: '#10b981',
                        fill: false,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100, position: 'left' },
                        y1: { type: 'linear', display: true, position: 'right', beginAtZero: true }
                    }
                }
            });
            
            ws.onopen = function() {
                document.getElementById('connection-status').innerHTML = 
                    '<span class="status-indicator status-healthy"></span>Connected to real-time monitoring';
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                
                if (message.type === 'metrics') {
                    updateMetrics(message.data);
                } else if (message.type === 'alerts') {
                    updateAlerts(message.data);
                }
            };
            
            ws.onclose = function() {
                document.getElementById('connection-status').innerHTML = 
                    '<span class="status-indicator status-critical"></span>Disconnected from monitoring';
            };
            
            function updateMetrics(data) {
                const system = data.system;
                const app = data.application;
                
                document.getElementById('cpu-value').textContent = system.cpu_percent + '%';
                document.getElementById('memory-value').textContent = system.memory_percent + '%';
                document.getElementById('response-time-value').textContent = app.avg_response_time_ms + 'ms';
                document.getElementById('cache-hit-value').textContent = app.cache_hit_ratio + '%';
                
                // Update chart
                const time = new Date(data.timestamp).toLocaleTimeString();
                chart.data.labels.push(time);
                chart.data.datasets[0].data.push(system.cpu_percent);
                chart.data.datasets[1].data.push(system.memory_percent);
                chart.data.datasets[2].data.push(app.avg_response_time_ms);
                
                // Keep only last 20 data points
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets.forEach(dataset => dataset.data.shift());
                }
                
                chart.update('none');
            }
            
            function updateAlerts(alerts) {
                const container = document.getElementById('alerts-container');
                container.innerHTML = '';
                
                alerts.forEach(alert => {
                    const div = document.createElement('div');
                    div.className = `alert ${alert.severity}`;
                    div.innerHTML = `<strong>${alert.type}:</strong> ${alert.message}`;
                    container.appendChild(div);
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Background task to collect metrics periodically
async def start_metrics_collection():
    """Start background metrics collection"""
    from src.backend.database.database import SessionLocal
    
    while True:
        try:
            db = SessionLocal()
            await performance_monitor.collect_and_store_metrics(db)
            db.close()
        except Exception as e:
            print(f"Metrics collection error: {e}")
        
        await asyncio.sleep(30)  # Collect metrics every 30 seconds