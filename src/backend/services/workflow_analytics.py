"""
Workflow Analytics and Performance Monitoring Service

This service provides comprehensive analytics for workflow performance,
execution statistics, error tracking, and optimization insights.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics
import json
from loguru import logger

from src.backend.database.database import SessionLocal
from src.backend.models.workflow import (
    Workflow, WorkflowExecution, WorkflowStep, WorkflowStepExecution,
    WorkflowAnalytics, WorkflowExecutionStatus, WorkflowStatus
)
from src.backend.crud.crud_workflow import crud_workflow, crud_workflow_execution


@dataclass
class ExecutionMetrics:
    """Data class for execution metrics"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    cancelled_executions: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    success_rate: float
    failure_rate: float
    
    
@dataclass
class PerformanceMetrics:
    """Data class for performance metrics"""
    throughput_per_hour: float
    concurrent_executions: int
    queue_depth: int
    avg_step_time: float
    bottleneck_steps: List[Dict]
    resource_utilization: Dict[str, float]


@dataclass
class ErrorAnalysis:
    """Data class for error analysis"""
    total_errors: int
    error_categories: Dict[str, int]
    most_common_errors: List[Dict]
    error_trends: List[Dict]
    problematic_workflows: List[Dict]


class WorkflowAnalyticsService:
    """Service for workflow analytics and performance monitoring"""
    
    def __init__(self):
        self.analytics_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = {}
    
    def get_workflow_metrics(
        self,
        workflow_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ExecutionMetrics:
        """Get execution metrics for workflows"""
        db = SessionLocal()
        try:
            # Build base query
            query = db.query(WorkflowExecution)
            
            if workflow_id:
                query = query.filter(WorkflowExecution.workflow_id == workflow_id)
            
            if workspace_id:
                query = query.join(Workflow).filter(Workflow.workspace_id == workspace_id)
            
            if start_date:
                query = query.filter(WorkflowExecution.started_at >= start_date)
            
            if end_date:
                query = query.filter(WorkflowExecution.started_at <= end_date)
            
            executions = query.all()
            
            if not executions:
                return ExecutionMetrics(
                    total_executions=0, successful_executions=0, failed_executions=0,
                    cancelled_executions=0, avg_execution_time=0, min_execution_time=0,
                    max_execution_time=0, success_rate=0, failure_rate=0
                )
            
            # Calculate metrics
            total = len(executions)
            successful = len([e for e in executions if e.status == WorkflowExecutionStatus.COMPLETED])
            failed = len([e for e in executions if e.status == WorkflowExecutionStatus.FAILED])
            cancelled = len([e for e in executions if e.status == WorkflowExecutionStatus.CANCELLED])
            
            # Calculate execution times
            execution_times = [
                e.execution_time_seconds for e in executions 
                if e.execution_time_seconds is not None
            ]
            
            avg_time = statistics.mean(execution_times) if execution_times else 0
            min_time = min(execution_times) if execution_times else 0
            max_time = max(execution_times) if execution_times else 0
            
            success_rate = (successful / total * 100) if total > 0 else 0
            failure_rate = (failed / total * 100) if total > 0 else 0
            
            return ExecutionMetrics(
                total_executions=total,
                successful_executions=successful,
                failed_executions=failed,
                cancelled_executions=cancelled,
                avg_execution_time=avg_time,
                min_execution_time=min_time,
                max_execution_time=max_time,
                success_rate=success_rate,
                failure_rate=failure_rate
            )
            
        finally:
            db.close()
    
    def get_performance_metrics(
        self,
        workflow_id: Optional[int] = None,
        time_window_hours: int = 24
    ) -> PerformanceMetrics:
        """Get performance metrics"""
        db = SessionLocal()
        try:
            start_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            
            # Build query
            query = db.query(WorkflowExecution).filter(
                WorkflowExecution.started_at >= start_time
            )
            
            if workflow_id:
                query = query.filter(WorkflowExecution.workflow_id == workflow_id)
            
            executions = query.all()
            
            # Calculate throughput
            throughput = len(executions) / time_window_hours if time_window_hours > 0 else 0
            
            # Get concurrent executions
            concurrent = db.query(WorkflowExecution).filter(
                WorkflowExecution.status == WorkflowExecutionStatus.RUNNING
            ).count()
            
            # Get queue depth (pending executions)
            queue_depth = db.query(WorkflowExecution).filter(
                WorkflowExecution.status == WorkflowExecutionStatus.PENDING
            ).count()
            
            # Calculate average step execution time
            step_times = []
            bottleneck_steps = []
            
            for execution in executions:
                step_executions = db.query(WorkflowStepExecution).filter(
                    WorkflowStepExecution.execution_id == execution.id
                ).all()
                
                for step_exec in step_executions:
                    if step_exec.execution_time_seconds:
                        step_times.append(step_exec.execution_time_seconds)
            
            avg_step_time = statistics.mean(step_times) if step_times else 0
            
            # Identify bottleneck steps
            bottleneck_steps = self._identify_bottleneck_steps(db, workflow_id, start_time)
            
            # Resource utilization (placeholder)
            resource_utilization = {
                "cpu": 65.0,
                "memory": 45.0,
                "disk": 30.0,
                "network": 25.0
            }
            
            return PerformanceMetrics(
                throughput_per_hour=throughput,
                concurrent_executions=concurrent,
                queue_depth=queue_depth,
                avg_step_time=avg_step_time,
                bottleneck_steps=bottleneck_steps,
                resource_utilization=resource_utilization
            )
            
        finally:
            db.close()
    
    def _identify_bottleneck_steps(
        self,
        db: Session,
        workflow_id: Optional[int],
        start_time: datetime
    ) -> List[Dict]:
        """Identify steps that are performance bottlenecks"""
        query = db.query(
            WorkflowStepExecution.step_id,
            func.avg(WorkflowStepExecution.execution_time_seconds).label('avg_time'),
            func.count(WorkflowStepExecution.id).label('execution_count')
        ).filter(
            and_(
                WorkflowStepExecution.started_at >= start_time,
                WorkflowStepExecution.execution_time_seconds.isnot(None)
            )
        )
        
        if workflow_id:
            query = query.join(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id
            )
        
        step_stats = query.group_by(WorkflowStepExecution.step_id).all()
        
        # Sort by average execution time (descending)
        bottlenecks = []
        for stat in sorted(step_stats, key=lambda x: x.avg_time, reverse=True)[:5]:
            step = db.query(WorkflowStep).filter(WorkflowStep.id == stat.step_id).first()
            
            bottlenecks.append({
                "step_id": stat.step_id,
                "step_name": step.name if step else "Unknown",
                "step_type": step.step_type.value if step else "Unknown",
                "avg_execution_time": round(stat.avg_time, 2),
                "execution_count": stat.execution_count
            })
        
        return bottlenecks
    
    def get_error_analysis(
        self,
        workflow_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        days: int = 7
    ) -> ErrorAnalysis:
        """Analyze errors in workflow executions"""
        db = SessionLocal()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get failed executions
            query = db.query(WorkflowExecution).filter(
                and_(
                    WorkflowExecution.status == WorkflowExecutionStatus.FAILED,
                    WorkflowExecution.started_at >= start_date
                )
            )
            
            if workflow_id:
                query = query.filter(WorkflowExecution.workflow_id == workflow_id)
            
            if workspace_id:
                query = query.join(Workflow).filter(Workflow.workspace_id == workspace_id)
            
            failed_executions = query.all()
            
            # Categorize errors
            error_categories = defaultdict(int)
            error_messages = []
            
            for execution in failed_executions:
                if execution.error_message:
                    # Simple error categorization
                    error_msg = execution.error_message.lower()
                    
                    if 'timeout' in error_msg:
                        error_categories['timeout'] += 1
                    elif 'permission' in error_msg or 'auth' in error_msg:
                        error_categories['permission'] += 1
                    elif 'network' in error_msg or 'connection' in error_msg:
                        error_categories['network'] += 1
                    elif 'validation' in error_msg or 'invalid' in error_msg:
                        error_categories['validation'] += 1
                    elif 'not found' in error_msg or '404' in error_msg:
                        error_categories['not_found'] += 1
                    else:
                        error_categories['other'] += 1
                    
                    error_messages.append(execution.error_message)
            
            # Find most common errors
            error_counter = Counter(error_messages)
            most_common_errors = [
                {"error": error, "count": count}
                for error, count in error_counter.most_common(10)
            ]
            
            # Error trends (daily counts)
            error_trends = self._calculate_error_trends(db, start_date, workflow_id, workspace_id)
            
            # Problematic workflows
            problematic_workflows = self._identify_problematic_workflows(
                db, start_date, workspace_id
            )
            
            return ErrorAnalysis(
                total_errors=len(failed_executions),
                error_categories=dict(error_categories),
                most_common_errors=most_common_errors,
                error_trends=error_trends,
                problematic_workflows=problematic_workflows
            )
            
        finally:
            db.close()
    
    def _calculate_error_trends(
        self,
        db: Session,
        start_date: datetime,
        workflow_id: Optional[int] = None,
        workspace_id: Optional[int] = None
    ) -> List[Dict]:
        """Calculate daily error trends"""
        trends = []
        
        for i in range(7):  # Last 7 days
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            query = db.query(WorkflowExecution).filter(
                and_(
                    WorkflowExecution.status == WorkflowExecutionStatus.FAILED,
                    WorkflowExecution.started_at >= day_start,
                    WorkflowExecution.started_at < day_end
                )
            )
            
            if workflow_id:
                query = query.filter(WorkflowExecution.workflow_id == workflow_id)
            
            if workspace_id:
                query = query.join(Workflow).filter(Workflow.workspace_id == workspace_id)
            
            error_count = query.count()
            
            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "error_count": error_count
            })
        
        return trends
    
    def _identify_problematic_workflows(
        self,
        db: Session,
        start_date: datetime,
        workspace_id: Optional[int] = None
    ) -> List[Dict]:
        """Identify workflows with high failure rates"""
        query = db.query(
            WorkflowExecution.workflow_id,
            func.count(WorkflowExecution.id).label('total_executions'),
            func.sum(
                func.case(
                    [(WorkflowExecution.status == WorkflowExecutionStatus.FAILED, 1)],
                    else_=0
                )
            ).label('failed_executions')
        ).filter(WorkflowExecution.started_at >= start_date)
        
        if workspace_id:
            query = query.join(Workflow).filter(Workflow.workspace_id == workspace_id)
        
        workflow_stats = query.group_by(WorkflowExecution.workflow_id).all()
        
        problematic = []
        for stat in workflow_stats:
            if stat.total_executions >= 5:  # Only consider workflows with enough executions
                failure_rate = (stat.failed_executions / stat.total_executions) * 100
                
                if failure_rate > 20:  # More than 20% failure rate
                    workflow = db.query(Workflow).filter(
                        Workflow.id == stat.workflow_id
                    ).first()
                    
                    problematic.append({
                        "workflow_id": stat.workflow_id,
                        "workflow_name": workflow.name if workflow else "Unknown",
                        "total_executions": stat.total_executions,
                        "failed_executions": stat.failed_executions,
                        "failure_rate": round(failure_rate, 2)
                    })
        
        return sorted(problematic, key=lambda x: x["failure_rate"], reverse=True)[:10]
    
    def get_workflow_efficiency_report(
        self,
        workflow_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive efficiency report for a workflow"""
        db = SessionLocal()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError("Workflow not found")
            
            # Get executions
            executions = db.query(WorkflowExecution).filter(
                and_(
                    WorkflowExecution.workflow_id == workflow_id,
                    WorkflowExecution.started_at >= start_date
                )
            ).all()
            
            # Basic metrics
            metrics = self.get_workflow_metrics(workflow_id, start_date=start_date)
            
            # Step-level analysis
            step_analysis = self._analyze_workflow_steps(db, workflow_id, start_date)
            
            # Time distribution analysis
            time_distribution = self._analyze_execution_time_distribution(executions)
            
            # Success/failure patterns
            patterns = self._analyze_execution_patterns(executions)
            
            # Optimization recommendations
            recommendations = self._generate_optimization_recommendations(
                workflow, metrics, step_analysis
            )
            
            return {
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "total_steps": len(workflow.steps)
                },
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                    "days": days
                },
                "execution_metrics": metrics.__dict__,
                "step_analysis": step_analysis,
                "time_distribution": time_distribution,
                "execution_patterns": patterns,
                "optimization_recommendations": recommendations
            }
            
        finally:
            db.close()
    
    def _analyze_workflow_steps(
        self,
        db: Session,
        workflow_id: int,
        start_date: datetime
    ) -> List[Dict]:
        """Analyze individual step performance"""
        steps = db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == workflow_id
        ).all()
        
        step_analysis = []
        
        for step in steps:
            # Get step executions
            step_executions = db.query(WorkflowStepExecution).join(
                WorkflowExecution
            ).filter(
                and_(
                    WorkflowStepExecution.step_id == step.id,
                    WorkflowExecution.started_at >= start_date
                )
            ).all()
            
            if not step_executions:
                continue
            
            # Calculate step metrics
            total_executions = len(step_executions)
            successful = len([se for se in step_executions 
                            if se.status == WorkflowExecutionStatus.COMPLETED])
            failed = len([se for se in step_executions 
                        if se.status == WorkflowExecutionStatus.FAILED])
            
            execution_times = [se.execution_time_seconds for se in step_executions 
                             if se.execution_time_seconds is not None]
            
            avg_time = statistics.mean(execution_times) if execution_times else 0
            
            step_analysis.append({
                "step_id": step.id,
                "step_name": step.name,
                "step_type": step.step_type.value,
                "order": step.order,
                "total_executions": total_executions,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
                "avg_execution_time": round(avg_time, 2),
                "retry_count": step.retry_count,
                "timeout_seconds": step.timeout_seconds
            })
        
        return sorted(step_analysis, key=lambda x: x["order"])
    
    def _analyze_execution_time_distribution(
        self,
        executions: List[WorkflowExecution]
    ) -> Dict[str, Any]:
        """Analyze execution time distribution"""
        execution_times = [e.execution_time_seconds for e in executions 
                          if e.execution_time_seconds is not None]
        
        if not execution_times:
            return {"message": "No execution time data available"}
        
        # Calculate percentiles
        execution_times.sort()
        n = len(execution_times)
        
        return {
            "total_samples": n,
            "min_time": execution_times[0],
            "max_time": execution_times[-1],
            "median_time": execution_times[n // 2],
            "p90_time": execution_times[int(n * 0.9)],
            "p95_time": execution_times[int(n * 0.95)],
            "p99_time": execution_times[int(n * 0.99)],
            "avg_time": statistics.mean(execution_times),
            "std_dev": statistics.stdev(execution_times) if n > 1 else 0
        }
    
    def _analyze_execution_patterns(
        self,
        executions: List[WorkflowExecution]
    ) -> Dict[str, Any]:
        """Analyze execution patterns over time"""
        if not executions:
            return {"message": "No execution data available"}
        
        # Group by hour of day
        hourly_distribution = defaultdict(int)
        daily_distribution = defaultdict(int)
        
        for execution in executions:
            hour = execution.started_at.hour
            day = execution.started_at.strftime("%A")
            
            hourly_distribution[hour] += 1
            daily_distribution[day] += 1
        
        # Find peak hours
        peak_hour = max(hourly_distribution.items(), key=lambda x: x[1])
        peak_day = max(daily_distribution.items(), key=lambda x: x[1])
        
        return {
            "peak_hour": {"hour": peak_hour[0], "executions": peak_hour[1]},
            "peak_day": {"day": peak_day[0], "executions": peak_day[1]},
            "hourly_distribution": dict(hourly_distribution),
            "daily_distribution": dict(daily_distribution)
        }
    
    def _generate_optimization_recommendations(
        self,
        workflow: Workflow,
        metrics: ExecutionMetrics,
        step_analysis: List[Dict]
    ) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # High failure rate
        if metrics.failure_rate > 10:
            recommendations.append({
                "type": "error_reduction",
                "priority": "high",
                "title": "High Failure Rate Detected",
                "description": f"Workflow has {metrics.failure_rate:.1f}% failure rate. Consider reviewing error handling and step configurations.",
                "suggested_actions": [
                    "Review failed execution logs",
                    "Implement better error handling",
                    "Add retry logic to failing steps",
                    "Validate input data more thoroughly"
                ]
            })
        
        # Long execution time
        if metrics.avg_execution_time > 1800:  # 30 minutes
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "title": "Long Execution Time",
                "description": f"Average execution time is {metrics.avg_execution_time/60:.1f} minutes. Consider optimizing slow steps.",
                "suggested_actions": [
                    "Enable parallel execution if possible",
                    "Optimize slow-running steps",
                    "Break down complex steps into smaller ones",
                    "Review timeout settings"
                ]
            })
        
        # Bottleneck steps
        slow_steps = [step for step in step_analysis if step["avg_execution_time"] > 300]
        if slow_steps:
            recommendations.append({
                "type": "bottleneck",
                "priority": "medium",
                "title": "Performance Bottlenecks",
                "description": f"Found {len(slow_steps)} slow steps that may be bottlenecks.",
                "suggested_actions": [
                    f"Optimize step: {step['step_name']}" for step in slow_steps[:3]
                ] + ["Consider parallel execution", "Review step configurations"]
            })
        
        # Steps with high failure rates
        failing_steps = [step for step in step_analysis if step["success_rate"] < 90]
        if failing_steps:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "title": "Unreliable Steps",
                "description": f"Found {len(failing_steps)} steps with low success rates.",
                "suggested_actions": [
                    f"Review step: {step['step_name']} ({step['success_rate']:.1f}% success)" 
                    for step in failing_steps[:3]
                ] + ["Add error handling", "Increase retry counts"]
            })
        
        # No parallel execution for multi-step workflows
        if len(workflow.steps) > 5 and not workflow.is_parallel:
            recommendations.append({
                "type": "optimization",
                "priority": "low",
                "title": "Consider Parallel Execution",
                "description": "Workflow has multiple steps that could potentially run in parallel.",
                "suggested_actions": [
                    "Review step dependencies",
                    "Enable parallel execution where safe",
                    "Optimize step ordering"
                ]
            })
        
        return recommendations
    
    def generate_daily_analytics(self) -> None:
        """Generate and store daily analytics"""
        db = SessionLocal()
        try:
            yesterday = datetime.utcnow().date() - timedelta(days=1)
            
            # Get all active workflows
            workflows = db.query(Workflow).filter(
                Workflow.status == WorkflowStatus.ACTIVE
            ).all()
            
            for workflow in workflows:
                try:
                    # Calculate daily metrics
                    day_start = datetime.combine(yesterday, datetime.min.time())
                    day_end = day_start + timedelta(days=1)
                    
                    executions = db.query(WorkflowExecution).filter(
                        and_(
                            WorkflowExecution.workflow_id == workflow.id,
                            WorkflowExecution.started_at >= day_start,
                            WorkflowExecution.started_at < day_end
                        )
                    ).all()
                    
                    if not executions:
                        continue
                    
                    # Calculate metrics
                    total = len(executions)
                    successful = len([e for e in executions 
                                    if e.status == WorkflowExecutionStatus.COMPLETED])
                    failed = len([e for e in executions 
                                if e.status == WorkflowExecutionStatus.FAILED])
                    cancelled = len([e for e in executions 
                                   if e.status == WorkflowExecutionStatus.CANCELLED])
                    
                    execution_times = [e.execution_time_seconds for e in executions 
                                     if e.execution_time_seconds is not None]
                    
                    avg_time = statistics.mean(execution_times) if execution_times else 0
                    min_time = min(execution_times) if execution_times else 0
                    max_time = max(execution_times) if execution_times else 0
                    total_time = sum(execution_times) if execution_times else 0
                    
                    # Count timeouts and retries
                    timeout_count = len([e for e in executions 
                                       if e.status == WorkflowExecutionStatus.TIMEOUT])
                    
                    # Find most common error
                    error_messages = [e.error_message for e in executions 
                                    if e.error_message and e.status == WorkflowExecutionStatus.FAILED]
                    most_common_error = None
                    if error_messages:
                        error_counter = Counter(error_messages)
                        most_common_error = error_counter.most_common(1)[0][0]
                    
                    # Store analytics
                    analytics = WorkflowAnalytics(
                        workflow_id=workflow.id,
                        date=day_start,
                        executions_total=total,
                        executions_successful=successful,
                        executions_failed=failed,
                        executions_cancelled=cancelled,
                        avg_execution_time=avg_time,
                        min_execution_time=min_time,
                        max_execution_time=max_time,
                        total_execution_time=total_time,
                        timeout_count=timeout_count,
                        retry_count=0,  # TODO: Implement retry counting
                        most_common_error=most_common_error,
                        cpu_usage_avg=0.0,  # TODO: Implement resource monitoring
                        memory_usage_avg=0.0
                    )
                    
                    db.add(analytics)
                    
                except Exception as e:
                    logger.error(f"Error generating analytics for workflow {workflow.id}: {e}")
            
            db.commit()
            logger.info(f"Generated daily analytics for {len(workflows)} workflows")
            
        finally:
            db.close()
    
    def get_system_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Current system status
            active_executions = db.query(WorkflowExecution).filter(
                WorkflowExecution.status == WorkflowExecutionStatus.RUNNING
            ).count()
            
            pending_executions = db.query(WorkflowExecution).filter(
                WorkflowExecution.status == WorkflowExecutionStatus.PENDING
            ).count()
            
            # Today's metrics
            today_start = datetime.combine(now.date(), datetime.min.time())
            today_executions = db.query(WorkflowExecution).filter(
                WorkflowExecution.started_at >= today_start
            ).count()
            
            # Last 24 hours
            last_24h = now - timedelta(hours=24)
            recent_metrics = self.get_workflow_metrics(start_date=last_24h)
            
            # Top workflows by execution count
            top_workflows = db.query(
                Workflow.id,
                Workflow.name,
                func.count(WorkflowExecution.id).label('execution_count')
            ).join(WorkflowExecution).filter(
                WorkflowExecution.started_at >= last_24h
            ).group_by(Workflow.id, Workflow.name).order_by(
                desc('execution_count')
            ).limit(5).all()
            
            # Error summary
            error_analysis = self.get_error_analysis(days=1)
            
            return {
                "system_status": {
                    "active_executions": active_executions,
                    "pending_executions": pending_executions,
                    "today_total_executions": today_executions,
                    "timestamp": now.isoformat()
                },
                "last_24h_metrics": recent_metrics.__dict__,
                "top_workflows": [
                    {
                        "id": w.id,
                        "name": w.name,
                        "executions": w.execution_count
                    } for w in top_workflows
                ],
                "error_summary": {
                    "total_errors": error_analysis.total_errors,
                    "error_categories": error_analysis.error_categories
                }
            }
            
        finally:
            db.close()


# Global analytics service instance
workflow_analytics = WorkflowAnalyticsService()