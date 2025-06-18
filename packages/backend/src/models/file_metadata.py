from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base

# Association table for many-to-many relationship between files and tags
file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('file_metadata.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    file_path = Column(String(500), nullable=False, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    file_extension = Column(String(50), index=True)
    file_size = Column(BigInteger)  # Size in bytes
    mime_type = Column(String(100))
    checksum = Column(String(64))  # SHA256 hash
    
    # AI-generated metadata
    ai_category = Column(String(100))  # AI-suggested category
    ai_description = Column(Text)  # AI-generated description
    ai_tags = Column(Text)  # Comma-separated AI-suggested tags
    importance_score = Column(Integer)  # AI-calculated importance (0-100)
    
    # User metadata
    user_category = Column(String(100))
    user_description = Column(Text)
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    file_created_at = Column(DateTime(timezone=True))
    file_modified_at = Column(DateTime(timezone=True))
    last_accessed_at = Column(DateTime(timezone=True))
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tags = relationship("Tag", secondary=file_tags, back_populates="files")
    
    def __repr__(self):
        return f"<FileMetadata(id={self.id}, name='{self.file_name}')>"


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7))  # Hex color code
    is_system = Column(Boolean, default=False)  # System-generated vs user-created
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    files = relationship("FileMetadata", secondary=file_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


# FileTag is handled by the association table above
# No need for a separate class since we use the many-to-many relationship