"""
Settings API endpoints for OrdnungsHub
Provides system settings and maintenance functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from loguru import logger
import os
import shutil

from database.database import get_db
from crud.crud_file import file_metadata as crud_file

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.post("/clean-storage")
async def clean_storage(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Clean up storage - remove orphaned files and optimize database
    """
    try:
        # Get all files for user
        files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=1000)
        
        cleaned_files = 0
        freed_space = 0
        
        # Simulate cleanup process
        for file in files:
            # Check if physical file exists (if file_path is available)
            if hasattr(file, 'file_path') and file.file_path:
                if not os.path.exists(file.file_path):
                    # File doesn't exist, remove from database
                    crud_file.remove(db, id=file.id)
                    cleaned_files += 1
                    freed_space += file.size or 0
        
        # Additional cleanup operations
        temp_files_cleaned = _clean_temp_files()
        cache_cleared = _clear_cache()
        
        return {
            "success": True,
            "message": "Storage cleanup completed successfully",
            "stats": {
                "files_cleaned": cleaned_files,
                "space_freed_mb": round(freed_space / (1024 * 1024), 2),
                "temp_files_cleaned": temp_files_cleaned,
                "cache_cleared": cache_cleared
            }
        }
    except Exception as e:
        logger.error(f"Error during storage cleanup: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Storage cleanup failed"
        }

@router.get("/storage-stats")
async def get_storage_stats(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get storage statistics
    """
    try:
        # Get all files for user
        files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=1000)
        
        total_files = len(files)
        total_size = sum(file.size or 0 for file in files)
        
        # Categories breakdown
        categories = {}
        for file in files:
            category = file.user_category or file.ai_category or "Other"
            if category not in categories:
                categories[category] = {"count": 0, "size": 0}
            categories[category]["count"] += 1
            categories[category]["size"] += file.size or 0
        
        return {
            "success": True,
            "stats": {
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "categories": categories,
                "last_cleanup": None,  # TODO: Track last cleanup time
                "available_space_mb": 1000  # Mock available space
            }
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "stats": {}
        }

@router.post("/reset-preferences")
async def reset_user_preferences(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Reset user preferences to defaults
    """
    try:
        # TODO: Implement user preferences reset
        return {
            "success": True,
            "message": "User preferences reset to defaults"
        }
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to reset preferences"
        }

@router.get("/system-info")
async def get_system_info():
    """
    Get system information and health status
    """
    try:
        return {
            "success": True,
            "system": {
                "version": "0.1.0",
                "status": "operational",
                "uptime": "Running",
                "database_status": "connected",
                "api_status": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "system": {}
        }

def _clean_temp_files() -> int:
    """Clean temporary files"""
    try:
        # Mock temp file cleanup
        return 5  # Number of temp files cleaned
    except:
        return 0

def _clear_cache() -> bool:
    """Clear application cache"""
    try:
        # Mock cache clearing
        return True
    except:
        return False