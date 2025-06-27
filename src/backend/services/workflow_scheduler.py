"""
Workflow Scheduler Service

This service handles scheduled workflow execution, cron job management,
and automatic workflow triggers based on time and events.
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from croniter import croniter
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger
import threading
from concurrent.futures import ThreadPoolExecutor

from src.backend.database.database import SessionLocal
from src.backend.crud.crud_workflow import (
    crud_workflow, crud_workflow_trigger, crud_workflow_execution
)
from src.backend.models.workflow import (
    WorkflowTrigger, WorkflowSchedule, TriggerType, WorkflowStatus
)
from src.backend.services.workflow_execution_engine import workflow_execution_engine


class WorkflowScheduler:
    """Service for scheduling and managing workflow executions"""
    
    def __init__(self):
        self.running = False
        self.scheduler_task = None
        self.check_interval = 60  # Check every minute
        self.scheduled_jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
    
    async def start(self):
        """Start the workflow scheduler"""
        if self.running:
            logger.warning("Workflow scheduler is already running")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Workflow scheduler started")
    
    async def stop(self):
        """Stop the workflow scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        logger.info("Workflow scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_scheduled_workflows()
                await self._check_event_triggers()
                await self._cleanup_completed_schedules()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_scheduled_workflows(self):
        """Check for scheduled workflows that need to be executed"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Get scheduled triggers that are due
            scheduled_triggers = db.query(WorkflowTrigger).filter(
                and_(
                    WorkflowTrigger.trigger_type == TriggerType.SCHEDULE,
                    WorkflowTrigger.is_enabled == True,
                    WorkflowTrigger.cron_expression.isnot(None)
                )
            ).all()
            
            for trigger in scheduled_triggers:
                try:
                    if await self._should_execute_scheduled_trigger(trigger, now):
                        await self._execute_scheduled_workflow(db, trigger)
                except Exception as e:
                    logger.error(f"Error processing scheduled trigger {trigger.id}: {e}")
                    
        finally:
            db.close()
    
    async def _should_execute_scheduled_trigger(
        self, 
        trigger: WorkflowTrigger, 
        current_time: datetime
    ) -> bool:
        """Check if a scheduled trigger should be executed"""
        try:
            # Parse cron expression
            timezone = pytz.timezone(trigger.timezone)
            local_time = current_time.replace(tzinfo=pytz.UTC).astimezone(timezone)
            
            cron = croniter(trigger.cron_expression, local_time)
            
            # Check if we're within the execution window
            last_execution_time = cron.get_prev(datetime)
            next_execution_time = cron.get_next(datetime)
            
            # If last triggered time is None or before the last scheduled time, execute
            if (not trigger.last_triggered_at or 
                trigger.last_triggered_at < last_execution_time.replace(tzinfo=None)):
                
                # Make sure we're not too early (within 1 minute of scheduled time)
                time_until_next = (next_execution_time - local_time).total_seconds()
                time_since_last = (local_time - last_execution_time).total_seconds()
                
                return 0 <= time_since_last <= 60  # Within 1 minute window
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating cron expression '{trigger.cron_expression}': {e}")
            return False
    
    async def _execute_scheduled_workflow(self, db: Session, trigger: WorkflowTrigger):
        """Execute a scheduled workflow"""
        try:
            # Get workflow
            workflow = db.query(crud_workflow.model).filter(
                crud_workflow.model.id == trigger.workflow_id
            ).first()
            
            if not workflow:
                logger.error(f"Workflow {trigger.workflow_id} not found for trigger {trigger.id}")
                return
            
            if workflow.status != WorkflowStatus.ACTIVE:
                logger.warning(f"Workflow {workflow.id} is not active, skipping execution")
                return
            
            # Execute workflow
            execution_id = await workflow_execution_engine.execute_workflow(
                workflow_id=workflow.id,
                trigger_id=trigger.id,
                input_data=trigger.config.get('input_data', {}),
                context={'triggered_by': 'scheduler', 'trigger_type': 'schedule'}
            )
            
            # Update trigger last triggered time
            trigger.last_triggered_at = datetime.utcnow()
            trigger.trigger_count += 1
            db.commit()
            
            logger.info(f"Scheduled workflow {workflow.id} executed with execution_id {execution_id}")
            
        except Exception as e:
            logger.error(f"Error executing scheduled workflow: {e}")
            raise
    
    async def _check_event_triggers(self):
        """Check for event-based triggers"""
        db = SessionLocal()
        try:
            # Get event triggers
            event_triggers = db.query(WorkflowTrigger).filter(
                and_(
                    WorkflowTrigger.trigger_type == TriggerType.EVENT,
                    WorkflowTrigger.is_enabled == True
                )
            ).all()
            
            for trigger in event_triggers:
                try:
                    # Check if trigger conditions are met
                    if await self._evaluate_event_trigger(trigger):
                        await self._execute_triggered_workflow(db, trigger)
                except Exception as e:
                    logger.error(f"Error processing event trigger {trigger.id}: {e}")
                    
        finally:
            db.close()
    
    async def _evaluate_event_trigger(self, trigger: WorkflowTrigger) -> bool:
        """Evaluate if an event trigger should fire"""
        event_config = trigger.config
        event_type = event_config.get('event_type')
        
        if not event_type:
            return False
        
        # Check different event types
        if event_type == 'task_status_change':
            return await self._check_task_status_event(trigger)
        elif event_type == 'file_upload':
            return await self._check_file_upload_event(trigger)
        elif event_type == 'workspace_activity':
            return await self._check_workspace_activity_event(trigger)
        elif event_type == 'user_action':
            return await self._check_user_action_event(trigger)
        
        return False
    
    async def _check_task_status_event(self, trigger: WorkflowTrigger) -> bool:
        """Check for task status change events"""
        # This would integrate with the task system to check for status changes
        # Placeholder implementation
        return False
    
    async def _check_file_upload_event(self, trigger: WorkflowTrigger) -> bool:
        """Check for file upload events"""
        # This would integrate with the file system to check for new uploads
        # Placeholder implementation
        return False
    
    async def _check_workspace_activity_event(self, trigger: WorkflowTrigger) -> bool:
        """Check for workspace activity events"""
        # This would integrate with workspace activity monitoring
        # Placeholder implementation
        return False
    
    async def _check_user_action_event(self, trigger: WorkflowTrigger) -> bool:
        """Check for user action events"""
        # This would integrate with user activity tracking
        # Placeholder implementation
        return False
    
    async def _execute_triggered_workflow(self, db: Session, trigger: WorkflowTrigger):
        """Execute a workflow triggered by an event"""
        try:
            # Similar to scheduled execution but with event context
            workflow = db.query(crud_workflow.model).filter(
                crud_workflow.model.id == trigger.workflow_id
            ).first()
            
            if not workflow or workflow.status != WorkflowStatus.ACTIVE:
                return
            
            execution_id = await workflow_execution_engine.execute_workflow(
                workflow_id=workflow.id,
                trigger_id=trigger.id,
                input_data=trigger.config.get('input_data', {}),
                context={'triggered_by': 'event', 'trigger_type': 'event'}
            )
            
            # Update trigger stats
            trigger.last_triggered_at = datetime.utcnow()
            trigger.trigger_count += 1
            db.commit()
            
            logger.info(f"Event-triggered workflow {workflow.id} executed with execution_id {execution_id}")
            
        except Exception as e:
            logger.error(f"Error executing event-triggered workflow: {e}")
    
    async def _cleanup_completed_schedules(self):
        """Clean up completed or expired schedules"""
        db = SessionLocal()
        try:
            # Clean up old execution records (keep last 1000 per workflow)
            # This would be implemented based on retention policy
            pass
        finally:
            db.close()
    
    def schedule_workflow(
        self,
        workflow_id: int,
        cron_expression: str,
        timezone: str = "UTC",
        input_data: Optional[Dict] = None,
        enabled: bool = True
    ) -> str:
        """Schedule a workflow with cron expression"""
        db = SessionLocal()
        try:
            # Validate cron expression
            try:
                croniter(cron_expression)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
            
            # Create trigger
            trigger_data = {
                "workflow_id": workflow_id,
                "name": f"Scheduled Trigger - {cron_expression}",
                "trigger_type": TriggerType.SCHEDULE,
                "cron_expression": cron_expression,
                "timezone": timezone,
                "is_enabled": enabled,
                "config": {"input_data": input_data or {}}
            }
            
            trigger = crud_workflow_trigger.create(db, obj_in=trigger_data)
            logger.info(f"Scheduled workflow {workflow_id} with trigger {trigger.id}")
            
            return trigger.id
            
        finally:
            db.close()
    
    def unschedule_workflow(self, trigger_id: int) -> bool:
        """Remove a scheduled workflow"""
        db = SessionLocal()
        try:
            trigger = crud_workflow_trigger.get(db, id=trigger_id)
            if trigger and trigger.trigger_type == TriggerType.SCHEDULE:
                crud_workflow_trigger.remove(db, id=trigger_id)
                logger.info(f"Unscheduled workflow trigger {trigger_id}")
                return True
            return False
        finally:
            db.close()
    
    def update_schedule(
        self,
        trigger_id: int,
        cron_expression: Optional[str] = None,
        timezone: Optional[str] = None,
        enabled: Optional[bool] = None,
        input_data: Optional[Dict] = None
    ) -> bool:
        """Update an existing schedule"""
        db = SessionLocal()
        try:
            trigger = crud_workflow_trigger.get(db, id=trigger_id)
            if not trigger or trigger.trigger_type != TriggerType.SCHEDULE:
                return False
            
            updates = {}
            if cron_expression is not None:
                # Validate cron expression
                try:
                    croniter(cron_expression)
                    updates["cron_expression"] = cron_expression
                except Exception as e:
                    raise ValueError(f"Invalid cron expression: {e}")
            
            if timezone is not None:
                updates["timezone"] = timezone
            
            if enabled is not None:
                updates["is_enabled"] = enabled
            
            if input_data is not None:
                config = trigger.config or {}
                config["input_data"] = input_data
                updates["config"] = config
            
            if updates:
                crud_workflow_trigger.update(db, db_obj=trigger, obj_in=updates)
                logger.info(f"Updated schedule for trigger {trigger_id}")
            
            return True
            
        finally:
            db.close()
    
    def get_scheduled_workflows(self, workspace_id: Optional[int] = None) -> List[Dict]:
        """Get all scheduled workflows"""
        db = SessionLocal()
        try:
            query = db.query(WorkflowTrigger).filter(
                WorkflowTrigger.trigger_type == TriggerType.SCHEDULE
            )
            
            if workspace_id:
                from src.backend.models.workflow import Workflow
                query = query.join(Workflow).filter(
                    Workflow.workspace_id == workspace_id
                )
            
            triggers = query.all()
            
            schedules = []
            for trigger in triggers:
                schedule_info = {
                    "trigger_id": trigger.id,
                    "workflow_id": trigger.workflow_id,
                    "workflow_name": trigger.workflow.name if trigger.workflow else "Unknown",
                    "cron_expression": trigger.cron_expression,
                    "timezone": trigger.timezone,
                    "is_enabled": trigger.is_enabled,
                    "last_triggered": trigger.last_triggered_at,
                    "trigger_count": trigger.trigger_count,
                    "next_run": self._get_next_run_time(trigger)
                }
                schedules.append(schedule_info)
            
            return schedules
            
        finally:
            db.close()
    
    def _get_next_run_time(self, trigger: WorkflowTrigger) -> Optional[datetime]:
        """Get the next run time for a scheduled trigger"""
        if not trigger.cron_expression or not trigger.is_enabled:
            return None
        
        try:
            timezone = pytz.timezone(trigger.timezone)
            now = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(timezone)
            cron = croniter(trigger.cron_expression, now)
            return cron.get_next(datetime).replace(tzinfo=None)
        except Exception:
            return None
    
    def get_schedule_statistics(self) -> Dict:
        """Get scheduler statistics"""
        db = SessionLocal()
        try:
            total_scheduled = db.query(WorkflowTrigger).filter(
                WorkflowTrigger.trigger_type == TriggerType.SCHEDULE
            ).count()
            
            active_scheduled = db.query(WorkflowTrigger).filter(
                and_(
                    WorkflowTrigger.trigger_type == TriggerType.SCHEDULE,
                    WorkflowTrigger.is_enabled == True
                )
            ).count()
            
            # Get recent executions
            recent_executions = db.query(crud_workflow_execution.model).filter(
                crud_workflow_execution.model.started_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                "total_scheduled_workflows": total_scheduled,
                "active_scheduled_workflows": active_scheduled,
                "recent_executions_24h": recent_executions,
                "scheduler_running": self.running,
                "last_check": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
    
    async def trigger_workflow_by_event(
        self,
        event_type: str,
        event_data: Dict,
        workspace_id: Optional[int] = None
    ) -> List[int]:
        """Trigger workflows based on an event"""
        db = SessionLocal()
        try:
            # Find triggers that match this event
            query = db.query(WorkflowTrigger).filter(
                and_(
                    WorkflowTrigger.trigger_type == TriggerType.EVENT,
                    WorkflowTrigger.is_enabled == True
                )
            )
            
            if workspace_id:
                from src.backend.models.workflow import Workflow
                query = query.join(Workflow).filter(
                    Workflow.workspace_id == workspace_id
                )
            
            triggers = query.all()
            execution_ids = []
            
            for trigger in triggers:
                try:
                    # Check if this trigger matches the event
                    trigger_config = trigger.config or {}
                    trigger_event_type = trigger_config.get('event_type')
                    
                    if trigger_event_type == event_type:
                        # Check additional conditions if any
                        if self._evaluate_event_conditions(trigger, event_data):
                            # Execute workflow
                            execution_id = await workflow_execution_engine.execute_workflow(
                                workflow_id=trigger.workflow_id,
                                trigger_id=trigger.id,
                                input_data=event_data,
                                context={
                                    'triggered_by': 'event',
                                    'event_type': event_type,
                                    'event_data': event_data
                                }
                            )
                            execution_ids.append(execution_id)
                            
                            # Update trigger stats
                            trigger.last_triggered_at = datetime.utcnow()
                            trigger.trigger_count += 1
                
                except Exception as e:
                    logger.error(f"Error executing event trigger {trigger.id}: {e}")
            
            if execution_ids:
                db.commit()
                logger.info(f"Event '{event_type}' triggered {len(execution_ids)} workflows")
            
            return execution_ids
            
        finally:
            db.close()
    
    def _evaluate_event_conditions(self, trigger: WorkflowTrigger, event_data: Dict) -> bool:
        """Evaluate if event data matches trigger conditions"""
        conditions = trigger.conditions or []
        
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if field not in event_data:
                return False
            
            event_value = event_data[field]
            
            if operator == 'equals' and event_value != value:
                return False
            elif operator == 'not_equals' and event_value == value:
                return False
            elif operator == 'contains' and value not in str(event_value):
                return False
            elif operator == 'greater_than' and event_value <= value:
                return False
            elif operator == 'less_than' and event_value >= value:
                return False
        
        return True


# Webhook handler for external triggers
class WorkflowWebhookHandler:
    """Handler for webhook-based workflow triggers"""
    
    def __init__(self, scheduler: WorkflowScheduler):
        self.scheduler = scheduler
    
    async def handle_webhook(
        self,
        webhook_url: str,
        payload: Dict,
        headers: Dict,
        method: str = "POST"
    ) -> Dict:
        """Handle incoming webhook and trigger workflows"""
        db = SessionLocal()
        try:
            from src.backend.models.workflow import WorkflowWebhook
            
            # Find webhook configuration
            webhook = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.webhook_url.endswith(webhook_url.split('/')[-1])
            ).first()
            
            if not webhook:
                return {"error": "Webhook not found", "status": 404}
            
            if not webhook.is_enabled:
                return {"error": "Webhook is disabled", "status": 403}
            
            # Validate method
            if method not in webhook.allowed_methods:
                return {"error": f"Method {method} not allowed", "status": 405}
            
            # Validate headers if required
            required_headers = webhook.headers or {}
            for header, expected_value in required_headers.items():
                if headers.get(header) != expected_value:
                    return {"error": f"Invalid header {header}", "status": 403}
            
            # Verify secret key if configured
            if webhook.secret_key:
                provided_signature = headers.get('X-Webhook-Signature')
                expected_signature = self._generate_webhook_signature(
                    webhook.secret_key, json.dumps(payload)
                )
                if provided_signature != expected_signature:
                    return {"error": "Invalid signature", "status": 403}
            
            # Rate limiting check
            if not self._check_rate_limit(webhook):
                return {"error": "Rate limit exceeded", "status": 429}
            
            # Execute workflow
            execution_id = await workflow_execution_engine.execute_workflow(
                workflow_id=webhook.workflow_id,
                trigger_id=webhook.trigger_id,
                input_data=payload,
                context={
                    'triggered_by': 'webhook',
                    'webhook_url': webhook_url,
                    'headers': headers
                }
            )
            
            # Update webhook stats
            webhook.request_count += 1
            webhook.last_request_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Webhook {webhook_url} triggered workflow {webhook.workflow_id}")
            
            return {
                "success": True,
                "execution_id": execution_id,
                "workflow_id": webhook.workflow_id,
                "status": 200
            }
            
        except Exception as e:
            logger.error(f"Webhook handler error: {e}")
            return {"error": str(e), "status": 500}
        finally:
            db.close()
    
    def _generate_webhook_signature(self, secret_key: str, payload: str) -> str:
        """Generate webhook signature for verification"""
        import hmac
        import hashlib
        
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _check_rate_limit(self, webhook) -> bool:
        """Check if webhook request is within rate limits"""
        # Simple rate limiting - could be improved with Redis
        if webhook.last_request_at:
            time_since_last = datetime.utcnow() - webhook.last_request_at
            if time_since_last.total_seconds() < 3600:  # 1 hour window
                hourly_requests = webhook.request_count  # Simplified
                return hourly_requests < webhook.rate_limit
        
        return True


# Global scheduler instance
workflow_scheduler = WorkflowScheduler()
webhook_handler = WorkflowWebhookHandler(workflow_scheduler)