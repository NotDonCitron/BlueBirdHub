"""
Analytics service for comprehensive data collection and processing.
"""

import asyncio
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from loguru import logger

from src.backend.models.analytics import (
    ActivityEvent, TimeTracking, ProductivityMetrics, TeamMetrics,
    KPITracking, AnalyticsInsights, ReportGeneration, EventType
)
from src.backend.models.user import User
from src.backend.models.workspace import Workspace
from src.backend.models.task import Task, TaskStatus
from src.backend.models.team import Team, TeamMembership
from src.backend.models.file_metadata import FileMetadata


class AnalyticsCollectionService:
    """Service for collecting and processing analytics data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def track_event(
        self,
        event_type: EventType,
        user_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        task_id: Optional[int] = None,
        file_id: Optional[int] = None,
        properties: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        duration_seconds: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> ActivityEvent:
        """Track a user activity event."""
        try:
            # Determine event category
            category = self._get_event_category(event_type)
            
            # Create activity event
            event = ActivityEvent(
                user_id=user_id,
                workspace_id=workspace_id,
                task_id=task_id,
                file_id=file_id,
                event_type=event_type.value,
                event_category=category,
                duration_seconds=duration_seconds,
                properties=properties or {},
                metadata=metadata or {},
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            # Trigger async metrics update
            asyncio.create_task(self._update_real_time_metrics(event))
            
            logger.info(f"Tracked event: {event_type.value} for user {user_id}")
            return event
            
        except Exception as e:
            logger.error(f"Failed to track event {event_type.value}: {e}")
            self.db.rollback()
            raise
    
    def _get_event_category(self, event_type: EventType) -> str:
        """Categorize events for better organization."""
        productivity_events = [
            EventType.TASK_CREATED, EventType.TASK_COMPLETED,
            EventType.TASK_UPDATED, EventType.TASK_DELETED
        ]
        collaboration_events = [
            EventType.COLLABORATION_COMMENT, EventType.COLLABORATION_MENTION,
            EventType.FILE_SHARED, EventType.MEETING_ATTENDED
        ]
        system_events = [
            EventType.LOGIN, EventType.LOGOUT, EventType.SESSION_START,
            EventType.SESSION_END, EventType.SEARCH_PERFORMED, EventType.VOICE_COMMAND_USED
        ]
        
        if event_type in productivity_events:
            return "productivity"
        elif event_type in collaboration_events:
            return "collaboration"
        elif event_type in system_events:
            return "system"
        else:
            return "other"
    
    async def start_time_tracking(
        self,
        user_id: int,
        workspace_id: Optional[int] = None,
        task_id: Optional[int] = None,
        activity_type: str = "focus",
        category: str = "work",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TimeTracking:
        """Start tracking time for a user activity."""
        try:
            # End any existing active tracking for this user
            await self.end_active_time_tracking(user_id)
            
            time_entry = TimeTracking(
                user_id=user_id,
                workspace_id=workspace_id,
                task_id=task_id,
                start_time=datetime.utcnow(),
                activity_type=activity_type,
                category=category,
                description=description,
                tags=tags
            )
            
            self.db.add(time_entry)
            self.db.commit()
            self.db.refresh(time_entry)
            
            logger.info(f"Started time tracking for user {user_id}")
            return time_entry
            
        except Exception as e:
            logger.error(f"Failed to start time tracking: {e}")
            self.db.rollback()
            raise
    
    async def end_time_tracking(
        self,
        time_tracking_id: int,
        focus_score: Optional[float] = None,
        interruptions_count: int = 0,
        breaks_count: int = 0
    ) -> TimeTracking:
        """End time tracking and calculate duration."""
        try:
            time_entry = self.db.query(TimeTracking).filter(
                TimeTracking.id == time_tracking_id
            ).first()
            
            if not time_entry:
                raise ValueError(f"Time tracking entry {time_tracking_id} not found")
            
            if time_entry.end_time:
                raise ValueError("Time tracking already ended")
            
            end_time = datetime.utcnow()
            duration = (end_time - time_entry.start_time).total_seconds()
            
            time_entry.end_time = end_time
            time_entry.duration_seconds = int(duration)
            time_entry.focus_score = focus_score
            time_entry.interruptions_count = interruptions_count
            time_entry.breaks_count = breaks_count
            
            self.db.commit()
            
            # Track completion event
            await self.track_event(
                EventType.SESSION_END,
                user_id=time_entry.user_id,
                workspace_id=time_entry.workspace_id,
                task_id=time_entry.task_id,
                duration_seconds=duration,
                properties={
                    "activity_type": time_entry.activity_type,
                    "focus_score": focus_score,
                    "interruptions": interruptions_count
                }
            )
            
            logger.info(f"Ended time tracking {time_tracking_id}, duration: {duration}s")
            return time_entry
            
        except Exception as e:
            logger.error(f"Failed to end time tracking: {e}")
            self.db.rollback()
            raise
    
    async def end_active_time_tracking(self, user_id: int) -> List[TimeTracking]:
        """End all active time tracking sessions for a user."""
        try:
            active_entries = self.db.query(TimeTracking).filter(
                and_(
                    TimeTracking.user_id == user_id,
                    TimeTracking.end_time.is_(None)
                )
            ).all()
            
            ended_entries = []
            for entry in active_entries:
                ended_entry = await self.end_time_tracking(entry.id)
                ended_entries.append(ended_entry)
            
            return ended_entries
            
        except Exception as e:
            logger.error(f"Failed to end active time tracking: {e}")
            raise
    
    async def _update_real_time_metrics(self, event: ActivityEvent):
        """Update real-time metrics based on events."""
        try:
            if not event.user_id:
                return
            
            # Update daily metrics
            today = datetime.utcnow().date()
            await self._update_daily_metrics(event.user_id, today, event)
            
        except Exception as e:
            logger.error(f"Failed to update real-time metrics: {e}")
    
    async def _update_daily_metrics(self, user_id: int, date: datetime, event: ActivityEvent):
        """Update daily productivity metrics."""
        try:
            # Get or create daily metrics
            metrics = self.db.query(ProductivityMetrics).filter(
                and_(
                    ProductivityMetrics.user_id == user_id,
                    ProductivityMetrics.date == date,
                    ProductivityMetrics.period_type == "daily"
                )
            ).first()
            
            if not metrics:
                metrics = ProductivityMetrics(
                    user_id=user_id,
                    workspace_id=event.workspace_id,
                    date=date,
                    period_type="daily"
                )
                self.db.add(metrics)
            
            # Update metrics based on event type
            if event.event_type == EventType.TASK_CREATED.value:
                metrics.tasks_created += 1
            elif event.event_type == EventType.TASK_COMPLETED.value:
                metrics.tasks_completed += 1
            elif event.event_type == EventType.COLLABORATION_COMMENT.value:
                metrics.comments_made += 1
            elif event.event_type == EventType.FILE_SHARED.value:
                metrics.files_shared += 1
            elif event.event_type == EventType.MEETING_ATTENDED.value:
                metrics.meetings_attended += 1
            elif event.event_type == EventType.LOGIN.value:
                metrics.logins_count += 1
            elif event.event_type == EventType.SEARCH_PERFORMED.value:
                metrics.search_queries += 1
            elif event.event_type == EventType.VOICE_COMMAND_USED.value:
                metrics.voice_commands_used += 1
            elif event.event_type == EventType.PLUGIN_USED.value:
                metrics.plugins_used += 1
            
            # Recalculate completion rate
            if metrics.tasks_created > 0:
                metrics.completion_rate = (metrics.tasks_completed / metrics.tasks_created) * 100
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update daily metrics: {e}")
            self.db.rollback()


class AnalyticsQueryService:
    """Service for querying analytics data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_productivity_summary(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive productivity summary for a user."""
        try:
            # Get productivity metrics
            metrics = self.db.query(ProductivityMetrics).filter(
                and_(
                    ProductivityMetrics.user_id == user_id,
                    ProductivityMetrics.date >= start_date,
                    ProductivityMetrics.date <= end_date,
                    ProductivityMetrics.period_type == "daily"
                )
            ).all()
            
            if not metrics:
                return self._empty_summary()
            
            # Calculate aggregated statistics
            total_tasks_created = sum(m.tasks_created for m in metrics)
            total_tasks_completed = sum(m.tasks_completed for m in metrics)
            total_active_time = sum(m.total_active_time for m in metrics)
            avg_productivity_score = statistics.mean([m.overall_productivity_score for m in metrics if m.overall_productivity_score > 0])
            
            # Get time tracking data
            time_entries = self.db.query(TimeTracking).filter(
                and_(
                    TimeTracking.user_id == user_id,
                    TimeTracking.start_time >= start_date,
                    TimeTracking.start_time <= end_date,
                    TimeTracking.end_time.isnot(None)
                )
            ).all()
            
            # Calculate time distribution
            time_by_category = {}
            time_by_activity = {}
            total_tracked_time = 0
            
            for entry in time_entries:
                duration_hours = entry.duration_seconds / 3600 if entry.duration_seconds else 0
                total_tracked_time += duration_hours
                
                time_by_category[entry.category] = time_by_category.get(entry.category, 0) + duration_hours
                time_by_activity[entry.activity_type] = time_by_activity.get(entry.activity_type, 0) + duration_hours
            
            # Get activity events
            events = self.db.query(ActivityEvent).filter(
                and_(
                    ActivityEvent.user_id == user_id,
                    ActivityEvent.timestamp >= start_date,
                    ActivityEvent.timestamp <= end_date
                )
            ).all()
            
            # Activity breakdown
            activity_counts = {}
            for event in events:
                activity_counts[event.event_type] = activity_counts.get(event.event_type, 0) + 1
            
            return {
                "user_id": user_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days + 1
                },
                "task_metrics": {
                    "total_created": total_tasks_created,
                    "total_completed": total_tasks_completed,
                    "completion_rate": (total_tasks_completed / total_tasks_created * 100) if total_tasks_created > 0 else 0,
                    "daily_average_created": total_tasks_created / len(metrics) if metrics else 0,
                    "daily_average_completed": total_tasks_completed / len(metrics) if metrics else 0
                },
                "time_metrics": {
                    "total_tracked_hours": total_tracked_time,
                    "average_daily_hours": total_tracked_time / len(metrics) if metrics else 0,
                    "time_by_category": time_by_category,
                    "time_by_activity": time_by_activity
                },
                "productivity_scores": {
                    "overall_average": avg_productivity_score,
                    "trend": self._calculate_trend([m.overall_productivity_score for m in metrics])
                },
                "activity_summary": activity_counts,
                "collaboration": {
                    "comments_made": sum(m.comments_made for m in metrics),
                    "files_shared": sum(m.files_shared for m in metrics),
                    "meetings_attended": sum(m.meetings_attended for m in metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get productivity summary: {e}")
            raise
    
    async def get_team_performance_metrics(
        self,
        team_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get team performance analytics."""
        try:
            # Get team members
            members = self.db.query(TeamMembership).filter(
                and_(
                    TeamMembership.team_id == team_id,
                    TeamMembership.is_active == True
                )
            ).all()
            
            member_ids = [m.user_id for m in members]
            
            if not member_ids:
                return {"error": "No active team members found"}
            
            # Get individual productivity summaries
            member_summaries = {}
            for member_id in member_ids:
                summary = await self.get_user_productivity_summary(member_id, start_date, end_date)
                member_summaries[member_id] = summary
            
            # Calculate team aggregates
            total_tasks_created = sum(s["task_metrics"]["total_created"] for s in member_summaries.values())
            total_tasks_completed = sum(s["task_metrics"]["total_completed"] for s in member_summaries.values())
            total_hours = sum(s["time_metrics"]["total_tracked_hours"] for s in member_summaries.values())
            
            # Calculate workload distribution
            workloads = [s["time_metrics"]["total_tracked_hours"] for s in member_summaries.values()]
            workload_std = statistics.stdev(workloads) if len(workloads) > 1 else 0
            workload_balance_score = max(0, 100 - (workload_std / statistics.mean(workloads) * 100)) if workloads and statistics.mean(workloads) > 0 else 0
            
            # Get team metrics from database
            team_metrics = self.db.query(TeamMetrics).filter(
                and_(
                    TeamMetrics.team_id == team_id,
                    TeamMetrics.date >= start_date,
                    TeamMetrics.date <= end_date
                )
            ).all()
            
            return {
                "team_id": team_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "team_size": len(member_ids),
                "aggregated_metrics": {
                    "total_tasks_created": total_tasks_created,
                    "total_tasks_completed": total_tasks_completed,
                    "team_completion_rate": (total_tasks_completed / total_tasks_created * 100) if total_tasks_created > 0 else 0,
                    "total_hours_worked": total_hours,
                    "average_hours_per_member": total_hours / len(member_ids) if member_ids else 0
                },
                "workload_distribution": {
                    "balance_score": workload_balance_score,
                    "standard_deviation": workload_std,
                    "member_workloads": {str(uid): s["time_metrics"]["total_tracked_hours"] for uid, s in member_summaries.items()}
                },
                "member_summaries": member_summaries,
                "collaboration_metrics": {
                    "total_comments": sum(s["collaboration"]["comments_made"] for s in member_summaries.values()),
                    "total_files_shared": sum(s["collaboration"]["files_shared"] for s in member_summaries.values()),
                    "total_meetings": sum(s["collaboration"]["meetings_attended"] for s in member_summaries.values())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get team performance metrics: {e}")
            raise
    
    async def get_workspace_analytics(
        self,
        workspace_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive workspace analytics."""
        try:
            # Get all activity in the workspace
            events = self.db.query(ActivityEvent).filter(
                and_(
                    ActivityEvent.workspace_id == workspace_id,
                    ActivityEvent.timestamp >= start_date,
                    ActivityEvent.timestamp <= end_date
                )
            ).all()
            
            # Get unique users in workspace
            user_ids = list(set(e.user_id for e in events if e.user_id))
            
            # Get tasks in workspace
            tasks = self.db.query(Task).filter(
                and_(
                    Task.workspace_id == workspace_id,
                    Task.created_at >= start_date,
                    Task.created_at <= end_date
                )
            ).all()
            
            # Get files in workspace
            files = self.db.query(FileMetadata).filter(
                and_(
                    FileMetadata.workspace_id == workspace_id,
                    FileMetadata.created_at >= start_date,
                    FileMetadata.created_at <= end_date
                )
            ).all()
            
            # Calculate activity heatmap data
            activity_by_hour = {}
            activity_by_day = {}
            
            for event in events:
                hour = event.timestamp.hour
                day = event.timestamp.strftime('%Y-%m-%d')
                
                activity_by_hour[hour] = activity_by_hour.get(hour, 0) + 1
                activity_by_day[day] = activity_by_day.get(day, 0) + 1
            
            # Task status distribution
            task_status_counts = {}
            for task in tasks:
                status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                task_status_counts[status] = task_status_counts.get(status, 0) + 1
            
            # File type distribution
            file_type_counts = {}
            for file in files:
                file_type = file.file_type or 'unknown'
                file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
            
            return {
                "workspace_id": workspace_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "overview": {
                    "active_users": len(user_ids),
                    "total_events": len(events),
                    "total_tasks": len(tasks),
                    "total_files": len(files)
                },
                "activity_patterns": {
                    "hourly_distribution": activity_by_hour,
                    "daily_activity": activity_by_day,
                    "peak_hours": sorted(activity_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
                },
                "task_metrics": {
                    "status_distribution": task_status_counts,
                    "completion_rate": (task_status_counts.get('completed', 0) / len(tasks) * 100) if tasks else 0
                },
                "file_metrics": {
                    "type_distribution": file_type_counts,
                    "total_size_mb": sum(f.file_size or 0 for f in files) / (1024 * 1024) if files else 0
                },
                "user_activity": {
                    str(uid): len([e for e in events if e.user_id == uid]) for uid in user_ids
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get workspace analytics: {e}")
            raise
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure."""
        return {
            "task_metrics": {"total_created": 0, "total_completed": 0, "completion_rate": 0},
            "time_metrics": {"total_tracked_hours": 0, "time_by_category": {}, "time_by_activity": {}},
            "productivity_scores": {"overall_average": 0, "trend": "stable"},
            "activity_summary": {},
            "collaboration": {"comments_made": 0, "files_shared": 0, "meetings_attended": 0}
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


class AnalyticsInsightsService:
    """Service for generating AI-powered insights and recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_productivity_insights(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate productivity insights for a user."""
        try:
            # Get recent productivity data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            query_service = AnalyticsQueryService(self.db)
            summary = await query_service.get_user_productivity_summary(user_id, start_date, end_date)
            
            insights = []
            
            # Task completion rate insight
            completion_rate = summary["task_metrics"]["completion_rate"]
            if completion_rate < 70:
                insights.append({
                    "type": "recommendation",
                    "category": "productivity",
                    "title": "Low Task Completion Rate",
                    "description": f"Your task completion rate is {completion_rate:.1f}%, which is below the recommended 80%. Consider breaking down large tasks into smaller, manageable subtasks.",
                    "impact_level": "medium",
                    "recommended_actions": [
                        "Break large tasks into smaller subtasks",
                        "Set more realistic deadlines",
                        "Use time-boxing techniques"
                    ]
                })
            elif completion_rate > 90:
                insights.append({
                    "type": "positive",
                    "category": "productivity",
                    "title": "Excellent Task Completion",
                    "description": f"Outstanding! You're completing {completion_rate:.1f}% of your tasks. Keep up the great work!",
                    "impact_level": "low"
                })
            
            # Time tracking insights
            total_hours = summary["time_metrics"]["total_tracked_hours"]
            if total_hours < 20:  # Less than 20 hours in 30 days
                insights.append({
                    "type": "recommendation",
                    "category": "time_management",
                    "title": "Limited Time Tracking",
                    "description": "You've tracked less than 20 hours in the past month. Better time tracking can help improve productivity awareness.",
                    "impact_level": "low",
                    "recommended_actions": [
                        "Use automatic time tracking",
                        "Set reminders to start time tracking",
                        "Track time for all work activities"
                    ]
                })
            
            # Collaboration insights
            comments = summary["collaboration"]["comments_made"]
            meetings = summary["collaboration"]["meetings_attended"]
            
            if comments < 5 and meetings < 3:
                insights.append({
                    "type": "recommendation",
                    "category": "collaboration",
                    "title": "Low Collaboration Activity",
                    "description": "Your collaboration activity seems limited. Increased team interaction can improve project outcomes.",
                    "impact_level": "medium",
                    "recommended_actions": [
                        "Participate more in team discussions",
                        "Schedule regular check-ins with teammates",
                        "Share updates on your progress"
                    ]
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate productivity insights: {e}")
            return []
    
    async def detect_productivity_anomalies(self, user_id: int) -> List[Dict[str, Any]]:
        """Detect anomalies in productivity patterns."""
        try:
            # Get daily metrics for the past 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            metrics = self.db.query(ProductivityMetrics).filter(
                and_(
                    ProductivityMetrics.user_id == user_id,
                    ProductivityMetrics.date >= start_date,
                    ProductivityMetrics.date <= end_date,
                    ProductivityMetrics.period_type == "daily"
                )
            ).order_by(ProductivityMetrics.date).all()
            
            if len(metrics) < 7:  # Need at least a week of data
                return []
            
            anomalies = []
            
            # Check for productivity score anomalies
            scores = [m.overall_productivity_score for m in metrics if m.overall_productivity_score > 0]
            if len(scores) > 3:
                avg_score = statistics.mean(scores)
                std_score = statistics.stdev(scores)
                
                # Check recent scores for significant drops
                recent_scores = scores[-7:]  # Last 7 days
                for i, score in enumerate(recent_scores):
                    if score < (avg_score - 2 * std_score):
                        date = metrics[-(7-i)].date
                        anomalies.append({
                            "type": "anomaly",
                            "category": "productivity",
                            "title": "Significant Productivity Drop",
                            "description": f"Your productivity score on {date.strftime('%Y-%m-%d')} was {score:.1f}, significantly below your average of {avg_score:.1f}.",
                            "impact_level": "high",
                            "date": date.isoformat()
                        })
            
            # Check for unusual working patterns
            daily_hours = []
            for metric in metrics:
                if metric.total_active_time > 0:
                    daily_hours.append(metric.total_active_time / 60)  # Convert to hours
            
            if len(daily_hours) > 5:
                avg_hours = statistics.mean(daily_hours)
                
                # Check for overwork patterns (>10 hours/day for multiple days)
                overwork_days = sum(1 for h in daily_hours[-7:] if h > 10)
                if overwork_days >= 3:
                    anomalies.append({
                        "type": "warning",
                        "category": "wellbeing",
                        "title": "Potential Overwork Pattern",
                        "description": f"You've worked over 10 hours for {overwork_days} days in the past week. Consider taking breaks to maintain productivity.",
                        "impact_level": "medium",
                        "recommended_actions": [
                            "Schedule regular breaks",
                            "Set daily hour limits",
                            "Consider delegation opportunities"
                        ]
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return []