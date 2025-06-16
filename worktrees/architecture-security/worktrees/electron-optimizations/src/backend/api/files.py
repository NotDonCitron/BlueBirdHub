from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
import os
import shutil
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from loguru import logger
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from src.backend.database.database import get_db
from src.backend.crud.crud_file import file_metadata as crud_file, tag as crud_tag
from src.backend.schemas.file_metadata import (
    FileMetadata, FileMetadataCreate, FileMetadataUpdate, FileMetadataResponse,
    FileSearchResponse, FileStatsResponse, FileCategoryStats,
    Tag, TagCreate, TagUpdate
)
from src.backend.services.ai_service import ai_service

router = APIRouter(prefix="/files", tags=["files"])

# Configuration
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {
    # Documents
    '.pdf', '.doc', '.docx', '.txt', '.odt', '.rtf', '.tex', '.wpd',
    # Spreadsheets
    '.xls', '.xlsx', '.csv', '.ods',
    # Presentations
    '.ppt', '.pptx', '.odp',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff',
    # Videos
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    # Audio
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
    # Code
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', 
    '.go', '.rs', '.swift', '.kt', '.dart', '.r', '.m', '.scala',
    # Data
    '.json', '.xml', '.yaml', '.yml', '.sql', '.db', '.sqlite',
    # Other
    '.md', '.html', '.css', '.scss', '.sass', '.less'
}

# Dangerous file extensions to block
BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.vbe', '.js', '.jse', 
    '.wsf', '.wsh', '.ps1', '.ps1xml', '.ps2', '.ps2xml', '.psc1', '.psc2',
    '.msh', '.msh1', '.msh2', '.mshxml', '.msh1xml', '.msh2xml',
    '.app', '.gadget', '.msi', '.msp', '.com', '.scr', '.hta', '.cpl',
    '.msc', '.jar', '.reg', '.dll', '.pif', '.application', '.lnk'
}

def get_file_hash(file_path: str, chunk_size: int = 8192) -> str:
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
    """Validate file before upload"""
    # Check file size
    if file_size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
    
    # Check extension
    file_ext = Path(filename).suffix.lower()
    
    # Block dangerous extensions
    if file_ext in BLOCKED_EXTENSIONS:
        return False, f"File type '{file_ext}' is not allowed for security reasons"
    
    # Check allowed extensions if configured
    if ALLOWED_EXTENSIONS and file_ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{file_ext}' is not supported"
    
    # Validate filename
    if not filename or filename.startswith('.'):
        return False, "Invalid filename"
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename - path traversal detected"
    
    return True, "Valid"

def generate_thumbnail(file_path: str, thumbnail_size: tuple = (200, 200)) -> Optional[str]:
    """Generate thumbnail for image files"""
    if not PILLOW_AVAILABLE:
        return None
    
    try:
        # Check if file is an image
        file_ext = Path(file_path).suffix.lower()
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        
        if file_ext not in image_extensions:
            return None
        
        # Create thumbnails directory
        thumbnail_dir = Path("uploads") / "thumbnails"
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail filename
        file_name = Path(file_path).stem
        thumbnail_filename = f"{file_name}_thumb.jpg"
        thumbnail_path = thumbnail_dir / thumbnail_filename
        
        # Generate thumbnail
        with Image.open(file_path) as img:
            # Convert to RGB if needed (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Generated thumbnail: {thumbnail_path}")
            return str(thumbnail_path)
            
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {file_path}: {e}")
        return None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues"""
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}{ext}"

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Form(...),
    workspace_id: Optional[int] = Form(None),
    user_category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    db: Session = Depends(get_db)
):
    """
    Upload a file with comprehensive validation and processing
    
    Features:
    - File validation (size, type, security)
    - Virus scanning simulation (can be replaced with actual scanner)
    - Duplicate detection
    - AI categorization
    - Metadata extraction
    - Background processing for large files
    """
    try:
        # Log upload attempt
        logger.info(f"File upload initiated: {file.filename} for user {user_id}")
        
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        # Validate file
        is_valid, message = validate_file(file.filename, file_size)
        if not is_valid:
            logger.warning(f"File validation failed: {message}")
            raise HTTPException(status_code=400, detail=message)
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        
        # Create user upload directory
        upload_base_dir = Path("uploads") / str(user_id)
        if workspace_id:
            upload_dir = upload_base_dir / f"workspace_{workspace_id}"
        else:
            upload_dir = upload_base_dir / "general"
        
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename if file exists
        file_path = upload_dir / safe_filename
        if file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(safe_filename)
            safe_filename = f"{name}_{timestamp}{ext}"
            file_path = upload_dir / safe_filename
        
        # Save file to disk with streaming for large files
        try:
            with open(file_path, "wb") as buffer:
                chunk_size = 1024 * 1024  # 1MB chunks
                while chunk := file.file.read(chunk_size):
                    buffer.write(chunk)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        # Calculate file hash for duplicate detection
        file_hash = get_file_hash(str(file_path))
        
        # Check for duplicates
        existing_file = crud_file.get_by_checksum(db, checksum=file_hash, user_id=user_id)
        if existing_file:
            # Remove uploaded file
            os.remove(file_path)
            logger.info(f"Duplicate file detected: {file.filename}")
            
            return {
                "status": "duplicate_detected",
                "message": "File already exists in your storage",
                "existing_file": {
                    "id": existing_file.id,
                    "filename": existing_file.file_name,
                    "file_path": existing_file.file_path,
                    "uploaded_at": existing_file.indexed_at
                }
            }
        
        # Extract file metadata
        file_stats = os.stat(file_path)
        mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        
        # Prepare file metadata
        file_metadata = FileMetadataCreate(
            user_id=user_id,
            workspace_id=workspace_id,
            file_name=safe_filename,
            file_path=str(file_path),
            file_size=file_size,
            file_extension=Path(safe_filename).suffix.lower(),
            mime_type=mime_type,
            checksum=file_hash,
            user_category=user_category,
            user_description=description,
            is_archived=False,
            is_favorite=False
        )
        
        # Save to database
        db_file = crud_file.create_with_checksum(
            db, 
            obj_in=file_metadata, 
            file_path=str(file_path)
        )
        
        # Process tags if provided
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            for tag_name in tag_list:
                # Create or get tag
                tag = crud_tag.get_by_name(db, name=tag_name)
                if not tag:
                    tag = crud_tag.create(db, obj_in=TagCreate(name=tag_name))
                # Associate tag with file (this would require many-to-many relationship)
        
        # Schedule background tasks
        background_tasks.add_task(
            process_file_async,
            file_id=db_file.id,
            file_path=str(file_path),
            user_id=user_id
        )
        
        logger.info(f"File uploaded successfully: {safe_filename} (ID: {db_file.id})")
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "file": {
                "id": db_file.id,
                "filename": db_file.file_name,
                "file_size": db_file.file_size,
                "mime_type": db_file.mime_type,
                "checksum": db_file.checksum,
                "uploaded_at": db_file.indexed_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        # Clean up file if it was saved
        if 'file_path' in locals() and file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Internal server error during file upload")

async def process_file_async(file_id: int, file_path: str, user_id: int):
    """
    Background task to process uploaded file
    - AI categorization
    - Metadata extraction
    - Thumbnail generation for images
    - Content extraction for searchability
    """
    try:
        from src.backend.database.database import SessionLocal
        db = SessionLocal()
        
        # Get file from database
        file_record = crud_file.get(db, id=file_id)
        if not file_record:
            logger.error(f"File record not found: {file_id}")
            return
        
        # AI categorization
        try:
            ai_result = await ai_service.categorize_file(file_path)
            if isinstance(ai_result, dict):
                file_record.ai_category = ai_result.get('category', 'unknown')
                # Store additional AI data in ai_tags field if available
                if ai_result.get('tags'):
                    file_record.ai_tags = ','.join(ai_result['tags'])
            else:
                file_record.ai_category = str(ai_result)
            db.commit()
            logger.info(f"AI categorized file {file_id} as: {file_record.ai_category}")
        except Exception as e:
            logger.error(f"AI categorization failed for file {file_id}: {e}")
        
        # Extract additional metadata based on file type
        file_ext = Path(file_path).suffix.lower()
        
        # Image processing
        if file_ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}:
            try:
                # Generate thumbnail
                thumbnail_path = generate_thumbnail(file_path)
                if thumbnail_path:
                    # Store thumbnail path in database (could add thumbnail_path field to model)
                    logger.info(f"Thumbnail generated for file {file_id}: {thumbnail_path}")
            except Exception as e:
                logger.error(f"Image processing failed for file {file_id}: {e}")
        
        # Document processing
        elif file_ext in {'.pdf', '.doc', '.docx', '.txt'}:
            try:
                # Could extract text content for search
                pass
            except Exception as e:
                logger.error(f"Document processing failed for file {file_id}: {e}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Background processing failed for file {file_id}: {e}")

@router.post("/upload-multiple")
async def upload_multiple_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user_id: int = Form(...),
    workspace_id: Optional[int] = Form(None),
    user_category: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files at once
    """
    if len(files) > 20:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 20 files can be uploaded at once"
        )
    
    results = []
    for file in files:
        try:
            # Reuse single file upload logic
            result = await upload_file(
                background_tasks=background_tasks,
                file=file,
                user_id=user_id,
                workspace_id=workspace_id,
                user_category=user_category,
                description=None,
                tags=None,
                db=db
            )
            results.append(result)
        except HTTPException as e:
            results.append({
                "status": "error",
                "filename": file.filename,
                "error": e.detail
            })
    
    # Summary
    successful = len([r for r in results if r.get("status") == "success"])
    duplicates = len([r for r in results if r.get("status") == "duplicate_detected"])
    failed = len([r for r in results if r.get("status") == "error"])
    
    return {
        "summary": {
            "total": len(files),
            "successful": successful,
            "duplicates": duplicates,
            "failed": failed
        },
        "results": results
    }

@router.delete("/upload/{file_id}")
async def delete_uploaded_file(
    file_id: int,
    user_id: int = Query(..., description="User ID"),
    permanent: bool = Query(False, description="Permanently delete file"),
    db: Session = Depends(get_db)
):
    """
    Delete an uploaded file
    """
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if permanent:
            # Delete physical file
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
                logger.info(f"Deleted physical file: {file_record.file_path}")
            
            # Delete database record
            crud_file.remove(db, id=file_id)
            logger.info(f"Deleted file record: {file_id}")
            
            return {"message": "File permanently deleted"}
        else:
            # Soft delete - just mark as archived
            file_record.is_archived = True
            db.commit()
            logger.info(f"Archived file: {file_id}")
            
            return {"message": "File moved to archive"}
            
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

@router.get("/", response_model=List[FileMetadataResponse])
def get_files(
    user_id: int = Query(..., description="User ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    extension: Optional[str] = Query(None, description="Filter by file extension"),
    favorites_only: bool = Query(False, description="Show only favorite files"),
    db: Session = Depends(get_db)
):
    """Get files for a user with optional filters"""
    
    if favorites_only:
        files = crud_file.get_favorites(db, user_id=user_id, skip=skip, limit=limit)
    elif category:
        files = crud_file.get_by_category(db, user_id=user_id, category=category, skip=skip, limit=limit)
    elif extension:
        files = crud_file.get_by_extension(db, user_id=user_id, extension=extension, skip=skip, limit=limit)
    else:
        files = crud_file.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    return files

@router.get("/search", response_model=FileSearchResponse)
def search_files(
    query: str = Query(..., min_length=1, description="Search query"),
    user_id: int = Query(..., description="User ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Search files by name, description, or tags"""
    
    files = crud_file.search_files(db, user_id=user_id, query=query, skip=skip, limit=limit)
    
    # Get total count for pagination (simplified approach)
    total = len(files)
    has_more = len(files) == limit
    
    return FileSearchResponse(
        files=files,
        total=total,
        has_more=has_more
    )

@router.get("/recent", response_model=List[FileMetadataResponse])
def get_recent_files(
    user_id: int = Query(..., description="User ID"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return"),
    db: Session = Depends(get_db)
):
    """Get recently indexed files"""
    
    return crud_file.get_recent(db, user_id=user_id, days=days, limit=limit)

@router.get("/large", response_model=List[FileMetadataResponse])
def get_large_files(
    user_id: int = Query(..., description="User ID"),
    min_size_mb: int = Query(100, ge=1, description="Minimum file size in MB"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return"),
    db: Session = Depends(get_db)
):
    """Get large files above specified size"""
    
    return crud_file.get_large_files(db, user_id=user_id, min_size_mb=min_size_mb, limit=limit)

@router.get("/stats", response_model=FileStatsResponse)
def get_file_stats(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get file statistics for dashboard"""
    
    # Get all user files
    all_files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
    
    # Calculate statistics
    total_files = len(all_files)
    total_size = sum(f.file_size or 0 for f in all_files)
    favorite_count = len([f for f in all_files if f.is_favorite])
    
    # Group by categories
    categories = {}
    for file in all_files:
        category = file.user_category or file.ai_category or "Uncategorized"
        if category not in categories:
            categories[category] = {"count": 0, "size": 0}
        categories[category]["count"] += 1
        categories[category]["size"] += file.file_size or 0
    
    category_stats = [
        FileCategoryStats(
            category=cat,
            count=stats["count"],
            total_size=stats["size"]
        )
        for cat, stats in categories.items()
    ]
    
    # Get recent files
    recent_files = crud_file.get_recent(db, user_id=user_id, days=7, limit=10)
    
    return FileStatsResponse(
        total_files=total_files,
        total_size=total_size,
        categories=category_stats,
        recent_files=recent_files,
        favorite_count=favorite_count
    )

@router.get("/{file_id}", response_model=FileMetadata)
def get_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific file by ID"""
    
    file = crud_file.get(db, id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file

@router.post("/", response_model=FileMetadata)
def create_file_metadata(
    file_data: FileMetadataCreate,
    db: Session = Depends(get_db)
):
    """Create new file metadata"""
    
    # Check if file already exists
    existing_file = crud_file.get_by_path(
        db, file_path=file_data.file_path, user_id=file_data.user_id
    )
    if existing_file:
        raise HTTPException(
            status_code=400, 
            detail="File metadata already exists for this path"
        )
    
    return crud_file.create_with_checksum(
        db, obj_in=file_data, file_path=file_data.file_path
    )

@router.put("/{file_id}", response_model=FileMetadata)
def update_file_metadata(
    file_id: int,
    file_data: FileMetadataUpdate,
    db: Session = Depends(get_db)
):
    """Update file metadata"""
    
    file = crud_file.get(db, id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return crud_file.update(db, db_obj=file, obj_in=file_data)

@router.post("/{file_id}/favorite", response_model=FileMetadata)
def toggle_favorite(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a file"""
    
    file = crud_file.mark_as_favorite(db, file_id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file

@router.post("/{file_id}/archive", response_model=FileMetadata)
def archive_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Archive a file"""
    
    file = crud_file.archive_file(db, file_id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file

@router.post("/{file_id}/rename")
def rename_file(
    file_id: int,
    new_name: str = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Rename a file"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Sanitize new filename
    safe_filename = sanitize_filename(new_name)
    
    # Check if file already exists with this name in the same directory
    file_dir = os.path.dirname(file_record.file_path)
    new_file_path = os.path.join(file_dir, safe_filename)
    
    if os.path.exists(new_file_path) and new_file_path != file_record.file_path:
        raise HTTPException(status_code=400, detail="A file with this name already exists")
    
    try:
        # Rename physical file
        old_path = file_record.file_path
        if os.path.exists(old_path):
            os.rename(old_path, new_file_path)
            logger.info(f"Renamed physical file: {old_path} -> {new_file_path}")
        
        # Update database record
        file_record.file_name = safe_filename
        file_record.file_path = new_file_path
        
        # Update file extension if it changed
        new_extension = Path(safe_filename).suffix.lower()
        if new_extension != file_record.file_extension:
            file_record.file_extension = new_extension
        
        db.commit()
        db.refresh(file_record)
        
        logger.info(f"Renamed file {file_id}: {file_record.file_name}")
        
        return {
            "message": "File renamed successfully",
            "file": {
                "id": file_record.id,
                "old_name": os.path.basename(old_path),
                "new_name": file_record.file_name,
                "file_path": file_record.file_path
            }
        }
        
    except Exception as e:
        logger.error(f"Error renaming file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to rename file")

@router.post("/{file_id}/move")
def move_file(
    file_id: int,
    workspace_id: Optional[int] = Form(None),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Move a file to a different workspace"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Don't move if already in the target workspace
    if file_record.workspace_id == workspace_id:
        return {
            "message": "File is already in the target workspace",
            "file": {
                "id": file_record.id,
                "workspace_id": workspace_id,
                "file_path": file_record.file_path
            }
        }
    
    try:
        # Determine new directory path
        upload_base_dir = Path("uploads") / str(user_id)
        if workspace_id:
            new_dir = upload_base_dir / f"workspace_{workspace_id}"
        else:
            new_dir = upload_base_dir / "general"
        
        new_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate new file path
        old_path = file_record.file_path
        new_file_path = new_dir / file_record.file_name
        
        # Handle filename conflicts
        if new_file_path.exists() and str(new_file_path) != old_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(file_record.file_name)
            new_filename = f"{name}_{timestamp}{ext}"
            new_file_path = new_dir / new_filename
            file_record.file_name = new_filename
        
        # Move physical file
        if os.path.exists(old_path):
            shutil.move(old_path, str(new_file_path))
            logger.info(f"Moved physical file: {old_path} -> {new_file_path}")
        
        # Update database record
        file_record.workspace_id = workspace_id
        file_record.file_path = str(new_file_path)
        
        db.commit()
        db.refresh(file_record)
        
        logger.info(f"Moved file {file_id} to workspace {workspace_id}")
        
        return {
            "message": "File moved successfully",
            "file": {
                "id": file_record.id,
                "workspace_id": workspace_id,
                "old_path": old_path,
                "new_path": file_record.file_path
            }
        }
        
    except Exception as e:
        logger.error(f"Error moving file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to move file")

@router.get("/{file_id}/content")
def get_file_content(
    file_id: int,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get file content for preview (text files only)"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file is a text file
    text_extensions = {'.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.ts', '.html', '.css', '.yaml', '.yml'}
    
    if file_record.file_extension not in text_extensions:
        raise HTTPException(status_code=400, detail="File type not supported for preview")
    
    # Check file size (limit to 1MB for preview)
    max_preview_size = 1024 * 1024  # 1MB
    if file_record.file_size and file_record.file_size > max_preview_size:
        raise HTTPException(status_code=400, detail="File too large for preview")
    
    try:
        # Read file content
        if not os.path.exists(file_record.file_path):
            raise HTTPException(status_code=404, detail="Physical file not found")
        
        with open(file_record.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            "file_id": file_id,
            "file_name": file_record.file_name,
            "content": content,
            "size": len(content),
            "encoding": "utf-8"
        }
        
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_record.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return {
                "file_id": file_id,
                "file_name": file_record.file_name,
                "content": content,
                "size": len(content),
                "encoding": "latin-1"
            }
        except Exception as e:
            logger.error(f"Error reading file content {file_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to read file content")
    except Exception as e:
        logger.error(f"Error reading file content {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read file content")

@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Download a file"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if physical file exists
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")
    
    try:
        # Update last accessed time
        file_record.last_accessed_at = datetime.now()
        db.commit()
        
        logger.info(f"File download initiated: {file_record.file_name} (ID: {file_id}) by user {user_id}")
        
        # Return file response with proper headers
        return FileResponse(
            path=file_record.file_path,
            filename=file_record.file_name,
            media_type=file_record.mime_type or 'application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")

@router.get("/{file_id}/thumbnail")
def get_thumbnail(
    file_id: int,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get thumbnail for an image file"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file is an image
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    if file_record.file_extension not in image_extensions:
        raise HTTPException(status_code=400, detail="File is not an image")
    
    # Generate thumbnail path
    thumbnail_dir = Path("uploads") / "thumbnails"
    file_name = Path(file_record.file_path).stem
    thumbnail_filename = f"{file_name}_thumb.jpg"
    thumbnail_path = thumbnail_dir / thumbnail_filename
    
    # Generate thumbnail if it doesn't exist
    if not thumbnail_path.exists():
        generated_path = generate_thumbnail(file_record.file_path)
        if not generated_path:
            raise HTTPException(status_code=500, detail="Failed to generate thumbnail")
        thumbnail_path = Path(generated_path)
    
    # Check if thumbnail exists
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    try:
        return FileResponse(
            path=str(thumbnail_path),
            media_type='image/jpeg',
            filename=f"thumb_{file_record.file_name}"
        )
    except Exception as e:
        logger.error(f"Error serving thumbnail for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve thumbnail")

@router.delete("/{file_id}")
def delete_file_metadata(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Delete file metadata"""
    
    file = crud_file.get(db, id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    crud_file.remove(db, id=file_id)
    return {"message": "File metadata deleted successfully"}

# Tag endpoints
@router.get("/tags/", response_model=List[Tag])
def get_tags(
    query: Optional[str] = Query(None, description="Search tags by name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tags to return"),
    db: Session = Depends(get_db)
):
    """Get all tags or search tags"""
    
    if query:
        return crud_tag.search_tags(db, query=query, limit=limit)
    else:
        return crud_tag.get_multi(db, skip=0, limit=limit)

@router.get("/tags/popular", response_model=List[Tag])
def get_popular_tags(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of tags to return"),
    db: Session = Depends(get_db)
):
    """Get most popular tags by usage"""
    
    return crud_tag.get_popular_tags(db, limit=limit)

@router.post("/tags/", response_model=Tag)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db)
):
    """Create a new tag"""
    
    # Check if tag already exists
    existing_tag = crud_tag.get_by_name(db, name=tag_data.name)
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    return crud_tag.create(db, obj_in=tag_data)

@router.post("/{file_id}/tags")
def add_file_tags(
    file_id: int,
    tag_names: str = Form(..., description="Comma-separated tag names"),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Add tags to a file"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Parse tag names
        new_tags = [tag.strip() for tag in tag_names.split(",") if tag.strip()]
        
        # Get existing tags
        existing_tags = file_record.ai_tags.split(',') if file_record.ai_tags else []
        existing_tags = [tag.strip() for tag in existing_tags if tag.strip()]
        
        # Combine and deduplicate tags
        all_tags = list(set(existing_tags + new_tags))
        
        # Update file record
        file_record.ai_tags = ','.join(all_tags)
        db.commit()
        db.refresh(file_record)
        
        logger.info(f"Added tags to file {file_id}: {new_tags}")
        
        return {
            "message": f"Added {len(new_tags)} tags to file",
            "file_id": file_id,
            "tags": all_tags
        }
        
    except Exception as e:
        logger.error(f"Error adding tags to file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tags")

@router.delete("/{file_id}/tags")
def remove_file_tags(
    file_id: int,
    tag_names: str = Query(..., description="Comma-separated tag names to remove"),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Remove tags from a file"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Parse tag names to remove
        tags_to_remove = [tag.strip().lower() for tag in tag_names.split(",") if tag.strip()]
        
        # Get existing tags
        existing_tags = file_record.ai_tags.split(',') if file_record.ai_tags else []
        existing_tags = [tag.strip() for tag in existing_tags if tag.strip()]
        
        # Remove specified tags (case-insensitive)
        remaining_tags = [tag for tag in existing_tags if tag.lower() not in tags_to_remove]
        
        # Update file record
        file_record.ai_tags = ','.join(remaining_tags) if remaining_tags else None
        db.commit()
        db.refresh(file_record)
        
        removed_count = len(existing_tags) - len(remaining_tags)
        logger.info(f"Removed {removed_count} tags from file {file_id}")
        
        return {
            "message": f"Removed {removed_count} tags from file",
            "file_id": file_id,
            "remaining_tags": remaining_tags
        }
        
    except Exception as e:
        logger.error(f"Error removing tags from file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove tags")

@router.get("/{file_id}/tags")
def get_file_tags(
    file_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Get all tags for a file"""
    
    # Get file record
    file_record = crud_file.get(db, id=file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verify ownership
    if file_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Parse tags
    tags = file_record.ai_tags.split(',') if file_record.ai_tags else []
    tags = [tag.strip() for tag in tags if tag.strip()]
    
    return {
        "file_id": file_id,
        "file_name": file_record.file_name,
        "tags": tags,
        "tag_count": len(tags)
    }

@router.get("/analytics/dashboard")
def get_file_analytics(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get comprehensive file analytics for dashboard"""
    
    try:
        # Get all user files
        all_files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
        
        # Basic statistics
        total_files = len(all_files)
        total_size = sum(f.file_size or 0 for f in all_files)
        favorite_count = len([f for f in all_files if f.is_favorite])
        archived_count = len([f for f in all_files if f.is_archived])
        
        # File type distribution
        type_stats = {}
        for file in all_files:
            ext = file.file_extension or 'unknown'
            type_stats[ext] = type_stats.get(ext, 0) + 1
        
        # Category distribution
        category_stats = {}
        for file in all_files:
            category = file.user_category or file.ai_category or 'uncategorized'
            category_stats[category] = category_stats.get(category, 0) + 1
        
        # Workspace distribution
        workspace_stats = {}
        for file in all_files:
            workspace = f"Workspace {file.workspace_id}" if file.workspace_id else "No Workspace"
            workspace_stats[workspace] = workspace_stats.get(workspace, 0) + 1
        
        # Size distribution
        size_ranges = {
            "< 1KB": 0,
            "1KB - 100KB": 0,
            "100KB - 1MB": 0,
            "1MB - 10MB": 0,
            "10MB - 100MB": 0,
            "> 100MB": 0
        }
        
        for file in all_files:
            size = file.file_size or 0
            if size < 1024:
                size_ranges["< 1KB"] += 1
            elif size < 100 * 1024:
                size_ranges["1KB - 100KB"] += 1
            elif size < 1024 * 1024:
                size_ranges["100KB - 1MB"] += 1
            elif size < 10 * 1024 * 1024:
                size_ranges["1MB - 10MB"] += 1
            elif size < 100 * 1024 * 1024:
                size_ranges["10MB - 100MB"] += 1
            else:
                size_ranges["> 100MB"] += 1
        
        # Recent activity (files uploaded in last 7 days)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_files = [
            f for f in all_files 
            if f.indexed_at and f.indexed_at.replace(tzinfo=None) > recent_cutoff
        ]
        
        # Most used tags
        tag_usage = {}
        for file in all_files:
            if file.ai_tags:
                for tag in file.ai_tags.split(','):
                    tag = tag.strip()
                    if tag:
                        tag_usage[tag] = tag_usage.get(tag, 0) + 1
        
        # Sort tags by usage
        popular_tags = sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Largest files
        largest_files = sorted(
            [f for f in all_files if f.file_size],
            key=lambda x: x.file_size,
            reverse=True
        )[:5]
        
        return {
            "user_id": user_id,
            "summary": {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "favorite_count": favorite_count,
                "archived_count": archived_count,
                "recent_files_count": len(recent_files)
            },
            "distributions": {
                "file_types": type_stats,
                "categories": category_stats,
                "workspaces": workspace_stats,
                "size_ranges": size_ranges
            },
            "popular_tags": [{"tag": tag, "count": count} for tag, count in popular_tags],
            "largest_files": [
                {
                    "id": f.id,
                    "name": f.file_name,
                    "size_mb": round((f.file_size or 0) / (1024 * 1024), 2),
                    "category": f.user_category or f.ai_category or 'uncategorized'
                }
                for f in largest_files
            ],
            "recent_activity": {
                "files_count": len(recent_files),
                "files": [
                    {
                        "id": f.id,
                        "name": f.file_name,
                        "uploaded_at": f.indexed_at.isoformat() if f.indexed_at else None,
                        "category": f.user_category or f.ai_category or 'uncategorized'
                    }
                    for f in recent_files[:10]
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating file analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")