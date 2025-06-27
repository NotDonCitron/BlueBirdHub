"""
CRUD operations for calendar entities
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import BackgroundTasks
import pytz
from icalendar import Calendar as ICalendar, Event as ICalEvent
import uuid

from src.backend.models.calendar import (
    Calendar, CalendarEvent, CalendarIntegration, CalendarShare, 
    CalendarConflict, CalendarSyncLog, TimeBlock, CalendarEventAttendee,
    CalendarProvider, CalendarEventStatus, SyncStatus
)
from src.backend.models.task import Task
from src.backend.models.user import User
from src.backend.schemas.calendar import (
    CalendarCreate, CalendarUpdate, CalendarEventCreate, CalendarEventUpdate,
    CalendarIntegrationCreate, CalendarIntegrationUpdate,
    CalendarShareCreate, CalendarShareUpdate,
    TimeBlockCreate, TimeBlockUpdate,
    CalendarEventFilter, CalendarEventList,
    BulkEventOperation, BulkEventResult,
    FreeBusyInfo, MeetingTimeSlot, CalendarAnalytics,
    ICSExportRequest, TimezoneInfo
)

logger = logging.getLogger(__name__)

class CalendarCRUD:
    """CRUD operations for calendar management"""
    
    # Calendar Integration Operations
    def get_user_integrations(self, db: Session, user_id: int) -> List[CalendarIntegration]:
        """Get all calendar integrations for a user"""
        return db.query(CalendarIntegration).filter(
            CalendarIntegration.user_id == user_id
        ).order_by(CalendarIntegration.created_at.desc()).all()
    
    def get_integration(self, db: Session, integration_id: int) -> Optional[CalendarIntegration]:
        """Get calendar integration by ID"""
        return db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id
        ).first()
    
    def create_integration(self, db: Session, integration_data: CalendarIntegrationCreate, user_id: int) -> CalendarIntegration:
        """Create new calendar integration"""
        integration = CalendarIntegration(
            user_id=user_id,
            **integration_data.dict()
        )
        db.add(integration)
        db.commit()
        db.refresh(integration)
        return integration
    
    def update_integration(self, db: Session, integration_id: int, integration_update: CalendarIntegrationUpdate) -> CalendarIntegration:
        """Update calendar integration"""
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id
        ).first()
        
        if integration:
            update_data = integration_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(integration, field, value)
            
            db.commit()
            db.refresh(integration)
        
        return integration
    
    def delete_integration(self, db: Session, integration_id: int) -> bool:
        """Delete calendar integration"""
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id
        ).first()
        
        if integration:
            db.delete(integration)
            db.commit()
            return True
        
        return False
    
    # Calendar Operations
    def get_user_calendars(self, db: Session, user_id: int, workspace_id: Optional[int] = None) -> List[Calendar]:
        """Get all calendars for a user"""
        query = db.query(Calendar).filter(Calendar.user_id == user_id)
        
        if workspace_id:
            query = query.filter(Calendar.workspace_id == workspace_id)
        
        return query.order_by(Calendar.is_primary.desc(), Calendar.name).all()
    
    def get_calendar(self, db: Session, calendar_id: int) -> Optional[Calendar]:
        """Get calendar by ID"""
        return db.query(Calendar).filter(Calendar.id == calendar_id).first()
    
    def create_calendar(self, db: Session, calendar_data: CalendarCreate, user_id: int) -> Calendar:
        """Create new calendar"""
        calendar = Calendar(
            user_id=user_id,
            **calendar_data.dict()
        )
        db.add(calendar)
        db.commit()
        db.refresh(calendar)
        return calendar
    
    def update_calendar(self, db: Session, calendar_id: int, calendar_update: CalendarUpdate) -> Calendar:
        """Update calendar"""
        calendar = db.query(Calendar).filter(Calendar.id == calendar_id).first()
        
        if calendar:
            update_data = calendar_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(calendar, field, value)
            
            db.commit()
            db.refresh(calendar)
        
        return calendar
    
    def delete_calendar(self, db: Session, calendar_id: int) -> bool:
        """Delete calendar"""
        calendar = db.query(Calendar).filter(Calendar.id == calendar_id).first()
        
        if calendar:
            db.delete(calendar)
            db.commit()
            return True
        
        return False
    
    # Calendar Event Operations
    def get_events(self, db: Session, user_id: int, filter_params: CalendarEventFilter, 
                  page: int = 1, page_size: int = 50) -> CalendarEventList:
        """Get calendar events with filtering and pagination"""
        query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)
        
        # Apply filters
        if filter_params.calendar_ids:
            query = query.filter(CalendarEvent.calendar_id.in_(filter_params.calendar_ids))
        
        if filter_params.start_date:
            start_datetime = datetime.combine(filter_params.start_date, datetime.min.time())
            query = query.filter(CalendarEvent.start_time >= start_datetime)
        
        if filter_params.end_date:
            end_datetime = datetime.combine(filter_params.end_date, datetime.max.time())
            query = query.filter(CalendarEvent.end_time <= end_datetime)
        
        if filter_params.status:
            query = query.filter(CalendarEvent.status.in_(filter_params.status))
        
        if filter_params.search_query:
            search_term = f"%{filter_params.search_query}%"
            query = query.filter(
                or_(
                    CalendarEvent.title.ilike(search_term),
                    CalendarEvent.description.ilike(search_term),
                    CalendarEvent.location.ilike(search_term)
                )
            )
        
        if filter_params.attendee_email:
            # Join with attendees table
            query = query.join(CalendarEvent.attendees).filter(
                CalendarEventAttendee.email == filter_params.attendee_email
            )
        
        if filter_params.location:
            query = query.filter(CalendarEvent.location.ilike(f"%{filter_params.location}%"))
        
        if filter_params.has_conflicts is not None:
            if filter_params.has_conflicts:
                # Events that have conflicts
                conflict_event_ids = db.query(CalendarConflict.event1_id).union(
                    db.query(CalendarConflict.event2_id)
                ).filter(CalendarConflict.is_resolved == False).subquery()
                query = query.filter(CalendarEvent.id.in_(conflict_event_ids))
            else:
                # Events without conflicts
                conflict_event_ids = db.query(CalendarConflict.event1_id).union(
                    db.query(CalendarConflict.event2_id)
                ).filter(CalendarConflict.is_resolved == False).subquery()
                query = query.filter(~CalendarEvent.id.in_(conflict_event_ids))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        events = query.order_by(CalendarEvent.start_time).offset(offset).limit(page_size).all()
        
        return CalendarEventList(
            events=events,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=total_count > (page * page_size)
        )
    
    def get_event(self, db: Session, event_id: int) -> Optional[CalendarEvent]:
        """Get calendar event by ID"""
        return db.query(CalendarEvent).options(
            joinedload(CalendarEvent.attendees)
        ).filter(CalendarEvent.id == event_id).first()
    
    def create_event(self, db: Session, event_data: CalendarEventCreate, user_id: int) -> CalendarEvent:
        """Create new calendar event"""
        # Create the event
        event_dict = event_data.dict(exclude={'attendees'})
        event = CalendarEvent(
            user_id=user_id,
            **event_dict
        )
        db.add(event)
        db.flush()  # Get the event ID
        
        # Add attendees if provided
        if event_data.attendees:
            for attendee_data in event_data.attendees:
                attendee = CalendarEventAttendee(
                    event_id=event.id,
                    **attendee_data.dict()
                )
                db.add(attendee)
        
        db.commit()
        db.refresh(event)
        return event
    
    def update_event(self, db: Session, event_id: int, event_update: CalendarEventUpdate) -> CalendarEvent:
        """Update calendar event"""
        event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        
        if event:
            update_data = event_update.dict(exclude_unset=True, exclude={'attendees'})
            for field, value in update_data.items():
                setattr(event, field, value)
            
            event.sync_status = SyncStatus.PENDING  # Mark for sync
            
            db.commit()
            db.refresh(event)
        
        return event
    
    def delete_event(self, db: Session, event_id: int) -> bool:
        """Delete calendar event"""
        event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        
        if event:
            db.delete(event)
            db.commit()
            return True
        
        return False
    
    def bulk_event_operation(self, db: Session, bulk_operation: BulkEventOperation, 
                           user_id: int, background_tasks: BackgroundTasks) -> BulkEventResult:
        """Perform bulk operations on calendar events"""
        result = BulkEventResult(total_processed=len(bulk_operation.event_ids))
        
        for event_id in bulk_operation.event_ids:
            try:
                event = db.query(CalendarEvent).filter(
                    CalendarEvent.id == event_id,
                    CalendarEvent.user_id == user_id
                ).first()
                
                if not event:
                    result.failed.append({
                        "event_id": event_id,
                        "error": "Event not found or access denied"
                    })
                    continue
                
                if bulk_operation.operation == "delete":
                    db.delete(event)
                    result.successful.append(event_id)
                
                elif bulk_operation.operation == "update":
                    if bulk_operation.data:
                        for field, value in bulk_operation.data.items():
                            if hasattr(event, field):
                                setattr(event, field, value)
                        event.sync_status = SyncStatus.PENDING
                        result.successful.append(event_id)
                
                elif bulk_operation.operation == "reschedule":
                    if bulk_operation.data and "time_offset_minutes" in bulk_operation.data:
                        offset = timedelta(minutes=bulk_operation.data["time_offset_minutes"])
                        event.start_time += offset
                        event.end_time += offset
                        event.sync_status = SyncStatus.PENDING
                        result.successful.append(event_id)
                
            except Exception as e:
                result.failed.append({
                    "event_id": event_id,
                    "error": str(e)
                })
        
        db.commit()
        return result
    
    # Calendar Sharing Operations
    def get_calendar_shares(self, db: Session, calendar_id: int) -> List[CalendarShare]:
        """Get all shares for a calendar"""
        return db.query(CalendarShare).filter(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.is_active == True
        ).all()
    
    def create_calendar_share(self, db: Session, share_data: CalendarShareCreate, shared_by_user_id: int) -> CalendarShare:
        """Share calendar with another user"""
        share = CalendarShare(
            shared_by_user_id=shared_by_user_id,
            **share_data.dict()
        )
        db.add(share)
        db.commit()
        db.refresh(share)
        return share
    
    def get_calendar_share(self, db: Session, share_id: int) -> Optional[CalendarShare]:
        """Get calendar share by ID"""
        return db.query(CalendarShare).filter(CalendarShare.id == share_id).first()
    
    def update_calendar_share(self, db: Session, share_id: int, share_update: CalendarShareUpdate) -> CalendarShare:
        """Update calendar share permissions"""
        share = db.query(CalendarShare).filter(CalendarShare.id == share_id).first()
        
        if share:
            update_data = share_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(share, field, value)
            
            db.commit()
            db.refresh(share)
        
        return share
    
    def delete_calendar_share(self, db: Session, share_id: int) -> bool:
        """Remove calendar share"""
        share = db.query(CalendarShare).filter(CalendarShare.id == share_id).first()
        
        if share:
            db.delete(share)
            db.commit()
            return True
        
        return False
    
    def has_calendar_access(self, db: Session, calendar_id: int, user_id: int) -> bool:
        """Check if user has access to calendar"""
        # Check if user owns the calendar
        calendar = db.query(Calendar).filter(
            Calendar.id == calendar_id,
            Calendar.user_id == user_id
        ).first()
        
        if calendar:
            return True
        
        # Check if calendar is shared with user
        share = db.query(CalendarShare).filter(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.user_id == user_id,
            CalendarShare.is_active == True
        ).first()
        
        return share is not None
    
    # Time Block Operations
    def get_time_blocks(self, db: Session, user_id: int, start_date: Optional[date] = None, 
                       end_date: Optional[date] = None, block_type: Optional[str] = None) -> List[TimeBlock]:
        """Get time blocks for user"""
        query = db.query(TimeBlock).filter(TimeBlock.user_id == user_id)
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(TimeBlock.start_time >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(TimeBlock.end_time <= end_datetime)
        
        if block_type:
            query = query.filter(TimeBlock.block_type == block_type)
        
        return query.order_by(TimeBlock.start_time).all()
    
    def get_time_block(self, db: Session, block_id: int) -> Optional[TimeBlock]:
        """Get time block by ID"""
        return db.query(TimeBlock).filter(TimeBlock.id == block_id).first()
    
    def create_time_block(self, db: Session, block_data: TimeBlockCreate, user_id: int) -> TimeBlock:
        """Create new time block"""
        block = TimeBlock(
            user_id=user_id,
            **block_data.dict()
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block
    
    def update_time_block(self, db: Session, block_id: int, block_update: TimeBlockUpdate) -> TimeBlock:
        """Update time block"""
        block = db.query(TimeBlock).filter(TimeBlock.id == block_id).first()
        
        if block:
            update_data = block_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(block, field, value)
            
            db.commit()
            db.refresh(block)
        
        return block
    
    def delete_time_block(self, db: Session, block_id: int) -> bool:
        """Delete time block"""
        block = db.query(TimeBlock).filter(TimeBlock.id == block_id).first()
        
        if block:
            db.delete(block)
            db.commit()
            return True
        
        return False
    
    # Sync Log Operations
    def get_sync_logs(self, db: Session, user_id: int, calendar_id: Optional[int] = None, 
                     limit: int = 50) -> List[CalendarSyncLog]:
        """Get calendar sync logs"""
        query = db.query(CalendarSyncLog).filter(CalendarSyncLog.user_id == user_id)
        
        if calendar_id:
            query = query.filter(CalendarSyncLog.calendar_id == calendar_id)
        
        return query.order_by(CalendarSyncLog.started_at.desc()).limit(limit).all()
    
    def get_conflict(self, db: Session, conflict_id: int) -> Optional[CalendarConflict]:
        """Get calendar conflict by ID"""
        return db.query(CalendarConflict).filter(CalendarConflict.id == conflict_id).first()
    
    # Free/Busy and Meeting Scheduling
    def get_free_busy_info(self, db: Session, calendar_ids: List[int], 
                          start_time: datetime, end_time: datetime) -> List[FreeBusyInfo]:
        """Get free/busy information for calendars"""
        results = []
        
        for calendar_id in calendar_ids:
            busy_periods = []
            
            # Get events that overlap with the requested time range
            events = db.query(CalendarEvent).filter(
                CalendarEvent.calendar_id == calendar_id,
                CalendarEvent.status == CalendarEventStatus.CONFIRMED,
                CalendarEvent.start_time < end_time,
                CalendarEvent.end_time > start_time
            ).all()
            
            for event in events:
                busy_periods.append({
                    "start": max(event.start_time, start_time),
                    "end": min(event.end_time, end_time)
                })
            
            results.append(FreeBusyInfo(
                calendar_id=str(calendar_id),
                busy_periods=busy_periods
            ))
        
        return results
    
    def find_meeting_times(self, db: Session, attendee_emails: List[str], duration_minutes: int,
                          start_time: datetime, end_time: datetime, user_id: int) -> List[MeetingTimeSlot]:
        """Find available meeting times"""
        # This is a simplified implementation
        # In production, you would integrate with external calendar APIs
        
        # Get all events for the time period
        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time < end_time,
            CalendarEvent.end_time > start_time,
            CalendarEvent.status == CalendarEventStatus.CONFIRMED
        ).order_by(CalendarEvent.start_time).all()
        
        # Find gaps between events
        available_slots = []
        current_time = start_time
        duration = timedelta(minutes=duration_minutes)
        
        for event in events:
            # Check if there's a gap before this event
            if current_time + duration <= event.start_time:
                available_slots.append(MeetingTimeSlot(
                    start=current_time,
                    end=current_time + duration,
                    confidence=0.8
                ))
            
            # Move to the end of this event
            current_time = max(current_time, event.end_time)
        
        # Check for slot after last event
        if current_time + duration <= end_time:
            available_slots.append(MeetingTimeSlot(
                start=current_time,
                end=current_time + duration,
                confidence=0.8
            ))
        
        return available_slots[:10]  # Return top 10 suggestions
    
    # Analytics
    def get_calendar_analytics(self, db: Session, user_id: int, calendar_ids: Optional[List[int]] = None,
                              start_date: Optional[date] = None, end_date: Optional[date] = None) -> CalendarAnalytics:
        """Get calendar analytics and insights"""
        query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)
        
        if calendar_ids:
            query = query.filter(CalendarEvent.calendar_id.in_(calendar_ids))
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(CalendarEvent.start_time >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(CalendarEvent.end_time <= end_datetime)
        
        events = query.all()
        
        if not events:
            return CalendarAnalytics()
        
        # Calculate analytics
        total_events = len(events)
        
        # Events this week/month
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1)
        
        events_this_week = len([e for e in events if e.start_time >= week_start])
        events_this_month = len([e for e in events if e.start_time >= month_start])
        
        # Average event duration
        durations = [(e.end_time - e.start_time).total_seconds() / 3600 for e in events]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Busiest day/hour analysis
        weekdays = [e.start_time.strftime('%A') for e in events]
        hours = [e.start_time.hour for e in events]
        
        from collections import Counter
        weekday_counts = Counter(weekdays)
        hour_counts = Counter(hours)
        
        busiest_day = weekday_counts.most_common(1)[0][0] if weekday_counts else None
        busiest_hour = hour_counts.most_common(1)[0][0] if hour_counts else None
        
        return CalendarAnalytics(
            total_events=total_events,
            events_this_week=events_this_week,
            events_this_month=events_this_month,
            average_event_duration=avg_duration,
            busiest_day_of_week=busiest_day,
            busiest_hour_of_day=busiest_hour,
            event_types={},  # Would categorize by event type
            time_utilization=0.0  # Would calculate based on working hours
        )
    
    # ICS Export
    def export_to_ics(self, db: Session, export_request: ICSExportRequest, user_id: int) -> str:
        """Export calendar events to ICS format"""
        # Create calendar
        cal = ICalendar()
        cal.add('prodid', '-//BlueBirdHub//Calendar//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        
        # Get events to export
        query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)
        
        if export_request.calendar_ids:
            query = query.filter(CalendarEvent.calendar_id.in_(export_request.calendar_ids))
        
        if export_request.start_date:
            start_datetime = datetime.combine(export_request.start_date, datetime.min.time())
            query = query.filter(CalendarEvent.start_time >= start_datetime)
        
        if export_request.end_date:
            end_datetime = datetime.combine(export_request.end_date, datetime.max.time())
            query = query.filter(CalendarEvent.end_time <= end_datetime)
        
        if not export_request.include_private:
            query = query.filter(CalendarEvent.visibility != 'PRIVATE')
        
        events = query.all()
        
        # Add events to calendar
        for event in events:
            ical_event = ICalEvent()
            ical_event.add('uid', f"{event.id}@bluebirdhub.com")
            ical_event.add('dtstart', event.start_time)
            ical_event.add('dtend', event.end_time)
            ical_event.add('summary', event.title)
            
            if event.description:
                ical_event.add('description', event.description)
            
            if event.location:
                ical_event.add('location', event.location)
            
            ical_event.add('status', event.status.value)
            ical_event.add('created', event.created_at)
            ical_event.add('last-modified', event.updated_at or event.created_at)
            
            cal.add_component(ical_event)
        
        return cal.to_ical().decode('utf-8')
    
    # Timezone Utilities
    def get_available_timezones(self) -> List[TimezoneInfo]:
        """Get list of available timezones"""
        common_timezones = [
            'UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome',
            'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney'
        ]
        
        timezone_info = []
        now = datetime.utcnow()
        
        for tz_name in common_timezones:
            try:
                tz = pytz.timezone(tz_name)
                dt = tz.localize(now.replace(tzinfo=None))
                
                timezone_info.append(TimezoneInfo(
                    timezone=tz_name,
                    offset=dt.strftime('%z'),
                    dst_active=bool(dt.dst()),
                    display_name=str(tz)
                ))
            except Exception:
                continue
        
        return timezone_info
    
    def convert_timezone(self, datetime_str: str, from_timezone: str, to_timezone: str) -> Dict[str, Any]:
        """Convert datetime between timezones"""
        try:
            # Parse datetime
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
            # Convert from source timezone
            from_tz = pytz.timezone(from_timezone)
            if dt.tzinfo is None:
                dt = from_tz.localize(dt)
            else:
                dt = dt.astimezone(from_tz)
            
            # Convert to target timezone
            to_tz = pytz.timezone(to_timezone)
            converted_dt = dt.astimezone(to_tz)
            
            return {
                "original": dt.isoformat(),
                "converted": converted_dt.isoformat(),
                "from_timezone": from_timezone,
                "to_timezone": to_timezone
            }
            
        except Exception as e:
            return {"error": str(e)}

# Global instance
calendar_crud = CalendarCRUD()