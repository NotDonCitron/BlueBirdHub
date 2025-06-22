"""
Smart File Organization API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from ..database import get_db
from ..dependencies.auth import get_current_active_user
from ..models.user import User
from ..services.smart_file_organizer import smart_organizer
from loguru import logger

router = APIRouter(prefix="/api/smart-organize", tags=["smart-organization"])

# Pydantic Models
class FileAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="Path to the file to analyze")

class DirectoryOrganizationRequest(BaseModel):
    directory_path: str = Field(..., description="Path to the directory to organize")
    dry_run: bool = Field(True, description="Whether to perform a dry run or actually move files")

class SmartFolderRequest(BaseModel):
    files: List[str] = Field(..., description="List of file paths to analyze for folder suggestions")

class FileAnalysisResponse(BaseModel):
    file_info: Dict[str, Any]
    suggested_category: str
    confidence: float
    reasoning: str
    ai_suggested_category: Optional[str] = None
    ai_confidence: Optional[float] = None

class OrganizationPlanResponse(BaseModel):
    total_files: int
    categories: Dict[str, List[Dict]]
    suggestions: List[Dict]
    dry_run: bool
    timestamp: str

@router.post("/analyze-file", response_model=FileAnalysisResponse)
async def analyze_file(
    request: FileAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a single file and return AI-powered categorization suggestions
    """
    try:
        # Validate file path
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform analysis
        analysis = smart_organizer.analyze_file(str(file_path))
        
        if 'error' in analysis:
            raise HTTPException(status_code=400, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/organize-directory", response_model=OrganizationPlanResponse)
async def organize_directory(
    request: DirectoryOrganizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze and optionally organize all files in a directory using AI categorization
    """
    try:
        # Validate directory path
        directory_path = Path(request.directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        # Perform organization analysis
        organization_plan = smart_organizer.organize_directory(
            str(directory_path), 
            dry_run=request.dry_run
        )
        
        if 'error' in organization_plan:
            raise HTTPException(status_code=400, detail=organization_plan['error'])
        
        # Log the organization activity
        if not request.dry_run:
            background_tasks.add_task(
                _log_organization_activity,
                user_id=current_user.id,
                directory_path=str(directory_path),
                organization_plan=organization_plan,
                db=db
            )
        
        return organization_plan
        
    except Exception as e:
        logger.error(f"Directory organization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Organization failed: {str(e)}")

@router.post("/suggest-folders")
async def suggest_smart_folders(
    request: SmartFolderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate intelligent folder structure suggestions based on file analysis
    """
    try:
        # Validate file paths
        valid_files = []
        for file_path in request.files:
            path = Path(file_path)
            if path.exists():
                valid_files.append(file_path)
        
        if not valid_files:
            raise HTTPException(status_code=400, detail="No valid files provided")
        
        # Analyze all files
        files_analysis = []
        for file_path in valid_files:
            try:
                analysis = smart_organizer.analyze_file(file_path)
                if 'error' not in analysis:
                    files_analysis.append(analysis)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Generate folder suggestions
        folder_suggestions = smart_organizer.suggest_smart_folders(files_analysis)
        
        return {
            "total_files_analyzed": len(files_analysis),
            "folder_suggestions": folder_suggestions,
            "ai_powered": smart_organizer.ai_available
        }
        
    except Exception as e:
        logger.error(f"Folder suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestion failed: {str(e)}")

@router.get("/capabilities")
async def get_organization_capabilities():
    """
    Get information about available smart organization capabilities
    """
    return {
        "ai_available": smart_organizer.ai_available,
        "features": {
            "semantic_analysis": smart_organizer.ai_available,
            "file_clustering": smart_organizer.ai_available,
            "similarity_search": smart_organizer.ai_available,
            "rule_based_categorization": True,
            "bulk_organization": True,
            "dry_run_mode": True
        },
        "supported_categories": list(smart_organizer.standard_categories.keys()),
        "ai_model": "all-MiniLM-L6-v2" if smart_organizer.ai_available else None
    }

@router.get("/categories")
async def get_organization_categories():
    """
    Get available file organization categories and their rules
    """
    return {
        "categories": smart_organizer.standard_categories,
        "total_categories": len(smart_organizer.standard_categories)
    }

async def _log_organization_activity(
    user_id: int,
    directory_path: str,
    organization_plan: Dict,
    db: Session
):
    """
    Background task to log organization activity
    """
    try:
        # This would typically save to a database table for activity tracking
        logger.info(f"User {user_id} organized directory {directory_path}")
        logger.info(f"Organization result: {organization_plan.get('move_results', {})}")
        
        # Could implement database logging here
        # Example:
        # activity = OrganizationActivity(
        #     user_id=user_id,
        #     directory_path=directory_path,
        #     files_organized=organization_plan.get('total_files', 0),
        #     categories_created=len(organization_plan.get('categories', {})),
        #     timestamp=datetime.now()
        # )
        # db.add(activity)
        # db.commit()
        
    except Exception as e:
        logger.error(f"Failed to log organization activity: {e}")

# Additional utility endpoints

@router.post("/batch-analyze")
async def batch_analyze_files(
    file_paths: List[str],
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze multiple files in batch for performance
    """
    try:
        results = []
        for file_path in file_paths:
            try:
                analysis = smart_organizer.analyze_file(file_path)
                results.append({
                    "file_path": file_path,
                    "analysis": analysis,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "total_files": len(file_paths),
            "successful_analyses": sum(1 for r in results if r["success"]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/stats")
async def get_organization_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics about the smart organization service
    """
    return {
        "ai_available": smart_organizer.ai_available,
        "cached_embeddings": len(smart_organizer.file_embeddings),
        "categories_count": len(smart_organizer.standard_categories),
        "total_file_types_supported": sum(
            len(rules["extensions"]) 
            for rules in smart_organizer.standard_categories.values()
        )
    }