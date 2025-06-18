"""
Error Logging API endpoints for OrdnungsHub
Provides endpoints for frontend error logging and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from schemas.error_log import (
    ErrorLogCreate, 
    ErrorLogResponse, 
    ErrorLogFilter,
    ErrorLogStats,
    ErrorLogSummary
)
from crud.crud_error_log import error_log
from loguru import logger

router = APIRouter(prefix="/api/logs", tags=["error-logs"])

@router.post("/frontend-error", response_model=dict)
async def log_frontend_error(
    error_data: ErrorLogCreate,
    db: Session = Depends(get_db)
):
    """
    Log a frontend error
    """
    try:
        created_error = error_log.create_error_log(db=db, error_data=error_data)
        logger.warning(f"Frontend error logged: {error_data.message} from {error_data.source}")
        
        return {
            "status": "success",
            "message": "Error logged successfully",
            "error_id": created_error.id
        }
    except Exception as e:
        logger.error(f"Failed to log frontend error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log error")

@router.get("/frontend-errors", response_model=List[ErrorLogResponse])
async def get_frontend_errors(
    source: Optional[str] = Query(None, description="Filter by error source"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[int] = Query(None, description="Filter by resolved status (0/1)"),
    limit: int = Query(100, le=1000, description="Maximum number of errors to return"),
    offset: int = Query(0, ge=0, description="Number of errors to skip"),
    db: Session = Depends(get_db)
):
    """
    Get frontend errors with optional filtering
    """
    try:
        filters = ErrorLogFilter(
            source=source,
            severity=severity,
            resolved=resolved,
            limit=limit,
            offset=offset
        )
        
        errors = error_log.get_errors_filtered(db=db, filters=filters)
        return errors
    except Exception as e:
        logger.error(f"Failed to retrieve frontend errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve errors")

@router.get("/error-stats", response_model=ErrorLogStats)
async def get_error_statistics(db: Session = Depends(get_db)):
    """
    Get error statistics and metrics
    """
    try:
        stats = error_log.get_error_stats(db=db)
        return ErrorLogStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get error statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/error-summary", response_model=ErrorLogSummary)
async def get_error_summary(db: Session = Depends(get_db)):
    """
    Get comprehensive error summary including stats, recent errors, and patterns
    """
    try:
        stats = error_log.get_error_stats(db=db)
        recent_errors = error_log.get_recent_errors(db=db, limit=10)
        common_patterns = error_log.find_common_patterns(db=db, limit=5)
        
        return ErrorLogSummary(
            stats=ErrorLogStats(**stats),
            recent_errors=recent_errors,
            common_patterns=common_patterns
        )
    except Exception as e:
        logger.error(f"Failed to get error summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get error summary")

@router.get("/recent-errors", response_model=List[ErrorLogResponse])
async def get_recent_errors(
    limit: int = Query(10, le=50, description="Number of recent errors to return"),
    db: Session = Depends(get_db)
):
    """
    Get most recent errors (for quick debugging)
    """
    try:
        errors = error_log.get_recent_errors(db=db, limit=limit)
        return errors
    except Exception as e:
        logger.error(f"Failed to get recent errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent errors")

@router.put("/resolve-error/{error_id}", response_model=dict)
async def resolve_error(
    error_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark an error as resolved
    """
    try:
        resolved_error = error_log.mark_resolved(db=db, error_id=error_id)
        if not resolved_error:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return {
            "status": "success",
            "message": f"Error {error_id} marked as resolved"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve error {error_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve error")

@router.delete("/cleanup-errors", response_model=dict)
async def cleanup_old_errors(
    days: int = Query(30, ge=1, le=365, description="Delete errors older than this many days"),
    db: Session = Depends(get_db)
):
    """
    Delete old errors (cleanup maintenance)
    """
    try:
        deleted_count = error_log.delete_old_errors(db=db, days=days)
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} old errors",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup old errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup errors")

@router.get("/patterns", response_model=List[dict])
async def get_error_patterns(
    limit: int = Query(10, le=50, description="Number of patterns to return"),
    db: Session = Depends(get_db)
):
    """
    Get common error patterns for analysis
    """
    try:
        patterns = error_log.find_common_patterns(db=db, limit=limit)
        return patterns
    except Exception as e:
        logger.error(f"Failed to get error patterns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get error patterns")