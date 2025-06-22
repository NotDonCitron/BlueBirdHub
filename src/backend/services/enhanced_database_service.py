"""
Enhanced Database Service with Caching and Performance Optimization
Integrates Redis caching, performance monitoring, and intelligent query optimization
"""
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from src.backend.database.database import get_db, engine
from src.backend.services.cache_service import (
    WorkspaceCacheService, 
    FileMetadataCacheService, 
    UserSessionCacheService,
    QueryCacheService,
    CacheInvalidationService,
    cache_result
)
from src.backend.services.db_performance_monitor import (
    db_monitor, 
    setup_sqlalchemy_monitoring,
    time_query
)
from src.backend.models.workspace import Workspace
from src.backend.models.file_metadata import FileMetadata
from src.backend.models.user import User
from src.backend.models.task import Task


class EnhancedDatabaseService:
    """
    High-performance database service with intelligent caching and monitoring
    """
    
    def __init__(self):
        """Initialize enhanced database service"""
        # Setup performance monitoring
        setup_sqlalchemy_monitoring(engine)
        logger.info("Enhanced database service initialized with performance monitoring")
    
    # Workspace Operations with Caching
    
    async def get_workspace_by_id(self, workspace_id: int, user_id: int, db: Session) -> Optional[Dict]:
        """Get workspace with intelligent caching"""
        # Try cache first
        cached_workspace = await WorkspaceCacheService.get_workspace(workspace_id)
        if cached_workspace:
            return cached_workspace
        
        # Query database with monitoring
        with time_query(f"get_workspace_by_id:{workspace_id}"):
            workspace = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.owner_id == user_id
            ).first()
            
            if workspace:
                workspace_data = {
                    'id': workspace.id,
                    'name': workspace.name,
                    'description': workspace.description,
                    'owner_id': workspace.owner_id,
                    'created_at': workspace.created_at.isoformat() if workspace.created_at else None,
                    'updated_at': workspace.updated_at.isoformat() if workspace.updated_at else None
                }
                
                # Cache the result
                await WorkspaceCacheService.set_workspace(workspace_id, workspace_data)
                return workspace_data
        
        return None
    
    async def get_user_workspaces(self, user_id: int, db: Session, limit: int = 50) -> List[Dict]:
        """Get user workspaces with caching"""
        # Try cache first
        cached_workspaces = await WorkspaceCacheService.get_user_workspaces(user_id)
        if cached_workspaces:
            return cached_workspaces[:limit]
        
        # Query database
        with time_query(f"get_user_workspaces:{user_id}"):
            workspaces = db.query(Workspace).filter(
                Workspace.owner_id == user_id
            ).order_by(Workspace.updated_at.desc()).limit(limit).all()
            
            workspace_data = []
            for workspace in workspaces:
                workspace_data.append({
                    'id': workspace.id,
                    'name': workspace.name,
                    'description': workspace.description,
                    'owner_id': workspace.owner_id,
                    'created_at': workspace.created_at.isoformat() if workspace.created_at else None,
                    'updated_at': workspace.updated_at.isoformat() if workspace.updated_at else None
                })
        
        # Cache the result
        await WorkspaceCacheService.set_user_workspaces(user_id, workspace_data)
        return workspace_data
    
    async def update_workspace(self, workspace_id: int, user_id: int, update_data: Dict, db: Session) -> Optional[Dict]:
        """Update workspace and invalidate cache"""
        with time_query(f"update_workspace:{workspace_id}"):
            workspace = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.owner_id == user_id
            ).first()
            
            if workspace:
                for key, value in update_data.items():
                    if hasattr(workspace, key):
                        setattr(workspace, key, value)
                
                workspace.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(workspace)
                
                # Invalidate related caches
                await CacheInvalidationService.invalidate_workspace_related(workspace_id)
                await WorkspaceCacheService.invalidate_user_workspaces(user_id)
                
                return await self.get_workspace_by_id(workspace_id, user_id, db)
        
        return None
    
    # File Operations with Caching
    
    async def get_workspace_files(self, workspace_id: int, user_id: int, db: Session, 
                                limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get workspace files with caching"""
        # Try cache first (only for first page)
        if offset == 0:
            cached_files = await FileMetadataCacheService.get_workspace_files(workspace_id, user_id)
            if cached_files:
                return cached_files[:limit]
        
        # Query database
        with time_query(f"get_workspace_files:{workspace_id}"):
            files = db.query(FileMetadata).filter(
                FileMetadata.workspace_id == workspace_id,
                FileMetadata.user_id == user_id
            ).order_by(FileMetadata.updated_at.desc()).limit(limit).offset(offset).all()
            
            files_data = []
            for file in files:
                files_data.append({
                    'id': file.id,
                    'file_name': file.file_name,
                    'file_path': file.file_path,
                    'file_extension': file.file_extension,
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'ai_category': file.ai_category,
                    'ai_description': file.ai_description,
                    'importance_score': file.importance_score,
                    'is_favorite': file.is_favorite,
                    'is_archived': file.is_archived,
                    'updated_at': file.updated_at.isoformat() if file.updated_at else None
                })
        
        # Cache first page results
        if offset == 0:
            await FileMetadataCacheService.set_workspace_files(workspace_id, user_id, files_data)
        
        return files_data
    
    async def get_file_metadata(self, file_id: int, user_id: int, db: Session) -> Optional[Dict]:
        """Get file metadata with caching"""
        # Try cache first
        cached_file = await FileMetadataCacheService.get_file_metadata(file_id)
        if cached_file:
            return cached_file
        
        # Query database
        with time_query(f"get_file_metadata:{file_id}"):
            file = db.query(FileMetadata).filter(
                FileMetadata.id == file_id,
                FileMetadata.user_id == user_id
            ).first()
            
            if file:
                file_data = {
                    'id': file.id,
                    'user_id': file.user_id,
                    'workspace_id': file.workspace_id,
                    'file_name': file.file_name,
                    'file_path': file.file_path,
                    'file_extension': file.file_extension,
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'checksum': file.checksum,
                    'ai_category': file.ai_category,
                    'ai_description': file.ai_description,
                    'ai_tags': file.ai_tags,
                    'importance_score': file.importance_score,
                    'user_category': file.user_category,
                    'user_description': file.user_description,
                    'is_favorite': file.is_favorite,
                    'is_archived': file.is_archived,
                    'file_created_at': file.file_created_at.isoformat() if file.file_created_at else None,
                    'file_modified_at': file.file_modified_at.isoformat() if file.file_modified_at else None,
                    'last_accessed_at': file.last_accessed_at.isoformat() if file.last_accessed_at else None,
                    'indexed_at': file.indexed_at.isoformat() if file.indexed_at else None,
                    'updated_at': file.updated_at.isoformat() if file.updated_at else None
                }
                
                # Cache the result
                await FileMetadataCacheService.set_file_metadata(file_id, file_data)
                return file_data
        
        return None
    
    # Analytics and Aggregations with Caching
    
    @cache_result(ttl=900, key_prefix="workspace_analytics")  # 15-minute cache
    async def get_workspace_analytics(self, workspace_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Get workspace analytics with intelligent caching"""
        with time_query(f"get_workspace_analytics:{workspace_id}"):
            # File statistics
            file_stats = db.query(
                func.count(FileMetadata.id).label('total_files'),
                func.sum(FileMetadata.file_size).label('total_size'),
                func.avg(FileMetadata.importance_score).label('avg_importance'),
                func.count(func.distinct(FileMetadata.file_extension)).label('unique_extensions')
            ).filter(
                FileMetadata.workspace_id == workspace_id,
                FileMetadata.user_id == user_id
            ).first()
            
            # File categories
            categories = db.query(
                FileMetadata.ai_category,
                func.count(FileMetadata.id).label('count')
            ).filter(
                FileMetadata.workspace_id == workspace_id,
                FileMetadata.user_id == user_id,
                FileMetadata.ai_category.isnot(None)
            ).group_by(FileMetadata.ai_category).all()
            
            # Recent activity
            recent_files = db.query(func.count(FileMetadata.id)).filter(
                FileMetadata.workspace_id == workspace_id,
                FileMetadata.user_id == user_id,
                FileMetadata.indexed_at >= datetime.utcnow() - timedelta(days=7)
            ).scalar()
            
            analytics = {
                'workspace_id': workspace_id,
                'total_files': file_stats.total_files or 0,
                'total_size_bytes': file_stats.total_size or 0,
                'average_importance': round(file_stats.avg_importance or 0, 2),
                'unique_extensions': file_stats.unique_extensions or 0,
                'categories': [{'category': cat.ai_category, 'count': cat.count} for cat in categories],
                'recent_files_7days': recent_files or 0,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        return analytics
    
    @cache_result(ttl=900, key_prefix="user_dashboard")  # 15-minute cache
    async def get_user_dashboard_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user dashboard data with caching"""
        with time_query(f"get_user_dashboard:{user_id}"):
            # User statistics
            workspace_count = db.query(func.count(Workspace.id)).filter(
                Workspace.owner_id == user_id
            ).scalar()
            
            total_files = db.query(func.count(FileMetadata.id)).filter(
                FileMetadata.user_id == user_id
            ).scalar()
            
            total_storage = db.query(func.sum(FileMetadata.file_size)).filter(
                FileMetadata.user_id == user_id
            ).scalar()
            
            # Recent activity
            recent_files = db.query(FileMetadata).filter(
                FileMetadata.user_id == user_id
            ).order_by(FileMetadata.indexed_at.desc()).limit(5).all()
            
            dashboard_data = {
                'user_id': user_id,
                'workspace_count': workspace_count or 0,
                'total_files': total_files or 0,
                'total_storage_bytes': total_storage or 0,
                'recent_files': [
                    {
                        'id': f.id,
                        'name': f.file_name,
                        'workspace_id': f.workspace_id,
                        'indexed_at': f.indexed_at.isoformat() if f.indexed_at else None
                    } for f in recent_files
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
        
        return dashboard_data
    
    # Search Operations
    
    async def search_files(self, user_id: int, query: str, workspace_id: Optional[int] = None,
                          file_type: Optional[str] = None, db: Session = None, 
                          limit: int = 50) -> List[Dict]:
        """Search files with performance optimization"""
        search_key = f"search:{user_id}:{query}:{workspace_id}:{file_type}:{limit}"
        
        with time_query(f"search_files:{hash(search_key)}"):
            # Build query
            db_query = db.query(FileMetadata).filter(FileMetadata.user_id == user_id)
            
            if workspace_id:
                db_query = db_query.filter(FileMetadata.workspace_id == workspace_id)
            
            if file_type:
                db_query = db_query.filter(FileMetadata.file_extension == file_type)
            
            # Text search across multiple fields
            search_filter = func.lower(FileMetadata.file_name).contains(query.lower())
            if len(query) > 2:  # More complex search for longer queries
                search_filter = search_filter | func.lower(FileMetadata.ai_description).contains(query.lower())
                search_filter = search_filter | func.lower(FileMetadata.user_description).contains(query.lower())
            
            files = db_query.filter(search_filter).order_by(
                FileMetadata.importance_score.desc(),
                FileMetadata.updated_at.desc()
            ).limit(limit).all()
            
            results = []
            for file in files:
                results.append({
                    'id': file.id,
                    'file_name': file.file_name,
                    'file_path': file.file_path,
                    'workspace_id': file.workspace_id,
                    'ai_category': file.ai_category,
                    'ai_description': file.ai_description,
                    'importance_score': file.importance_score,
                    'updated_at': file.updated_at.isoformat() if file.updated_at else None
                })
        
        return results
    
    # Cache Management
    
    async def invalidate_workspace_cache(self, workspace_id: int, user_id: int) -> None:
        """Invalidate all workspace-related caches"""
        await CacheInvalidationService.invalidate_workspace_related(workspace_id)
        await WorkspaceCacheService.invalidate_user_workspaces(user_id)
    
    async def invalidate_file_cache(self, file_id: int, workspace_id: int = None) -> None:
        """Invalidate file-related caches"""
        await CacheInvalidationService.invalidate_file_related(file_id, workspace_id)
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        return db_monitor.get_performance_summary()


# Global enhanced database service instance
enhanced_db_service = EnhancedDatabaseService()