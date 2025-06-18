from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import hashlib
import os

from .base import CRUDBase
from models.file_metadata import FileMetadata, Tag, file_tags
from schemas.file_metadata import FileMetadataCreate, FileMetadataUpdate, TagCreate, TagUpdate

class CRUDFileMetadata(CRUDBase[FileMetadata, FileMetadataCreate, FileMetadataUpdate]):
    """CRUD operations for File Metadata"""
    
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[FileMetadata]:
        """Get files for a specific user"""
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.is_archived == False)
            .order_by(FileMetadata.indexed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_path(self, db: Session, *, file_path: str, user_id: int) -> Optional[FileMetadata]:
        """Get file metadata by path"""
        return (
            db.query(self.model)
            .filter(FileMetadata.file_path == file_path)
            .filter(FileMetadata.user_id == user_id)
            .first()
        )
    
    def get_by_category(
        self, db: Session, *, user_id: int, category: str, skip: int = 0, limit: int = 100
    ) -> List[FileMetadata]:
        """Get files by category"""
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(
                or_(
                    FileMetadata.ai_category == category,
                    FileMetadata.user_category == category
                )
            )
            .filter(FileMetadata.is_archived == False)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_favorites(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[FileMetadata]:
        """Get favorite files"""
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.is_favorite == True)
            .filter(FileMetadata.is_archived == False)
            .order_by(FileMetadata.indexed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent(
        self, db: Session, *, user_id: int, days: int = 7, limit: int = 50
    ) -> List[FileMetadata]:
        """Get recently indexed files"""
        since_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.indexed_at >= since_date)
            .filter(FileMetadata.is_archived == False)
            .order_by(FileMetadata.indexed_at.desc())
            .limit(limit)
            .all()
        )
    
    def search_files(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[FileMetadata]:
        """Search files by name, description, or tags"""
        search_filter = f"%{query}%"
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.is_archived == False)
            .filter(
                or_(
                    FileMetadata.file_name.ilike(search_filter),
                    FileMetadata.ai_description.ilike(search_filter),
                    FileMetadata.user_description.ilike(search_filter),
                    FileMetadata.ai_tags.ilike(search_filter)
                )
            )
            .order_by(FileMetadata.importance_score.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_extension(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        extension: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[FileMetadata]:
        """Get files by extension"""
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.file_extension == extension.lower())
            .filter(FileMetadata.is_archived == False)
            .order_by(FileMetadata.indexed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_large_files(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        min_size_mb: int = 100, 
        limit: int = 50
    ) -> List[FileMetadata]:
        """Get large files above specified size"""
        min_size_bytes = min_size_mb * 1024 * 1024
        return (
            db.query(self.model)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.file_size >= min_size_bytes)
            .filter(FileMetadata.is_archived == False)
            .order_by(FileMetadata.file_size.desc())
            .limit(limit)
            .all()
        )
    
    def create_with_checksum(
        self, db: Session, *, obj_in: FileMetadataCreate, file_path: str
    ) -> FileMetadata:
        """Create file metadata with automatic checksum calculation"""
        # Calculate checksum if file exists
        checksum = None
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
        
        # Create object with checksum
        obj_data = obj_in.dict()
        obj_data['checksum'] = checksum
        obj_data['indexed_at'] = datetime.utcnow()
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def mark_as_favorite(self, db: Session, *, file_id: int) -> Optional[FileMetadata]:
        """Toggle favorite status"""
        file_metadata = db.query(self.model).filter(self.model.id == file_id).first()
        if file_metadata:
            file_metadata.is_favorite = not file_metadata.is_favorite
            db.commit()
            db.refresh(file_metadata)
        return file_metadata
    
    def archive_file(self, db: Session, *, file_id: int) -> Optional[FileMetadata]:
        """Archive a file"""
        file_metadata = db.query(self.model).filter(self.model.id == file_id).first()
        if file_metadata:
            file_metadata.is_archived = True
            db.commit()
            db.refresh(file_metadata)
        return file_metadata
    
    def get_by_checksum(self, db: Session, *, checksum: str, user_id: int) -> Optional[FileMetadata]:
        """Get file by checksum to detect duplicates"""
        return (
            db.query(self.model)
            .filter(FileMetadata.checksum == checksum)
            .filter(FileMetadata.user_id == user_id)
            .filter(FileMetadata.is_archived == False)
            .first()
        )


class CRUDTag(CRUDBase[Tag, TagCreate, TagUpdate]):
    """CRUD operations for Tags"""
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Tag]:
        """Get tag by name"""
        return db.query(self.model).filter(Tag.name == name.lower()).first()
    
    def get_or_create(self, db: Session, *, name: str, color: str = None) -> Tag:
        """Get existing tag or create new one"""
        tag = self.get_by_name(db, name=name)
        if not tag:
            tag_data = TagCreate(name=name.lower(), color=color)
            tag = self.create(db, obj_in=tag_data)
        return tag
    
    def get_popular_tags(self, db: Session, *, limit: int = 20) -> List[Tag]:
        """Get most popular tags by usage count"""
        return (
            db.query(Tag)
            .join(file_tags)
            .group_by(Tag.id)
            .order_by(db.func.count(file_tags.c.file_id).desc())
            .limit(limit)
            .all()
        )
    
    def search_tags(self, db: Session, *, query: str, limit: int = 10) -> List[Tag]:
        """Search tags by name"""
        search_filter = f"%{query.lower()}%"
        return (
            db.query(self.model)
            .filter(Tag.name.ilike(search_filter))
            .limit(limit)
            .all()
        )


# Create instances
file_metadata = CRUDFileMetadata(FileMetadata)
tag = CRUDTag(Tag)