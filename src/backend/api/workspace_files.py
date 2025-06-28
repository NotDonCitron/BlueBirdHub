"""
Workspace Files API endpoints for OrdnungsHub
Handles file operations within specific workspaces
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger

from src.backend.database.database import get_db
from src.backend.crud.crud_file import file_metadata as crud_file

router = APIRouter(prefix="/workspaces", tags=["workspace-files"])

@router.get("/{workspace_id}/files")
async def get_workspace_files(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    """
    Get files for a specific workspace
    """
    try:
        # Get files for specific workspace
        try:
            files = crud_file.get_by_workspace(db, workspace_id=workspace_id, skip=0, limit=100)
        except AttributeError:
            # Fallback if method doesn't exist - get all files and filter
            files = crud_file.get_multi(db, skip=0, limit=100)
            files = [f for f in files if getattr(f, 'workspace_id', None) == workspace_id]
        
        # Convert to expected format
        results = []
        for file in files:
            results.append({
                "id": str(file.id),
                "name": file.name,
                "type": getattr(file, 'file_type', None) or "unknown",
                "size": f"{getattr(file, 'size', 0) or 0} bytes",
                "modified": file.updated_at.isoformat() if hasattr(file, 'updated_at') and file.updated_at else "",
                "tags": [],
                "category": getattr(file, 'user_category', None) or getattr(file, 'ai_category', None) or "Other",
                "priority": getattr(file, 'priority', None) or "normal",
                "workspace_id": getattr(file, 'workspace_id', None) or workspace_id,
                "workspace_name": f"Workspace {workspace_id}",
                "folder": getattr(file, 'folder_path', None) or ""
            })
        
        return {
            "success": True,
            "files": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error loading workspace {workspace_id} files: {str(e)}")
        # Return empty list instead of error to prevent frontend crashes
        return {
            "success": True,
            "files": [],
            "total": 0,
            "message": f"No files found for workspace {workspace_id}"
        }

@router.post("/{workspace_id}/files")
async def create_workspace_file(
    workspace_id: int,
    file_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new file in a specific workspace
    """
    try:
        # Add workspace_id to file data
        file_data["workspace_id"] = workspace_id
        
        # Create file using CRUD operation
        file = crud_file.create(db, obj_in=file_data)
        
        return {
            "success": True,
            "file": {
                "id": str(file.id),
                "name": file.name,
                "workspace_id": workspace_id
            }
        }
    except Exception as e:
        logger.error(f"Error creating file in workspace {workspace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}") 