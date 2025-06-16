from pydantic import BaseModel
from typing import Optional

class DashboardStats(BaseModel):
    """Dashboard statistics data model."""
    total_tasks: int
    completed_tasks: int
    active_workspaces: int
    total_files: int
    completion_percentage: int = 0

class DashboardResponse(BaseModel):
    """Dashboard API response model."""
    success: bool
    stats: DashboardStats
    message: str

class ActivityItem(BaseModel):
    """Activity item model for recent activity."""
    type: str
    icon: str
    text: str
    timestamp: Optional[str] = None
    id: Optional[int] = None

class ActivityResponse(BaseModel):
    """Activity API response model."""
    success: bool
    activities: list[ActivityItem]
    count: int