"""
Automation schemas for OrdnungsHub
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AutomationBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    enabled: bool = True

class AutomationCreate(AutomationBase):
    actions: Optional[List[Dict[str, Any]]] = None
    schedule: Optional[str] = None
    event_type: Optional[str] = None

class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    actions: Optional[List[Dict[str, Any]]] = None

class AutomationResponse(AutomationBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_run: Optional[datetime] = None

    class Config:
        from_attributes = True