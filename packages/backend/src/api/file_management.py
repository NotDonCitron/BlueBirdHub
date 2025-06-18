"""
File Management API endpoints for OrdnungsHub
Provides advanced file operations and organization features
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session

from database.database import get_db
from services.file_manager import file_manager
from services.file_scanner import file_scanner

router = APIRouter(prefix="/file-management", tags=["file-management"])

# Request/Response Models
class OrganizeRequest(BaseModel):
    source_directory: str = Field(..., description="Source directory to organize")
    user_id: int = Field(..., description="User ID")
    organize_mode: str = Field("copy", description="Operation mode: 'copy' or 'move'")

class WorkspaceCreateRequest(BaseModel):
    workspace_name: str = Field(..., description="Name of the workspace")
    template: str = Field("default", description="Template: default, development, creative, business")

class DeduplicationRequest(BaseModel):
    user_id: int
    directory: Optional[str] = Field(None, description="Specific directory to check")
    delete_duplicates: bool = Field(False, description="Delete duplicate files")

class BatchOperationRequest(BaseModel):
    operations: List[Dict[str, Any]] = Field(..., description="List of file operations")

class ArchiveRequest(BaseModel):
    files: List[str] = Field(..., description="List of file paths to archive")
    archive_name: str = Field(..., description="Name of the archive")
    compression: str = Field("zip", description="Compression type: zip or tar")
    password: Optional[str] = Field(None, description="Optional password for zip archives")

class StorageAnalysisRequest(BaseModel):
    user_id: int
    directory: Optional[str] = Field(None, description="Specific directory to analyze")

# Endpoints

@router.post("/organize-by-category")
async def organize_files_by_category(
    request: OrganizeRequest,
    background_tasks: BackgroundTasks
):
    """
    Organize files from source directory into AI-categorized folders
    """
    try:
        if request.organize_mode not in ["copy", "move"]:
            raise HTTPException(
                status_code=400, 
                detail="organize_mode must be 'copy' or 'move'"
            )
        
        # Run organization in background for large directories
        result = await file_manager.organize_files_by_category(
            user_id=request.user_id,
            source_directory=request.source_directory,
            organize_mode=request.organize_mode
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error organizing files: {e}")
        raise HTTPException(status_code=500, detail=f"Organization failed: {str(e)}")

@router.post("/create-workspace")
async def create_workspace_structure(request: WorkspaceCreateRequest):
    """
    Create a structured workspace with predefined folder template
    """
    try:
        result = await file_manager.create_workspace_structure(
            workspace_name=request.workspace_name,
            template=request.template
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Workspace creation failed: {str(e)}")

@router.post("/deduplicate")
async def find_and_remove_duplicates(request: DeduplicationRequest):
    """
    Find duplicate files and optionally remove them
    """
    try:
        result = await file_manager.smart_file_deduplication(
            user_id=request.user_id,
            directory=request.directory,
            delete_duplicates=request.delete_duplicates
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in deduplication: {e}")
        raise HTTPException(status_code=500, detail=f"Deduplication failed: {str(e)}")

@router.post("/batch-operations")
async def perform_batch_operations(request: BatchOperationRequest):
    """
    Perform multiple file operations in batch
    
    Operation format:
    {
        "type": "move|copy|delete|rename",
        "source": "/path/to/source",
        "destination": "/path/to/destination"  // Not required for delete
    }
    """
    try:
        if not request.operations:
            raise HTTPException(status_code=400, detail="No operations provided")
        
        # Validate operations
        valid_types = {"move", "copy", "delete", "rename"}
        for op in request.operations:
            if op.get("type") not in valid_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid operation type: {op.get('type')}"
                )
            if not op.get("source"):
                raise HTTPException(
                    status_code=400, 
                    detail="Source path is required for all operations"
                )
            if op.get("type") != "delete" and not op.get("destination"):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Destination required for {op.get('type')} operation"
                )
        
        result = await file_manager.batch_file_operations(request.operations)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch operations: {e}")
        raise HTTPException(status_code=500, detail=f"Batch operations failed: {str(e)}")

@router.post("/create-archive")
async def create_smart_archive(request: ArchiveRequest):
    """
    Create compressed archive from selected files
    """
    try:
        if not request.files:
            raise HTTPException(status_code=400, detail="No files provided for archive")
        
        if request.compression not in ["zip", "tar"]:
            raise HTTPException(
                status_code=400, 
                detail="Compression must be 'zip' or 'tar'"
            )
        
        result = await file_manager.create_smart_archive(
            files=request.files,
            archive_name=request.archive_name,
            compression=request.compression,
            password=request.password
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating archive: {e}")
        raise HTTPException(status_code=500, detail=f"Archive creation failed: {str(e)}")

@router.post("/analyze-storage")
async def analyze_storage_usage(request: StorageAnalysisRequest):
    """
    Analyze storage usage and provide insights
    """
    try:
        result = await file_manager.analyze_storage_usage(
            user_id=request.user_id,
            directory=request.directory
        )
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing storage: {e}")
        raise HTTPException(status_code=500, detail=f"Storage analysis failed: {str(e)}")

@router.get("/workspace-templates")
async def get_workspace_templates():
    """
    Get available workspace templates
    """
    return {
        "templates": [
            {
                "name": "default",
                "description": "General purpose workspace",
                "folders": [
                    "Documents", "Images", "Videos", "Audio", 
                    "Archives", "Projects", "Temp"
                ]
            },
            {
                "name": "development",
                "description": "Software development workspace",
                "folders": [
                    "src", "docs", "tests", "resources", 
                    "build", "dist", "config", ".vscode"
                ]
            },
            {
                "name": "creative",
                "description": "Creative projects workspace",
                "folders": [
                    "Designs", "References", "Exports", "Projects",
                    "Assets/Images", "Assets/Fonts", "Assets/Icons", "Archives"
                ]
            },
            {
                "name": "business",
                "description": "Business and office workspace",
                "folders": [
                    "Contracts", "Invoices", "Reports", "Presentations",
                    "Meeting Notes", "Clients", "Templates", "Archives"
                ]
            }
        ]
    }

@router.get("/quick-actions")
async def get_quick_actions(user_id: int = Query(..., description="User ID")):
    """
    Get suggested quick actions based on current file state
    """
    try:
        # Get storage analysis
        storage_analysis = await file_manager.analyze_storage_usage(user_id)
        
        actions = []
        
        # Suggest deduplication if duplicates found
        if storage_analysis.get("insights"):
            for insight in storage_analysis["insights"]:
                if insight["type"] == "duplicates":
                    actions.append({
                        "action": "deduplicate",
                        "title": "Remove Duplicate Files",
                        "description": insight["message"],
                        "priority": "high",
                        "estimated_savings_mb": insight.get("space_wasted_mb", 0)
                    })
                elif insight["type"] == "large_files":
                    actions.append({
                        "action": "archive_large",
                        "title": "Archive Large Files",
                        "description": insight["message"],
                        "priority": "medium"
                    })
                elif insight["type"] == "old_files":
                    actions.append({
                        "action": "archive_old",
                        "title": "Archive Old Files",
                        "description": insight["message"],
                        "priority": "low"
                    })
        
        # Suggest organization if many uncategorized files
        category_stats = storage_analysis.get("category_stats", {})
        if category_stats.get("uncategorized", {}).get("count", 0) > 50:
            actions.append({
                "action": "organize",
                "title": "Organize Uncategorized Files",
                "description": f"{category_stats['uncategorized']['count']} files need categorization",
                "priority": "medium"
            })
        
        return {
            "quick_actions": actions,
            "total_files": storage_analysis["total_files"],
            "total_size_gb": storage_analysis["total_size_gb"]
        }
        
    except Exception as e:
        logger.error(f"Error getting quick actions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quick actions: {str(e)}")

@router.post("/smart-cleanup")
async def perform_smart_cleanup(
    user_id: int = Query(..., description="User ID"),
    cleanup_old: bool = Query(False, description="Archive files older than 6 months"),
    cleanup_duplicates: bool = Query(False, description="Remove duplicate files"),
    cleanup_temp: bool = Query(True, description="Clean temporary files")
):
    """
    Perform intelligent cleanup operations
    """
    try:
        results = {
            "operations": [],
            "total_freed_space": 0,
            "files_processed": 0
        }
        
        # Remove duplicates
        if cleanup_duplicates:
            dup_result = await file_manager.smart_file_deduplication(
                user_id=user_id,
                delete_duplicates=True
            )
            results["operations"].append({
                "type": "deduplication",
                "result": dup_result
            })
            results["total_freed_space"] += dup_result.get("space_wasted", 0)
            results["files_processed"] += dup_result.get("deleted_count", 0)
        
        # Archive old files
        if cleanup_old:
            # This would be implemented with additional logic
            # to move old files to archive
            pass
        
        # Clean temporary files
        if cleanup_temp:
            # This would clean known temp directories
            pass
        
        results["total_freed_space_mb"] = round(results["total_freed_space"] / (1024 * 1024), 2)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in smart cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Smart cleanup failed: {str(e)}")