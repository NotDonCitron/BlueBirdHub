from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from src.backend.crud.base import CRUDBase
from src.backend.models.workspace import Workspace
from src.backend.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

class CRUDWorkspace(CRUDBase[Workspace, WorkspaceCreate, WorkspaceUpdate]):
    """CRUD operations for Workspace"""
    
    def get_multi_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Workspace]:
        """Get all workspaces for a specific user"""
        return (
            db.query(self.model)
            .filter(Workspace.user_id == user_id)
            .filter(Workspace.is_active == True)
            .order_by(Workspace.last_accessed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Workspace]:
        """Get workspaces for a specific user (legacy method)"""
        return self.get_multi_by_user(db, user_id=user_id, skip=skip, limit=limit)

    def get_default_workspace(self, db: Session, *, user_id: int) -> Optional[Workspace]:
        """Get the default workspace for a user"""
        return (
            db.query(self.model)
            .filter(Workspace.user_id == user_id)
            .filter(Workspace.is_default == True)
            .filter(Workspace.is_active == True)
            .first()
        )
    
    def get_by_name(self, db: Session, *, name: str, user_id: int) -> Optional[Workspace]:
        """Get workspace by name for a specific user"""
        return (
            db.query(self.model)
            .filter(Workspace.name == name)
            .filter(Workspace.user_id == user_id)
            .filter(Workspace.is_active == True)
            .first()
        )
    
    def mark_as_accessed(self, db: Session, *, workspace_id: int) -> Workspace:
        """Mark workspace as recently accessed"""
        workspace = db.query(self.model).filter(Workspace.id == workspace_id).first()
        if workspace:
            workspace.last_accessed_at = datetime.utcnow()
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
        return workspace
    
    def update_state(
        self, 
        db: Session, 
        *, 
        workspace_id: int, 
        state: Dict[str, Any]
    ) -> Workspace:
        """Update workspace state for UI restoration"""
        workspace = db.query(self.model).filter(Workspace.id == workspace_id).first()
        if workspace:
            # Merge new state with existing state
            current_state = workspace.layout_config or {}
            current_state.update(state)
            workspace.layout_config = current_state
            workspace.updated_at = datetime.utcnow()
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
        return workspace
    
    def set_default(self, db: Session, *, workspace_id: int, user_id: int) -> Workspace:
        """Set a workspace as default and unset others"""
        # First, unset all other default workspaces for this user
        db.query(self.model).filter(
            Workspace.user_id == user_id,
            Workspace.is_default == True
        ).update({"is_default": False})
        
        # Set the new default workspace
        workspace = db.query(self.model).filter(Workspace.id == workspace_id).first()
        if workspace and workspace.user_id == user_id:
            workspace.is_default = True
            workspace.updated_at = datetime.utcnow()
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
        
        return workspace

    def set_as_default(self, db: Session, *, workspace_id: int, user_id: int) -> Workspace:
        """Set a workspace as the default for a user (legacy method)"""
        return self.set_default(db, workspace_id=workspace_id, user_id=user_id)

    def get_by_theme(
        self, db: Session, *, user_id: int, theme: str
    ) -> List[Workspace]:
        """Get workspaces by theme"""
        return db.query(Workspace).filter(
            Workspace.user_id == user_id,
            Workspace.theme == theme,
            Workspace.is_active == True
        ).all()

    def update_last_accessed(self, db: Session, *, workspace_id: int) -> Optional[Workspace]:
        """Update the last accessed timestamp (legacy method)"""
        return self.mark_as_accessed(db, workspace_id=workspace_id)
    
    def get_recent_workspaces(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        limit: int = 5
    ) -> List[Workspace]:
        """Get recently accessed workspaces"""
        return (
            db.query(self.model)
            .filter(Workspace.user_id == user_id)
            .filter(Workspace.is_active == True)
            .filter(Workspace.last_accessed_at.isnot(None))
            .order_by(Workspace.last_accessed_at.desc())
            .limit(limit)
            .all()
        )
    
    def search_workspaces(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Workspace]:
        """Search workspaces by name or description"""
        search_filter = f"%{query}%"
        return (
            db.query(self.model)
            .filter(Workspace.user_id == user_id)
            .filter(Workspace.is_active == True)
            .filter(
                (Workspace.name.ilike(search_filter)) |
                (Workspace.description.ilike(search_filter))
            )
            .order_by(Workspace.last_accessed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

workspace = CRUDWorkspace(Workspace)