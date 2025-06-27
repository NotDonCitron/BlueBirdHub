"""
Calendar conflict detection and resolution service
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.backend.database.database import SessionLocal
from src.backend.models.calendar import (
    CalendarEvent, CalendarConflict, Calendar, CalendarEventStatus
)

logger = logging.getLogger(__name__)

class ConflictDetectionService:
    """Service for detecting and managing calendar conflicts"""
    
    def detect_calendar_conflicts(self, user_id: int, calendar_id: Optional[int] = None) -> List[CalendarConflict]:
        """Detect conflicts for user's calendar events"""
        db = SessionLocal()
        conflicts = []
        
        try:
            # Get query base for events
            events_query = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.status != CalendarEventStatus.CANCELLED
            )
            
            if calendar_id:
                events_query = events_query.filter(CalendarEvent.calendar_id == calendar_id)
            
            # Get all events in the next 30 days
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)
            
            events = events_query.filter(
                CalendarEvent.start_time >= start_date,
                CalendarEvent.start_time <= end_date
            ).order_by(CalendarEvent.start_time).all()
            
            # Check for overlapping events
            for i, event1 in enumerate(events):
                for event2 in events[i+1:]:
                    # Stop checking if event2 starts after event1 ends
                    if event2.start_time >= event1.end_time:
                        break
                    
                    # Check for overlap
                    if self._events_overlap(event1, event2):
                        conflict = self._create_or_update_conflict(
                            db, user_id, event1, event2, "overlap"
                        )
                        if conflict:
                            conflicts.append(conflict)
            
            # Check for double booking (same resource/person)
            resource_conflicts = self._detect_resource_conflicts(db, user_id, events)
            conflicts.extend(resource_conflicts)
            
            # Check for scheduling conflicts (too many events in short time)
            scheduling_conflicts = self._detect_scheduling_conflicts(db, user_id, events)
            conflicts.extend(scheduling_conflicts)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts for user {user_id}: {str(e)}")
            return []
        finally:
            db.close()
    
    def _events_overlap(self, event1: CalendarEvent, event2: CalendarEvent) -> bool:
        """Check if two events overlap in time"""
        # Events overlap if one starts before the other ends
        return (event1.start_time < event2.end_time and 
                event2.start_time < event1.end_time)
    
    def _create_or_update_conflict(self, db: Session, user_id: int, event1: CalendarEvent, 
                                 event2: CalendarEvent, conflict_type: str) -> Optional[CalendarConflict]:
        """Create or update a conflict record"""
        try:
            # Check if conflict already exists
            existing_conflict = db.query(CalendarConflict).filter(
                or_(
                    and_(
                        CalendarConflict.event1_id == event1.id,
                        CalendarConflict.event2_id == event2.id
                    ),
                    and_(
                        CalendarConflict.event1_id == event2.id,
                        CalendarConflict.event2_id == event1.id
                    )
                ),
                CalendarConflict.is_resolved == False
            ).first()
            
            if existing_conflict:
                # Update existing conflict
                existing_conflict.conflict_type = conflict_type
                existing_conflict.severity = self._calculate_conflict_severity(event1, event2)
                existing_conflict.updated_at = datetime.utcnow()
                db.commit()
                return existing_conflict
            
            # Create new conflict
            conflict = CalendarConflict(
                user_id=user_id,
                event1_id=event1.id,
                event2_id=event2.id,
                conflict_type=conflict_type,
                severity=self._calculate_conflict_severity(event1, event2),
                is_resolved=False
            )
            
            db.add(conflict)
            db.commit()
            return conflict
            
        except Exception as e:
            logger.error(f"Failed to create conflict: {str(e)}")
            db.rollback()
            return None
    
    def _calculate_conflict_severity(self, event1: CalendarEvent, event2: CalendarEvent) -> str:
        """Calculate severity of conflict between two events"""
        # Calculate overlap duration
        overlap_start = max(event1.start_time, event2.start_time)
        overlap_end = min(event1.end_time, event2.end_time)
        overlap_duration = overlap_end - overlap_start
        
        # Get event durations
        event1_duration = event1.end_time - event1.start_time
        event2_duration = event2.end_time - event2.start_time
        
        # Calculate overlap percentage
        min_duration = min(event1_duration, event2_duration)
        overlap_percentage = overlap_duration.total_seconds() / min_duration.total_seconds()
        
        # Determine severity based on overlap percentage
        if overlap_percentage >= 0.8:
            return "high"
        elif overlap_percentage >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _detect_resource_conflicts(self, db: Session, user_id: int, events: List[CalendarEvent]) -> List[CalendarConflict]:
        """Detect conflicts based on resource availability"""
        conflicts = []
        
        # Group events by location (resource)
        location_events = {}
        for event in events:
            if event.location:
                location = event.location.strip().lower()
                if location not in location_events:
                    location_events[location] = []
                location_events[location].append(event)
        
        # Check for conflicts within each location
        for location, location_event_list in location_events.items():
            location_event_list.sort(key=lambda e: e.start_time)
            
            for i, event1 in enumerate(location_event_list):
                for event2 in location_event_list[i+1:]:
                    if event2.start_time >= event1.end_time:
                        break
                    
                    if self._events_overlap(event1, event2):
                        conflict = self._create_or_update_conflict(
                            db, user_id, event1, event2, "resource_conflict"
                        )
                        if conflict:
                            conflicts.append(conflict)
        
        return conflicts
    
    def _detect_scheduling_conflicts(self, db: Session, user_id: int, events: List[CalendarEvent]) -> List[CalendarConflict]:
        """Detect scheduling conflicts (too many events in short periods)"""
        conflicts = []
        
        # Sort events by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)
        
        # Check for back-to-back events without buffer time
        for i in range(len(sorted_events) - 1):
            event1 = sorted_events[i]
            event2 = sorted_events[i + 1]
            
            # Check if there's less than 15 minutes between events
            time_between = event2.start_time - event1.end_time
            if timedelta(0) <= time_between < timedelta(minutes=15):
                # Check if events are in different locations
                if (event1.location and event2.location and 
                    event1.location.strip().lower() != event2.location.strip().lower()):
                    
                    conflict = self._create_or_update_conflict(
                        db, user_id, event1, event2, "scheduling_conflict"
                    )
                    if conflict:
                        conflicts.append(conflict)
        
        return conflicts
    
    def resolve_conflict(self, conflict_id: int, resolution_type: str, resolution_notes: str = "", 
                        resolved_by_user_id: Optional[int] = None) -> bool:
        """Resolve a calendar conflict"""
        db = SessionLocal()
        try:
            conflict = db.query(CalendarConflict).get(conflict_id)
            if not conflict:
                return False
            
            conflict.is_resolved = True
            conflict.resolution_type = resolution_type
            conflict.resolution_notes = resolution_notes
            conflict.resolved_by_user_id = resolved_by_user_id
            conflict.resolved_at = datetime.utcnow()
            
            # Apply resolution based on type
            if resolution_type == "reschedule":
                self._apply_reschedule_resolution(db, conflict)
            elif resolution_type == "cancel":
                self._apply_cancel_resolution(db, conflict)
            elif resolution_type == "merge":
                self._apply_merge_resolution(db, conflict)
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def _apply_reschedule_resolution(self, db: Session, conflict: CalendarConflict):
        """Apply reschedule resolution to conflict"""
        # Get the events
        event1 = db.query(CalendarEvent).get(conflict.event1_id)
        event2 = db.query(CalendarEvent).get(conflict.event2_id)
        
        if not event1 or not event2:
            return
        
        # Find next available time slot for the later event
        later_event = event2 if event2.start_time > event1.start_time else event1
        duration = later_event.end_time - later_event.start_time
        
        # Try to find a slot within the next 7 days
        search_start = later_event.end_time
        search_end = search_start + timedelta(days=7)
        
        new_slot = self._find_available_time_slot(
            db, later_event.user_id, duration, search_start, search_end
        )
        
        if new_slot:
            later_event.start_time = new_slot["start"]
            later_event.end_time = new_slot["end"]
            later_event.sync_status = "pending"  # Mark for resync
    
    def _apply_cancel_resolution(self, db: Session, conflict: CalendarConflict):
        """Apply cancel resolution to conflict"""
        # This would typically be handled by user choice
        # For now, we just mark the conflict as resolved
        pass
    
    def _apply_merge_resolution(self, db: Session, conflict: CalendarConflict):
        """Apply merge resolution to conflict"""
        # Get the events
        event1 = db.query(CalendarEvent).get(conflict.event1_id)
        event2 = db.query(CalendarEvent).get(conflict.event2_id)
        
        if not event1 or not event2:
            return
        
        # Merge into the earlier event
        earlier_event = event1 if event1.start_time <= event2.start_time else event2
        later_event = event2 if earlier_event == event1 else event1
        
        # Extend the earlier event to include the later one
        earlier_event.end_time = max(earlier_event.end_time, later_event.end_time)
        
        # Merge descriptions
        if later_event.description:
            if earlier_event.description:
                earlier_event.description += f"\n\n--- Merged from: {later_event.title} ---\n{later_event.description}"
            else:
                earlier_event.description = f"Merged from: {later_event.title}\n{later_event.description}"
        
        # Mark the later event as cancelled
        later_event.status = CalendarEventStatus.CANCELLED
    
    def _find_available_time_slot(self, db: Session, user_id: int, duration: timedelta, 
                                search_start: datetime, search_end: datetime) -> Optional[Dict[str, datetime]]:
        """Find an available time slot for an event"""
        # Get all events in the search period
        existing_events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.status != CalendarEventStatus.CANCELLED,
            CalendarEvent.start_time >= search_start,
            CalendarEvent.start_time <= search_end
        ).order_by(CalendarEvent.start_time).all()
        
        # Try to find a gap
        current_time = search_start
        
        for event in existing_events:
            # Check if there's enough time before this event
            if event.start_time - current_time >= duration:
                return {
                    "start": current_time,
                    "end": current_time + duration
                }
            
            # Move to after this event
            current_time = event.end_time
        
        # Check if there's time after the last event
        if search_end - current_time >= duration:
            return {
                "start": current_time,
                "end": current_time + duration
            }
        
        return None
    
    def get_conflicts_for_user(self, user_id: int, include_resolved: bool = False) -> List[CalendarConflict]:
        """Get all conflicts for a user"""
        db = SessionLocal()
        try:
            query = db.query(CalendarConflict).filter(
                CalendarConflict.user_id == user_id
            )
            
            if not include_resolved:
                query = query.filter(CalendarConflict.is_resolved == False)
            
            return query.order_by(CalendarConflict.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Failed to get conflicts for user {user_id}: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_conflict_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get conflict statistics for a user"""
        db = SessionLocal()
        try:
            # Total conflicts
            total_conflicts = db.query(CalendarConflict).filter(
                CalendarConflict.user_id == user_id
            ).count()
            
            # Resolved conflicts
            resolved_conflicts = db.query(CalendarConflict).filter(
                CalendarConflict.user_id == user_id,
                CalendarConflict.is_resolved == True
            ).count()
            
            # Conflicts by type
            conflict_types = db.query(
                CalendarConflict.conflict_type,
                db.func.count(CalendarConflict.id).label('count')
            ).filter(
                CalendarConflict.user_id == user_id
            ).group_by(CalendarConflict.conflict_type).all()
            
            # Conflicts by severity
            conflict_severities = db.query(
                CalendarConflict.severity,
                db.func.count(CalendarConflict.id).label('count')
            ).filter(
                CalendarConflict.user_id == user_id
            ).group_by(CalendarConflict.severity).all()
            
            return {
                "total_conflicts": total_conflicts,
                "resolved_conflicts": resolved_conflicts,
                "pending_conflicts": total_conflicts - resolved_conflicts,
                "resolution_rate": resolved_conflicts / total_conflicts if total_conflicts > 0 else 0,
                "conflict_types": {ct.conflict_type: ct.count for ct in conflict_types},
                "conflict_severities": {cs.severity: cs.count for cs in conflict_severities}
            }
            
        except Exception as e:
            logger.error(f"Failed to get conflict statistics for user {user_id}: {str(e)}")
            return {}
        finally:
            db.close()
    
    def suggest_conflict_resolution(self, conflict_id: int) -> List[Dict[str, Any]]:
        """Suggest resolution options for a conflict"""
        db = SessionLocal()
        try:
            conflict = db.query(CalendarConflict).get(conflict_id)
            if not conflict:
                return []
            
            event1 = db.query(CalendarEvent).get(conflict.event1_id)
            event2 = db.query(CalendarEvent).get(conflict.event2_id)
            
            if not event1 or not event2:
                return []
            
            suggestions = []
            
            # Always suggest ignoring the conflict
            suggestions.append({
                "type": "ignore",
                "title": "Keep both events as is",
                "description": "Accept the overlap and keep both events unchanged",
                "confidence": 0.3
            })
            
            # Suggest rescheduling if possible
            later_event = event2 if event2.start_time > event1.start_time else event1
            duration = later_event.end_time - later_event.start_time
            
            next_slot = self._find_available_time_slot(
                db, conflict.user_id, duration, 
                later_event.end_time, later_event.end_time + timedelta(days=7)
            )
            
            if next_slot:
                suggestions.append({
                    "type": "reschedule",
                    "title": f"Reschedule '{later_event.title}'",
                    "description": f"Move to {next_slot['start'].strftime('%Y-%m-%d %H:%M')}",
                    "confidence": 0.8,
                    "details": next_slot
                })
            
            # Suggest merging if events are similar
            if self._events_can_merge(event1, event2):
                suggestions.append({
                    "type": "merge",
                    "title": "Merge events",
                    "description": "Combine both events into one extended event",
                    "confidence": 0.6
                })
            
            # Suggest canceling one event
            suggestions.append({
                "type": "cancel",
                "title": f"Cancel '{event1.title}'",
                "description": "Remove this event from calendar",
                "confidence": 0.4
            })
            
            suggestions.append({
                "type": "cancel",
                "title": f"Cancel '{event2.title}'",
                "description": "Remove this event from calendar",
                "confidence": 0.4
            })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest resolution for conflict {conflict_id}: {str(e)}")
            return []
        finally:
            db.close()
    
    def _events_can_merge(self, event1: CalendarEvent, event2: CalendarEvent) -> bool:
        """Check if two events can be merged"""
        # Events can merge if they:
        # 1. Have similar titles
        # 2. Have the same location
        # 3. Overlap significantly
        
        # Check title similarity (simple approach)
        title_similarity = self._calculate_title_similarity(event1.title, event2.title)
        
        # Check location match
        location_match = (event1.location and event2.location and 
                         event1.location.strip().lower() == event2.location.strip().lower())
        
        # Check overlap percentage
        overlap_start = max(event1.start_time, event2.start_time)
        overlap_end = min(event1.end_time, event2.end_time)
        overlap_duration = overlap_end - overlap_start
        
        total_duration = max(event1.end_time, event2.end_time) - min(event1.start_time, event2.start_time)
        overlap_percentage = overlap_duration.total_seconds() / total_duration.total_seconds()
        
        return (title_similarity > 0.5 or location_match) and overlap_percentage > 0.5
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two event titles"""
        if not title1 or not title2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0