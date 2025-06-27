"""
Pydantic schemas for analytics API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class EventTypeEnum(str, Enum):
    """Event types for activity tracking."""
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_ACCESSED = "workspace_accessed"
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_SHARED = "file_shared"
    COLLABORATION_COMMENT = "collaboration_comment"
    COLLABORATION_MENTION = "collaboration_mention"
    SEARCH_PERFORMED = "search_performed"
    VOICE_COMMAND_USED = "voice_command_used"
    PLUGIN_USED = "plugin_used"
    CALENDAR_EVENT_CREATED = "calendar_event_created"
    MEETING_ATTENDED = "meeting_attended"
    LOGIN = "login"
    LOGOUT = "logout"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class ActivityEventCreate(BaseModel):
    """Schema for creating activity events."""
    event_type: EventTypeEnum
    user_id: Optional[int] = None
    workspace_id: Optional[int] = None
    task_id: Optional[int] = None
    file_id: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None
    response_time_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class ActivityEventResponse(BaseModel):
    """Schema for activity event responses."""
    id: int
    event_type: str
    category: str
    timestamp: datetime
    user_id: Optional[int]
    workspace_id: Optional[int]
    duration_seconds: Optional[float]
    success: bool
    properties: Dict[str, Any]


class TimeTrackingCreate(BaseModel):
    """Schema for starting time tracking."""
    user_id: int
    workspace_id: Optional[int] = None
    task_id: Optional[int] = None
    activity_type: str = Field(default="focus", description="Type of activity being tracked")
    category: str = Field(default="work", description="Category of the activity")
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class TimeTrackingResponse(BaseModel):
    """Schema for time tracking responses."""
    id: int
    user_id: int
    workspace_id: Optional[int]
    task_id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    activity_type: str
    category: str
    description: Optional[str]
    focus_score: Optional[float]
    is_manual: bool


class ProductivityMetrics(BaseModel):
    """Schema for productivity metrics."""
    tasks_created: int = 0
    tasks_completed: int = 0
    tasks_overdue: int = 0
    completion_rate: float = 0.0
    average_task_completion_time: Optional[float] = None
    total_active_time: int = 0
    focus_time: int = 0
    meeting_time: int = 0
    break_time: int = 0
    comments_made: int = 0
    files_shared: int = 0
    meetings_attended: int = 0
    overall_productivity_score: float = 0.0
    focus_score: float = 0.0
    collaboration_score: float = 0.0
    efficiency_score: float = 0.0


class ProductivitySummaryResponse(BaseModel):
    """Schema for productivity summary responses."""
    success: bool
    data: Dict[str, Any]


class TeamMetricsResponse(BaseModel):
    """Schema for team metrics responses."""
    success: bool
    data: Dict[str, Any]


class InsightItem(BaseModel):
    """Schema for individual insights."""
    type: str = Field(description="Type of insight: recommendation, positive, warning, anomaly")
    category: str = Field(description="Category: productivity, collaboration, time_management, wellbeing")
    title: str
    description: str
    impact_level: str = Field(description="Impact level: low, medium, high, critical")
    recommended_actions: Optional[List[str]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=100)
    date: Optional[str] = None


class InsightsResponse(BaseModel):
    """Schema for insights responses."""
    success: bool
    insights: List[InsightItem]
    anomalies: List[InsightItem]
    total_insights: int


class KPICreate(BaseModel):
    """Schema for creating KPIs."""
    name: str = Field(max_length=200)
    description: Optional[str] = None
    category: str = Field(max_length=100)
    metric_type: str = Field(description="count, percentage, ratio, score, time")
    target_value: float
    unit: Optional[str] = Field(None, max_length=50)
    start_date: datetime
    end_date: datetime
    measurement_frequency: str = Field(description="daily, weekly, monthly")
    alert_threshold: Optional[float] = None
    calculation_formula: Optional[str] = None
    data_sources: Optional[Dict[str, Any]] = None


class KPIResponse(BaseModel):
    """Schema for KPI responses."""
    id: int
    name: str
    description: Optional[str]
    category: str
    metric_type: str
    target_value: float
    current_value: float
    unit: Optional[str]
    progress_percentage: float
    status: str
    is_achieved: bool
    start_date: datetime
    end_date: datetime
    last_measured_at: Optional[datetime]


class ChartDataPoint(BaseModel):
    """Schema for chart data points."""
    date: str
    value: Union[int, float]
    label: Optional[str] = None


class ChartResponse(BaseModel):
    """Schema for chart responses."""
    success: bool
    chart_data: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    chart_type: str = Field(description="line, bar, pie, heatmap, etc.")


class HeatmapDataPoint(BaseModel):
    """Schema for heatmap data points."""
    day: str
    hour: int
    value: int


class AnalyticsFilterRequest(BaseModel):
    """Schema for analytics filter requests."""
    user_ids: Optional[List[int]] = None
    workspace_ids: Optional[List[int]] = None
    team_ids: Optional[List[int]] = None
    event_types: Optional[List[EventTypeEnum]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    categories: Optional[List[str]] = None


class ReportGenerationRequest(BaseModel):
    """Schema for report generation requests."""
    report_type: str = Field(description="productivity, team, project, custom")
    format: str = Field(regex="^(pdf|csv|xlsx|json)$")
    date_range_start: datetime
    date_range_end: datetime
    filters: Optional[AnalyticsFilterRequest] = None
    metrics_included: List[str] = Field(description="List of metrics to include")
    name: Optional[str] = None
    
    @validator('date_range_end')
    def end_date_after_start(cls, v, values):
        if 'date_range_start' in values and v <= values['date_range_start']:
            raise ValueError('End date must be after start date')
        return v


class ReportGenerationResponse(BaseModel):
    """Schema for report generation responses."""
    success: bool
    report_id: str
    status: str = Field(description="pending, generating, completed, failed")
    format: str
    estimated_completion: Optional[datetime] = None
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    message: str


class DashboardWidget(BaseModel):
    """Schema for dashboard widgets."""
    widget_id: str
    widget_type: str = Field(description="chart, metric, table, insight")
    title: str
    data: Dict[str, Any]
    position: Dict[str, int] = Field(description="x, y, width, height")
    config: Dict[str, Any] = {}


class AnalyticsDashboardResponse(BaseModel):
    """Schema for analytics dashboard responses."""
    success: bool
    period: Dict[str, Any]
    overview: Dict[str, Any]
    productivity_summary: Optional[Dict[str, Any]] = None
    team_metrics: Optional[Dict[str, Any]] = None
    workspace_analytics: Optional[Dict[str, Any]] = None
    recent_activities: List[Dict[str, Any]] = []
    widgets: Optional[List[DashboardWidget]] = None


class TimeDistributionChart(BaseModel):
    """Schema for time distribution chart data."""
    category_distribution: List[Dict[str, Union[str, float]]]
    activity_distribution: List[Dict[str, Union[str, float]]]
    total_hours: float
    period_days: int


class TaskVelocityChart(BaseModel):
    """Schema for task velocity chart data."""
    chart_data: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    period_days: int


class ActivityHeatmapChart(BaseModel):
    """Schema for activity heatmap chart data."""
    heatmap_data: List[HeatmapDataPoint]
    hourly_distribution: List[Dict[str, int]]
    peak_hours: List[Dict[str, int]]
    total_events: int
    period_days: int


class CollaborationMetrics(BaseModel):
    """Schema for collaboration metrics."""
    comments_made: int = 0
    files_shared: int = 0
    meetings_attended: int = 0
    collaborations_initiated: int = 0
    cross_team_collaborations: int = 0
    knowledge_sharing_events: int = 0
    communication_effectiveness: float = 0.0


class WorkloadMetrics(BaseModel):
    """Schema for workload metrics."""
    total_hours: float = 0.0
    billable_hours: float = 0.0
    overtime_hours: float = 0.0
    capacity_utilization: float = 0.0
    workload_balance_score: float = 0.0
    stress_indicators: List[str] = []


class PredictiveAnalytics(BaseModel):
    """Schema for predictive analytics."""
    project_completion_prediction: Optional[datetime] = None
    capacity_forecast: Dict[str, float] = {}
    burnout_risk_score: float = 0.0
    productivity_trend: str = Field(description="increasing, decreasing, stable")
    confidence_level: float = Field(ge=0, le=100)


class AlertConfig(BaseModel):
    """Schema for alert configuration."""
    alert_type: str = Field(description="productivity_drop, overwork, deadline_risk, goal_achievement")
    threshold_value: float
    comparison_operator: str = Field(description="gt, lt, eq, gte, lte")
    notification_channels: List[str] = Field(description="email, slack, webhook")
    is_active: bool = True
    frequency: str = Field(description="immediate, daily, weekly")


class AlertResponse(BaseModel):
    """Schema for alert responses."""
    id: int
    alert_type: str
    title: str
    description: str
    severity: str = Field(description="low, medium, high, critical")
    triggered_at: datetime
    is_acknowledged: bool = False
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    workspace_id: Optional[int] = None