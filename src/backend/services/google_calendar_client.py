"""
Google Calendar API client for comprehensive calendar operations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from dateutil import parser as date_parser
from dateutil.tz import tzutc, gettz
import pytz

from src.backend.models.calendar import CalendarIntegration, CalendarEvent, CalendarEventStatus
from src.backend.services.oauth_service import oauth_service

logger = logging.getLogger(__name__)

class GoogleCalendarClient:
    """Google Calendar API client"""
    
    BASE_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self, integration: CalendarIntegration):
        self.integration = integration
        self.access_token = None
        self._update_access_token()
    
    def _update_access_token(self):
        """Get valid access token from OAuth service"""
        self.access_token = oauth_service.get_valid_token(self.integration)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
        """Make authenticated request to Google Calendar API"""
        if not self.access_token:
            self._update_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle token expiration
            if response.status_code == 401:
                logger.warning("Access token expired, refreshing...")
                self._update_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                
                # Retry request with new token
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers, json=data, params=params)
                elif method.upper() == "PUT":
                    response = requests.put(url, headers=headers, json=data, params=params)
                elif method.upper() == "PATCH":
                    response = requests.patch(url, headers=headers, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers, params=params)
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Google Calendar API request failed: {str(e)}")
            raise
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """Get list of user's calendars"""
        response = self._make_request("GET", "/users/me/calendarList")
        
        if response.status_code != 200:
            logger.error(f"Failed to list calendars: {response.text}")
            return []
        
        data = response.json()
        return data.get("items", [])
    
    def get_calendar(self, calendar_id: str) -> Optional[Dict[str, Any]]:
        """Get calendar details by ID"""
        response = self._make_request("GET", f"/calendars/{calendar_id}")
        
        if response.status_code != 200:
            logger.error(f"Failed to get calendar {calendar_id}: {response.text}")
            return None
        
        return response.json()
    
    def create_calendar(self, name: str, description: str = "", timezone: str = "UTC") -> Optional[Dict[str, Any]]:
        """Create new calendar"""
        data = {
            "summary": name,
            "description": description,
            "timeZone": timezone
        }
        
        response = self._make_request("POST", "/calendars", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to create calendar: {response.text}")
            return None
        
        return response.json()
    
    def update_calendar(self, calendar_id: str, name: str = None, description: str = None, timezone: str = None) -> Optional[Dict[str, Any]]:
        """Update calendar details"""
        data = {}
        if name:
            data["summary"] = name
        if description is not None:
            data["description"] = description
        if timezone:
            data["timeZone"] = timezone
        
        if not data:
            return None
        
        response = self._make_request("PATCH", f"/calendars/{calendar_id}", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to update calendar {calendar_id}: {response.text}")
            return None
        
        return response.json()
    
    def delete_calendar(self, calendar_id: str) -> bool:
        """Delete calendar"""
        response = self._make_request("DELETE", f"/calendars/{calendar_id}")
        return response.status_code == 204
    
    def list_events(self, calendar_id: str = "primary", time_min: Optional[datetime] = None, 
                   time_max: Optional[datetime] = None, max_results: int = 250, 
                   sync_token: Optional[str] = None) -> Dict[str, Any]:
        """List events from calendar"""
        params = {
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_min:
            params["timeMin"] = time_min.isoformat()
        if time_max:
            params["timeMax"] = time_max.isoformat()
        if sync_token:
            params["syncToken"] = sync_token
        
        response = self._make_request("GET", f"/calendars/{calendar_id}/events", params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to list events for calendar {calendar_id}: {response.text}")
            return {"items": [], "nextSyncToken": None}
        
        return response.json()
    
    def get_event(self, calendar_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event details by ID"""
        response = self._make_request("GET", f"/calendars/{calendar_id}/events/{event_id}")
        
        if response.status_code != 200:
            logger.error(f"Failed to get event {event_id}: {response.text}")
            return None
        
        return response.json()
    
    def create_event(self, calendar_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new event"""
        response = self._make_request("POST", f"/calendars/{calendar_id}/events", data=event_data)
        
        if response.status_code != 200:
            logger.error(f"Failed to create event: {response.text}")
            return None
        
        return response.json()
    
    def update_event(self, calendar_id: str, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing event"""
        response = self._make_request("PUT", f"/calendars/{calendar_id}/events/{event_id}", data=event_data)
        
        if response.status_code != 200:
            logger.error(f"Failed to update event {event_id}: {response.text}")
            return None
        
        return response.json()
    
    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete event"""
        response = self._make_request("DELETE", f"/calendars/{calendar_id}/events/{event_id}")
        return response.status_code == 204
    
    def create_event_from_task(self, calendar_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create Google Calendar event from task data"""
        # Convert task data to Google Calendar event format
        start_time = task_data.get("start_time")
        end_time = task_data.get("end_time")
        
        if not start_time or not end_time:
            # If no times specified, create an all-day event for due date
            due_date = task_data.get("due_date")
            if due_date:
                start_time = due_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=1)
            else:
                # Default to 1-hour event starting now
                start_time = datetime.utcnow()
                end_time = start_time + timedelta(hours=1)
        
        event_data = {
            "summary": task_data["title"],
            "description": task_data.get("description", ""),
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": task_data.get("timezone", "UTC")
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": task_data.get("timezone", "UTC")
            }
        }
        
        # Add location if provided
        if task_data.get("location"):
            event_data["location"] = task_data["location"]
        
        # Add reminders
        reminders = task_data.get("reminders", [])
        if reminders:
            event_data["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": reminder["minutes"]} 
                    for reminder in reminders
                ]
            }
        
        # Add attendees if provided
        attendees = task_data.get("attendees", [])
        if attendees:
            event_data["attendees"] = [
                {"email": attendee["email"], "displayName": attendee.get("name", "")}
                for attendee in attendees
            ]
        
        # Add recurrence if specified
        if task_data.get("recurrence_rule"):
            event_data["recurrence"] = [task_data["recurrence_rule"]]
        
        return self.create_event(calendar_id, event_data)
    
    def update_event_from_task(self, calendar_id: str, event_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update Google Calendar event from task data"""
        # Get existing event first
        existing_event = self.get_event(calendar_id, event_id)
        if not existing_event:
            return None
        
        # Update event with task data
        start_time = task_data.get("start_time")
        end_time = task_data.get("end_time")
        
        if start_time and end_time:
            existing_event["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": task_data.get("timezone", "UTC")
            }
            existing_event["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": task_data.get("timezone", "UTC")
            }
        
        existing_event["summary"] = task_data["title"]
        existing_event["description"] = task_data.get("description", "")
        
        if task_data.get("location"):
            existing_event["location"] = task_data["location"]
        
        # Update reminders
        reminders = task_data.get("reminders", [])
        if reminders:
            existing_event["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": reminder["minutes"]} 
                    for reminder in reminders
                ]
            }
        
        return self.update_event(calendar_id, event_id, existing_event)
    
    def convert_google_event_to_internal(self, google_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Google Calendar event to internal event format"""
        # Parse start and end times
        start = google_event.get("start", {})
        end = google_event.get("end", {})
        
        # Handle all-day events
        if "date" in start:
            start_time = date_parser.parse(start["date"]).replace(tzinfo=tzutc())
            is_all_day = True
        else:
            start_time = date_parser.parse(start["dateTime"])
            is_all_day = False
        
        if "date" in end:
            end_time = date_parser.parse(end["date"]).replace(tzinfo=tzutc())
        else:
            end_time = date_parser.parse(end["dateTime"])
        
        # Convert status
        status_mapping = {
            "confirmed": CalendarEventStatus.CONFIRMED,
            "tentative": CalendarEventStatus.TENTATIVE,
            "cancelled": CalendarEventStatus.CANCELLED
        }
        status = status_mapping.get(google_event.get("status", "confirmed"), CalendarEventStatus.CONFIRMED)
        
        # Extract attendees
        attendees = []
        for attendee in google_event.get("attendees", []):
            attendees.append({
                "email": attendee["email"],
                "name": attendee.get("displayName", ""),
                "response_status": attendee.get("responseStatus", "needsAction"),
                "is_organizer": attendee.get("organizer", False)
            })
        
        # Extract reminders
        reminders = []
        reminder_overrides = google_event.get("reminders", {}).get("overrides", [])
        for reminder in reminder_overrides:
            reminders.append({
                "method": reminder["method"],
                "minutes": reminder["minutes"]
            })
        
        return {
            "external_event_id": google_event["id"],
            "title": google_event.get("summary", ""),
            "description": google_event.get("description", ""),
            "location": google_event.get("location", ""),
            "start_time": start_time,
            "end_time": end_time,
            "timezone": start.get("timeZone") or end.get("timeZone", "UTC"),
            "is_all_day": is_all_day,
            "status": status,
            "attendees": attendees,
            "reminders": reminders,
            "meeting_url": google_event.get("hangoutLink", ""),
            "recurrence_rule": google_event.get("recurrence", [None])[0] if google_event.get("recurrence") else None,
            "external_sync_token": google_event.get("etag", ""),
            "last_synced_at": datetime.utcnow()
        }
    
    def setup_webhook(self, calendar_id: str, webhook_url: str, webhook_token: str) -> Optional[Dict[str, Any]]:
        """Setup webhook for real-time calendar updates"""
        data = {
            "id": f"bluebirdhub-{calendar_id}-{webhook_token}",
            "type": "web_hook",
            "address": webhook_url,
            "token": webhook_token
        }
        
        response = self._make_request("POST", f"/calendars/{calendar_id}/events/watch", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to setup webhook for calendar {calendar_id}: {response.text}")
            return None
        
        return response.json()
    
    def stop_webhook(self, channel_id: str, resource_id: str) -> bool:
        """Stop webhook channel"""
        data = {
            "id": channel_id,
            "resourceId": resource_id
        }
        
        response = self._make_request("POST", "/channels/stop", data=data)
        return response.status_code == 204
    
    def get_free_busy(self, calendar_ids: List[str], time_min: datetime, time_max: datetime) -> Dict[str, Any]:
        """Get free/busy information for calendars"""
        data = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": cal_id} for cal_id in calendar_ids]
        }
        
        response = self._make_request("POST", "/freeBusy", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to get free/busy info: {response.text}")
            return {}
        
        return response.json()
    
    def find_meeting_times(self, attendees: List[str], duration_minutes: int, 
                          time_min: datetime, time_max: datetime, 
                          timezone: str = "UTC") -> List[Dict[str, Any]]:
        """Find available meeting times for attendees"""
        # Get free/busy info for attendees
        freebusy_data = self.get_free_busy(attendees, time_min, time_max)
        
        if not freebusy_data:
            return []
        
        # Analyze busy periods and find free slots
        busy_periods = []
        for calendar_id, info in freebusy_data.get("calendars", {}).items():
            for busy_period in info.get("busy", []):
                start = date_parser.parse(busy_period["start"])
                end = date_parser.parse(busy_period["end"])
                busy_periods.append((start, end))
        
        # Sort busy periods by start time
        busy_periods.sort(key=lambda x: x[0])
        
        # Find free slots
        free_slots = []
        current_time = time_min
        duration = timedelta(minutes=duration_minutes)
        
        for busy_start, busy_end in busy_periods:
            # Check if there's a free slot before this busy period
            if current_time + duration <= busy_start:
                free_slots.append({
                    "start": current_time,
                    "end": current_time + duration
                })
            
            # Move current time to end of busy period
            current_time = max(current_time, busy_end)
        
        # Check for free slot after last busy period
        if current_time + duration <= time_max:
            free_slots.append({
                "start": current_time,
                "end": current_time + duration
            })
        
        return free_slots[:10]  # Return up to 10 suggestions