from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ErrorLogCreate(BaseModel):
    message: str = Field(..., description="Error message")
    stack: Optional[str] = Field(None, description="Error stack trace")
    source: str = Field(..., description="Error source (e.g., 'JavaScript Error', 'Console Error')")
    timestamp: str = Field(..., description="ISO timestamp when error occurred")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    url: str = Field(..., description="URL where error occurred")
    error_type: Optional[str] = Field(None, description="Type of error")
    severity: str = Field("error", description="Severity level: error, warning, info")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

class ErrorLogResponse(BaseModel):
    id: int
    message: str
    stack: Optional[str]
    source: str
    timestamp: datetime
    user_agent: Optional[str]
    url: str
    error_type: Optional[str]
    severity: str
    resolved: int
    additional_data: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class ErrorLogFilter(BaseModel):
    source: Optional[str] = None
    severity: Optional[str] = None
    resolved: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = Field(100, le=1000)
    offset: Optional[int] = Field(0, ge=0)

class ErrorLogStats(BaseModel):
    total_errors: int
    unresolved_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_source: Dict[str, int]
    recent_errors_count: int  # Last 24 hours
    
class ErrorLogSummary(BaseModel):
    stats: ErrorLogStats
    recent_errors: list[ErrorLogResponse]
    common_patterns: list[Dict[str, Any]]