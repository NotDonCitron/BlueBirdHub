"""
Workspace Files API endpoints for OrdnungsHub
Separate router to avoid conflicts with workspace_id routing
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger

from database.database import get_db

router = APIRouter(prefix="/workspaces", tags=["workspace-files"])

@router.get("/files")
async def get_workspace_files(
    workspace_id: Optional[int] = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get files for workspace(s) - compatible with frontend expectations
    """
    try:
        from crud.crud_file import file_metadata as crud_file
        
        if workspace_id:
            # Get files for specific workspace
            try:
                files = crud_file.get_by_workspace(db, workspace_id=workspace_id, skip=0, limit=100)
            except AttributeError:
                # Fallback if method doesn't exist
                files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=100)
                files = [f for f in files if f.workspace_id == workspace_id]
        else:
            # Get all files for user
            files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=100)
        
        # Convert to expected format
        results = []
        for file in files:
            results.append({
                "id": str(file.id),
                "name": file.name,
                "type": file.file_type or "unknown",
                "size": f"{file.size or 0} bytes",
                "modified": file.updated_at.isoformat() if file.updated_at else "",
                "tags": [],
                "category": file.user_category or file.ai_category or "Other",
                "priority": file.priority or "normal",
                "workspace_id": file.workspace_id or 1,
                "workspace_name": "Default",
                "folder": file.folder_path or ""
            })
        
        return {
            "success": True,
            "files": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error loading workspace files: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "files": [],
            "total": 0
        }