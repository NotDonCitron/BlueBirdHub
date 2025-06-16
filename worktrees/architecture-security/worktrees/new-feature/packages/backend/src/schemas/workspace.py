from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    theme: Optional[str] = "default"
    color: Optional[str] = "#4a9eff"  # Hex color code
    icon: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    ambient_sound: Optional[str] = None
    is_default: Optional[bool] = False

class WorkspaceCreate(WorkspaceBase):
    user_id: int

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    ambient_sound: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class WorkspaceStateUpdate(BaseModel):
    state: Dict[str, Any]

class WorkspaceResponse(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_active: bool = True
    last_accessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# Legacy classes for backward compatibility
class WorkspaceInDBBase(WorkspaceBase):
    id: Optional[int] = None
    user_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Workspace(WorkspaceInDBBase):
    pass

class WorkspaceInDB(WorkspaceInDBBase):
    pass

class WorkspaceThemeBase(BaseModel):
    name: str
    display_name: str
    primary_color: str
    secondary_color: str
    background_color: str
    text_color: str
    accent_color: str
    sidebar_color: Optional[str] = None
    widget_background: Optional[str] = None

class WorkspaceThemeCreate(WorkspaceThemeBase):
    pass

class WorkspaceThemeResponse(WorkspaceThemeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime