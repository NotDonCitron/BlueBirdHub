"""
Microsoft Graph API client for comprehensive Outlook calendar operations
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

class MicrosoftGraphClient:
    """Microsoft Graph API client for Outlook calendar"""
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, integration: CalendarIntegration):
        self.integration = integration
        self.access_token = None
        self._update_access_token()
    
    def _update_access_token(self):
        """Get valid access token from OAuth service"""
        self.access_token = oauth_service.get_valid_token(self.integration)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
        """Make authenticated request to Microsoft Graph API"""
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
            logger.error(f"Microsoft Graph API request failed: {str(e)}")
            raise
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """Get list of user's calendars"""
        response = self._make_request("GET", "/me/calendars")
        
        if response.status_code != 200:
            logger.error(f"Failed to list calendars: {response.text}")
            return []
        
        data = response.json()
        return data.get("value", [])
    
    def get_calendar(self, calendar_id: str) -> Optional[Dict[str, Any]]:
        """Get calendar details by ID"""
        response = self._make_request("GET", f"/me/calendars/{calendar_id}")
        
        if response.status_code != 200:
            logger.error(f"Failed to get calendar {calendar_id}: {response.text}")
            return None
        
        return response.json()
    
    def create_calendar(self, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """Create new calendar"""
        data = {
            "name": name,
            "description": description
        }
        
        response = self._make_request("POST", "/me/calendars", data=data)
        
        if response.status_code != 201:
            logger.error(f"Failed to create calendar: {response.text}")
            return None
        
        return response.json()
    
    def update_calendar(self, calendar_id: str, name: str = None, description: str = None) -> Optional[Dict[str, Any]]:
        """Update calendar details"""
        data = {}
        if name:
            data["name"] = name
        if description is not None:
            data["description"] = description
        
        if not data:
            return None
        
        response = self._make_request("PATCH", f"/me/calendars/{calendar_id}", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to update calendar {calendar_id}: {response.text}")
            return None
        
        return response.json()
    
    def delete_calendar(self, calendar_id: str) -> bool:
        """Delete calendar"""
        response = self._make_request("DELETE", f"/me/calendars/{calendar_id}")
        return response.status_code == 204
    
    def list_events(self, calendar_id: str = None, time_min: Optional[datetime] = None, 
                   time_max: Optional[datetime] = None, max_results: int = 250,
                   delta_token: Optional[str] = None) -> Dict[str, Any]:
        """List events from calendar"""
        # Use default calendar if none specified
        endpoint = f"/me/calendars/{calendar_id}/events" if calendar_id else "/me/events"
        
        params = {
            "$top": max_results,
            "$orderby": "start/dateTime"
        }
        
        # Build filter for time range
        filters = []
        if time_min:
            filters.append(f"start/dateTime ge '{time_min.isoformat()}'")
        if time_max:
            filters.append(f"start/dateTime le '{time_max.isoformat()}'")
        
        if filters:
            params["$filter"] = " and ".join(filters)
        
        if delta_token:
            params["$deltatoken"] = delta_token
        
        response = self._make_request("GET", endpoint, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to list events for calendar {calendar_id}: {response.text}")
            return {"value": [], "@odata.deltaLink": None}
        
        return response.json()
    
    def get_event(self, event_id: str, calendar_id: str = None) -> Optional[Dict[str, Any]]:
        """Get event details by ID"""
        endpoint = f"/me/calendars/{calendar_id}/events/{event_id}" if calendar_id else f"/me/events/{event_id}"
        response = self._make_request("GET", endpoint)
        
        if response.status_code != 200:
            logger.error(f"Failed to get event {event_id}: {response.text}")
            return None
        
        return response.json()
    
    def create_event(self, event_data: Dict[str, Any], calendar_id: str = None) -> Optional[Dict[str, Any]]:
        """Create new event"""
        endpoint = f"/me/calendars/{calendar_id}/events" if calendar_id else "/me/events"
        response = self._make_request("POST", endpoint, data=event_data)
        
        if response.status_code != 201:
            logger.error(f"Failed to create event: {response.text}")
            return None
        
        return response.json()
    
    def update_event(self, event_id: str, event_data: Dict[str, Any], calendar_id: str = None) -> Optional[Dict[str, Any]]:
        """Update existing event"""
        endpoint = f"/me/calendars/{calendar_id}/events/{event_id}" if calendar_id else f"/me/events/{event_id}"
        response = self._make_request("PATCH", endpoint, data=event_data)
        
        if response.status_code != 200:
            logger.error(f"Failed to update event {event_id}: {response.text}")
            return None
        
        return response.json()
    
    def delete_event(self, event_id: str, calendar_id: str = None) -> bool:
        """Delete event"""
        endpoint = f"/me/calendars/{calendar_id}/events/{event_id}" if calendar_id else f"/me/events/{event_id}"
        response = self._make_request("DELETE", endpoint)
        return response.status_code == 204
    
    def create_event_from_task(self, task_data: Dict[str, Any], calendar_id: str = None) -> Optional[Dict[str, Any]]:
        """Create Outlook event from task data"""
        # Convert task data to Microsoft Graph event format
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
            "subject": task_data["title"],
            "body": {
                "contentType": "HTML",
                "content": task_data.get("description", "")
            },
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
            event_data["location"] = {
                "displayName": task_data["location"]
            }
        
        # Add attendees if provided
        attendees = task_data.get("attendees", [])
        if attendees:
            event_data["attendees"] = [
                {
                    "emailAddress": {
                        "address": attendee["email"],
                        "name": attendee.get("name", "")
                    },
                    "type": "required"
                }
                for attendee in attendees
            ]
        
        # Add reminders
        reminders = task_data.get("reminders", [])
        if reminders:
            # Use the first reminder (Outlook supports one reminder per event)
            reminder = reminders[0]
            event_data["reminderMinutesBeforeStart"] = reminder["minutes"]
            event_data["isReminderOn"] = True
        
        # Add recurrence if specified
        if task_data.get("recurrence_rule"):
            recurrence_data = self._parse_recurrence_rule(task_data["recurrence_rule"])
            if recurrence_data:
                event_data["recurrence"] = recurrence_data
        
        return self.create_event(event_data, calendar_id)
    
    def update_event_from_task(self, event_id: str, task_data: Dict[str, Any], calendar_id: str = None) -> Optional[Dict[str, Any]]:
        """Update Outlook event from task data"""
        start_time = task_data.get("start_time")
        end_time = task_data.get("end_time")
        
        event_data = {
            "subject": task_data["title"],
            "body": {
                "contentType": "HTML",
                "content": task_data.get("description", "")
            }
        }
        
        if start_time and end_time:
            event_data["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": task_data.get("timezone", "UTC")
            }
            event_data["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": task_data.get("timezone", "UTC")
            }
        
        if task_data.get("location"):
            event_data["location"] = {
                "displayName": task_data["location"]
            }
        
        # Update reminders
        reminders = task_data.get("reminders", [])
        if reminders:
            reminder = reminders[0]
            event_data["reminderMinutesBeforeStart"] = reminder["minutes"]
            event_data["isReminderOn"] = True
        
        return self.update_event(event_id, event_data, calendar_id)
    
    def convert_outlook_event_to_internal(self, outlook_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Outlook event to internal event format"""
        # Parse start and end times
        start = outlook_event.get("start", {})
        end = outlook_event.get("end", {})
        
        start_time = date_parser.parse(start["dateTime"])
        end_time = date_parser.parse(end["dateTime"])
        
        # Check if it's an all-day event
        is_all_day = outlook_event.get("isAllDay", False)
        
        # Convert status
        status_mapping = {
            "free": CalendarEventStatus.TENTATIVE,
            "busy": CalendarEventStatus.CONFIRMED,
            "tentative": CalendarEventStatus.TENTATIVE,
            "outOfOffice": CalendarEventStatus.CONFIRMED
        }
        
        show_as = outlook_event.get("showAs", "busy")
        status = status_mapping.get(show_as, CalendarEventStatus.CONFIRMED)
        
        # Extract attendees
        attendees = []
        for attendee in outlook_event.get("attendees", []):
            email_addr = attendee.get("emailAddress", {})
            attendees.append({
                "email": email_addr.get("address", ""),
                "name": email_addr.get("name", ""),
                "response_status": attendee.get("status", {}).get("response", "none"),
                "is_organizer": attendee.get("type") == "organizer"
            })
        
        # Extract reminders
        reminders = []
        if outlook_event.get("isReminderOn", False):
            minutes = outlook_event.get("reminderMinutesBeforeStart", 15)
            reminders.append({
                "method": "popup",
                "minutes": minutes
            })
        
        # Extract location
        location = ""
        location_data = outlook_event.get("location", {})
        if location_data:
            location = location_data.get("displayName", "")
        
        # Extract body content
        body = outlook_event.get("body", {})
        description = body.get("content", "") if body else ""
        
        # Extract meeting details
        meeting_url = ""
        online_meeting = outlook_event.get("onlineMeeting")
        if online_meeting:
            meeting_url = online_meeting.get("joinUrl", "")
        
        return {
            "external_event_id": outlook_event["id"],
            "title": outlook_event.get("subject", ""),
            "description": description,
            "location": location,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": start.get("timeZone", "UTC"),
            "is_all_day": is_all_day,
            "status": status,
            "attendees": attendees,
            "reminders": reminders,
            "meeting_url": meeting_url,
            "recurrence_rule": self._extract_recurrence_rule(outlook_event.get("recurrence")),
            "external_sync_token": outlook_event.get("@odata.etag", ""),
            "last_synced_at": datetime.utcnow()
        }
    
    def _parse_recurrence_rule(self, rrule: str) -> Optional[Dict[str, Any]]:
        """Parse RRULE into Outlook recurrence format"""
        if not rrule:
            return None
        
        # Basic RRULE parsing (simplified)
        # In production, use a proper RRULE parser
        recurrence_data = {
            "pattern": {},
            "range": {}
        }
        
        if "DAILY" in rrule:
            recurrence_data["pattern"]["type"] = "daily"
            recurrence_data["pattern"]["interval"] = 1
        elif "WEEKLY" in rrule:
            recurrence_data["pattern"]["type"] = "weekly"
            recurrence_data["pattern"]["interval"] = 1
        elif "MONTHLY" in rrule:
            recurrence_data["pattern"]["type"] = "absoluteMonthly"
            recurrence_data["pattern"]["interval"] = 1
        
        # Set default range
        recurrence_data["range"]["type"] = "noEnd"
        recurrence_data["range"]["startDate"] = datetime.utcnow().date().isoformat()
        
        return recurrence_data
    
    def _extract_recurrence_rule(self, recurrence: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract RRULE from Outlook recurrence format"""
        if not recurrence:
            return None
        
        pattern = recurrence.get("pattern", {})
        pattern_type = pattern.get("type", "")
        interval = pattern.get("interval", 1)
        
        # Convert to basic RRULE format
        if pattern_type == "daily":
            return f"RRULE:FREQ=DAILY;INTERVAL={interval}"
        elif pattern_type == "weekly":
            return f"RRULE:FREQ=WEEKLY;INTERVAL={interval}"
        elif pattern_type in ["absoluteMonthly", "relativeMonthly"]:
            return f"RRULE:FREQ=MONTHLY;INTERVAL={interval}"
        
        return None
    
    def setup_webhook(self, calendar_id: str, webhook_url: str, webhook_token: str) -> Optional[Dict[str, Any]]:
        """Setup webhook for real-time calendar updates"""
        resource = f"/me/calendars/{calendar_id}/events" if calendar_id else "/me/events"
        
        data = {
            "changeType": "created,updated,deleted",
            "notificationUrl": webhook_url,
            "resource": resource,
            "expirationDateTime": (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z",
            "clientState": webhook_token
        }
        
        response = self._make_request("POST", "/subscriptions", data=data)
        
        if response.status_code != 201:
            logger.error(f"Failed to setup webhook for calendar {calendar_id}: {response.text}")
            return None
        
        return response.json()
    
    def update_webhook(self, subscription_id: str, expiration_datetime: datetime) -> Optional[Dict[str, Any]]:
        """Update webhook subscription expiration"""
        data = {
            "expirationDateTime": expiration_datetime.isoformat() + "Z"
        }
        
        response = self._make_request("PATCH", f"/subscriptions/{subscription_id}", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to update webhook {subscription_id}: {response.text}")
            return None
        
        return response.json()
    
    def delete_webhook(self, subscription_id: str) -> bool:
        """Delete webhook subscription"""
        response = self._make_request("DELETE", f"/subscriptions/{subscription_id}")
        return response.status_code == 204
    
    def get_free_busy(self, schedules: List[str], start_time: datetime, end_time: datetime, 
                     interval_minutes: int = 60) -> Dict[str, Any]:
        """Get free/busy information for schedules"""
        data = {
            "schedules": schedules,
            "startTime": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "endTime": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "availabilityViewInterval": interval_minutes
        }
        
        response = self._make_request("POST", "/me/calendar/getSchedule", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to get free/busy info: {response.text}")
            return {"value": []}
        
        return response.json()
    
    def find_meeting_times(self, attendees: List[str], duration_minutes: int, 
                          time_min: datetime, time_max: datetime,
                          max_candidates: int = 20) -> List[Dict[str, Any]]:
        """Find available meeting times using Outlook's findMeetingTimes API"""
        data = {
            "attendees": [
                {
                    "emailAddress": {
                        "address": email,
                        "name": email
                    }
                }
                for email in attendees
            ],
            "timeConstraint": {
                "timeslots": [
                    {
                        "start": {
                            "dateTime": time_min.isoformat(),
                            "timeZone": "UTC"
                        },
                        "end": {
                            "dateTime": time_max.isoformat(),
                            "timeZone": "UTC"
                        }
                    }
                ]
            },
            "meetingDuration": f"PT{duration_minutes}M",
            "maxCandidates": max_candidates
        }
        
        response = self._make_request("POST", "/me/calendar/findMeetingTimes", data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to find meeting times: {response.text}")
            return []
        
        result = response.json()
        suggestions = result.get("meetingTimeSuggestions", [])
        
        # Convert to standard format
        meeting_times = []
        for suggestion in suggestions:
            meeting_time = suggestion.get("meetingTimeSlot", {})
            start = meeting_time.get("start", {})
            end = meeting_time.get("end", {})
            
            if start and end:
                meeting_times.append({
                    "start": date_parser.parse(start["dateTime"]),
                    "end": date_parser.parse(end["dateTime"]),
                    "confidence": suggestion.get("confidence", 0)
                })
        
        return meeting_times