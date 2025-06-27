"""
Analytics API endpoints for comprehensive productivity insights and data visualization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from src.backend.database.database import get_db
from src.backend.schemas.analytics import (
    AnalyticsDashboardResponse, ProductivitySummaryResponse, TeamMetricsResponse,
    TimeTrackingResponse, InsightsResponse, KPIResponse, ActivityEventCreate,
    TimeTrackingCreate, ReportGenerationRequest, AnalyticsFilterRequest
)
from src.backend.services.analytics_service import (
    AnalyticsCollectionService, AnalyticsQueryService, AnalyticsInsightsService
)
from src.backend.models.analytics import EventType, ActivityEvent, TimeTracking
from src.backend.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
) -> AnalyticsDashboardResponse:
    """
    Get comprehensive analytics dashboard data.
    """
    try:
        logger.info(f"Fetching analytics dashboard for user {user_id}, workspace {workspace_id}, team {team_id}")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query_service = AnalyticsQueryService(db)
        
        # Get user productivity summary
        productivity_summary = None
        if user_id:
            productivity_summary = await query_service.get_user_productivity_summary(
                user_id, start_date, end_date
            )
        
        # Get team metrics if team_id provided
        team_metrics = None
        if team_id:
            team_metrics = await query_service.get_team_performance_metrics(
                team_id, start_date, end_date
            )
        
        # Get workspace analytics if workspace_id provided
        workspace_analytics = None
        if workspace_id:
            workspace_analytics = await query_service.get_workspace_analytics(
                workspace_id, start_date, end_date
            )
        
        # Get recent activity events
        activity_query = db.query(ActivityEvent).filter(
            ActivityEvent.timestamp >= start_date
        )
        
        if user_id:
            activity_query = activity_query.filter(ActivityEvent.user_id == user_id)
        if workspace_id:
            activity_query = activity_query.filter(ActivityEvent.workspace_id == workspace_id)
        
        recent_activities = activity_query.order_by(
            desc(ActivityEvent.timestamp)
        ).limit(50).all()
        
        # Format activities for response
        formatted_activities = []
        for activity in recent_activities:
            formatted_activities.append({
                "id": activity.id,
                "event_type": activity.event_type,
                "category": activity.event_category,
                "timestamp": activity.timestamp.isoformat(),
                "user_id": activity.user_id,
                "workspace_id": activity.workspace_id,
                "duration_seconds": activity.duration_seconds,
                "success": activity.success,
                "properties": activity.properties or {}
            })
        
        # Get overall statistics
        total_events = db.query(ActivityEvent).filter(
            ActivityEvent.timestamp >= start_date
        ).count()
        
        active_users = db.query(ActivityEvent.user_id).filter(
            and_(
                ActivityEvent.timestamp >= start_date,
                ActivityEvent.user_id.isnot(None)
            )
        ).distinct().count()
        
        return AnalyticsDashboardResponse(
            success=True,
            period={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            overview={
                "total_events": total_events,
                "active_users": active_users,
                "data_points": len(formatted_activities)
            },
            productivity_summary=productivity_summary,
            team_metrics=team_metrics,
            workspace_analytics=workspace_analytics,
            recent_activities=formatted_activities
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics dashboard: {str(e)}"
        )


@router.post("/events")
async def track_event(
    event_data: ActivityEventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Track a user activity event.
    """
    try:
        collection_service = AnalyticsCollectionService(db)
        
        event = await collection_service.track_event(
            event_type=EventType(event_data.event_type),
            user_id=event_data.user_id,
            workspace_id=event_data.workspace_id,
            task_id=event_data.task_id,
            file_id=event_data.file_id,
            properties=event_data.properties,
            metadata=event_data.metadata,
            duration_seconds=event_data.duration_seconds,
            response_time_ms=event_data.response_time_ms,
            success=event_data.success,
            error_message=event_data.error_message,
            user_agent=event_data.user_agent,
            ip_address=event_data.ip_address
        )
        
        return {
            "success": True,
            "event_id": event.id,
            "message": "Event tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track event: {str(e)}"
        )


@router.post("/time-tracking/start")
async def start_time_tracking(
    tracking_data: TimeTrackingCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Start time tracking for a user activity.
    """
    try:
        collection_service = AnalyticsCollectionService(db)
        
        time_entry = await collection_service.start_time_tracking(
            user_id=tracking_data.user_id,
            workspace_id=tracking_data.workspace_id,
            task_id=tracking_data.task_id,
            activity_type=tracking_data.activity_type,
            category=tracking_data.category,
            description=tracking_data.description,
            tags=tracking_data.tags
        )
        
        return {
            "success": True,
            "tracking_id": time_entry.id,
            "start_time": time_entry.start_time.isoformat(),
            "message": "Time tracking started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start time tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start time tracking: {str(e)}"
        )


@router.post("/time-tracking/{tracking_id}/end")
async def end_time_tracking(
    tracking_id: int,
    focus_score: Optional[float] = Query(None, ge=0, le=100),
    interruptions_count: int = Query(0, ge=0),
    breaks_count: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    End time tracking and calculate duration.
    """
    try:
        collection_service = AnalyticsCollectionService(db)
        
        time_entry = await collection_service.end_time_tracking(
            tracking_id,
            focus_score=focus_score,
            interruptions_count=interruptions_count,
            breaks_count=breaks_count
        )
        
        return {
            "success": True,
            "tracking_id": time_entry.id,
            "duration_seconds": time_entry.duration_seconds,
            "duration_hours": time_entry.duration_seconds / 3600 if time_entry.duration_seconds else 0,
            "focus_score": time_entry.focus_score,
            "message": "Time tracking ended successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to end time tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end time tracking: {str(e)}"
        )


@router.get("/time-tracking/active/{user_id}")
async def get_active_time_tracking(
    user_id: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get active time tracking sessions for a user.
    """
    try:
        active_sessions = db.query(TimeTracking).filter(
            and_(
                TimeTracking.user_id == user_id,
                TimeTracking.end_time.is_(None)
            )
        ).all()
        
        sessions = []
        for session in active_sessions:
            current_duration = (datetime.utcnow() - session.start_time).total_seconds()
            sessions.append({
                "id": session.id,
                "start_time": session.start_time.isoformat(),
                "current_duration_seconds": current_duration,
                "current_duration_hours": current_duration / 3600,
                "activity_type": session.activity_type,
                "category": session.category,
                "description": session.description,
                "workspace_id": session.workspace_id,
                "task_id": session.task_id
            })
        
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get active time tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active time tracking: {str(e)}"
        )


@router.get("/productivity/{user_id}")
async def get_user_productivity(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> ProductivitySummaryResponse:
    """
    Get comprehensive productivity analytics for a user.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query_service = AnalyticsQueryService(db)
        summary = await query_service.get_user_productivity_summary(
            user_id, start_date, end_date
        )
        
        return ProductivitySummaryResponse(
            success=True,
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get user productivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user productivity: {str(e)}"
        )


@router.get("/team/{team_id}/metrics")
async def get_team_metrics(
    team_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> TeamMetricsResponse:
    """
    Get team performance analytics and metrics.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query_service = AnalyticsQueryService(db)
        metrics = await query_service.get_team_performance_metrics(
            team_id, start_date, end_date
        )
        
        return TeamMetricsResponse(
            success=True,
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Failed to get team metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team metrics: {str(e)}"
        )


@router.get("/workspace/{workspace_id}/analytics")
async def get_workspace_analytics(
    workspace_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive workspace analytics.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query_service = AnalyticsQueryService(db)
        analytics = await query_service.get_workspace_analytics(
            workspace_id, start_date, end_date
        )
        
        return {
            "success": True,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get workspace analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace analytics: {str(e)}"
        )


@router.get("/insights/{user_id}")
async def get_productivity_insights(
    user_id: int,
    db: Session = Depends(get_db)
) -> InsightsResponse:
    """
    Get AI-powered productivity insights and recommendations.
    """
    try:
        insights_service = AnalyticsInsightsService(db)
        
        insights = await insights_service.generate_productivity_insights(user_id)
        anomalies = await insights_service.detect_productivity_anomalies(user_id)
        
        return InsightsResponse(
            success=True,
            insights=insights,
            anomalies=anomalies,
            total_insights=len(insights) + len(anomalies)
        )
        
    except Exception as e:
        logger.error(f"Failed to get productivity insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get productivity insights: {str(e)}"
        )


@router.get("/charts/task-velocity")
async def get_task_velocity_chart(
    user_id: Optional[int] = Query(None),
    workspace_id: Optional[int] = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get task velocity chart data for visualization.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily task completion data
        query = db.query(
            func.date(ActivityEvent.timestamp).label('date'),
            func.count(ActivityEvent.id).label('completed_tasks')
        ).filter(
            and_(
                ActivityEvent.event_type == EventType.TASK_COMPLETED.value,
                ActivityEvent.timestamp >= start_date,
                ActivityEvent.timestamp <= end_date
            )
        )
        
        if user_id:
            query = query.filter(ActivityEvent.user_id == user_id)
        if workspace_id:
            query = query.filter(ActivityEvent.workspace_id == workspace_id)
        
        results = query.group_by(func.date(ActivityEvent.timestamp)).all()
        
        # Create chart data
        chart_data = []
        for result in results:
            chart_data.append({
                "date": result.date.isoformat(),
                "completed_tasks": result.completed_tasks
            })
        
        # Calculate velocity metrics
        total_completed = sum(item["completed_tasks"] for item in chart_data)
        average_daily = total_completed / days if days > 0 else 0
        
        return {
            "success": True,
            "chart_data": chart_data,
            "metrics": {
                "total_completed": total_completed,
                "average_daily": round(average_daily, 2),
                "period_days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get task velocity chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task velocity chart: {str(e)}"
        )


@router.get("/charts/time-distribution")
async def get_time_distribution_chart(
    user_id: int,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get time distribution chart data by category and activity type.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get time tracking data
        time_entries = db.query(TimeTracking).filter(
            and_(
                TimeTracking.user_id == user_id,
                TimeTracking.start_time >= start_date,
                TimeTracking.start_time <= end_date,
                TimeTracking.end_time.isnot(None)
            )
        ).all()
        
        # Calculate distributions
        category_distribution = {}
        activity_distribution = {}
        
        for entry in time_entries:
            duration_hours = entry.duration_seconds / 3600 if entry.duration_seconds else 0
            
            category_distribution[entry.category] = category_distribution.get(entry.category, 0) + duration_hours
            activity_distribution[entry.activity_type] = activity_distribution.get(entry.activity_type, 0) + duration_hours
        
        # Format for chart
        category_chart = [{"name": k, "value": round(v, 2)} for k, v in category_distribution.items()]
        activity_chart = [{"name": k, "value": round(v, 2)} for k, v in activity_distribution.items()]
        
        total_hours = sum(category_distribution.values())
        
        return {
            "success": True,
            "category_distribution": category_chart,
            "activity_distribution": activity_chart,
            "total_hours": round(total_hours, 2),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Failed to get time distribution chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time distribution chart: {str(e)}"
        )


@router.get("/charts/activity-heatmap")
async def get_activity_heatmap(
    user_id: Optional[int] = Query(None),
    workspace_id: Optional[int] = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get activity heatmap data showing patterns by hour and day.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(ActivityEvent).filter(
            and_(
                ActivityEvent.timestamp >= start_date,
                ActivityEvent.timestamp <= end_date
            )
        )
        
        if user_id:
            query = query.filter(ActivityEvent.user_id == user_id)
        if workspace_id:
            query = query.filter(ActivityEvent.workspace_id == workspace_id)
        
        events = query.all()
        
        # Create heatmap data
        heatmap_data = {}
        hourly_totals = {}
        daily_totals = {}
        
        for event in events:
            hour = event.timestamp.hour
            day_name = event.timestamp.strftime('%A')
            date_str = event.timestamp.strftime('%Y-%m-%d')
            
            # Heatmap by day of week and hour
            key = f"{day_name}-{hour}"
            heatmap_data[key] = heatmap_data.get(key, 0) + 1
            
            # Hourly totals
            hourly_totals[hour] = hourly_totals.get(hour, 0) + 1
            
            # Daily totals
            daily_totals[date_str] = daily_totals.get(date_str, 0) + 1
        
        # Format heatmap data for visualization
        formatted_heatmap = []
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in days_of_week:
            for hour in range(24):
                key = f"{day}-{hour}"
                formatted_heatmap.append({
                    "day": day,
                    "hour": hour,
                    "value": heatmap_data.get(key, 0)
                })
        
        # Format hourly data
        hourly_chart = [{"hour": h, "count": hourly_totals.get(h, 0)} for h in range(24)]
        
        # Get most active hours
        peak_hours = sorted(hourly_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "success": True,
            "heatmap_data": formatted_heatmap,
            "hourly_distribution": hourly_chart,
            "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
            "total_events": len(events),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Failed to get activity heatmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity heatmap: {str(e)}"
        )


@router.get("/export/report")
async def generate_analytics_report(
    user_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    workspace_id: Optional[int] = Query(None),
    format: str = Query("pdf", regex="^(pdf|csv|xlsx)$"),
    days: int = Query(30, ge=1, le=365),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate and export analytics report in specified format.
    """
    try:
        # This would typically be handled by a background task
        # For now, return a placeholder response
        
        report_id = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Add background task for report generation
        background_tasks.add_task(
            _generate_report_background,
            report_id=report_id,
            user_id=user_id,
            team_id=team_id,
            workspace_id=workspace_id,
            format=format,
            days=days,
            db=db
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "status": "generating",
            "format": format,
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "message": f"Report generation started. Check status with report ID: {report_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate analytics report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics report: {str(e)}"
        )


async def _generate_report_background(
    report_id: str,
    user_id: Optional[int],
    team_id: Optional[int],
    workspace_id: Optional[int],
    format: str,
    days: int,
    db: Session
):
    """Background task for generating reports."""
    try:
        logger.info(f"Starting background report generation: {report_id}")
        
        # Simulate report generation
        await asyncio.sleep(2)
        
        logger.info(f"Report generated successfully: {report_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate report {report_id}: {e}")


@router.get("/predict/project-completion/{workspace_id}")
async def predict_project_completion(
    workspace_id: int,
    include_historical: bool = Query(True, description="Include historical data in prediction"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Predict project completion date for a workspace.
    """
    try:
        from src.backend.services.predictive_analytics_service import PredictiveAnalyticsService
        
        predictive_service = PredictiveAnalyticsService(db)
        prediction = await predictive_service.predict_project_completion(
            workspace_id, include_historical
        )
        
        return {
            "success": True,
            "prediction": {
                "workspace_id": prediction.workspace_id,
                "estimated_completion_date": prediction.estimated_completion_date.isoformat(),
                "confidence_level": prediction.confidence_level,
                "current_progress": prediction.current_progress,
                "velocity_trend": prediction.velocity_trend,
                "risk_factors": prediction.risk_factors,
                "recommended_actions": prediction.recommended_actions
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to predict project completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict project completion: {str(e)}"
        )


@router.get("/predict/user-productivity/{user_id}")
async def predict_user_productivity(
    user_id: int,
    forecast_days: int = Query(30, ge=7, le=365, description="Number of days to forecast"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Forecast user productivity for the specified period.
    """
    try:
        from src.backend.services.predictive_analytics_service import PredictiveAnalyticsService
        
        predictive_service = PredictiveAnalyticsService(db)
        forecast = await predictive_service.forecast_user_productivity(user_id, forecast_days)
        
        return {
            "success": True,
            "forecast": {
                "user_id": forecast.user_id,
                "forecast_period_days": forecast.forecast_period_days,
                "predicted_task_completion": forecast.predicted_task_completion,
                "predicted_focus_hours": forecast.predicted_focus_hours,
                "productivity_trend": forecast.productivity_trend,
                "burnout_risk_score": forecast.burnout_risk_score,
                "capacity_utilization": forecast.capacity_utilization,
                "recommendations": forecast.recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to forecast user productivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forecast user productivity: {str(e)}"
        )


@router.get("/predict/team-capacity/{team_id}")
async def predict_team_capacity(
    team_id: int,
    forecast_days: int = Query(30, ge=7, le=365, description="Number of days to forecast"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Predict team capacity and workload distribution.
    """
    try:
        from src.backend.services.predictive_analytics_service import PredictiveAnalyticsService
        
        predictive_service = PredictiveAnalyticsService(db)
        prediction = await predictive_service.predict_team_capacity(team_id, forecast_days)
        
        return {
            "success": True,
            "prediction": prediction
        }
        
    except Exception as e:
        logger.error(f"Failed to predict team capacity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict team capacity: {str(e)}"
        )


@router.post("/insights/run-analysis")
async def run_automated_analysis(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger automated insights analysis.
    """
    try:
        from src.backend.services.automated_insights_service import AutomatedInsightsService
        
        # Run analysis in background
        insights_service = AutomatedInsightsService(db)
        background_tasks.add_task(insights_service.run_automated_analysis)
        
        return {
            "success": True,
            "message": "Automated analysis started",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Failed to start automated analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start automated analysis: {str(e)}"
        )


@router.get("/insights/latest")
async def get_latest_insights(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of insights to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get latest automated insights.
    """
    try:
        from src.backend.models.analytics import AnalyticsInsights
        
        query = db.query(AnalyticsInsights).filter(
            AnalyticsInsights.status == "new"
        )
        
        if user_id:
            query = query.filter(AnalyticsInsights.user_id == user_id)
        if team_id:
            query = query.filter(AnalyticsInsights.team_id == team_id)
        if workspace_id:
            query = query.filter(AnalyticsInsights.workspace_id == workspace_id)
        
        insights = query.order_by(
            desc(AnalyticsInsights.created_at)
        ).limit(limit).all()
        
        formatted_insights = []
        for insight in insights:
            formatted_insights.append({
                "id": insight.id,
                "insight_type": insight.insight_type,
                "category": insight.category,
                "title": insight.title,
                "description": insight.description,
                "impact_level": insight.impact_level,
                "confidence_score": insight.confidence_score,
                "user_id": insight.user_id,
                "team_id": insight.team_id,
                "workspace_id": insight.workspace_id,
                "created_at": insight.created_at.isoformat(),
                "supporting_data": insight.supporting_data or {},
                "recommended_actions": insight.recommended_actions or [],
                "status": insight.status
            })
        
        return {
            "success": True,
            "insights": formatted_insights,
            "total_count": len(formatted_insights)
        }
        
    except Exception as e:
        logger.error(f"Failed to get latest insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest insights: {str(e)}"
        )


@router.post("/insights/{insight_id}/acknowledge")
async def acknowledge_insight(
    insight_id: int,
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Acknowledge an insight (mark as read/acted upon).
    """
    try:
        from src.backend.models.analytics import AnalyticsInsights
        
        insight = db.query(AnalyticsInsights).filter(
            AnalyticsInsights.id == insight_id
        ).first()
        
        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insight not found"
            )
        
        insight.status = "acknowledged"
        insight.acknowledged_at = datetime.utcnow()
        insight.acknowledged_by = user_id
        
        db.commit()
        
        return {
            "success": True,
            "message": "Insight acknowledged successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge insight: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge insight: {str(e)}"
        )


@router.get("/alerts/active")
async def get_active_alerts(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200, description="Number of alerts to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get active alerts (placeholder implementation).
    """
    try:
        # This would query an alerts table when implemented
        # For now, return sample data
        sample_alerts = [
            {
                "id": 1,
                "alert_type": "productivity_drop",
                "severity": "medium",
                "title": "Productivity Drop Detected",
                "description": "Your productivity has decreased by 25% this week",
                "user_id": user_id,
                "triggered_at": datetime.utcnow().isoformat(),
                "suggested_actions": [
                    "Review recent workload changes",
                    "Consider taking a short break"
                ]
            }
        ] if user_id else []
        
        return {
            "success": True,
            "alerts": sample_alerts,
            "total_count": len(sample_alerts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active alerts: {str(e)}"
        )


@router.get("/health")
async def analytics_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint for analytics services.
    """
    try:
        # Test database connection
        event_count = db.query(ActivityEvent).count()
        
        return {
            "status": "healthy",
            "service": "analytics",
            "database": "connected",
            "total_events": event_count,
            "message": "Analytics service is operational"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service unhealthy: {str(e)}"
        )