from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from loguru import logger

from database.database import get_db
from models.task import Task, TaskStatus
from models.workspace import Workspace
from models.file_metadata import FileMetadata
from schemas.dashboard import DashboardStats, DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardResponse:
    """
    Get dashboard statistics including tasks, workspaces, and file counts.
    """
    try:
        logger.info("Fetching dashboard statistics")
        
        # Get task statistics with error handling
        try:
            total_tasks = db.query(Task).count()
            completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to fetch task statistics: {e}")
            total_tasks = 0
            completed_tasks = 0
        
        # Get workspace statistics with error handling
        try:
            active_workspaces = db.query(Workspace).filter(Workspace.is_active == True).count()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to fetch workspace statistics: {e}")
            active_workspaces = 0
        
        # Get file statistics with error handling
        try:
            total_files = db.query(FileMetadata).count()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to fetch file statistics: {e}")
            total_files = 0
        
        # Calculate completion percentage
        completion_percentage = 0
        if total_tasks > 0:
            completion_percentage = round((completed_tasks / total_tasks) * 100)
        
        # Create statistics object
        stats = DashboardStats(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            active_workspaces=active_workspaces,
            total_files=total_files,
            completion_percentage=completion_percentage
        )
        
        logger.info(f"Dashboard statistics retrieved: {stats}")
        
        return DashboardResponse(
            success=True,
            stats=stats,
            message="Dashboard statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard statistics: {str(e)}"
        )

@router.get("/health")
async def dashboard_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint for dashboard services.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "dashboard",
            "database": "connected",
            "message": "Dashboard service is operational"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Dashboard service unhealthy: {str(e)}"
        )

@router.get("/recent-activity")
async def get_recent_activity(db: Session = Depends(get_db), limit: int = 10) -> Dict[str, Any]:
    """
    Get recent activity for the dashboard.
    """
    try:
        # Get recent completed tasks
        recent_tasks = (
            db.query(Task)
            .filter(Task.status == TaskStatus.COMPLETED)
            .order_by(Task.updated_at.desc())
            .limit(limit // 2)
            .all()
        )
        
        # Get recently created workspaces
        recent_workspaces = (
            db.query(Workspace)
            .order_by(Workspace.created_at.desc())
            .limit(limit // 2)
            .all()
        )
        
        activities = []
        
        # Add task activities
        for task in recent_tasks:
            timestamp_str = None
            if task.updated_at:
                try:
                    timestamp_str = task.updated_at.isoformat()
                except:
                    timestamp_str = None
                    
            activities.append({
                "type": "task_completed",
                "icon": "✅",
                "text": f'Completed task "{task.title}"',
                "timestamp": timestamp_str,
                "id": task.id
            })
        
        # Add workspace activities
        for workspace in recent_workspaces:
            timestamp_str = None
            if workspace.created_at:
                try:
                    timestamp_str = workspace.created_at.isoformat()
                except:
                    timestamp_str = None
                    
            activities.append({
                "type": "workspace_created",
                "icon": "🏠",
                "text": f'Created workspace "{workspace.name}"',
                "timestamp": timestamp_str,
                "id": workspace.id
            })
        
        # Sort by timestamp (most recent first)
        activities = sorted(
            activities, 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "activities": activities,
            "count": len(activities)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent activity: {str(e)}"
        )