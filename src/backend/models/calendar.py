from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, VARCHAR
import enum
import json
from typing import Dict, Any, Optional, List
from src.backend.database.database import Base

class CalendarProvider(enum.Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    APPLE = "APPLE"
    INTERNAL = "INTERNAL"

class CalendarEventStatus(enum.Enum):
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"

class CalendarEventVisibility(enum.Enum):
    DEFAULT = "DEFAULT"
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    CONFIDENTIAL = "CONFIDENTIAL"

class CalendarEventRecurrenceType(enum.Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"

class CalendarSharePermission(enum.Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"

class SyncStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CONFLICT = "CONFLICT"

class JSONType(TypeDecorator):
    """Custom JSON type for SQLAlchemy that handles serialization."""
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class Calendar(Base):
    """
    Represents a calendar that can be internal or external (Google, Outlook, etc.)
    """
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # External integration details
    provider = Column(Enum(CalendarProvider), default=CalendarProvider.INTERNAL)
    external_calendar_id = Column(String(255))  # ID from external provider
    integration_id = Column(Integer, ForeignKey("calendar_integrations.id"))
    
    # Sync settings
    auto_sync_enabled = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=15)
    last_sync_at = Column(DateTime(timezone=True))
    sync_token = Column(String(500))  # For incremental sync
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendars")
    workspace = relationship("Workspace", back_populates="calendars")
    integration = relationship("CalendarIntegration", back_populates="calendars")
    events = relationship("CalendarEvent", back_populates="calendar", cascade="all, delete-orphan")
    shares = relationship("CalendarShare", back_populates="calendar", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Calendar(id={self.id}, name='{self.name}', provider={self.provider.value})>"

class CalendarIntegration(Base):
    """
    Stores OAuth tokens and settings for external calendar providers
    """
    __tablename__ = "calendar_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    provider = Column(Enum(CalendarProvider), nullable=False)
    provider_user_id = Column(String(255))  # User ID from the provider
    email = Column(String(255))  # Email associated with the account
    
    # OAuth tokens
    access_token = Column(Text)  # Encrypted access token
    refresh_token = Column(Text)  # Encrypted refresh token
    token_expires_at = Column(DateTime(timezone=True))
    scope = Column(String(500))  # OAuth scopes granted
    
    # Provider-specific settings
    settings = Column(JSONType)  # JSON field for provider-specific configs
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    sync_error_message = Column(Text)
    
    # Webhook settings
    webhook_url = Column(String(500))
    webhook_token = Column(String(255))
    webhook_expires_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_integrations")
    calendars = relationship("Calendar", back_populates="integration")
    
    # Unique constraint on user_id + provider
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uix_user_provider'),
    )
    
    def __repr__(self):
        return f"<CalendarIntegration(id={self.id}, provider={self.provider.value}, email='{self.email}')>"

class CalendarEvent(Base):
    """
    Represents a calendar event that can be synced with external calendars
    """
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))  # Link to task if created from task
    
    # Basic event details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    location = Column(String(500))
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), default="UTC")
    is_all_day = Column(Boolean, default=False)
    
    # Status and visibility
    status = Column(Enum(CalendarEventStatus), default=CalendarEventStatus.CONFIRMED)
    visibility = Column(Enum(CalendarEventVisibility), default=CalendarEventVisibility.DEFAULT)
    
    # Recurrence
    recurrence_type = Column(Enum(CalendarEventRecurrenceType), default=CalendarEventRecurrenceType.NONE)
    recurrence_rule = Column(Text)  # RRULE format
    recurrence_end_date = Column(DateTime(timezone=True))
    recurrence_count = Column(Integer)
    is_recurring_instance = Column(Boolean, default=False)
    recurring_event_id = Column(Integer, ForeignKey("calendar_events.id"))
    
    # External sync
    external_event_id = Column(String(255))  # ID from external provider
    external_sync_token = Column(String(255))
    last_synced_at = Column(DateTime(timezone=True))
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    
    # Meeting details
    meeting_url = Column(String(500))
    meeting_phone = Column(String(50))
    meeting_passcode = Column(String(50))
    
    # Reminders and notifications
    reminders = Column(JSONType)  # List of reminder settings
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    calendar = relationship("Calendar", back_populates="events")
    user = relationship("User", back_populates="calendar_events")
    task = relationship("Task", back_populates="calendar_event")
    attendees = relationship("CalendarEventAttendee", back_populates="event", cascade="all, delete-orphan")
    recurring_instances = relationship("CalendarEvent", backref="recurring_event", remote_side=[id])
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', start_time='{self.start_time}')>"

class CalendarEventAttendee(Base):
    """
    Represents attendees for calendar events
    """
    __tablename__ = "calendar_event_attendees"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=False)
    
    email = Column(String(255), nullable=False)
    name = Column(String(200))
    response_status = Column(String(20), default="needsAction")  # needsAction, accepted, declined, tentative
    is_organizer = Column(Boolean, default=False)
    is_resource = Column(Boolean, default=False)  # Meeting room, equipment, etc.
    
    # Internal user mapping
    user_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    event = relationship("CalendarEvent", back_populates="attendees")
    user = relationship("User", back_populates="calendar_attendees")
    
    def __repr__(self):
        return f"<CalendarEventAttendee(id={self.id}, email='{self.email}', status='{self.response_status}')>"

class CalendarShare(Base):
    """
    Represents calendar sharing permissions within workspaces
    """
    __tablename__ = "calendar_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User being shared with
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who shared
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    
    permission = Column(Enum(CalendarSharePermission), default=CalendarSharePermission.READ)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    calendar = relationship("Calendar", back_populates="shares")
    user = relationship("User", foreign_keys=[user_id], back_populates="calendar_shares_received")
    shared_by = relationship("User", foreign_keys=[shared_by_user_id], back_populates="calendar_shares_given")
    workspace = relationship("Workspace", back_populates="calendar_shares")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('calendar_id', 'user_id', name='uix_calendar_user_share'),
    )
    
    def __repr__(self):
        return f"<CalendarShare(id={self.id}, calendar_id={self.calendar_id}, permission={self.permission.value})>"

class CalendarConflict(Base):
    """
    Tracks calendar conflicts and their resolution status
    """
    __tablename__ = "calendar_conflicts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Conflicting events
    event1_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=False)
    event2_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=False)
    
    conflict_type = Column(String(50))  # "overlap", "double_booking", "resource_conflict"
    severity = Column(String(20), default="medium")  # "low", "medium", "high"
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolution_type = Column(String(50))  # "ignore", "reschedule", "cancel", "merge"
    resolution_notes = Column(Text)
    resolved_by_user_id = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="calendar_conflicts")
    event1 = relationship("CalendarEvent", foreign_keys=[event1_id])
    event2 = relationship("CalendarEvent", foreign_keys=[event2_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])
    
    def __repr__(self):
        return f"<CalendarConflict(id={self.id}, type='{self.conflict_type}', resolved={self.is_resolved})>"

class CalendarSyncLog(Base):
    """
    Logs calendar synchronization operations for debugging and analytics
    """
    __tablename__ = "calendar_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("calendar_integrations.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    sync_type = Column(String(50))  # "full", "incremental", "webhook"
    direction = Column(String(20))  # "import", "export", "bidirectional"
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    
    # Sync statistics
    events_processed = Column(Integer, default=0)
    events_created = Column(Integer, default=0)
    events_updated = Column(Integer, default=0)
    events_deleted = Column(Integer, default=0)
    conflicts_detected = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSONType)
    
    # Relationships
    calendar = relationship("Calendar")
    integration = relationship("CalendarIntegration")
    user = relationship("User", back_populates="calendar_sync_logs")
    
    def __repr__(self):
        return f"<CalendarSyncLog(id={self.id}, status={self.status.value}, events_processed={self.events_processed})>"

class TimeBlock(Base):
    """
    Represents time blocks for task scheduling and time management
    """
    __tablename__ = "time_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    calendar_id = Column(Integer, ForeignKey("calendars.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    
    title = Column(String(200), nullable=False)
    description = Column(Text)
    color = Column(String(7))
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), default="UTC")
    
    # Type and status
    block_type = Column(String(50), default="work")  # "work", "break", "focus", "meeting", "travel"
    is_flexible = Column(Boolean, default=False)  # Can be moved if conflicts arise
    priority = Column(Integer, default=50)  # 1-100 priority for scheduling
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="time_blocks")
    calendar = relationship("Calendar")
    task = relationship("Task", back_populates="time_blocks")
    
    def __repr__(self):
        return f"<TimeBlock(id={self.id}, title='{self.title}', type='{self.block_type}')>"