"""
Pydantic schemas for calendar data validation and serialization
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

from src.backend.models.calendar import (
    CalendarProvider, CalendarEventStatus, CalendarEventVisibility,
    CalendarEventRecurrenceType, CalendarSharePermission, SyncStatus
)

# Base schemas
class CalendarProviderEnum(str, Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    APPLE = "APPLE"
    INTERNAL = "INTERNAL"

class CalendarEventStatusEnum(str, Enum):
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"

class CalendarEventVisibilityEnum(str, Enum):
    DEFAULT = "DEFAULT"
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    CONFIDENTIAL = "CONFIDENTIAL"

class CalendarEventRecurrenceTypeEnum(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"

class CalendarSharePermissionEnum(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"

class SyncStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CONFLICT = "CONFLICT"

# Calendar Integration schemas
class CalendarIntegrationBase(BaseModel):
    provider: CalendarProviderEnum
    email: Optional[str] = None
    is_active: bool = True

class CalendarIntegrationCreate(CalendarIntegrationBase):
    pass

class CalendarIntegrationUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None

class CalendarIntegration(CalendarIntegrationBase):
    id: int
    user_id: int
    provider_user_id: Optional[str] = None
    scope: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    sync_status: SyncStatusEnum
    sync_error_message: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Calendar schemas
class CalendarBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    timezone: str = "UTC"
    is_active: bool = True
    is_primary: bool = False
    is_public: bool = False

class CalendarCreate(CalendarBase):
    workspace_id: Optional[int] = None
    provider: CalendarProviderEnum = CalendarProviderEnum.INTERNAL
    external_calendar_id: Optional[str] = None
    integration_id: Optional[int] = None

class CalendarUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    is_public: Optional[bool] = None
    auto_sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = Field(None, ge=5, le=1440)

class Calendar(CalendarBase):
    id: int
    user_id: int
    workspace_id: Optional[int] = None
    provider: CalendarProviderEnum
    external_calendar_id: Optional[str] = None
    integration_id: Optional[int] = None
    auto_sync_enabled: bool
    sync_interval_minutes: int
    last_sync_at: Optional[datetime] = None
    sync_token: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Event Attendee schemas
class CalendarEventAttendeeBase(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    name: Optional[str] = None
    response_status: str = "needsAction"
    is_organizer: bool = False
    is_resource: bool = False

class CalendarEventAttendeeCreate(CalendarEventAttendeeBase):
    pass

class CalendarEventAttendeeUpdate(BaseModel):
    name: Optional[str] = None
    response_status: Optional[str] = None
    is_organizer: Optional[bool] = None
    is_resource: Optional[bool] = None

class CalendarEventAttendee(CalendarEventAttendeeBase):
    id: int
    event_id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Reminder schema
class ReminderSchema(BaseModel):
    method: str = "popup"  # popup, email, sms
    minutes: int = Field(..., ge=0, le=40320)  # Max 4 weeks

# Calendar Event schemas
class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    is_all_day: bool = False
    status: CalendarEventStatusEnum = CalendarEventStatusEnum.CONFIRMED
    visibility: CalendarEventVisibilityEnum = CalendarEventVisibilityEnum.DEFAULT

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class CalendarEventCreate(CalendarEventBase):
    calendar_id: int
    task_id: Optional[int] = None
    recurrence_type: CalendarEventRecurrenceTypeEnum = CalendarEventRecurrenceTypeEnum.NONE
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = Field(None, ge=1, le=999)
    meeting_url: Optional[str] = None
    meeting_phone: Optional[str] = None
    meeting_passcode: Optional[str] = None
    reminders: Optional[List[ReminderSchema]] = []
    attendees: Optional[List[CalendarEventAttendeeCreate]] = []

    @root_validator(skip_on_failure=True)
    def validate_recurrence(cls, values):
        recurrence_type = values.get('recurrence_type')
        recurrence_rule = values.get('recurrence_rule')
        recurrence_end_date = values.get('recurrence_end_date')
        recurrence_count = values.get('recurrence_count')
        
        if recurrence_type != CalendarEventRecurrenceTypeEnum.NONE:
            if recurrence_type == CalendarEventRecurrenceTypeEnum.CUSTOM and not recurrence_rule:
                raise ValueError('Recurrence rule required for custom recurrence')
            
            if recurrence_end_date and recurrence_count:
                raise ValueError('Cannot specify both recurrence end date and count')
        
        return values

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    is_all_day: Optional[bool] = None
    status: Optional[CalendarEventStatusEnum] = None
    visibility: Optional[CalendarEventVisibilityEnum] = None
    recurrence_type: Optional[CalendarEventRecurrenceTypeEnum] = None
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = Field(None, ge=1, le=999)
    meeting_url: Optional[str] = None
    meeting_phone: Optional[str] = None
    meeting_passcode: Optional[str] = None
    reminders: Optional[List[ReminderSchema]] = None

    @root_validator(skip_on_failure=True)
    def validate_times(cls, values):
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise ValueError('End time must be after start time')
        
        return values

class CalendarEvent(CalendarEventBase):
    id: int
    calendar_id: int
    user_id: int
    task_id: Optional[int] = None
    recurrence_type: CalendarEventRecurrenceTypeEnum
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = None
    is_recurring_instance: bool = False
    recurring_event_id: Optional[int] = None
    external_event_id: Optional[str] = None
    external_sync_token: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    sync_status: SyncStatusEnum
    meeting_url: Optional[str] = None
    meeting_phone: Optional[str] = None
    meeting_passcode: Optional[str] = None
    reminders: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    attendees: Optional[List[CalendarEventAttendee]] = []

    class Config:
        from_attributes = True

# Calendar Share schemas
class CalendarShareBase(BaseModel):
    permission: CalendarSharePermissionEnum = CalendarSharePermissionEnum.READ
    is_active: bool = True

class CalendarShareCreate(CalendarShareBase):
    calendar_id: int
    user_id: int
    workspace_id: Optional[int] = None

class CalendarShareUpdate(BaseModel):
    permission: Optional[CalendarSharePermissionEnum] = None
    is_active: Optional[bool] = None

class CalendarShare(CalendarShareBase):
    id: int
    calendar_id: int
    user_id: int
    shared_by_user_id: int
    workspace_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Calendar Conflict schemas
class CalendarConflictBase(BaseModel):
    conflict_type: str
    severity: str = "medium"

class CalendarConflict(CalendarConflictBase):
    id: int
    user_id: int
    event1_id: int
    event2_id: int
    is_resolved: bool = False
    resolution_type: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConflictResolution(BaseModel):
    resolution_type: str = Field(..., pattern=r'^(ignore|reschedule|cancel|merge)$')
    resolution_notes: Optional[str] = None

# Time Block schemas
class TimeBlockBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    block_type: str = "work"
    is_flexible: bool = False
    priority: int = Field(50, ge=1, le=100)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class TimeBlockCreate(TimeBlockBase):
    calendar_id: Optional[int] = None
    task_id: Optional[int] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None

class TimeBlockUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    block_type: Optional[str] = None
    is_flexible: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None

class TimeBlock(TimeBlockBase):
    id: int
    user_id: int
    calendar_id: Optional[int] = None
    task_id: Optional[int] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Sync Log schemas
class CalendarSyncLog(BaseModel):
    id: int
    calendar_id: int
    integration_id: Optional[int] = None
    user_id: int
    sync_type: str
    direction: str
    status: SyncStatusEnum
    events_processed: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    conflicts_detected: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# API Response schemas
class CalendarSyncResult(BaseModel):
    calendars_synced: int = 0
    events_processed: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    conflicts_detected: int = 0
    errors: List[str] = []

class ConflictSuggestion(BaseModel):
    type: str
    title: str
    description: str
    confidence: float = Field(..., ge=0, le=1)
    details: Optional[Dict[str, Any]] = None

class FreeBusyInfo(BaseModel):
    calendar_id: str
    busy_periods: List[Dict[str, datetime]] = []
    errors: List[str] = []

class MeetingTimeSlot(BaseModel):
    start: datetime
    end: datetime
    confidence: Optional[float] = None
    attendee_availability: Optional[Dict[str, str]] = None

class CalendarAnalytics(BaseModel):
    total_events: int = 0
    events_this_week: int = 0
    events_this_month: int = 0
    average_event_duration: Optional[float] = None
    busiest_day_of_week: Optional[str] = None
    busiest_hour_of_day: Optional[int] = None
    event_types: Dict[str, int] = {}
    time_utilization: float = 0.0

# OAuth schemas
class OAuthAuthorizationURL(BaseModel):
    authorization_url: str
    state: str

class OAuthCallback(BaseModel):
    code: str
    state: str

# Bulk operation schemas
class BulkEventOperation(BaseModel):
    event_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., pattern=r'^(delete|update|reschedule)$')
    data: Optional[Dict[str, Any]] = None

class BulkEventResult(BaseModel):
    successful: List[int] = []
    failed: List[Dict[str, Any]] = []
    total_processed: int = 0

# Search and filter schemas
class CalendarEventFilter(BaseModel):
    calendar_ids: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[List[CalendarEventStatusEnum]] = None
    search_query: Optional[str] = None
    attendee_email: Optional[str] = None
    location: Optional[str] = None
    has_conflicts: Optional[bool] = None

class CalendarEventList(BaseModel):
    events: List[CalendarEvent]
    total_count: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False

# ICS Export schema
class ICSExportRequest(BaseModel):
    calendar_ids: Optional[List[int]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_private: bool = False

# Timezone schema
class TimezoneInfo(BaseModel):
    timezone: str
    offset: str
    dst_active: bool
    display_name: str