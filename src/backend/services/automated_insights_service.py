"""
Automated Insights and Alerting Service for proactive productivity management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from loguru import logger
from dataclasses import dataclass
from enum import Enum

from src.backend.models.analytics import (
    AnalyticsInsights, ActivityEvent, ProductivityMetrics, 
    TimeTracking, KPITracking
)
from src.backend.models.user import User
from src.backend.models.task import Task, TaskStatus
from src.backend.models.workspace import Workspace
from src.backend.services.analytics_service import AnalyticsQueryService, AnalyticsInsightsService
from src.backend.services.predictive_analytics_service import PredictiveAnalyticsService


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of automated alerts."""
    PRODUCTIVITY_DROP = "productivity_drop"
    OVERWORK_DETECTED = "overwork_detected"
    DEADLINE_RISK = "deadline_risk"
    GOAL_ACHIEVEMENT = "goal_achievement"
    TEAM_IMBALANCE = "team_imbalance"
    BURNOUT_RISK = "burnout_risk"
    CAPACITY_ALERT = "capacity_alert"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass
class AutomatedAlert:
    """Data class for automated alerts."""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    user_id: Optional[int]
    team_id: Optional[int]
    workspace_id: Optional[int]
    triggered_at: datetime
    data: Dict[str, Any]
    suggested_actions: List[str]
    expires_at: Optional[datetime] = None


@dataclass
class AutomatedInsight:
    """Data class for automated insights."""
    insight_type: str
    category: str
    title: str
    description: str
    impact_level: str
    confidence_score: float
    user_id: Optional[int]
    team_id: Optional[int]
    workspace_id: Optional[int]
    generated_at: datetime
    supporting_data: Dict[str, Any]
    recommended_actions: List[str]


class AutomatedInsightsService:
    """Service for generating automated insights and alerts."""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsQueryService(db)
        self.insights_service = AnalyticsInsightsService(db)
        self.predictive_service = PredictiveAnalyticsService(db)
    
    async def run_automated_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive automated analysis and generate insights/alerts.
        """
        try:
            logger.info("Starting automated analysis cycle")
            
            results = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "insights_generated": 0,
                "alerts_triggered": 0,
                "users_analyzed": 0,
                "workspaces_analyzed": 0,
                "errors": []
            }
            
            # Get active users and workspaces
            active_users = await self._get_active_users()
            active_workspaces = await self._get_active_workspaces()
            
            results["users_analyzed"] = len(active_users)
            results["workspaces_analyzed"] = len(active_workspaces)
            
            # Generate insights and alerts for each user
            for user_id in active_users:
                try:
                    user_insights = await self._analyze_user_productivity(user_id)
                    user_alerts = await self._check_user_alerts(user_id)
                    
                    # Store insights and alerts
                    for insight in user_insights:
                        await self._store_insight(insight)
                        results["insights_generated"] += 1
                    
                    for alert in user_alerts:
                        await self._trigger_alert(alert)
                        results["alerts_triggered"] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to analyze user {user_id}: {e}")
                    results["errors"].append(f"User {user_id}: {str(e)}")
            
            # Generate insights and alerts for each workspace
            for workspace_id in active_workspaces:
                try:
                    workspace_insights = await self._analyze_workspace_performance(workspace_id)
                    workspace_alerts = await self._check_workspace_alerts(workspace_id)
                    
                    for insight in workspace_insights:
                        await self._store_insight(insight)
                        results["insights_generated"] += 1
                    
                    for alert in workspace_alerts:
                        await self._trigger_alert(alert)
                        results["alerts_triggered"] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to analyze workspace {workspace_id}: {e}")
                    results["errors"].append(f"Workspace {workspace_id}: {str(e)}")
            
            # Generate team-level insights
            team_insights = await self._analyze_team_patterns()
            for insight in team_insights:
                await self._store_insight(insight)
                results["insights_generated"] += 1
            
            # Check for system-wide anomalies
            system_alerts = await self._check_system_anomalies()
            for alert in system_alerts:
                await self._trigger_alert(alert)
                results["alerts_triggered"] += 1
            
            logger.info(f"Automated analysis completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run automated analysis: {e}")
            raise
    
    async def _get_active_users(self, days_back: int = 7) -> List[int]:
        """Get list of users who have been active recently."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            active_user_ids = self.db.query(ActivityEvent.user_id).filter(
                and_(
                    ActivityEvent.user_id.isnot(None),
                    ActivityEvent.timestamp >= cutoff_date
                )
            ).distinct().all()
            
            return [user_id[0] for user_id in active_user_ids]
            
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
    
    async def _get_active_workspaces(self, days_back: int = 7) -> List[int]:
        """Get list of workspaces that have been active recently."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            active_workspace_ids = self.db.query(ActivityEvent.workspace_id).filter(
                and_(
                    ActivityEvent.workspace_id.isnot(None),
                    ActivityEvent.timestamp >= cutoff_date
                )
            ).distinct().all()
            
            return [workspace_id[0] for workspace_id in active_workspace_ids]
            
        except Exception as e:
            logger.error(f"Failed to get active workspaces: {e}")
            return []
    
    async def _analyze_user_productivity(self, user_id: int) -> List[AutomatedInsight]:
        """Analyze individual user productivity and generate insights."""
        insights = []
        
        try:
            # Get productivity summary
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            summary = await self.analytics_service.get_user_productivity_summary(
                user_id, start_date, end_date
            )
            
            # Check for productivity trends
            productivity_insight = await self._analyze_productivity_trends(user_id, summary)
            if productivity_insight:
                insights.append(productivity_insight)
            
            # Check time management patterns
            time_insight = await self._analyze_time_patterns(user_id, summary)
            if time_insight:
                insights.append(time_insight)
            
            # Check collaboration patterns
            collaboration_insight = await self._analyze_collaboration_patterns(user_id, summary)
            if collaboration_insight:
                insights.append(collaboration_insight)
            
            # Check goal progress
            goal_insight = await self._analyze_goal_progress(user_id)
            if goal_insight:
                insights.append(goal_insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze user productivity for {user_id}: {e}")
            return []
    
    async def _check_user_alerts(self, user_id: int) -> List[AutomatedAlert]:
        """Check for conditions that should trigger user alerts."""
        alerts = []
        
        try:
            # Check for productivity drops
            productivity_alert = await self._check_productivity_drop(user_id)
            if productivity_alert:
                alerts.append(productivity_alert)
            
            # Check for overwork
            overwork_alert = await self._check_overwork(user_id)
            if overwork_alert:
                alerts.append(overwork_alert)
            
            # Check for burnout risk
            burnout_alert = await self._check_burnout_risk(user_id)
            if burnout_alert:
                alerts.append(burnout_alert)
            
            # Check deadline risks
            deadline_alerts = await self._check_deadline_risks(user_id)
            alerts.extend(deadline_alerts)
            
            # Check KPI alerts
            kpi_alerts = await self._check_kpi_alerts(user_id)
            alerts.extend(kpi_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check user alerts for {user_id}: {e}")
            return []
    
    async def _analyze_productivity_trends(
        self, 
        user_id: int, 
        summary: Dict[str, Any]
    ) -> Optional[AutomatedInsight]:
        """Analyze productivity trends and generate insights."""
        try:
            completion_rate = summary.get("task_metrics", {}).get("completion_rate", 0)
            trend = summary.get("productivity_scores", {}).get("trend", "stable")
            
            if completion_rate < 50:
                return AutomatedInsight(
                    insight_type="performance_analysis",
                    category="productivity",
                    title="Low Task Completion Rate Detected",
                    description=f"Your task completion rate is {completion_rate:.1f}%, which is below optimal levels. This suggests tasks may be too large or there are blocking issues.",
                    impact_level="medium",
                    confidence_score=85.0,
                    user_id=user_id,
                    team_id=None,
                    workspace_id=None,
                    generated_at=datetime.utcnow(),
                    supporting_data={
                        "completion_rate": completion_rate,
                        "trend": trend,
                        "benchmark": 75.0
                    },
                    recommended_actions=[
                        "Break down large tasks into smaller, manageable subtasks",
                        "Identify and resolve any blocking issues",
                        "Review task prioritization and deadlines"
                    ]
                )
            
            elif completion_rate > 90 and trend == "increasing":
                return AutomatedInsight(
                    insight_type="performance_analysis",
                    category="productivity",
                    title="Exceptional Task Completion Performance",
                    description=f"Outstanding! You're completing {completion_rate:.1f}% of your tasks with an upward trend. Consider sharing your successful strategies with the team.",
                    impact_level="low",
                    confidence_score=90.0,
                    user_id=user_id,
                    team_id=None,
                    workspace_id=None,
                    generated_at=datetime.utcnow(),
                    supporting_data={
                        "completion_rate": completion_rate,
                        "trend": trend
                    },
                    recommended_actions=[
                        "Document successful work strategies",
                        "Consider mentoring team members",
                        "Look for opportunities to take on stretch goals"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to analyze productivity trends: {e}")
            return None
    
    async def _check_productivity_drop(self, user_id: int) -> Optional[AutomatedAlert]:
        """Check for significant productivity drops."""
        try:
            # Get recent productivity metrics
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=14)
            
            recent_metrics = self.db.query(ProductivityMetrics).filter(
                and_(
                    ProductivityMetrics.user_id == user_id,
                    ProductivityMetrics.date >= start_date,
                    ProductivityMetrics.period_type == "daily"
                )
            ).order_by(ProductivityMetrics.date).all()
            
            if len(recent_metrics) < 7:
                return None
            
            # Compare first week vs second week
            first_week = recent_metrics[:7]
            second_week = recent_metrics[7:14] if len(recent_metrics) >= 14 else recent_metrics[7:]
            
            if not second_week:
                return None
            
            first_week_avg = sum(m.overall_productivity_score for m in first_week) / len(first_week)
            second_week_avg = sum(m.overall_productivity_score for m in second_week) / len(second_week)
            
            # Check for significant drop (>20%)
            if first_week_avg > 0 and second_week_avg < first_week_avg * 0.8:
                drop_percentage = ((first_week_avg - second_week_avg) / first_week_avg) * 100
                
                return AutomatedAlert(
                    alert_type=AlertType.PRODUCTIVITY_DROP,
                    severity=AlertSeverity.MEDIUM if drop_percentage < 30 else AlertSeverity.HIGH,
                    title="Significant Productivity Drop Detected",
                    description=f"Your productivity score has dropped by {drop_percentage:.1f}% over the past week. This may indicate workload issues, burnout, or external factors affecting performance.",
                    user_id=user_id,
                    team_id=None,
                    workspace_id=None,
                    triggered_at=datetime.utcnow(),
                    data={
                        "previous_score": first_week_avg,
                        "current_score": second_week_avg,
                        "drop_percentage": drop_percentage
                    },
                    suggested_actions=[
                        "Review recent changes in workload or priorities",
                        "Consider taking a short break to reset",
                        "Discuss any blocking issues with your manager",
                        "Assess if task complexity has increased significantly"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check productivity drop for user {user_id}: {e}")
            return None
    
    async def _check_overwork(self, user_id: int) -> Optional[AutomatedAlert]:
        """Check for overwork patterns."""
        try:
            # Get recent time tracking data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            time_entries = self.db.query(TimeTracking).filter(
                and_(
                    TimeTracking.user_id == user_id,
                    TimeTracking.start_time >= start_date,
                    TimeTracking.end_time.isnot(None)
                )
            ).all()
            
            if not time_entries:
                return None
            
            # Calculate total hours
            total_seconds = sum(entry.duration_seconds or 0 for entry in time_entries)
            total_hours = total_seconds / 3600
            days_tracked = len(set(entry.start_time.date() for entry in time_entries))
            
            if days_tracked > 0:
                avg_daily_hours = total_hours / days_tracked
                
                # Alert if averaging more than 10 hours per day
                if avg_daily_hours > 10:
                    return AutomatedAlert(
                        alert_type=AlertType.OVERWORK_DETECTED,
                        severity=AlertSeverity.HIGH if avg_daily_hours > 12 else AlertSeverity.MEDIUM,
                        title="Excessive Work Hours Detected",
                        description=f"You've been working an average of {avg_daily_hours:.1f} hours per day over the past week. This level of work intensity may lead to burnout and decreased productivity.",
                        user_id=user_id,
                        team_id=None,
                        workspace_id=None,
                        triggered_at=datetime.utcnow(),
                        data={
                            "avg_daily_hours": avg_daily_hours,
                            "total_hours": total_hours,
                            "days_tracked": days_tracked
                        },
                        suggested_actions=[
                            "Consider delegating some tasks to team members",
                            "Review task priorities and defer non-essential work",
                            "Schedule regular breaks and respect work-life boundaries",
                            "Discuss workload concerns with your manager"
                        ]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check overwork for user {user_id}: {e}")
            return None
    
    async def _check_deadline_risks(self, user_id: int) -> List[AutomatedAlert]:
        """Check for tasks at risk of missing deadlines."""
        alerts = []
        
        try:
            # Get tasks approaching deadlines
            now = datetime.utcnow()
            warning_threshold = now + timedelta(days=3)  # 3 days ahead
            critical_threshold = now + timedelta(days=1)  # 1 day ahead
            
            at_risk_tasks = self.db.query(Task).filter(
                and_(
                    Task.user_id == user_id,
                    Task.status != TaskStatus.COMPLETED,
                    Task.due_date.isnot(None),
                    Task.due_date <= warning_threshold
                )
            ).all()
            
            if at_risk_tasks:
                critical_tasks = [t for t in at_risk_tasks if t.due_date <= critical_threshold]
                warning_tasks = [t for t in at_risk_tasks if t.due_date > critical_threshold]
                
                if critical_tasks:
                    alerts.append(AutomatedAlert(
                        alert_type=AlertType.DEADLINE_RISK,
                        severity=AlertSeverity.CRITICAL,
                        title="Tasks Due Within 24 Hours",
                        description=f"You have {len(critical_tasks)} task(s) due within the next 24 hours that are not yet completed.",
                        user_id=user_id,
                        team_id=None,
                        workspace_id=None,
                        triggered_at=datetime.utcnow(),
                        data={
                            "critical_tasks": len(critical_tasks),
                            "task_titles": [t.title for t in critical_tasks[:5]]  # Limit to 5
                        },
                        suggested_actions=[
                            "Prioritize these tasks immediately",
                            "Consider extending deadlines if possible",
                            "Delegate or seek help if tasks cannot be completed alone",
                            "Communicate potential delays to stakeholders"
                        ]
                    ))
                
                if warning_tasks:
                    alerts.append(AutomatedAlert(
                        alert_type=AlertType.DEADLINE_RISK,
                        severity=AlertSeverity.MEDIUM,
                        title="Upcoming Task Deadlines",
                        description=f"You have {len(warning_tasks)} task(s) due within the next 3 days.",
                        user_id=user_id,
                        team_id=None,
                        workspace_id=None,
                        triggered_at=datetime.utcnow(),
                        data={
                            "warning_tasks": len(warning_tasks),
                            "task_titles": [t.title for t in warning_tasks[:5]]
                        },
                        suggested_actions=[
                            "Plan your time to ensure these tasks are completed",
                            "Break down complex tasks into smaller steps",
                            "Clear your schedule of non-essential activities"
                        ]
                    ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check deadline risks for user {user_id}: {e}")
            return []
    
    async def _check_kpi_alerts(self, user_id: int) -> List[AutomatedAlert]:
        """Check for KPI-related alerts."""
        alerts = []
        
        try:
            # Get user's KPIs that are at risk
            at_risk_kpis = self.db.query(KPITracking).filter(
                and_(
                    KPITracking.user_id == user_id,
                    KPITracking.status == "active",
                    KPITracking.end_date >= datetime.utcnow(),
                    or_(
                        KPITracking.progress_percentage < 50,  # Behind schedule
                        and_(
                            KPITracking.alert_threshold.isnot(None),
                            KPITracking.current_value < KPITracking.alert_threshold
                        )
                    )
                )
            ).all()
            
            for kpi in at_risk_kpis:
                days_remaining = (kpi.end_date - datetime.utcnow()).days
                expected_progress = 100 * (1 - days_remaining / (kpi.end_date - kpi.start_date).days)
                
                if kpi.progress_percentage < expected_progress * 0.8:  # 20% behind expected
                    alerts.append(AutomatedAlert(
                        alert_type=AlertType.GOAL_ACHIEVEMENT,
                        severity=AlertSeverity.MEDIUM,
                        title=f"KPI '{kpi.name}' Behind Schedule",
                        description=f"Your KPI '{kpi.name}' is at {kpi.progress_percentage:.1f}% completion but should be around {expected_progress:.1f}% by now.",
                        user_id=user_id,
                        team_id=None,
                        workspace_id=None,
                        triggered_at=datetime.utcnow(),
                        data={
                            "kpi_id": kpi.id,
                            "kpi_name": kpi.name,
                            "current_progress": kpi.progress_percentage,
                            "expected_progress": expected_progress,
                            "days_remaining": days_remaining
                        },
                        suggested_actions=[
                            "Review the KPI target and adjust if necessary",
                            "Increase effort allocation to this goal",
                            "Break down remaining work into daily actions",
                            "Consider if external factors are affecting progress"
                        ]
                    ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check KPI alerts for user {user_id}: {e}")
            return []
    
    async def _store_insight(self, insight: AutomatedInsight) -> None:
        """Store insight in the database."""
        try:
            db_insight = AnalyticsInsights(
                user_id=insight.user_id,
                team_id=insight.team_id,
                workspace_id=insight.workspace_id,
                insight_type=insight.insight_type,
                category=insight.category,
                title=insight.title,
                description=insight.description,
                impact_level=insight.impact_level,
                confidence_score=insight.confidence_score,
                supporting_data=insight.supporting_data,
                recommended_actions=insight.recommended_actions,
                status="new"
            )
            
            self.db.add(db_insight)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store insight: {e}")
            self.db.rollback()
    
    async def _trigger_alert(self, alert: AutomatedAlert) -> None:
        """Trigger an alert (store and potentially send notifications)."""
        try:
            # Store alert in database (you might need to create an alerts table)
            logger.info(f"Alert triggered: {alert.title} for user {alert.user_id}")
            
            # Here you would implement notification logic:
            # - Send email notifications
            # - Push notifications
            # - Slack/Teams integration
            # - In-app notifications
            
            # For now, just log the alert
            logger.warning(f"ALERT [{alert.severity.upper()}]: {alert.title} - {alert.description}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    # Placeholder methods for additional analysis
    async def _analyze_time_patterns(self, user_id: int, summary: Dict[str, Any]) -> Optional[AutomatedInsight]:
        """Analyze time management patterns."""
        # Implementation would analyze time distribution, focus patterns, etc.
        return None
    
    async def _analyze_collaboration_patterns(self, user_id: int, summary: Dict[str, Any]) -> Optional[AutomatedInsight]:
        """Analyze collaboration patterns."""
        # Implementation would analyze team interaction, communication frequency, etc.
        return None
    
    async def _analyze_goal_progress(self, user_id: int) -> Optional[AutomatedInsight]:
        """Analyze progress towards goals."""
        # Implementation would analyze KPI progress, goal achievement patterns, etc.
        return None
    
    async def _analyze_workspace_performance(self, workspace_id: int) -> List[AutomatedInsight]:
        """Analyze workspace-level performance."""
        # Implementation would analyze workspace productivity trends, etc.
        return []
    
    async def _check_workspace_alerts(self, workspace_id: int) -> List[AutomatedAlert]:
        """Check for workspace-level alerts."""
        # Implementation would check for workspace-specific issues
        return []
    
    async def _analyze_team_patterns(self) -> List[AutomatedInsight]:
        """Analyze team-level patterns."""
        # Implementation would analyze cross-team patterns, etc.
        return []
    
    async def _check_system_anomalies(self) -> List[AutomatedAlert]:
        """Check for system-wide anomalies."""
        # Implementation would check for unusual system-wide patterns
        return []
    
    async def _check_burnout_risk(self, user_id: int) -> Optional[AutomatedAlert]:
        """Check for burnout risk indicators."""
        try:
            # Use predictive service to calculate burnout risk
            forecast = await self.predictive_service.forecast_user_productivity(user_id)
            
            if forecast.burnout_risk_score > 70:
                return AutomatedAlert(
                    alert_type=AlertType.BURNOUT_RISK,
                    severity=AlertSeverity.HIGH if forecast.burnout_risk_score > 85 else AlertSeverity.MEDIUM,
                    title="High Burnout Risk Detected",
                    description=f"Analysis indicates a {forecast.burnout_risk_score:.1f}% burnout risk based on recent work patterns and productivity trends.",
                    user_id=user_id,
                    team_id=None,
                    workspace_id=None,
                    triggered_at=datetime.utcnow(),
                    data={
                        "burnout_risk_score": forecast.burnout_risk_score,
                        "capacity_utilization": forecast.capacity_utilization
                    },
                    suggested_actions=[
                        "Schedule time off or vacation days",
                        "Reduce workload and delegate tasks where possible",
                        "Focus on work-life balance and stress management",
                        "Consider discussing workload with your manager"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check burnout risk for user {user_id}: {e}")
            return None


# Scheduler function for running automated analysis
async def run_scheduled_analysis(db: Session):
    """Run automated analysis on a schedule."""
    try:
        service = AutomatedInsightsService(db)
        results = await service.run_automated_analysis()
        logger.info(f"Scheduled analysis completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Scheduled analysis failed: {e}")
        raise