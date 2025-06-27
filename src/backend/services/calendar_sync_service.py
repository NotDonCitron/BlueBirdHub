"""
Comprehensive calendar synchronization service for two-way sync between
internal tasks/events and external calendar providers (Google, Outlook)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import asyncio
import json

from src.backend.database.database import SessionLocal
from src.backend.models.calendar import (
    Calendar, CalendarEvent, CalendarIntegration, CalendarProvider, 
    CalendarSyncLog, SyncStatus, CalendarConflict
)
from src.backend.models.task import Task, TaskStatus
from src.backend.services.google_calendar_client import GoogleCalendarClient
from src.backend.services.microsoft_graph_client import MicrosoftGraphClient
from src.backend.services.conflict_detection_service import ConflictDetectionService

logger = logging.getLogger(__name__)

class CalendarSyncService:
    """Main service for calendar synchronization operations"""
    
    def __init__(self):
        self.conflict_detector = ConflictDetectionService()
    
    def get_client_for_integration(self, integration: CalendarIntegration):
        """Get appropriate API client for integration"""
        if integration.provider == CalendarProvider.GOOGLE:
            return GoogleCalendarClient(integration)
        elif integration.provider == CalendarProvider.MICROSOFT:
            return MicrosoftGraphClient(integration)
        else:
            raise ValueError(f"Unsupported provider: {integration.provider}")
    
    def sync_all_user_calendars(self, user_id: int, force_full_sync: bool = False) -> Dict[str, Any]:
        """Sync all calendars for a user"""
        db = SessionLocal()
        results = {
            "calendars_synced": 0,
            "events_processed": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "conflicts_detected": 0,
            "errors": []
        }
        
        try:
            # Get all active integrations for user
            integrations = db.query(CalendarIntegration).filter(
                CalendarIntegration.user_id == user_id,
                CalendarIntegration.is_active == True
            ).all()
            
            if not integrations:
                return results
            
            for integration in integrations:
                try:
                    # Get calendars for this integration
                    calendars = db.query(Calendar).filter(
                        Calendar.user_id == user_id,
                        Calendar.integration_id == integration.id,
                        Calendar.is_active == True
                    ).all()
                    
                    for calendar in calendars:
                        sync_result = self.sync_calendar(calendar, force_full_sync)
                        
                        # Aggregate results
                        results["calendars_synced"] += 1
                        results["events_processed"] += sync_result.get("events_processed", 0)
                        results["events_created"] += sync_result.get("events_created", 0)
                        results["events_updated"] += sync_result.get("events_updated", 0)
                        results["events_deleted"] += sync_result.get("events_deleted", 0)
                        results["conflicts_detected"] += sync_result.get("conflicts_detected", 0)
                        
                        if sync_result.get("errors"):
                            results["errors"].extend(sync_result["errors"])
                    
                except Exception as e:
                    error_msg = f"Failed to sync integration {integration.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync calendars for user {user_id}: {str(e)}")
            results["errors"].append(str(e))
            return results
        finally:
            db.close()
    
    def sync_calendar(self, calendar: Calendar, force_full_sync: bool = False) -> Dict[str, Any]:
        """Sync a single calendar with its external provider"""
        db = SessionLocal()
        sync_log = None
        
        try:
            # Create sync log entry
            sync_log = CalendarSyncLog(
                calendar_id=calendar.id,
                integration_id=calendar.integration_id,
                user_id=calendar.user_id,
                sync_type="full" if force_full_sync else "incremental",
                direction="bidirectional",
                status=SyncStatus.IN_PROGRESS,
                started_at=datetime.utcnow()
            )
            db.add(sync_log)
            db.commit()
            
            # Get integration and client
            integration = db.query(CalendarIntegration).get(calendar.integration_id)
            if not integration or not integration.is_active:
                raise ValueError("Integration not found or inactive")
            
            client = self.get_client_for_integration(integration)
            
            # Perform bidirectional sync
            import_result = self._import_events_from_external(db, calendar, client, force_full_sync)
            export_result = self._export_events_to_external(db, calendar, client)
            task_sync_result = self._sync_tasks_with_events(db, calendar)
            
            # Detect and resolve conflicts
            conflicts = self.conflict_detector.detect_calendar_conflicts(calendar.user_id, calendar.id)
            
            # Update sync log with results
            sync_log.status = SyncStatus.COMPLETED
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            sync_log.events_processed = (import_result["events_processed"] + 
                                       export_result["events_processed"] + 
                                       task_sync_result["events_processed"])
            sync_log.events_created = (import_result["events_created"] + 
                                     export_result["events_created"] + 
                                     task_sync_result["events_created"])
            sync_log.events_updated = (import_result["events_updated"] + 
                                     export_result["events_updated"] + 
                                     task_sync_result["events_updated"])
            sync_log.events_deleted = (import_result["events_deleted"] + 
                                     export_result["events_deleted"] + 
                                     task_sync_result["events_deleted"])
            sync_log.conflicts_detected = len(conflicts)
            
            # Update calendar sync timestamp
            calendar.last_sync_at = datetime.utcnow()
            calendar.sync_token = import_result.get("sync_token")
            
            db.commit()
            
            return {
                "events_processed": sync_log.events_processed,
                "events_created": sync_log.events_created,
                "events_updated": sync_log.events_updated,
                "events_deleted": sync_log.events_deleted,
                "conflicts_detected": sync_log.conflicts_detected,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Calendar sync failed for calendar {calendar.id}: {str(e)}")
            
            if sync_log:
                sync_log.status = SyncStatus.FAILED
                sync_log.completed_at = datetime.utcnow()
                sync_log.error_message = str(e)
                db.commit()
            
            return {
                "events_processed": 0,
                "events_created": 0,
                "events_updated": 0,
                "events_deleted": 0,
                "conflicts_detected": 0,
                "errors": [str(e)]
            }
        finally:
            db.close()
    
    def _import_events_from_external(self, db: Session, calendar: Calendar, client, force_full_sync: bool = False) -> Dict[str, Any]:
        """Import events from external calendar provider"""
        results = {
            "events_processed": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "sync_token": None
        }
        
        try:
            # Determine sync parameters
            sync_token = None if force_full_sync else calendar.sync_token
            time_min = datetime.utcnow() - timedelta(days=30)  # Sync last 30 days
            time_max = datetime.utcnow() + timedelta(days=365)  # Sync next year
            
            # Get events from external provider
            if calendar.provider == CalendarProvider.GOOGLE:
                external_data = client.list_events(
                    calendar_id=calendar.external_calendar_id,
                    time_min=time_min,
                    time_max=time_max,
                    sync_token=sync_token
                )
                external_events = external_data.get("items", [])
                results["sync_token"] = external_data.get("nextSyncToken")
            else:  # Microsoft
                external_data = client.list_events(
                    calendar_id=calendar.external_calendar_id,
                    time_min=time_min,
                    time_max=time_max,
                    delta_token=sync_token
                )
                external_events = external_data.get("value", [])
                results["sync_token"] = external_data.get("@odata.deltaLink")
            
            # Process each external event
            for external_event in external_events:
                results["events_processed"] += 1
                
                try:
                    # Convert external event to internal format
                    if calendar.provider == CalendarProvider.GOOGLE:
                        event_data = client.convert_google_event_to_internal(external_event)
                    else:
                        event_data = client.convert_outlook_event_to_internal(external_event)
                    
                    # Check if event already exists
                    existing_event = db.query(CalendarEvent).filter(
                        CalendarEvent.calendar_id == calendar.id,
                        CalendarEvent.external_event_id == event_data["external_event_id"]
                    ).first()
                    
                    if existing_event:
                        # Update existing event
                        for key, value in event_data.items():
                            if hasattr(existing_event, key):
                                setattr(existing_event, key, value)
                        results["events_updated"] += 1
                    else:
                        # Create new event
                        new_event = CalendarEvent(
                            calendar_id=calendar.id,
                            user_id=calendar.user_id,
                            **event_data
                        )
                        db.add(new_event)
                        results["events_created"] += 1
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to process external event: {str(e)}")
                    db.rollback()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to import events from external calendar: {str(e)}")
            raise
    
    def _export_events_to_external(self, db: Session, calendar: Calendar, client) -> Dict[str, Any]:
        """Export local events to external calendar provider"""
        results = {
            "events_processed": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0
        }
        
        try:
            # Get local events that need to be synced
            local_events = db.query(CalendarEvent).filter(
                CalendarEvent.calendar_id == calendar.id,
                CalendarEvent.external_event_id.is_(None),  # Not yet synced
                CalendarEvent.sync_status.in_([SyncStatus.PENDING, SyncStatus.FAILED])
            ).all()
            
            for event in local_events:
                results["events_processed"] += 1
                
                try:
                    # Convert to external format
                    event_data = self._convert_internal_event_to_external(event, calendar.provider)
                    
                    # Create event in external calendar
                    if calendar.provider == CalendarProvider.GOOGLE:
                        external_event = client.create_event(calendar.external_calendar_id, event_data)
                    else:
                        external_event = client.create_event(event_data, calendar.external_calendar_id)
                    
                    if external_event:
                        # Update local event with external ID
                        event.external_event_id = external_event["id"]
                        event.sync_status = SyncStatus.COMPLETED
                        event.last_synced_at = datetime.utcnow()
                        results["events_created"] += 1
                    else:
                        event.sync_status = SyncStatus.FAILED
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to export event {event.id}: {str(e)}")
                    event.sync_status = SyncStatus.FAILED
                    db.commit()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to export events to external calendar: {str(e)}")
            raise
    
    def _sync_tasks_with_events(self, db: Session, calendar: Calendar) -> Dict[str, Any]:
        """Sync tasks with calendar events"""
        results = {
            "events_processed": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0
        }
        
        try:
            # Get tasks that should have calendar events
            tasks_needing_events = db.query(Task).filter(
                Task.user_id == calendar.user_id,
                Task.workspace_id == calendar.workspace_id,
                Task.due_date.isnot(None),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            ).all()
            
            for task in tasks_needing_events:
                results["events_processed"] += 1
                
                try:
                    # Check if task already has a calendar event
                    existing_event = db.query(CalendarEvent).filter(
                        CalendarEvent.task_id == task.id,
                        CalendarEvent.calendar_id == calendar.id
                    ).first()
                    
                    if existing_event:
                        # Update existing event if task changed
                        if task.updated_at > existing_event.last_synced_at:
                            self._update_event_from_task(db, existing_event, task, calendar)
                            results["events_updated"] += 1
                    else:
                        # Create new event from task
                        self._create_event_from_task(db, task, calendar)
                        results["events_created"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync task {task.id} with calendar: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync tasks with events: {str(e)}")
            raise
    
    def _create_event_from_task(self, db: Session, task: Task, calendar: Calendar):
        """Create calendar event from task"""
        # Determine event timing
        start_time = task.due_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=task.estimated_hours or 1)
        
        # Create event
        event = CalendarEvent(
            calendar_id=calendar.id,
            user_id=task.user_id,
            task_id=task.id,
            title=f"Task: {task.title}",
            description=task.description or "",
            start_time=start_time,
            end_time=end_time,
            timezone="UTC",
            sync_status=SyncStatus.PENDING
        )
        
        db.add(event)
        db.commit()
        
        # Sync to external provider if needed
        if calendar.provider != CalendarProvider.INTERNAL:
            self._sync_event_to_external(db, event, calendar)
    
    def _update_event_from_task(self, db: Session, event: CalendarEvent, task: Task, calendar: Calendar):
        """Update calendar event from task changes"""
        # Update event details
        event.title = f"Task: {task.title}"
        event.description = task.description or ""
        
        # Update timing if task due date changed
        if task.due_date and task.due_date != event.start_time.date():
            start_time = task.due_date.replace(hour=9, minute=0, second=0, microsecond=0)
            event.start_time = start_time
            event.end_time = start_time + timedelta(hours=task.estimated_hours or 1)
        
        event.sync_status = SyncStatus.PENDING
        event.last_synced_at = datetime.utcnow()
        
        db.commit()
        
        # Sync to external provider if needed
        if calendar.provider != CalendarProvider.INTERNAL:
            self._sync_event_to_external(db, event, calendar)
    
    def _sync_event_to_external(self, db: Session, event: CalendarEvent, calendar: Calendar):
        """Sync internal event to external calendar provider"""
        try:
            integration = db.query(CalendarIntegration).get(calendar.integration_id)
            if not integration or not integration.is_active:
                return
            
            client = self.get_client_for_integration(integration)
            
            # Convert to external format
            event_data = self._convert_internal_event_to_external(event, calendar.provider)
            
            if event.external_event_id:
                # Update existing external event
                if calendar.provider == CalendarProvider.GOOGLE:
                    result = client.update_event(calendar.external_calendar_id, event.external_event_id, event_data)
                else:
                    result = client.update_event(event.external_event_id, event_data, calendar.external_calendar_id)
            else:
                # Create new external event
                if calendar.provider == CalendarProvider.GOOGLE:
                    result = client.create_event(calendar.external_calendar_id, event_data)
                else:
                    result = client.create_event(event_data, calendar.external_calendar_id)
                
                if result:
                    event.external_event_id = result["id"]
            
            if result:
                event.sync_status = SyncStatus.COMPLETED
                event.last_synced_at = datetime.utcnow()
            else:
                event.sync_status = SyncStatus.FAILED
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to sync event {event.id} to external provider: {str(e)}")
            event.sync_status = SyncStatus.FAILED
            db.commit()
    
    def _convert_internal_event_to_external(self, event: CalendarEvent, provider: CalendarProvider) -> Dict[str, Any]:
        """Convert internal event to external provider format"""
        if provider == CalendarProvider.GOOGLE:
            return {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": event.timezone
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": event.timezone
                },
                "location": event.location or "",
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder["minutes"]}
                        for reminder in (event.reminders or [])
                    ]
                } if event.reminders else {"useDefault": True}
            }
        
        elif provider == CalendarProvider.MICROSOFT:
            return {
                "subject": event.title,
                "body": {
                    "contentType": "HTML",
                    "content": event.description
                },
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": event.timezone
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": event.timezone
                },
                "location": {
                    "displayName": event.location or ""
                },
                "isReminderOn": bool(event.reminders),
                "reminderMinutesBeforeStart": event.reminders[0]["minutes"] if event.reminders else 15
            }
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def create_event_from_task(self, task_id: int, calendar_id: int) -> Optional[CalendarEvent]:
        """Create a calendar event from a task"""
        db = SessionLocal()
        try:
            task = db.query(Task).get(task_id)
            calendar = db.query(Calendar).get(calendar_id)
            
            if not task or not calendar:
                return None
            
            # Check if event already exists
            existing_event = db.query(CalendarEvent).filter(
                CalendarEvent.task_id == task_id,
                CalendarEvent.calendar_id == calendar_id
            ).first()
            
            if existing_event:
                return existing_event
            
            self._create_event_from_task(db, task, calendar)
            
            # Return the created event
            return db.query(CalendarEvent).filter(
                CalendarEvent.task_id == task_id,
                CalendarEvent.calendar_id == calendar_id
            ).first()
            
        except Exception as e:
            logger.error(f"Failed to create event from task {task_id}: {str(e)}")
            return None
        finally:
            db.close()
    
    def update_task_from_event(self, event_id: int) -> Optional[Task]:
        """Update task from calendar event changes"""
        db = SessionLocal()
        try:
            event = db.query(CalendarEvent).get(event_id)
            if not event or not event.task_id:
                return None
            
            task = db.query(Task).get(event.task_id)
            if not task:
                return None
            
            # Update task from event
            if event.start_time:
                task.due_date = event.start_time.date()
            
            # Extract duration for estimated hours
            if event.start_time and event.end_time:
                duration = event.end_time - event.start_time
                task.estimated_hours = max(1, int(duration.total_seconds() / 3600))
            
            # Update title if it was auto-generated
            if task.title in event.title:
                # Extract original title by removing "Task: " prefix
                if event.title.startswith("Task: "):
                    original_title = event.title[6:]
                    if original_title and original_title != task.title:
                        task.title = original_title
            
            if event.description and not task.description:
                task.description = event.description
            
            db.commit()
            return task
            
        except Exception as e:
            logger.error(f"Failed to update task from event {event_id}: {str(e)}")
            return None
        finally:
            db.close()
    
    async def setup_real_time_sync(self, calendar: Calendar) -> bool:
        """Setup real-time synchronization via webhooks"""
        db = SessionLocal()
        try:
            integration = db.query(CalendarIntegration).get(calendar.integration_id)
            if not integration or not integration.is_active:
                return False
            
            client = self.get_client_for_integration(integration)
            
            # Generate webhook URL and token
            webhook_url = f"https://your-domain.com/api/calendar/webhook/{calendar.provider.value.lower()}"
            webhook_token = f"calendar_{calendar.id}_{integration.id}"
            
            # Setup webhook with provider
            if calendar.provider == CalendarProvider.GOOGLE:
                webhook_data = client.setup_webhook(
                    calendar.external_calendar_id, 
                    webhook_url, 
                    webhook_token
                )
            else:  # Microsoft
                webhook_data = client.setup_webhook(
                    calendar.external_calendar_id,
                    webhook_url,
                    webhook_token
                )
            
            if webhook_data:
                # Store webhook information
                integration.webhook_url = webhook_url
                integration.webhook_token = webhook_token
                if "expiration" in webhook_data:
                    integration.webhook_expires_at = datetime.fromisoformat(webhook_data["expiration"])
                
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to setup real-time sync for calendar {calendar.id}: {str(e)}")
            return False
        finally:
            db.close()

# Global instance
calendar_sync_service = CalendarSyncService()