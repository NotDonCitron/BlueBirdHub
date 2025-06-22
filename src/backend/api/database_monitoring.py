"""
Database Monitoring API Endpoints
Provides access to database performance metrics, health status, and maintenance operations
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from src.backend.database.database import get_db
from src.backend.services.db_performance_monitor import (
    db_monitor, 
    db_health_checker,
    get_database_metrics,
    get_database_health
)
from src.backend.services.cache_service import cache_service
from src.backend.services.enhanced_database_service import enhanced_db_service
from src.backend.database.maintenance import db_maintenance_service
from src.backend.database.database_config import DatabaseConfig

router = APIRouter(prefix="/api/database", tags=["database-monitoring"])


@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics():
    """
    Get comprehensive database performance metrics
    """
    try:
        metrics = get_database_metrics()
        
        # Add cache metrics if available
        cache_stats = await cache_service.get_cache_stats()
        metrics['cache_metrics'] = cache_stats
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def get_database_health_status():
    """
    Get database health status with recommendations
    """
    try:
        health_status = get_database_health()
        
        return {
            "status": "success",
            "data": health_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get database health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/slow-queries", response_model=Dict[str, Any])
async def get_slow_queries(limit: int = 10):
    """
    Get recent slow queries with execution details
    """
    try:
        slow_queries = db_monitor.get_slow_queries(limit)
        
        return {
            "status": "success",
            "data": {
                "slow_queries": slow_queries,
                "threshold_ms": db_monitor.slow_query_threshold * 1000,
                "total_slow_queries": db_monitor.slow_query_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve slow queries: {str(e)}")


@router.get("/performance-trends", response_model=Dict[str, Any])
async def get_performance_trends(hours: int = 24):
    """
    Get query performance trends over time
    """
    try:
        if hours > 168:  # Limit to 7 days
            hours = 168
        
        trends = db_monitor.get_query_trends(hours)
        
        return {
            "status": "success",
            "data": {
                "trends": trends,
                "period_hours": hours,
                "generated_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")


@router.get("/cache-stats", response_model=Dict[str, Any])
async def get_cache_statistics():
    """
    Get Redis cache performance statistics
    """
    try:
        cache_stats = await cache_service.get_cache_stats()
        
        return {
            "status": "success",
            "data": cache_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cache stats: {str(e)}")


@router.post("/maintenance/quick", response_model=Dict[str, Any])
async def run_quick_maintenance(background_tasks: BackgroundTasks):
    """
    Run quick database maintenance tasks
    """
    try:
        # Run maintenance in background
        background_tasks.add_task(db_maintenance_service.run_quick_maintenance)
        
        return {
            "status": "success",
            "message": "Quick maintenance started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start quick maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start maintenance: {str(e)}")


@router.post("/maintenance/full", response_model=Dict[str, Any])
async def run_full_maintenance(background_tasks: BackgroundTasks):
    """
    Run comprehensive database maintenance
    """
    try:
        # Run full maintenance in background
        background_tasks.add_task(db_maintenance_service.run_full_maintenance)
        
        return {
            "status": "success",
            "message": "Full maintenance started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start full maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start maintenance: {str(e)}")


@router.get("/maintenance/history", response_model=Dict[str, Any])
async def get_maintenance_history(limit: int = 10):
    """
    Get recent maintenance history
    """
    try:
        history = db_maintenance_service.get_maintenance_history(limit)
        
        return {
            "status": "success",
            "data": {
                "maintenance_history": history,
                "total_entries": len(history)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.post("/cache/clear", response_model=Dict[str, Any])
async def clear_cache(pattern: Optional[str] = None):
    """
    Clear cache entries (use with caution)
    """
    try:
        if pattern:
            cleared_count = await cache_service.delete_pattern(pattern)
            message = f"Cleared {cleared_count} keys matching pattern: {pattern}"
        else:
            cleared_count = await cache_service.delete_pattern("ordnungshub:*")
            message = f"Cleared all application cache ({cleared_count} keys)"
        
        return {
            "status": "success",
            "message": message,
            "keys_cleared": cleared_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/configuration", response_model=Dict[str, Any])
async def get_database_configuration():
    """
    Get current database configuration and optimization settings
    """
    try:
        config = DatabaseConfig()
        validation = config.validate_config()
        
        return {
            "status": "success",
            "data": {
                "configuration": {
                    "sqlite_pragmas": config.SQLITE_PRAGMAS,
                    "performance_thresholds": config.PERFORMANCE_THRESHOLDS,
                    "cache_config": {
                        k: v for k, v in config.CACHE_CONFIG.items() 
                        if not k.startswith('redis_url')  # Hide sensitive info
                    },
                    "monitoring_config": config.MONITORING_CONFIG
                },
                "validation": validation
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_database_status():
    """
    Get overall database system status
    """
    try:
        # Get various status indicators
        metrics = get_database_metrics()
        health = get_database_health()
        cache_stats = await cache_service.get_cache_stats()
        
        # Determine overall status
        overall_status = "healthy"
        if health['data']['status'] == "unhealthy":
            overall_status = "unhealthy"
        elif health['data']['warnings']:
            overall_status = "warning"
        
        status_summary = {
            "overall_status": overall_status,
            "database_connected": True,
            "cache_available": cache_stats.get('is_available', False),
            "total_queries": metrics['summary']['total_queries'],
            "slow_query_percentage": metrics['summary']['slow_query_percentage'],
            "cache_hit_rate": cache_stats.get('hit_rate_percent', 0),
            "last_maintenance": None,  # Would need to track this
            "uptime_info": {
                "queries_per_minute": metrics['summary'].get('queries_last_hour', 0) / 60,
                "active_connections": metrics.get('connection_status', {}).get('active_connections', 0)
            }
        }
        
        return {
            "status": "success",
            "data": status_summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {str(e)}")


@router.post("/reset-metrics", response_model=Dict[str, Any])
async def reset_performance_metrics():
    """
    Reset performance monitoring metrics (use with caution)
    """
    try:
        db_monitor.reset_metrics()
        
        return {
            "status": "success",
            "message": "Performance metrics have been reset",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


# Include router in main application
# In main.py, add: app.include_router(database_monitoring.router)