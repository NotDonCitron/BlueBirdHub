"""
Performance Monitoring API Endpoints
Provides real-time performance metrics and optimization insights
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import psutil
import time
from datetime import datetime, timedelta

from src.backend.database.database import get_db
from src.backend.services.database_optimizer import get_db_optimizer
from src.backend.services.cache_service import cache_service

router = APIRouter(prefix="/performance", tags=["performance"])

@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get comprehensive system health metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database health
        db_optimizer = get_db_optimizer()
        db_health = db_optimizer.get_database_health() if db_optimizer else {"status": "not_initialized"}
        
        # Cache statistics
        cache_stats = cache_service.get_stats()
        
        # Application uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "free_gb": round(memory.free / (1024**3), 2)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                },
                "uptime_hours": round(uptime_seconds / 3600, 2)
            },
            "database": db_health,
            "cache": cache_stats,
            "performance_level": _assess_performance_level(cpu_percent, memory.percent)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/database/analysis")
async def get_database_analysis(hours: int = 24) -> Dict[str, Any]:
    """
    Get detailed database performance analysis
    """
    db_optimizer = get_db_optimizer()
    if not db_optimizer:
        raise HTTPException(status_code=503, detail="Database optimizer not initialized")
    
    try:
        analysis = db_optimizer.analyze_query_performance(hours)
        
        # Add current database health
        health = db_optimizer.get_database_health()
        analysis["current_health"] = health
        
        return {
            "success": True,
            "analysis_period_hours": hours,
            "timestamp": datetime.now().isoformat(),
            **analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database analysis failed: {str(e)}")

@router.get("/cache/stats")
async def get_cache_statistics() -> Dict[str, Any]:
    """
    Get comprehensive cache performance statistics
    """
    try:
        stats = cache_service.get_stats()
        
        # Calculate additional metrics
        total_requests = stats["hits"] + stats["misses"]
        efficiency_score = _calculate_cache_efficiency(stats)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "metrics": {
                "total_requests": total_requests,
                "efficiency_score": efficiency_score,
                "memory_usage_estimation": f"{stats['entries'] * 0.5:.1f} KB",  # Rough estimate
                "recommendations": _get_cache_recommendations(stats)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache stats failed: {str(e)}")

@router.post("/cache/cleanup")
async def cleanup_cache(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Trigger cache cleanup and optimization
    """
    try:
        # Record stats before cleanup
        stats_before = cache_service.get_stats()
        
        # Schedule cleanup
        background_tasks.add_task(_perform_cache_cleanup)
        
        return {
            "success": True,
            "message": "Cache cleanup scheduled",
            "stats_before_cleanup": stats_before,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")

@router.get("/metrics/realtime")
async def get_realtime_metrics() -> Dict[str, Any]:
    """
    Get real-time performance metrics for monitoring dashboard
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Quick sample
        memory = psutil.virtual_memory()
        
        # Process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Database connection test
        start_time = time.time()
        db_optimizer = get_db_optimizer()
        if db_optimizer:
            with db_optimizer.get_optimized_session() as session:
                session.execute("SELECT 1")
            db_response_time = (time.time() - start_time) * 1000
        else:
            db_response_time = None
        
        # Cache metrics
        cache_stats = cache_service.get_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2)
            },
            "process": {
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent()
            },
            "database": {
                "response_time_ms": db_response_time,
                "status": "connected" if db_response_time is not None else "disconnected"
            },
            "cache": {
                "hit_rate": cache_stats.get("hit_rate", "0%"),
                "entries": cache_stats.get("entries", 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Realtime metrics failed: {str(e)}")

@router.get("/optimization/recommendations")
async def get_optimization_recommendations() -> Dict[str, Any]:
    """
    Get AI-powered optimization recommendations
    """
    try:
        recommendations = []
        
        # System recommendations
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        if cpu_percent > 80:
            recommendations.append({
                "type": "system",
                "level": "warning",
                "message": f"High CPU usage detected ({cpu_percent:.1f}%)",
                "suggestion": "Consider optimizing heavy operations or scaling resources"
            })
        
        if memory.percent > 85:
            recommendations.append({
                "type": "system", 
                "level": "warning",
                "message": f"High memory usage detected ({memory.percent:.1f}%)",
                "suggestion": "Review memory-intensive operations and consider adding more RAM"
            })
        
        # Database recommendations
        db_optimizer = get_db_optimizer()
        if db_optimizer:
            db_recommendations = db_optimizer.get_optimization_recommendations()
            for rec in db_recommendations:
                recommendations.append({
                    "type": "database",
                    "level": "info",
                    "message": rec,
                    "suggestion": "Review database queries and indexing strategy"
                })
        
        # Cache recommendations
        cache_stats = cache_service.get_stats()
        if cache_stats.get("hit_rate", "0%") != "0%":
            hit_rate_num = float(cache_stats["hit_rate"].replace("%", ""))
            if hit_rate_num < 50:
                recommendations.append({
                    "type": "cache",
                    "level": "warning", 
                    "message": f"Low cache hit rate ({cache_stats['hit_rate']})",
                    "suggestion": "Review cache TTL settings and caching strategy"
                })
        
        if not recommendations:
            recommendations.append({
                "type": "general",
                "level": "success",
                "message": "System performance is optimal",
                "suggestion": "Continue monitoring for any changes"
            })
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")

# Helper functions

def _assess_performance_level(cpu_percent: float, memory_percent: float) -> str:
    """Assess overall system performance level"""
    if cpu_percent > 80 or memory_percent > 85:
        return "critical"
    elif cpu_percent > 60 or memory_percent > 70:
        return "warning"
    elif cpu_percent > 40 or memory_percent > 50:
        return "moderate"
    else:
        return "optimal"

def _calculate_cache_efficiency(stats: Dict[str, Any]) -> float:
    """Calculate cache efficiency score (0-100)"""
    hits = stats.get("hits", 0)
    misses = stats.get("misses", 0)
    total = hits + misses
    
    if total == 0:
        return 100.0
    
    hit_rate = (hits / total) * 100
    
    # Efficiency considers hit rate and eviction rate
    evictions = stats.get("evictions", 0)
    eviction_penalty = min(evictions / max(total, 1) * 10, 20)  # Max 20 point penalty
    
    efficiency = max(0, hit_rate - eviction_penalty)
    return round(efficiency, 2)

def _get_cache_recommendations(stats: Dict[str, Any]) -> list:
    """Generate cache optimization recommendations"""
    recommendations = []
    
    hit_rate_str = stats.get("hit_rate", "0%")
    if hit_rate_str != "0%":
        hit_rate = float(hit_rate_str.replace("%", ""))
        
        if hit_rate < 50:
            recommendations.append("Increase cache TTL for frequently accessed data")
        elif hit_rate > 90:
            recommendations.append("Consider reducing cache TTL to save memory")
    
    evictions = stats.get("evictions", 0)
    total_requests = stats.get("hits", 0) + stats.get("misses", 0)
    
    if evictions > total_requests * 0.1:
        recommendations.append("High eviction rate detected - consider increasing memory allocation")
    
    if not recommendations:
        recommendations.append("Cache performance is optimal")
    
    return recommendations

async def _perform_cache_cleanup():
    """Background task for cache cleanup"""
    try:
        cache_service.cleanup_expired()
        logger.info("Cache cleanup completed successfully")
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")