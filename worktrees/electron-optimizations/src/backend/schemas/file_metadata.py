from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Tag Schemas
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_system: bool = False

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')

class Tag(TagBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# FileMetadata Schemas
class FileMetadataBase(BaseModel):
    file_path: str = Field(..., min_length=1, max_length=500)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_extension: Optional[str] = Field(None, max_length=50)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    
    # AI-generated metadata
    ai_category: Optional[str] = Field(None, max_length=100)
    ai_description: Optional[str] = None
    ai_tags: Optional[str] = None
    importance_score: Optional[int] = Field(None, ge=0, le=100)
    
    # User metadata
    user_category: Optional[str] = Field(None, max_length=100)
    user_description: Optional[str] = None
    is_favorite: bool = False
    is_archived: bool = False
    
    # File timestamps
    file_created_at: Optional[datetime] = None
    file_modified_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

class FileMetadataCreate(FileMetadataBase):
    user_id: int
    workspace_id: Optional[int] = None
    checksum: Optional[str] = None

class FileMetadataUpdate(BaseModel):
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    file_extension: Optional[str] = Field(None, max_length=50)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    
    # AI-generated metadata
    ai_category: Optional[str] = Field(None, max_length=100)
    ai_description: Optional[str] = None
    ai_tags: Optional[str] = None
    importance_score: Optional[int] = Field(None, ge=0, le=100)
    
    # User metadata
    user_category: Optional[str] = Field(None, max_length=100)
    user_description: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    
    # File timestamps
    file_created_at: Optional[datetime] = None
    file_modified_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

class FileMetadata(FileMetadataBase):
    id: int
    user_id: int
    checksum: Optional[str] = None
    indexed_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[Tag] = []
    
    class Config:
        from_attributes = True

# Response schemas for API
class FileMetadataResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_extension: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    ai_category: Optional[str]
    user_category: Optional[str]
    is_favorite: bool
    is_archived: bool
    importance_score: Optional[int]
    tags: List[Tag] = []
    indexed_at: datetime
    
    class Config:
        from_attributes = True

class FileSearchResponse(BaseModel):
    files: List[FileMetadataResponse]
    total: int
    has_more: bool

class FileCategoryStats(BaseModel):
    category: str
    count: int
    total_size: Optional[int] = None

class FileStatsResponse(BaseModel):
    total_files: int
    total_size: int
    categories: List[FileCategoryStats]
    recent_files: List[FileMetadataResponse]
    favorite_count: int