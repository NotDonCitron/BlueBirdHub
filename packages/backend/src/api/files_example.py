# File Upload API Implementation
# packages/backend/src/api/files.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import hashlib
from datetime import datetime
from pathlib import Path

from database.database import get_db
from models.file import File as FileModel
from services.ai_service import AIService

router = APIRouter(prefix="/api/files", tags=["files"])
ai_service = AIService()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    workspace_id: Optional[int] = Form(None)
):
    """Upload a file and process it with AI categorization"""
    try:
        # Generate unique filename
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file_hash}_{file.filename}"
        filepath = UPLOAD_DIR / filename

        # Save file to disk
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Get file metadata
        file_size = len(content)
        mime_type = file.content_type
        
        # AI categorization
        category = await ai_service.categorize_file(filepath)
        
        # Save to database
        db = next(get_db())
        db_file = FileModel(
            filename=file.filename,
            filepath=str(filepath),
            size=file_size,
            mime_type=mime_type,
            category=category,
            workspace_id=workspace_id,
            uploaded_at=datetime.utcnow()
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return JSONResponse(content={
            "id": db_file.id,
            "filename": db_file.filename,
            "category": category,
            "size": file_size,
            "workspace_id": workspace_id
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))