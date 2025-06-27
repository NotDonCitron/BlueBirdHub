"""
Predictive Analytics Service for project completion forecasting and productivity predictions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from loguru import logger
import statistics
from dataclasses import dataclass

from src.backend.models.analytics import ActivityEvent, TimeTracking, ProductivityMetrics, TeamMetrics
from src.backend.models.task import Task, TaskStatus
from src.backend.models.workspace import Workspace
from src.backend.models.user import User


@dataclass
class ProjectPrediction:
    """Data class for project completion predictions."""
    project_id: Optional[int]
    workspace_id: int
    estimated_completion_date: datetime
    confidence_level: float
    current_progress: float
    velocity_trend: str
    risk_factors: List[str]
    recommended_actions: List[str]


@dataclass
class ProductivityForecast:
    """Data class for productivity forecasting."""
    user_id: int
    forecast_period_days: int
    predicted_task_completion: int
    predicted_focus_hours: float
    productivity_trend: str
    burnout_risk_score: float
    capacity_utilization: float
    recommendations: List[str]


class PredictiveAnalyticsService:
    """Service for predictive analytics and forecasting."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def predict_project_completion(
        self,
        workspace_id: int,
        include_historical_data: bool = True
    ) -> ProjectPrediction:
        """
        Predict project completion date based on current velocity and historical data.
        """
        try:
            # Get all tasks in workspace
            tasks = self.db.query(Task).filter(
                Task.workspace_id == workspace_id
            ).all()
            
            if not tasks:
                raise ValueError(f"No tasks found for workspace {workspace_id}")
            
            # Calculate current progress
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            current_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            # Get task completion velocity (tasks per day)
            velocity_data = await self._calculate_task_velocity(workspace_id)
            
            # Calculate remaining work
            remaining_tasks = total_tasks - completed_tasks
            
            # Predict completion date based on velocity
            if velocity_data['current_velocity'] > 0:
                days_remaining = remaining_tasks / velocity_data['current_velocity']
                estimated_completion = datetime.utcnow() + timedelta(days=days_remaining)
            else:
                # If no velocity, use average historical velocity or default estimate
                avg_velocity = velocity_data.get('average_velocity', 0.5)  # Default: 0.5 tasks/day
                days_remaining = remaining_tasks / avg_velocity
                estimated_completion = datetime.utcnow() + timedelta(days=days_remaining)
            
            # Calculate confidence level based on velocity consistency
            confidence = self._calculate_confidence_level(velocity_data)
            
            # Identify risk factors
            risk_factors = await self._identify_risk_factors(workspace_id, velocity_data)
            
            # Generate recommendations
            recommendations = await self._generate_project_recommendations(
                workspace_id, velocity_data, risk_factors
            )
            
            return ProjectPrediction(
                project_id=None,  # Could be enhanced to support project-level tracking
                workspace_id=workspace_id,
                estimated_completion_date=estimated_completion,
                confidence_level=confidence,
                current_progress=current_progress,
                velocity_trend=velocity_data['trend'],
                risk_factors=risk_factors,
                recommended_actions=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to predict project completion: {e}")
            raise
    
    async def forecast_user_productivity(
        self,
        user_id: int,
        forecast_days: int = 30
    ) -> ProductivityForecast:
        """
        Forecast user productivity based on historical patterns and trends.
        """
        try:
            # Get historical productivity data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)  # Look back 90 days for patterns
            
            productivity_history = self.db.query(ProductivityMetrics).filter(
                and_(
                    ProductivityMetrics.user_id == user_id,
                    ProductivityMetrics.date >= start_date,
                    ProductivityMetrics.date <= end_date,
                    ProductivityMetrics.period_type == "daily"
                )
            ).order_by(ProductivityMetrics.date).all()
            
            if not productivity_history:
                raise ValueError(f"No productivity history found for user {user_id}")
            
            # Extract time series data
            task_completions = [m.tasks_completed for m in productivity_history]
            focus_hours = [m.focus_time / 60 for m in productivity_history]  # Convert to hours
            productivity_scores = [m.overall_productivity_score for m in productivity_history]
            
            # Calculate trends and predictions
            task_trend = self._calculate_trend(task_completions)
            predicted_tasks = self._forecast_metric(task_completions, forecast_days)
            
            focus_trend = self._calculate_trend(focus_hours)
            predicted_focus = self._forecast_metric(focus_hours, forecast_days)
            
            # Calculate burnout risk
            burnout_risk = await self._calculate_burnout_risk(user_id, productivity_history)
            
            # Calculate capacity utilization
            capacity_utilization = await self._calculate_capacity_utilization(user_id)
            
            # Generate productivity trend
            overall_trend = self._determine_productivity_trend(productivity_scores)
            
            # Generate recommendations
            recommendations = await self._generate_productivity_recommendations(
                user_id, burnout_risk, capacity_utilization, overall_trend
            )
            
            return ProductivityForecast(
                user_id=user_id,
                forecast_period_days=forecast_days,
                predicted_task_completion=max(0, int(predicted_tasks)),
                predicted_focus_hours=max(0, predicted_focus),
                productivity_trend=overall_trend,
                burnout_risk_score=burnout_risk,
                capacity_utilization=capacity_utilization,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to forecast user productivity: {e}")
            raise
    
    async def predict_team_capacity(
        self,
        team_id: int,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict team capacity and workload distribution for future periods.
        """
        try:
            # Get team members - this would need to be implemented based on your team model
            # For now, we'll use a placeholder
            team_member_ids = [1, 2, 3]  # This should come from team membership
            
            # Get individual forecasts for each team member
            member_forecasts = []
            for member_id in team_member_ids:
                try:
                    forecast = await self.forecast_user_productivity(member_id, forecast_days)
                    member_forecasts.append(forecast)
                except Exception as e:
                    logger.warning(f"Failed to get forecast for user {member_id}: {e}")
            
            if not member_forecasts:
                raise ValueError(f"No forecasts available for team {team_id}")
            
            # Aggregate team predictions
            total_predicted_tasks = sum(f.predicted_task_completion for f in member_forecasts)
            total_predicted_hours = sum(f.predicted_focus_hours for f in member_forecasts)
            avg_capacity_utilization = statistics.mean([f.capacity_utilization for f in member_forecasts])
            avg_burnout_risk = statistics.mean([f.burnout_risk_score for f in member_forecasts])
            
            # Identify capacity bottlenecks
            bottlenecks = [
                f"User {f.user_id}" for f in member_forecasts 
                if f.capacity_utilization > 90 or f.burnout_risk_score > 70
            ]
            
            # Calculate workload balance
            utilizations = [f.capacity_utilization for f in member_forecasts]
            workload_balance = 100 - (statistics.stdev(utilizations) if len(utilizations) > 1 else 0)
            
            return {
                "team_id": team_id,
                "forecast_period_days": forecast_days,
                "predicted_total_tasks": total_predicted_tasks,
                "predicted_total_hours": total_predicted_hours,
                "average_capacity_utilization": avg_capacity_utilization,
                "average_burnout_risk": avg_burnout_risk,
                "workload_balance_score": workload_balance,
                "capacity_bottlenecks": bottlenecks,
                "member_forecasts": [
                    {
                        "user_id": f.user_id,
                        "predicted_tasks": f.predicted_task_completion,
                        "predicted_hours": f.predicted_focus_hours,
                        "capacity_utilization": f.capacity_utilization,
                        "burnout_risk": f.burnout_risk_score
                    }
                    for f in member_forecasts
                ],
                "recommendations": await self._generate_team_capacity_recommendations(
                    team_id, avg_capacity_utilization, avg_burnout_risk, bottlenecks
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to predict team capacity: {e}")
            raise
    
    async def _calculate_task_velocity(self, workspace_id: int) -> Dict[str, Any]:
        """Calculate task completion velocity for a workspace."""
        try:
            # Get task completion events from the last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Get daily task completions
            daily_completions = self.db.query(
                func.date(ActivityEvent.timestamp).label('date'),
                func.count().label('completions')
            ).filter(
                and_(
                    ActivityEvent.workspace_id == workspace_id,
                    ActivityEvent.event_type == 'task_completed',
                    ActivityEvent.timestamp >= start_date,
                    ActivityEvent.timestamp <= end_date
                )
            ).group_by(func.date(ActivityEvent.timestamp)).all()
            
            if not daily_completions:
                return {
                    'current_velocity': 0,
                    'average_velocity': 0,
                    'trend': 'stable',
                    'velocity_history': []
                }
            
            # Convert to list of completions per day
            velocity_data = [completion.completions for completion in daily_completions]
            
            # Calculate current velocity (last 7 days average)
            current_velocity = statistics.mean(velocity_data[-7:]) if len(velocity_data) >= 7 else statistics.mean(velocity_data)
            
            # Calculate overall average
            average_velocity = statistics.mean(velocity_data)
            
            # Determine trend
            trend = self._calculate_trend(velocity_data)
            
            return {
                'current_velocity': current_velocity,
                'average_velocity': average_velocity,
                'trend': trend,
                'velocity_history': velocity_data
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate task velocity: {e}")
            return {
                'current_velocity': 0,
                'average_velocity': 0,
                'trend': 'stable',
                'velocity_history': []
            }
    
    def _calculate_confidence_level(self, velocity_data: Dict[str, Any]) -> float:
        """Calculate confidence level based on velocity consistency."""
        try:
            history = velocity_data.get('velocity_history', [])
            if len(history) < 7:
                return 50.0  # Low confidence with insufficient data
            
            # Calculate coefficient of variation (std dev / mean)
            if velocity_data['average_velocity'] > 0:
                std_dev = statistics.stdev(history)
                cv = std_dev / velocity_data['average_velocity']
                
                # Convert to confidence percentage (lower variation = higher confidence)
                confidence = max(20, 100 - (cv * 100))
                return min(confidence, 95)  # Cap at 95%
            
            return 30.0  # Low confidence if no velocity
            
        except Exception:
            return 40.0  # Default confidence
    
    async def _identify_risk_factors(
        self, 
        workspace_id: int, 
        velocity_data: Dict[str, Any]
    ) -> List[str]:
        """Identify potential risk factors for project completion."""
        risk_factors = []
        
        try:
            # Low velocity risk
            if velocity_data['current_velocity'] < velocity_data['average_velocity'] * 0.7:
                risk_factors.append("Declining task completion velocity")
            
            # Inconsistent velocity
            history = velocity_data.get('velocity_history', [])
            if len(history) > 5:
                std_dev = statistics.stdev(history)
                mean_velocity = statistics.mean(history)
                if mean_velocity > 0 and (std_dev / mean_velocity) > 0.5:
                    risk_factors.append("Highly variable task completion rate")
            
            # Check for overdue tasks
            overdue_tasks = self.db.query(Task).filter(
                and_(
                    Task.workspace_id == workspace_id,
                    Task.due_date < datetime.utcnow(),
                    Task.status != TaskStatus.COMPLETED
                )
            ).count()
            
            if overdue_tasks > 0:
                risk_factors.append(f"{overdue_tasks} overdue tasks affecting timeline")
            
            # Check team capacity issues
            # This would require team membership data
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Failed to identify risk factors: {e}")
            return ["Unable to assess project risks"]
    
    async def _generate_project_recommendations(
        self,
        workspace_id: int,
        velocity_data: Dict[str, Any],
        risk_factors: List[str]
    ) -> List[str]:
        """Generate actionable recommendations for project success."""
        recommendations = []
        
        try:
            # Velocity-based recommendations
            if velocity_data['current_velocity'] < velocity_data['average_velocity']:
                recommendations.append("Consider breaking down large tasks into smaller, manageable chunks")
                recommendations.append("Review and remove blockers that may be slowing progress")
            
            # Risk-based recommendations
            if "overdue" in ' '.join(risk_factors).lower():
                recommendations.append("Prioritize completion of overdue tasks to get back on track")
                recommendations.append("Review task priorities and adjust timeline expectations")
            
            if "variable" in ' '.join(risk_factors).lower():
                recommendations.append("Implement more consistent work planning and time-boxing")
                recommendations.append("Establish daily standups to maintain steady progress")
            
            # General recommendations
            if velocity_data['trend'] == 'decreasing':
                recommendations.append("Investigate causes of declining productivity")
                recommendations.append("Consider team morale and workload distribution")
            
            # Default recommendations if none specific
            if not recommendations:
                recommendations.extend([
                    "Maintain current pace and monitor progress regularly",
                    "Continue with established working patterns",
                    "Plan for potential scope changes or timeline adjustments"
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Continue monitoring project progress and adjust as needed"]
    
    async def _calculate_burnout_risk(
        self, 
        user_id: int, 
        productivity_history: List
    ) -> float:
        """Calculate burnout risk score based on productivity patterns."""
        try:
            if not productivity_history:
                return 0.0
            
            # Factors that indicate burnout risk
            recent_data = productivity_history[-14:]  # Last 2 weeks
            
            # Check for declining productivity scores
            productivity_scores = [m.overall_productivity_score for m in recent_data if m.overall_productivity_score > 0]
            if len(productivity_scores) > 5:
                trend = self._calculate_trend(productivity_scores)
                declining_productivity = 20 if trend == 'decreasing' else 0
            else:
                declining_productivity = 0
            
            # Check for excessive work hours
            total_active_times = [m.total_active_time for m in recent_data]
            avg_daily_minutes = statistics.mean(total_active_times) if total_active_times else 0
            excessive_hours = min(30, max(0, (avg_daily_minutes - 480) / 10))  # Above 8 hours
            
            # Check for low focus scores
            focus_scores = [m.focus_score for m in recent_data if m.focus_score > 0]
            low_focus = 15 if focus_scores and statistics.mean(focus_scores) < 60 else 0
            
            # Check for weekend work (would need day-of-week data)
            weekend_work = 0  # Placeholder
            
            # Calculate overall burnout risk
            burnout_risk = declining_productivity + excessive_hours + low_focus + weekend_work
            
            return min(100, burnout_risk)
            
        except Exception as e:
            logger.error(f"Failed to calculate burnout risk: {e}")
            return 0.0
    
    async def _calculate_capacity_utilization(self, user_id: int) -> float:
        """Calculate user's capacity utilization percentage."""
        try:
            # Get recent time tracking data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=14)
            
            time_entries = self.db.query(TimeTracking).filter(
                and_(
                    TimeTracking.user_id == user_id,
                    TimeTracking.start_time >= start_date,
                    TimeTracking.start_time <= end_date,
                    TimeTracking.end_time.isnot(None)
                )
            ).all()
            
            if not time_entries:
                return 0.0
            
            # Calculate total tracked hours
            total_seconds = sum(entry.duration_seconds or 0 for entry in time_entries)
            total_hours = total_seconds / 3600
            
            # Calculate workdays in period (assuming 5-day work week)
            days_in_period = (end_date - start_date).days
            workdays = days_in_period * (5/7)  # Approximate workdays
            
            # Assume 8-hour workday capacity
            total_capacity_hours = workdays * 8
            
            if total_capacity_hours > 0:
                utilization = (total_hours / total_capacity_hours) * 100
                return min(100, utilization)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate capacity utilization: {e}")
            return 0.0
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 3:
            return "stable"
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        # Calculate slope of best fit line
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _forecast_metric(self, historical_values: List[float], forecast_days: int) -> float:
        """Simple forecast based on historical trend."""
        if not historical_values:
            return 0.0
        
        # Calculate recent average and trend
        recent_avg = statistics.mean(historical_values[-7:]) if len(historical_values) >= 7 else statistics.mean(historical_values)
        
        # Apply trend factor
        trend = self._calculate_trend(historical_values)
        if trend == "increasing":
            trend_factor = 1.1
        elif trend == "decreasing":
            trend_factor = 0.9
        else:
            trend_factor = 1.0
        
        # Project forward
        forecasted_daily = recent_avg * trend_factor
        return forecasted_daily * forecast_days
    
    def _determine_productivity_trend(self, productivity_scores: List[float]) -> str:
        """Determine overall productivity trend."""
        if not productivity_scores:
            return "stable"
        
        # Look at recent trend vs historical average
        if len(productivity_scores) > 14:
            recent_avg = statistics.mean(productivity_scores[-7:])
            historical_avg = statistics.mean(productivity_scores[:-7])
            
            if recent_avg > historical_avg * 1.1:
                return "improving"
            elif recent_avg < historical_avg * 0.9:
                return "declining"
        
        return self._calculate_trend(productivity_scores)
    
    async def _generate_productivity_recommendations(
        self,
        user_id: int,
        burnout_risk: float,
        capacity_utilization: float,
        trend: str
    ) -> List[str]:
        """Generate personalized productivity recommendations."""
        recommendations = []
        
        # Burnout risk recommendations
        if burnout_risk > 70:
            recommendations.extend([
                "Consider taking breaks to prevent burnout",
                "Review workload and prioritize essential tasks",
                "Discuss capacity concerns with your manager"
            ])
        elif burnout_risk > 40:
            recommendations.append("Monitor stress levels and maintain work-life balance")
        
        # Capacity utilization recommendations
        if capacity_utilization > 100:
            recommendations.append("Workload appears to exceed normal capacity - consider delegation")
        elif capacity_utilization < 50:
            recommendations.append("Consider taking on additional responsibilities or training")
        
        # Trend-based recommendations
        if trend == "declining":
            recommendations.extend([
                "Identify factors affecting recent productivity decline",
                "Consider adjusting work methods or seeking support"
            ])
        elif trend == "improving":
            recommendations.append("Great progress! Consider documenting what's working well")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Continue current work patterns and monitor productivity regularly")
        
        return recommendations
    
    async def _generate_team_capacity_recommendations(
        self,
        team_id: int,
        avg_capacity: float,
        avg_burnout_risk: float,
        bottlenecks: List[str]
    ) -> List[str]:
        """Generate team capacity management recommendations."""
        recommendations = []
        
        if avg_capacity > 90:
            recommendations.append("Team capacity is near maximum - consider workload redistribution")
        
        if avg_burnout_risk > 60:
            recommendations.append("Monitor team stress levels and plan recovery time")
        
        if bottlenecks:
            recommendations.append(f"Address capacity constraints for: {', '.join(bottlenecks)}")
        
        if avg_capacity < 60:
            recommendations.append("Team has available capacity for additional work")
        
        recommendations.append("Regular check-ins to monitor team health and productivity")
        
        return recommendations