"""
Search API endpoints for OrdnungsHub
Provides search functionality that matches frontend expectations
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.backend.database.database import get_db
from src.backend.crud.crud_file import file_metadata as crud_file, tag as crud_tag

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/files")
async def search_files(
    q: Optional[str] = Query(None, description="Search query"),
    user_id: int = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    workspace: Optional[str] = Query(None, description="Filter by workspace"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search files - compatible with frontend expectations
    Maps to the existing files search functionality
    """
    
    if q:
        # Use the existing search functionality
        files = crud_file.search_files(db, user_id=user_id, query=q, skip=skip, limit=limit)
    elif category:
        # Filter by category
        files = crud_file.get_by_category(db, user_id=user_id, category=category, skip=skip, limit=limit)
    else:
        # Get all files for user
        files = crud_file.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    return {
        "success": True,
        "results": files,
        "total": len(files),
        "has_more": len(files) == limit
    }

@router.get("/tags")
async def search_tags(
    query: Optional[str] = Query(None, description="Search tags by name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tags to return"),
    db: Session = Depends(get_db)
):
    """
    Get tags - compatible with frontend expectations
    Maps to the existing tags functionality
    """
    
    if query:
        tags = crud_tag.search_tags(db, query=query, limit=limit)
    else:
        tags = crud_tag.get_multi(db, skip=0, limit=limit)
    
    return [{"name": tag.name, "color": tag.color} for tag in tags]

@router.get("/categories")
async def search_categories(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get available categories - compatible with frontend expectations
    """
    
    # Get all user files to extract categories
    all_files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=1000)
    
    # Extract unique categories
    categories = set()
    for file in all_files:
        if file.user_category:
            categories.add(file.user_category)
        if file.ai_category:
            categories.add(file.ai_category)
    
    return [{"name": cat} for cat in sorted(categories) if cat]