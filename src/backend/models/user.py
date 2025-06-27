from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.backend.database.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="user", cascade="all, delete-orphan")
    
    # Team and collaboration relationships
    created_teams = relationship("Team", back_populates="creator", foreign_keys="Team.created_by")
    team_memberships = relationship("TeamMembership", back_populates="user", foreign_keys="TeamMembership.user_id")
    task_assignments = relationship("TaskAssignment", back_populates="assignee", foreign_keys="TaskAssignment.assigned_to")
    workspace_activities = relationship("WorkspaceActivity", back_populates="user")
    task_comments = relationship("TaskComment", back_populates="user")
    
    # Calendar relationships - re-enabled
    calendars = relationship("Calendar", back_populates="user", cascade="all, delete-orphan")
    calendar_integrations = relationship("CalendarIntegration", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    calendar_attendees = relationship("CalendarEventAttendee", back_populates="user")
    calendar_shares_received = relationship("CalendarShare", foreign_keys="CalendarShare.user_id", back_populates="user")
    calendar_shares_given = relationship("CalendarShare", foreign_keys="CalendarShare.shared_by_user_id", back_populates="shared_by")
    calendar_conflicts = relationship("CalendarConflict", foreign_keys="CalendarConflict.user_id", back_populates="user")
    calendar_sync_logs = relationship("CalendarSyncLog", back_populates="user")
    time_blocks = relationship("TimeBlock", back_populates="user", cascade="all, delete-orphan")
    
    # Analytics relationships - re-enabled
    activity_events = relationship("ActivityEvent", back_populates="user", cascade="all, delete-orphan")
    time_tracking = relationship("TimeTracking", back_populates="user", cascade="all, delete-orphan")
    productivity_metrics = relationship("ProductivityMetrics", back_populates="user", cascade="all, delete-orphan")
    kpis = relationship("KPITracking", back_populates="user", cascade="all, delete-orphan")
    analytics_insights = relationship("AnalyticsInsights", foreign_keys="AnalyticsInsights.user_id", back_populates="user", cascade="all, delete-orphan")
    generated_reports = relationship("ReportGeneration", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    # Unique constraint on user_id + preference_key
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self):
        return f"<UserPreference(id={self.id}, key='{self.preference_key}')>"