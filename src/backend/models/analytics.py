"""
Analytics models for comprehensive data tracking and insights.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum

from src.backend.database.database import Base


class EventType(str, Enum):
    """Types of events that can be tracked."""
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


class ActivityEvent(Base):
    """Track all user activities and events for analytics."""
    
    __tablename__ = "activity_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    file_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=True, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # productivity, collaboration, system
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    duration_seconds = Column(Float, nullable=True)  # For events with duration
    
    # Contextual data
    properties = Column(JSON, nullable=True)  # Additional event properties
    event_metadata = Column(JSON, nullable=True)   # Technical metadata (renamed from 'metadata')
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Device and browser info
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships - re-enabled
    user = relationship("User", back_populates="activity_events", lazy="select")
    workspace = relationship("Workspace", back_populates="activity_events", lazy="select")


class TimeTracking(Base):
    """Track time spent on tasks, workspaces, and projects."""
    
    __tablename__ = "time_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)
    
    activity_type = Column(String(50), nullable=False)  # focus, meeting, break, research
    category = Column(String(50), nullable=False)       # work, personal, learning
    
    # Productivity metrics
    focus_score = Column(Float, nullable=True)           # 0-100 based on activity patterns
    interruptions_count = Column(Integer, default=0)
    breaks_count = Column(Integer, default=0)
    
    # Context
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Automatically tracked data
    active_window_title = Column(String(500), nullable=True)
    application_name = Column(String(200), nullable=True)
    
    is_manual = Column(Boolean, default=False, nullable=False)
    is_billable = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - re-enabled
    user = relationship("User", back_populates="time_tracking", lazy="select")
    workspace = relationship("Workspace", back_populates="time_tracking", lazy="select")


class ProductivityMetrics(Base):
    """Daily/weekly/monthly productivity metrics aggregations."""
    
    __tablename__ = "productivity_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Task metrics
    tasks_created = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_overdue = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)      # Percentage
    average_task_completion_time = Column(Float, nullable=True)  # Hours
    
    # Time metrics
    total_active_time = Column(Integer, default=0)    # Minutes
    focus_time = Column(Integer, default=0)           # Minutes of focused work
    meeting_time = Column(Integer, default=0)         # Minutes in meetings
    break_time = Column(Integer, default=0)           # Minutes on breaks
    
    # Collaboration metrics
    comments_made = Column(Integer, default=0)
    files_shared = Column(Integer, default=0)
    meetings_attended = Column(Integer, default=0)
    collaborations_initiated = Column(Integer, default=0)
    
    # System usage metrics
    logins_count = Column(Integer, default=0)
    search_queries = Column(Integer, default=0)
    voice_commands_used = Column(Integer, default=0)
    plugins_used = Column(Integer, default=0)
    
    # Productivity scores (0-100)
    overall_productivity_score = Column(Float, default=0.0)
    focus_score = Column(Float, default=0.0)
    collaboration_score = Column(Float, default=0.0)
    efficiency_score = Column(Float, default=0.0)
    
    # Goal achievement
    goals_set = Column(Integer, default=0)
    goals_achieved = Column(Integer, default=0)
    goal_achievement_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - re-enabled
    user = relationship("User", back_populates="productivity_metrics", lazy="select")
    workspace = relationship("Workspace", back_populates="productivity_metrics", lazy="select")


class TeamMetrics(Base):
    """Team-level analytics and performance metrics."""
    
    __tablename__ = "team_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Team size and composition
    active_members = Column(Integer, default=0)
    total_members = Column(Integer, default=0)
    new_members = Column(Integer, default=0)
    
    # Collective productivity
    total_tasks_completed = Column(Integer, default=0)
    total_active_time = Column(Integer, default=0)    # Minutes
    average_productivity_score = Column(Float, default=0.0)
    
    # Collaboration metrics
    cross_team_collaborations = Column(Integer, default=0)
    internal_collaborations = Column(Integer, default=0)
    knowledge_sharing_events = Column(Integer, default=0)
    
    # Workload distribution
    workload_balance_score = Column(Float, default=0.0)  # 0-100, higher = more balanced
    capacity_utilization = Column(Float, default=0.0)    # Percentage
    
    # Quality metrics
    task_completion_quality = Column(Float, default=0.0)  # Based on revisions, feedback
    meeting_efficiency_score = Column(Float, default=0.0)
    communication_effectiveness = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - re-enabled
    team = relationship("Team", back_populates="team_metrics", lazy="select")
    workspace = relationship("Workspace", back_populates="team_metrics", lazy="select")


class KPITracking(Base):
    """Track custom KPIs and goals."""
    
    __tablename__ = "kpi_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # productivity, quality, collaboration, custom
    
    # KPI definition
    metric_type = Column(String(50), nullable=False)  # count, percentage, ratio, score, time
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    unit = Column(String(50), nullable=True)          # tasks, hours, percentage, etc.
    
    # Time settings
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    measurement_frequency = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    last_measured_at = Column(DateTime(timezone=True), nullable=True)
    last_value = Column(Float, nullable=True)
    
    # Status and alerts
    status = Column(String(20), default="active")     # active, completed, paused, failed
    is_achieved = Column(Boolean, default=False)
    alert_threshold = Column(Float, nullable=True)    # Alert when below this value
    
    # Configuration
    calculation_formula = Column(Text, nullable=True)  # For complex KPIs
    data_sources = Column(JSON, nullable=True)        # Which metrics to use
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - re-enabled
    user = relationship("User", back_populates="kpis", lazy="select")
    team = relationship("Team", back_populates="kpis", lazy="select")
    workspace = relationship("Workspace", back_populates="kpis", lazy="select")


class AnalyticsInsights(Base):
    """AI-generated insights and recommendations."""
    
    __tablename__ = "analytics_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    
    insight_type = Column(String(50), nullable=False)  # trend, anomaly, recommendation, prediction
    category = Column(String(50), nullable=False)      # productivity, collaboration, workload, quality
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    impact_level = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Data analysis
    confidence_score = Column(Float, nullable=False)   # 0-100
    supporting_data = Column(JSON, nullable=True)      # Data that supports the insight
    metrics_affected = Column(JSON, nullable=True)     # Which metrics this relates to
    
    # Recommendations
    recommended_actions = Column(JSON, nullable=True)   # List of suggested actions
    expected_impact = Column(Text, nullable=True)       # What improvement to expect
    
    # Status tracking
    status = Column(String(20), default="new")         # new, acknowledged, in_progress, completed, dismissed
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Validation
    is_actionable = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - re-enabled
    user = relationship("User", foreign_keys=[user_id], back_populates="analytics_insights", lazy="select")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by], lazy="select")
    team = relationship("Team", back_populates="analytics_insights", lazy="select")
    workspace = relationship("Workspace", back_populates="analytics_insights", lazy="select")


class ReportGeneration(Base):
    """Track generated reports for analytics."""
    
    __tablename__ = "report_generation"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # productivity, team, project, custom
    format = Column(String(20), nullable=False)       # pdf, csv, xlsx, json
    
    # Report configuration
    date_range_start = Column(DateTime(timezone=True), nullable=False)
    date_range_end = Column(DateTime(timezone=True), nullable=False)
    filters = Column(JSON, nullable=True)             # Applied filters
    metrics_included = Column(JSON, nullable=False)   # Which metrics to include
    
    # Generation details
    status = Column(String(20), default="pending")    # pending, generating, completed, failed
    file_path = Column(String(500), nullable=True)    # Path to generated file
    file_size_bytes = Column(Integer, nullable=True)
    generation_time_seconds = Column(Float, nullable=True)
    
    # Sharing and access
    is_shared = Column(Boolean, default=False)
    shared_with = Column(JSON, nullable=True)         # List of user IDs
    download_count = Column(Integer, default=0)
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - re-enabled
    user = relationship("User", back_populates="generated_reports", lazy="select")