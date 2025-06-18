from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from models.task import TaskStatus, TaskPriority

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    is_recurring: Optional[bool] = False
    recurrence_pattern: Optional[str] = None

class TaskCreate(TaskBase):
    user_id: int
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None

class TaskInDBBase(TaskBase):
    id: Optional[int] = None
    user_id: int
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    actual_hours: Optional[int] = None
    ai_suggested_priority: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Task(TaskInDBBase):
    pass

class TaskInDB(TaskInDBBase):
    pass

class TaskResponse(TaskInDBBase):
    """Schema for task API responses"""
    pass

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    user_id: int

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectInDBBase(ProjectBase):
    id: Optional[int] = None
    user_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Project(ProjectInDBBase):
    pass

class ProjectInDB(ProjectInDBBase):
    pass