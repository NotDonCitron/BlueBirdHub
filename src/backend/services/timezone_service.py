"""
Comprehensive timezone handling and conversion utilities for calendar system
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, time, timedelta
import pytz
from dateutil import tz, parser as date_parser
from zoneinfo import ZoneInfo
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TimezoneInfo:
    """Detailed timezone information"""
    name: str
    display_name: str
    offset: str
    dst_offset: str
    is_dst_active: bool
    utc_offset_seconds: int
    dst_offset_seconds: int
    region: str
    country: str
    aliases: List[str]

@dataclass
class TimezoneConversion:
    """Result of timezone conversion"""
    original_datetime: datetime
    converted_datetime: datetime
    from_timezone: str
    to_timezone: str
    from_offset: str
    to_offset: str
    is_dst_change: bool

class TimezoneService:
    """Comprehensive timezone handling service"""
    
    def __init__(self):
        self.common_timezones = self._load_common_timezones()
        self.business_timezones = self._load_business_timezones()
        self.timezone_aliases = self._load_timezone_aliases()
    
    def _load_common_timezones(self) -> Dict[str, TimezoneInfo]:
        """Load commonly used timezones with detailed information"""
        common_zones = [
            # UTC and GMT
            'UTC', 'GMT',
            
            # US Timezones
            'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific',
            'US/Alaska', 'US/Hawaii',
            'America/New_York', 'America/Chicago', 'America/Denver', 
            'America/Los_Angeles', 'America/Anchorage', 'Pacific/Honolulu',
            
            # European Timezones
            'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome',
            'Europe/Madrid', 'Europe/Amsterdam', 'Europe/Vienna', 'Europe/Prague',
            'Europe/Stockholm', 'Europe/Helsinki', 'Europe/Moscow',
            
            # Asian Timezones
            'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore',
            'Asia/Seoul', 'Asia/Taipei', 'Asia/Bangkok', 'Asia/Jakarta',
            'Asia/Kolkata', 'Asia/Dubai', 'Asia/Riyadh',
            
            # Australian Timezones
            'Australia/Sydney', 'Australia/Melbourne', 'Australia/Perth',
            'Australia/Adelaide', 'Australia/Darwin', 'Australia/Brisbane',
            
            # Other Major Timezones
            'Canada/Eastern', 'Canada/Central', 'Canada/Mountain', 'Canada/Pacific',
            'Brazil/East', 'America/Sao_Paulo', 'America/Mexico_City',
            'Africa/Cairo', 'Africa/Johannesburg', 'Africa/Lagos',
            'Pacific/Auckland', 'Pacific/Fiji'
        ]
        
        timezone_info = {}
        now = datetime.utcnow()
        
        for tz_name in common_zones:
            try:
                tz_info = self._get_timezone_info(tz_name, now)
                if tz_info:
                    timezone_info[tz_name] = tz_info
            except Exception as e:
                logger.warning(f"Failed to load timezone {tz_name}: {str(e)}")
        
        return timezone_info
    
    def _load_business_timezones(self) -> Dict[str, List[str]]:
        """Load business hour timezones by region"""
        return {
            'americas': [
                'America/New_York', 'America/Chicago', 'America/Denver', 
                'America/Los_Angeles', 'America/Sao_Paulo', 'America/Mexico_City'
            ],
            'europe': [
                'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome',
                'Europe/Madrid', 'Europe/Amsterdam', 'Europe/Moscow'
            ],
            'asia_pacific': [
                'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore',
                'Asia/Seoul', 'Asia/Kolkata', 'Australia/Sydney'
            ],
            'middle_east_africa': [
                'Asia/Dubai', 'Asia/Riyadh', 'Africa/Cairo', 'Africa/Johannesburg'
            ]
        }
    
    def _load_timezone_aliases(self) -> Dict[str, str]:
        """Load timezone aliases and common names"""
        return {
            # US Aliases
            'EST': 'US/Eastern',
            'CST': 'US/Central',
            'MST': 'US/Mountain',
            'PST': 'US/Pacific',
            'EDT': 'US/Eastern',
            'CDT': 'US/Central',
            'MDT': 'US/Mountain',
            'PDT': 'US/Pacific',
            
            # European Aliases
            'CET': 'Europe/Paris',
            'EET': 'Europe/Helsinki',
            'WET': 'Europe/London',
            'BST': 'Europe/London',
            'CEST': 'Europe/Paris',
            'EEST': 'Europe/Helsinki',
            
            # Other Common Aliases
            'JST': 'Asia/Tokyo',
            'KST': 'Asia/Seoul',
            'IST': 'Asia/Kolkata',
            'CST_CHINA': 'Asia/Shanghai',
            'AEST': 'Australia/Sydney',
            'AEDT': 'Australia/Sydney',
        }
    
    def _get_timezone_info(self, tz_name: str, reference_dt: datetime) -> Optional[TimezoneInfo]:
        """Get detailed information about a timezone"""
        try:
            tz = pytz.timezone(tz_name)
            
            # Get timezone info for the reference datetime
            localized_dt = tz.localize(reference_dt.replace(tzinfo=None))
            utc_offset = localized_dt.utcoffset()
            dst_offset = localized_dt.dst()
            
            # Calculate offsets
            utc_offset_seconds = int(utc_offset.total_seconds())
            dst_offset_seconds = int(dst_offset.total_seconds()) if dst_offset else 0
            
            # Format offset strings
            offset_hours, offset_remainder = divmod(abs(utc_offset_seconds), 3600)
            offset_minutes = offset_remainder // 60
            offset_str = f"{'+'if utc_offset_seconds >= 0 else '-'}{offset_hours:02d}:{offset_minutes:02d}"
            
            if dst_offset_seconds:
                dst_hours, dst_remainder = divmod(abs(dst_offset_seconds), 3600)
                dst_minutes = dst_remainder // 60
                dst_offset_str = f"{'+'if dst_offset_seconds >= 0 else '-'}{dst_hours:02d}:{dst_minutes:02d}"
            else:
                dst_offset_str = "+00:00"
            
            # Extract region and country
            parts = tz_name.split('/')
            region = parts[0] if len(parts) > 1 else "Unknown"
            country = parts[1] if len(parts) > 1 else tz_name
            
            # Get display name
            display_name = self._get_display_name(tz_name, localized_dt)
            
            return TimezoneInfo(
                name=tz_name,
                display_name=display_name,
                offset=offset_str,
                dst_offset=dst_offset_str,
                is_dst_active=bool(dst_offset_seconds),
                utc_offset_seconds=utc_offset_seconds,
                dst_offset_seconds=dst_offset_seconds,
                region=region,
                country=country,
                aliases=self._get_aliases_for_timezone(tz_name)
            )
            
        except Exception as e:
            logger.error(f"Failed to get timezone info for {tz_name}: {str(e)}")
            return None
    
    def _get_display_name(self, tz_name: str, localized_dt: datetime) -> str:
        """Get human-readable display name for timezone"""
        display_names = {
            'UTC': 'Coordinated Universal Time',
            'GMT': 'Greenwich Mean Time',
            'US/Eastern': 'Eastern Time (US & Canada)',
            'US/Central': 'Central Time (US & Canada)',
            'US/Mountain': 'Mountain Time (US & Canada)',
            'US/Pacific': 'Pacific Time (US & Canada)',
            'Europe/London': 'London, Dublin, Edinburgh',
            'Europe/Paris': 'Paris, Brussels, Amsterdam',
            'Europe/Berlin': 'Berlin, Frankfurt, Vienna',
            'Asia/Tokyo': 'Tokyo, Osaka, Sapporo',
            'Asia/Shanghai': 'Beijing, Shanghai, Hong Kong',
            'Australia/Sydney': 'Sydney, Melbourne, Canberra'
        }
        
        if tz_name in display_names:
            return display_names[tz_name]
        
        # Generate display name from timezone name
        parts = tz_name.split('/')
        if len(parts) == 2:
            region, city = parts
            city = city.replace('_', ' ')
            return f"{city} ({region})"
        
        return tz_name.replace('_', ' ')
    
    def _get_aliases_for_timezone(self, tz_name: str) -> List[str]:
        """Get aliases for a timezone"""
        aliases = []
        for alias, canonical in self.timezone_aliases.items():
            if canonical == tz_name:
                aliases.append(alias)
        return aliases
    
    def get_timezone_info(self, timezone_name: str) -> Optional[TimezoneInfo]:
        """Get information about a specific timezone"""
        # Resolve alias if needed
        resolved_name = self.timezone_aliases.get(timezone_name, timezone_name)
        
        if resolved_name in self.common_timezones:
            return self.common_timezones[resolved_name]
        
        # Try to load it dynamically
        return self._get_timezone_info(resolved_name, datetime.utcnow())
    
    def list_timezones(self, region: Optional[str] = None) -> List[TimezoneInfo]:
        """List available timezones, optionally filtered by region"""
        timezones = list(self.common_timezones.values())
        
        if region:
            timezones = [tz for tz in timezones if tz.region.lower() == region.lower()]
        
        return sorted(timezones, key=lambda x: (x.region, x.name))
    
    def search_timezones(self, query: str) -> List[TimezoneInfo]:
        """Search timezones by name, city, or country"""
        query = query.lower()
        results = []
        
        for tz_info in self.common_timezones.values():
            if (query in tz_info.name.lower() or 
                query in tz_info.display_name.lower() or
                query in tz_info.country.lower() or
                any(query in alias.lower() for alias in tz_info.aliases)):
                results.append(tz_info)
        
        return sorted(results, key=lambda x: x.name)
    
    def convert_datetime(self, dt: datetime, from_tz: str, to_tz: str) -> TimezoneConversion:
        """Convert datetime between timezones"""
        try:
            # Resolve timezone aliases
            from_tz_resolved = self.timezone_aliases.get(from_tz, from_tz)
            to_tz_resolved = self.timezone_aliases.get(to_tz, to_tz)
            
            # Get timezone objects
            from_timezone = pytz.timezone(from_tz_resolved)
            to_timezone = pytz.timezone(to_tz_resolved)
            
            # Handle different input formats
            if dt.tzinfo is None:
                # Assume datetime is in the source timezone
                localized_dt = from_timezone.localize(dt)
            elif dt.tzinfo.zone != from_tz_resolved:
                # Convert to source timezone first
                localized_dt = dt.astimezone(from_timezone)
            else:
                localized_dt = dt
            
            # Convert to target timezone
            converted_dt = localized_dt.astimezone(to_timezone)
            
            # Get offset information
            from_offset = localized_dt.strftime('%z')
            to_offset = converted_dt.strftime('%z')
            
            # Check if DST changed
            is_dst_change = (localized_dt.dst() != converted_dt.dst())
            
            return TimezoneConversion(
                original_datetime=localized_dt,
                converted_datetime=converted_dt,
                from_timezone=from_tz_resolved,
                to_timezone=to_tz_resolved,
                from_offset=from_offset,
                to_offset=to_offset,
                is_dst_change=is_dst_change
            )
            
        except Exception as e:
            logger.error(f"Failed to convert datetime: {str(e)}")
            raise ValueError(f"Invalid timezone conversion: {str(e)}")
    
    def convert_to_utc(self, dt: datetime, source_tz: str) -> datetime:
        """Convert datetime to UTC"""
        conversion = self.convert_datetime(dt, source_tz, 'UTC')
        return conversion.converted_datetime
    
    def convert_from_utc(self, utc_dt: datetime, target_tz: str) -> datetime:
        """Convert UTC datetime to target timezone"""
        if utc_dt.tzinfo is None:
            utc_dt = pytz.UTC.localize(utc_dt)
        
        conversion = self.convert_datetime(utc_dt, 'UTC', target_tz)
        return conversion.converted_datetime
    
    def get_business_hours_overlap(self, timezones: List[str], 
                                  business_start: time = time(9, 0),
                                  business_end: time = time(17, 0)) -> Dict[str, Any]:
        """Find overlapping business hours across multiple timezones"""
        # Convert business hours to UTC for each timezone
        today = date.today()
        business_periods = []
        
        for tz_name in timezones:
            try:
                tz = pytz.timezone(tz_name)
                
                # Create business start and end times
                start_dt = datetime.combine(today, business_start)
                end_dt = datetime.combine(today, business_end)
                
                # Localize to timezone
                start_localized = tz.localize(start_dt)
                end_localized = tz.localize(end_dt)
                
                # Convert to UTC
                start_utc = start_localized.astimezone(pytz.UTC)
                end_utc = end_localized.astimezone(pytz.UTC)
                
                business_periods.append({
                    'timezone': tz_name,
                    'start_utc': start_utc,
                    'end_utc': end_utc,
                    'start_local': start_localized,
                    'end_local': end_localized
                })
                
            except Exception as e:
                logger.error(f"Failed to process timezone {tz_name}: {str(e)}")
        
        if not business_periods:
            return {'overlap_start': None, 'overlap_end': None, 'overlap_duration': 0}
        
        # Find overlap
        latest_start = max(period['start_utc'] for period in business_periods)
        earliest_end = min(period['end_utc'] for period in business_periods)
        
        if latest_start < earliest_end:
            overlap_duration = (earliest_end - latest_start).total_seconds() / 3600
            return {
                'overlap_start_utc': latest_start,
                'overlap_end_utc': earliest_end,
                'overlap_duration_hours': overlap_duration,
                'has_overlap': True,
                'timezone_periods': business_periods
            }
        else:
            return {
                'overlap_start_utc': None,
                'overlap_end_utc': None,
                'overlap_duration_hours': 0,
                'has_overlap': False,
                'timezone_periods': business_periods
            }
    
    def suggest_meeting_times(self, attendee_timezones: List[str],
                            meeting_duration_hours: float = 1.0,
                            preferred_hours: Tuple[int, int] = (9, 17),
                            days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Suggest optimal meeting times for attendees in different timezones"""
        suggestions = []
        
        for day_offset in range(days_ahead):
            target_date = date.today() + timedelta(days=day_offset)
            
            # Skip weekends for business meetings
            if target_date.weekday() >= 5:
                continue
            
            # Check each hour in the preferred range
            for hour in range(preferred_hours[0], preferred_hours[1]):
                meeting_start = datetime.combine(target_date, time(hour, 0))
                meeting_end = meeting_start + timedelta(hours=meeting_duration_hours)
                
                # Check if this time works for all attendees
                attendee_times = []
                all_in_business_hours = True
                
                for tz_name in attendee_timezones:
                    try:
                        # Convert meeting time to attendee's timezone
                        local_start = self.convert_from_utc(
                            pytz.UTC.localize(meeting_start), tz_name
                        )
                        local_end = self.convert_from_utc(
                            pytz.UTC.localize(meeting_end), tz_name
                        )
                        
                        # Check if it's within business hours
                        start_hour = local_start.hour
                        end_hour = local_end.hour
                        
                        if not (9 <= start_hour <= 17 and 9 <= end_hour <= 17):
                            all_in_business_hours = False
                        
                        attendee_times.append({
                            'timezone': tz_name,
                            'local_start': local_start,
                            'local_end': local_end,
                            'in_business_hours': 9 <= start_hour <= 17 and 9 <= end_hour <= 17
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to process timezone {tz_name}: {str(e)}")
                        all_in_business_hours = False
                
                if attendee_times:
                    score = sum(1 for at in attendee_times if at['in_business_hours']) / len(attendee_times)
                    
                    suggestions.append({
                        'utc_start': meeting_start,
                        'utc_end': meeting_end,
                        'date': target_date,
                        'attendee_times': attendee_times,
                        'all_in_business_hours': all_in_business_hours,
                        'business_hours_score': score,
                        'recommendation': 'excellent' if score >= 0.8 else 'good' if score >= 0.6 else 'fair'
                    })
        
        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x['business_hours_score'], reverse=True)
        return suggestions[:10]
    
    def detect_timezone_from_string(self, time_string: str) -> Optional[str]:
        """Detect timezone from a time string"""
        # Common timezone patterns
        timezone_patterns = [
            (r'\b(UTC|GMT)\b', 'UTC'),
            (r'\b(EST|Eastern)\b', 'US/Eastern'),
            (r'\b(CST|Central)\b', 'US/Central'),
            (r'\b(MST|Mountain)\b', 'US/Mountain'),
            (r'\b(PST|Pacific)\b', 'US/Pacific'),
            (r'\b(CET)\b', 'Europe/Paris'),
            (r'\b(JST)\b', 'Asia/Tokyo'),
            (r'\b(IST)\b', 'Asia/Kolkata'),
            (r'[+-]\d{2}:?\d{2}', None)  # Offset format
        ]
        
        time_string_upper = time_string.upper()
        
        for pattern, timezone in timezone_patterns:
            if re.search(pattern, time_string_upper):
                if timezone:
                    return timezone
                else:
                    # Extract offset and try to map to timezone
                    offset_match = re.search(r'([+-]\d{2}):?(\d{2})', time_string)
                    if offset_match:
                        hours = int(offset_match.group(1))
                        return self._offset_to_timezone(hours)
        
        return None
    
    def _offset_to_timezone(self, hours_offset: int) -> Optional[str]:
        """Map UTC offset to common timezone"""
        offset_mapping = {
            -8: 'US/Pacific',
            -7: 'US/Mountain',
            -6: 'US/Central',
            -5: 'US/Eastern',
            0: 'UTC',
            1: 'Europe/Paris',
            2: 'Europe/Helsinki',
            5: 'Asia/Kolkata',
            8: 'Asia/Shanghai',
            9: 'Asia/Tokyo',
            10: 'Australia/Sydney'
        }
        
        return offset_mapping.get(hours_offset)
    
    def validate_timezone(self, timezone_name: str) -> bool:
        """Validate if timezone name is valid"""
        try:
            resolved_name = self.timezone_aliases.get(timezone_name, timezone_name)
            pytz.timezone(resolved_name)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    def get_dst_transitions(self, timezone_name: str, year: int) -> List[Dict[str, Any]]:
        """Get DST transition dates for a timezone in a given year"""
        try:
            tz = pytz.timezone(timezone_name)
            transitions = []
            
            # Check transitions throughout the year
            for month in range(1, 13):
                for day in [1, 15]:
                    try:
                        dt = datetime(year, month, day)
                        localized = tz.localize(dt)
                        
                        # Check if DST is active
                        dst_offset = localized.dst()
                        is_dst = dst_offset.total_seconds() > 0
                        
                        transitions.append({
                            'date': dt.date(),
                            'is_dst_active': is_dst,
                            'utc_offset': localized.utcoffset(),
                            'dst_offset': dst_offset
                        })
                    except Exception:
                        continue
            
            # Find actual transition points
            actual_transitions = []
            for i in range(1, len(transitions)):
                if transitions[i]['is_dst_active'] != transitions[i-1]['is_dst_active']:
                    actual_transitions.append({
                        'date': transitions[i]['date'],
                        'transition_type': 'spring_forward' if transitions[i]['is_dst_active'] else 'fall_back',
                        'from_dst': transitions[i-1]['is_dst_active'],
                        'to_dst': transitions[i]['is_dst_active']
                    })
            
            return actual_transitions
            
        except Exception as e:
            logger.error(f"Failed to get DST transitions for {timezone_name}: {str(e)}")
            return []

# Global instance
timezone_service = TimezoneService()