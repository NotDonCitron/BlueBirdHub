"""
Comprehensive calendar API endpoints for BlueBirdHub
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from src.backend.database.database import get_db
from src.backend.dependencies.auth import get_current_user
from src.backend.models.user import User
from src.backend.models.calendar import CalendarProvider
from src.backend.schemas.calendar import (
    Calendar, CalendarCreate, CalendarUpdate,
    CalendarEvent, CalendarEventCreate, CalendarEventUpdate, CalendarEventList, CalendarEventFilter,
    CalendarIntegration, CalendarIntegrationCreate, CalendarIntegrationUpdate,
    CalendarShare, CalendarShareCreate, CalendarShareUpdate,
    CalendarConflict, ConflictResolution, ConflictSuggestion,
    TimeBlock, TimeBlockCreate, TimeBlockUpdate,
    CalendarSyncResult, CalendarSyncLog,
    OAuthAuthorizationURL, OAuthCallback,
    FreeBusyInfo, MeetingTimeSlot,
    BulkEventOperation, BulkEventResult,
    ICSExportRequest, TimezoneInfo, CalendarAnalytics
)
from src.backend.services.oauth_service import oauth_service
from src.backend.services.calendar_sync_service import calendar_sync_service
from src.backend.services.conflict_detection_service import ConflictDetectionService
from src.backend.crud.crud_calendar import calendar_crud

router = APIRouter(prefix="/calendar", tags=["calendar"])
logger = logging.getLogger(__name__)

conflict_service = ConflictDetectionService()

# OAuth Integration Endpoints
@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizationURL)
async def get_oauth_authorization_url(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Get OAuth authorization URL for calendar provider"""
    try:
        provider_enum = CalendarProvider(provider.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )
    
    auth_url = oauth_service.get_auth_url(current_user.id, provider_enum)
    state = oauth_service.generate_state_token(current_user.id, provider_enum)
    
    return OAuthAuthorizationURL(authorization_url=auth_url, state=state)

@router.post("/oauth/{provider}/callback", response_model=CalendarIntegration)
async def handle_oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    current_user: User = Depends(get_current_user)
):
    """Handle OAuth callback from calendar provider"""
    try:
        provider_enum = CalendarProvider(provider.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )
    
    integration = oauth_service.handle_callback(
        provider_enum, callback_data.code, callback_data.state, current_user.id
    )
    
    return integration

# Calendar Integration Management
@router.get("/integrations", response_model=List[CalendarIntegration])
async def get_calendar_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all calendar integrations for user"""
    return calendar_crud.get_user_integrations(db, current_user.id)

@router.get("/integrations/{integration_id}", response_model=CalendarIntegration)
async def get_calendar_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific calendar integration"""
    integration = calendar_crud.get_integration(db, integration_id)
    if not integration or integration.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    return integration

@router.put("/integrations/{integration_id}", response_model=CalendarIntegration)
async def update_calendar_integration(
    integration_id: int,
    integration_update: CalendarIntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update calendar integration"""
    integration = calendar_crud.get_integration(db, integration_id)
    if not integration or integration.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return calendar_crud.update_integration(db, integration_id, integration_update)

@router.delete("/integrations/{integration_id}")
async def delete_calendar_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete calendar integration and revoke OAuth tokens"""
    integration = calendar_crud.get_integration(db, integration_id)
    if not integration or integration.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Revoke OAuth tokens
    oauth_service.revoke_integration(integration)
    
    # Delete integration
    calendar_crud.delete_integration(db, integration_id)
    
    return {"message": "Integration deleted successfully"}

# Calendar Management
@router.get("/calendars", response_model=List[Calendar])
async def get_calendars(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: Optional[int] = Query(None)
):
    """Get all calendars for user"""
    return calendar_crud.get_user_calendars(db, current_user.id, workspace_id)

@router.post("/calendars", response_model=Calendar)
async def create_calendar(
    calendar_data: CalendarCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new calendar"""
    return calendar_crud.create_calendar(db, calendar_data, current_user.id)

@router.get("/calendars/{calendar_id}", response_model=Calendar)
async def get_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific calendar"""
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    return calendar

@router.put("/calendars/{calendar_id}", response_model=Calendar)
async def update_calendar(
    calendar_id: int,
    calendar_update: CalendarUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update calendar"""
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    return calendar_crud.update_calendar(db, calendar_id, calendar_update)

@router.delete("/calendars/{calendar_id}")
async def delete_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete calendar"""
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    calendar_crud.delete_calendar(db, calendar_id)
    return {"message": "Calendar deleted successfully"}

# Calendar Events
@router.get("/events", response_model=CalendarEventList)
async def get_calendar_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    calendar_ids: Optional[List[int]] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[List[str]] = Query(None),
    search_query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000)
):
    """Get calendar events with filtering and pagination"""
    filter_params = CalendarEventFilter(
        calendar_ids=calendar_ids,
        start_date=start_date,
        end_date=end_date,
        status=status,
        search_query=search_query
    )
    
    return calendar_crud.get_events(db, current_user.id, filter_params, page, page_size)

@router.post("/events", response_model=CalendarEvent)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new calendar event"""
    # Verify calendar ownership
    calendar = calendar_crud.get_calendar(db, event_data.calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    event = calendar_crud.create_event(db, event_data, current_user.id)
    
    # Schedule background sync if external calendar
    if calendar.provider != CalendarProvider.INTERNAL:
        background_tasks.add_task(
            calendar_sync_service.sync_calendar, 
            calendar, 
            force_full_sync=False
        )
    
    return event

@router.get("/events/{event_id}", response_model=CalendarEvent)
async def get_calendar_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific calendar event"""
    event = calendar_crud.get_event(db, event_id)
    if not event or event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event

@router.put("/events/{event_id}", response_model=CalendarEvent)
async def update_calendar_event(
    event_id: int,
    event_update: CalendarEventUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update calendar event"""
    event = calendar_crud.get_event(db, event_id)
    if not event or event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    updated_event = calendar_crud.update_event(db, event_id, event_update)
    
    # Schedule background sync if external calendar
    calendar = calendar_crud.get_calendar(db, event.calendar_id)
    if calendar and calendar.provider != CalendarProvider.INTERNAL:
        background_tasks.add_task(
            calendar_sync_service.sync_calendar, 
            calendar, 
            force_full_sync=False
        )
    
    return updated_event

@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete calendar event"""
    event = calendar_crud.get_event(db, event_id)
    if not event or event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    calendar = calendar_crud.get_calendar(db, event.calendar_id)
    calendar_crud.delete_event(db, event_id)
    
    # Schedule background sync if external calendar
    if calendar and calendar.provider != CalendarProvider.INTERNAL:
        background_tasks.add_task(
            calendar_sync_service.sync_calendar, 
            calendar, 
            force_full_sync=False
        )
    
    return {"message": "Event deleted successfully"}

# Bulk Operations
@router.post("/events/bulk", response_model=BulkEventResult)
async def bulk_event_operation(
    bulk_operation: BulkEventOperation,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform bulk operations on calendar events"""
    return calendar_crud.bulk_event_operation(db, bulk_operation, current_user.id, background_tasks)

# Calendar Synchronization
@router.post("/sync", response_model=CalendarSyncResult)
async def sync_all_calendars(
    force_full_sync: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Sync all user calendars with external providers"""
    return calendar_sync_service.sync_all_user_calendars(current_user.id, force_full_sync)

@router.post("/calendars/{calendar_id}/sync", response_model=Dict[str, Any])
async def sync_calendar(
    calendar_id: int,
    force_full_sync: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync specific calendar with external provider"""
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    return calendar_sync_service.sync_calendar(calendar, force_full_sync)

@router.get("/sync/logs", response_model=List[CalendarSyncLog])
async def get_sync_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    calendar_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500)
):
    """Get calendar sync logs"""
    return calendar_crud.get_sync_logs(db, current_user.id, calendar_id, limit)

# Task-Event Integration
@router.post("/tasks/{task_id}/create-event", response_model=CalendarEvent)
async def create_event_from_task(
    task_id: int,
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create calendar event from task"""
    # Verify calendar ownership
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    event = calendar_sync_service.create_event_from_task(task_id, calendar_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create event from task"
        )
    
    return event

# Calendar Sharing
@router.get("/calendars/{calendar_id}/shares", response_model=List[CalendarShare])
async def get_calendar_shares(
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calendar sharing information"""
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    return calendar_crud.get_calendar_shares(db, calendar_id)

@router.post("/calendars/{calendar_id}/shares", response_model=CalendarShare)
async def share_calendar(
    calendar_id: int,
    share_data: CalendarShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share calendar with another user"""
    calendar = calendar_crud.get_calendar(db, calendar_id)
    if not calendar or calendar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )
    
    share_data.calendar_id = calendar_id
    return calendar_crud.create_calendar_share(db, share_data, current_user.id)

@router.put("/shares/{share_id}", response_model=CalendarShare)
async def update_calendar_share(
    share_id: int,
    share_update: CalendarShareUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update calendar share permissions"""
    share = calendar_crud.get_calendar_share(db, share_id)
    if not share or share.shared_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    return calendar_crud.update_calendar_share(db, share_id, share_update)

@router.delete("/shares/{share_id}")
async def delete_calendar_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove calendar share"""
    share = calendar_crud.get_calendar_share(db, share_id)
    if not share or share.shared_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    calendar_crud.delete_calendar_share(db, share_id)
    return {"message": "Calendar share removed successfully"}

# Conflict Detection and Resolution
@router.get("/conflicts", response_model=List[CalendarConflict])
async def get_calendar_conflicts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    calendar_id: Optional[int] = Query(None),
    include_resolved: bool = Query(False)
):
    """Get calendar conflicts for user"""
    if calendar_id:
        # Verify calendar ownership
        calendar = calendar_crud.get_calendar(db, calendar_id)
        if not calendar or calendar.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar not found"
            )
    
    return conflict_service.get_conflicts_for_user(current_user.id, include_resolved)

@router.post("/conflicts/detect", response_model=List[CalendarConflict])
async def detect_calendar_conflicts(
    current_user: User = Depends(get_current_user),
    calendar_id: Optional[int] = Query(None)
):
    """Detect calendar conflicts for user"""
    return conflict_service.detect_calendar_conflicts(current_user.id, calendar_id)

@router.get("/conflicts/{conflict_id}/suggestions", response_model=List[ConflictSuggestion])
async def get_conflict_suggestions(
    conflict_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resolution suggestions for a conflict"""
    conflict = calendar_crud.get_conflict(db, conflict_id)
    if not conflict or conflict.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict not found"
        )
    
    return conflict_service.suggest_conflict_resolution(conflict_id)

@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_calendar_conflict(
    conflict_id: int,
    resolution: ConflictResolution,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a calendar conflict"""
    conflict = calendar_crud.get_conflict(db, conflict_id)
    if not conflict or conflict.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict not found"
        )
    
    success = conflict_service.resolve_conflict(
        conflict_id, 
        resolution.resolution_type, 
        resolution.resolution_notes or "",
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resolve conflict"
        )
    
    return {"message": "Conflict resolved successfully"}

# Time Blocking
@router.get("/time-blocks", response_model=List[TimeBlock])
async def get_time_blocks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    block_type: Optional[str] = Query(None)
):
    """Get time blocks for user"""
    return calendar_crud.get_time_blocks(db, current_user.id, start_date, end_date, block_type)

@router.post("/time-blocks", response_model=TimeBlock)
async def create_time_block(
    block_data: TimeBlockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new time block"""
    return calendar_crud.create_time_block(db, block_data, current_user.id)

@router.put("/time-blocks/{block_id}", response_model=TimeBlock)
async def update_time_block(
    block_id: int,
    block_update: TimeBlockUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update time block"""
    block = calendar_crud.get_time_block(db, block_id)
    if not block or block.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time block not found"
        )
    
    return calendar_crud.update_time_block(db, block_id, block_update)

@router.delete("/time-blocks/{block_id}")
async def delete_time_block(
    block_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete time block"""
    block = calendar_crud.get_time_block(db, block_id)
    if not block or block.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time block not found"
        )
    
    calendar_crud.delete_time_block(db, block_id)
    return {"message": "Time block deleted successfully"}

# Free/Busy and Meeting Scheduling
@router.post("/free-busy", response_model=List[FreeBusyInfo])
async def get_free_busy_info(
    calendar_ids: List[int],
    start_time: datetime,
    end_time: datetime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get free/busy information for calendars"""
    # Verify calendar access
    for calendar_id in calendar_ids:
        calendar = calendar_crud.get_calendar(db, calendar_id)
        if not calendar or (calendar.user_id != current_user.id and 
                          not calendar_crud.has_calendar_access(db, calendar_id, current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to calendar {calendar_id}"
            )
    
    return calendar_crud.get_free_busy_info(db, calendar_ids, start_time, end_time)

@router.post("/find-meeting-times", response_model=List[MeetingTimeSlot])
async def find_meeting_times(
    attendee_emails: List[str],
    duration_minutes: int,
    start_time: datetime,
    end_time: datetime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find available meeting times for attendees"""
    return calendar_crud.find_meeting_times(
        db, attendee_emails, duration_minutes, start_time, end_time, current_user.id
    )

# Analytics and Insights
@router.get("/analytics", response_model=CalendarAnalytics)
async def get_calendar_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    calendar_ids: Optional[List[int]] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get calendar analytics and insights"""
    return calendar_crud.get_calendar_analytics(db, current_user.id, calendar_ids, start_date, end_date)

# ICS Export
@router.post("/export/ics")
async def export_calendar_ics(
    export_request: ICSExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export calendar events to ICS format"""
    ics_content = calendar_crud.export_to_ics(db, export_request, current_user.id)
    
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=calendar.ics"}
    )

# Timezone Utilities
@router.get("/timezones", response_model=List[TimezoneInfo])
async def get_available_timezones():
    """Get list of available timezones"""
    return calendar_crud.get_available_timezones()

@router.post("/convert-timezone")
async def convert_timezone(
    datetime_str: str,
    from_timezone: str,
    to_timezone: str
):
    """Convert datetime between timezones"""
    return calendar_crud.convert_timezone(datetime_str, from_timezone, to_timezone)

# Webhook Endpoints
@router.post("/webhook/google")
async def google_calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle Google Calendar webhook notifications"""
    # Implementation would go here
    # This is a placeholder for the webhook handler
    return {"message": "Webhook received"}

@router.post("/webhook/microsoft")
async def microsoft_calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle Microsoft Graph webhook notifications"""
    # Implementation would go here
    # This is a placeholder for the webhook handler
    return {"message": "Webhook received"}

# Health Check
@router.get("/health")
async def calendar_health_check():
    """Health check for calendar service"""
    return {
        "status": "healthy",
        "service": "calendar",
        "timestamp": datetime.utcnow().isoformat()
    }