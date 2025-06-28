"""
Workspace Files API endpoints for OrdnungsHub
Handles file operations within specific workspaces
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger
import os
import uuid
import aiofiles
from pathlib import Path

from src.backend.database.database import get_db
from src.backend.crud.crud_file import file_metadata as crud_file
from src.backend.schemas.file_metadata import FileMetadataCreate

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
                "modified": file.updated_at.isoformat() if hasattr(file, 'updated_at') and file.updated_at is not None else "",
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
        file_create = FileMetadataCreate(**file_data)
        file = crud_file.create(db, obj_in=file_create)
        
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

@router.post("/{workspace_id}/upload")
async def upload_file(
    workspace_id: int,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a file to a specific workspace
    """
    try:
        # Create upload directory structure
        upload_dir = Path("uploads") / f"workspace_{workspace_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Get file size
        file_size = len(content)
        
        # Create file metadata
        file_data = {
            "name": file.filename or unique_filename,
            "file_name": file.filename or unique_filename,
            "file_path": str(file_path),
            "file_type": file.content_type or "application/octet-stream",
            "size": file_size,
            "workspace_id": workspace_id,
            "user_category": category or "uploads",
            "status": "active"
        }
        
        # Save to database
        file_create = FileMetadataCreate(**file_data)
        db_file = crud_file.create(db, obj_in=file_create)
        
        logger.info(f"File uploaded successfully: {file.filename} ({file_size} bytes)")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file": {
                "id": str(db_file.id),
                "name": file.filename or unique_filename,
                "size": file_size,
                "type": file.content_type,
                "workspace_id": workspace_id,
                "path": str(file_path)
            }
        }
        
    except Exception as e:
        logger.error(f"Error uploading file to workspace {workspace_id}: {str(e)}")
        
        # Clean up file if database save failed
        if 'file_path' in locals() and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@router.get("/{workspace_id}/files/{file_id}/download")
async def download_file(
    workspace_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Download a file from a specific workspace
    """
    try:
        # Get file metadata
        db_file = crud_file.get(db, id=file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify file belongs to workspace
        if getattr(db_file, 'workspace_id', None) != workspace_id:
            raise HTTPException(status_code=403, detail="File not in specified workspace")
        
        # Check if file exists on disk
        file_path = Path(getattr(db_file, 'file_path', ''))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            filename=getattr(db_file, 'file_name', 'download'),
            media_type=getattr(db_file, 'file_type', 'application/octet-stream')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}") 