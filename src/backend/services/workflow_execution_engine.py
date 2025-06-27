"""
Workflow Execution Engine

This service handles the execution of workflows, including step execution,
error handling, conditional logic, and parallel processing.
"""

import asyncio
import json
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.backend.crud.crud_workflow import (
    crud_workflow, crud_workflow_execution, crud_workflow_step
)
from src.backend.crud.crud_task import task
from src.backend.crud.crud_workspace import workspace
from src.backend.database.database import SessionLocal
from src.backend.models.workflow import (
    Workflow, WorkflowExecution, WorkflowStep, WorkflowStepExecution,
    WorkflowExecutionStatus, ActionType
)
from src.backend.services.ai_service import ai_service
from src.backend.services.enhanced_ai_service import enhanced_ai_service


class WorkflowExecutionEngine:
    """Engine for executing workflows with error handling and recovery"""
    
    def __init__(self):
        self.active_executions: Dict[int, asyncio.Task] = {}
        self.execution_context: Dict[int, Dict[str, Any]] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
    
    async def execute_workflow(
        self,
        workflow_id: int,
        trigger_id: Optional[int] = None,
        input_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> int:
        """Start workflow execution asynchronously"""
        db = SessionLocal()
        try:
            # Create execution record
            from src.backend.schemas.workflow import WorkflowExecutionCreate
            execution_create = WorkflowExecutionCreate(
                workflow_id=workflow_id,
                trigger_id=trigger_id,
                input_data=input_data or {},
                context=context or {}
            )
            
            execution = crud_workflow_execution.create_execution(
                db, obj_in=execution_create, user_id=user_id
            )
            
            # Start execution task
            task = asyncio.create_task(
                self._execute_workflow_async(execution.id)
            )
            self.active_executions[execution.id] = task
            
            logger.info(f"Started workflow execution {execution.id} for workflow {workflow_id}")
            return execution.id
            
        finally:
            db.close()
    
    async def _execute_workflow_async(self, execution_id: int) -> None:
        """Execute workflow asynchronously"""
        db = SessionLocal()
        try:
            # Get execution with workflow and steps
            execution = db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()
            
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return
            
            workflow = db.query(Workflow).filter(
                Workflow.id == execution.workflow_id
            ).first()
            
            if not workflow:
                logger.error(f"Workflow {execution.workflow_id} not found")
                return
            
            # Update execution status to running
            crud_workflow_execution.update_execution_status(
                db, execution_id=execution_id, status=WorkflowExecutionStatus.RUNNING
            )
            
            # Initialize execution context
            self.execution_context[execution_id] = {
                **execution.context,
                **execution.variables,
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "started_at": datetime.utcnow()
            }
            
            try:
                # Execute workflow steps
                if workflow.is_parallel:
                    await self._execute_parallel_workflow(db, execution, workflow)
                else:
                    await self._execute_sequential_workflow(db, execution, workflow)
                
                # Mark execution as completed
                crud_workflow_execution.update_execution_status(
                    db, 
                    execution_id=execution_id, 
                    status=WorkflowExecutionStatus.COMPLETED,
                    output_data=self.execution_context[execution_id]
                )
                
                logger.info(f"Workflow execution {execution_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Workflow execution {execution_id} failed: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Mark execution as failed
                crud_workflow_execution.update_execution_status(
                    db, 
                    execution_id=execution_id, 
                    status=WorkflowExecutionStatus.FAILED,
                    error_message=str(e)
                )
            
        finally:
            # Cleanup
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            if execution_id in self.execution_context:
                del self.execution_context[execution_id]
            db.close()
    
    async def _execute_sequential_workflow(
        self, 
        db: Session, 
        execution: WorkflowExecution, 
        workflow: Workflow
    ) -> None:
        """Execute workflow steps sequentially"""
        # Get ordered steps
        steps = crud_workflow_step.get_by_workflow(
            db, workflow_id=workflow.id, ordered=True
        )
        
        completed_steps = set()
        
        for step in steps:
            # Check if step dependencies are met
            if step.depends_on:
                if not all(dep_id in completed_steps for dep_id in step.depends_on):
                    logger.warning(f"Step {step.id} dependencies not met, skipping")
                    continue
            
            # Check step conditions
            if not await self._evaluate_conditions(step.conditions, execution.id):
                logger.info(f"Step {step.id} conditions not met, skipping")
                continue
            
            # Execute step
            success = await self._execute_step(db, execution.id, step)
            
            if success:
                completed_steps.add(step.id)
            else:
                # Handle step failure based on error handling strategy
                if step.on_error == "fail":
                    raise Exception(f"Step {step.name} failed and workflow is set to fail on error")
                elif step.on_error == "continue":
                    logger.warning(f"Step {step.name} failed but continuing workflow")
                    continue
                elif step.on_error == "retry":
                    # Retry logic is handled in _execute_step
                    logger.warning(f"Step {step.name} failed after retries")
                    continue
    
    async def _execute_parallel_workflow(
        self, 
        db: Session, 
        execution: WorkflowExecution, 
        workflow: Workflow
    ) -> None:
        """Execute workflow steps in parallel where possible"""
        steps = crud_workflow_step.get_by_workflow(
            db, workflow_id=workflow.id, ordered=True
        )
        
        completed_steps = set()
        pending_steps = {step.id: step for step in steps}
        
        while pending_steps:
            # Find steps that can be executed (dependencies met)
            ready_steps = []
            for step_id, step in pending_steps.items():
                if not step.depends_on or all(dep_id in completed_steps for dep_id in step.depends_on):
                    # Check conditions
                    if await self._evaluate_conditions(step.conditions, execution.id):
                        ready_steps.append(step)
            
            if not ready_steps:
                logger.warning("No more steps can be executed due to dependencies")
                break
            
            # Execute ready steps in parallel
            tasks = []
            for step in ready_steps:
                task = asyncio.create_task(self._execute_step(db, execution.id, step))
                tasks.append((step, task))
                del pending_steps[step.id]
            
            # Wait for all parallel tasks to complete
            for step, task in tasks:
                try:
                    success = await task
                    if success:
                        completed_steps.add(step.id)
                    else:
                        logger.warning(f"Parallel step {step.name} failed")
                except Exception as e:
                    logger.error(f"Parallel step {step.name} failed with error: {e}")
    
    async def _execute_step(
        self, 
        db: Session, 
        execution_id: int, 
        step: WorkflowStep
    ) -> bool:
        """Execute a single workflow step with retry logic"""
        max_attempts = step.retry_count + 1
        
        for attempt in range(max_attempts):
            try:
                # Create step execution record
                step_execution = WorkflowStepExecution(
                    execution_id=execution_id,
                    step_id=step.id,
                    attempt_number=attempt + 1,
                    started_at=datetime.utcnow(),
                    status=WorkflowExecutionStatus.RUNNING
                )
                db.add(step_execution)
                db.commit()
                db.refresh(step_execution)
                
                # Execute step based on type
                input_data = self._prepare_step_input(step, execution_id)
                output_data = await self._execute_step_action(step, input_data)
                
                # Process output mapping
                self._process_step_output(step, output_data, execution_id)
                
                # Update step execution as completed
                step_execution.status = WorkflowExecutionStatus.COMPLETED
                step_execution.completed_at = datetime.utcnow()
                step_execution.execution_time_seconds = (
                    step_execution.completed_at - step_execution.started_at
                ).total_seconds()
                step_execution.input_data = input_data
                step_execution.output_data = output_data
                
                db.commit()
                
                logger.info(f"Step {step.name} completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"Step {step.name} attempt {attempt + 1} failed: {str(e)}")
                
                # Update step execution as failed
                step_execution.status = WorkflowExecutionStatus.FAILED
                step_execution.completed_at = datetime.utcnow()
                step_execution.error_message = str(e)
                step_execution.logs = traceback.format_exc()
                
                if step_execution.started_at:
                    step_execution.execution_time_seconds = (
                        step_execution.completed_at - step_execution.started_at
                    ).total_seconds()
                
                db.commit()
                
                # If not last attempt, wait before retry
                if attempt < max_attempts - 1:
                    await asyncio.sleep(step.retry_count * 2)  # Exponential backoff
                
        return False
    
    async def _execute_step_action(
        self, 
        step: WorkflowStep, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute step action based on type"""
        action_type = step.step_type
        config = step.config
        
        if action_type == ActionType.CREATE_TASK:
            return await self._action_create_task(config, input_data)
        elif action_type == ActionType.UPDATE_TASK:
            return await self._action_update_task(config, input_data)
        elif action_type == ActionType.ASSIGN_TASK:
            return await self._action_assign_task(config, input_data)
        elif action_type == ActionType.SEND_EMAIL:
            return await self._action_send_email(config, input_data)
        elif action_type == ActionType.SEND_NOTIFICATION:
            return await self._action_send_notification(config, input_data)
        elif action_type == ActionType.CREATE_WORKSPACE:
            return await self._action_create_workspace(config, input_data)
        elif action_type == ActionType.MOVE_FILE:
            return await self._action_move_file(config, input_data)
        elif action_type == ActionType.GENERATE_REPORT:
            return await self._action_generate_report(config, input_data)
        elif action_type == ActionType.CALL_API:
            return await self._action_call_api(config, input_data)
        elif action_type == ActionType.WAIT:
            return await self._action_wait(config, input_data)
        elif action_type == ActionType.CONDITIONAL:
            return await self._action_conditional(config, input_data)
        elif action_type == ActionType.APPROVAL:
            return await self._action_approval(config, input_data)
        elif action_type == ActionType.AI_ANALYSIS:
            return await self._action_ai_analysis(config, input_data)
        elif action_type == ActionType.WEBHOOK_CALL:
            return await self._action_webhook_call(config, input_data)
        else:
            raise ValueError(f"Unsupported action type: {action_type}")
    
    def _prepare_step_input(self, step: WorkflowStep, execution_id: int) -> Dict[str, Any]:
        """Prepare input data for step execution"""
        context = self.execution_context.get(execution_id, {})
        input_data = {}
        
        # Apply input mapping
        for step_input, context_key in step.input_mapping.items():
            if context_key in context:
                input_data[step_input] = context[context_key]
        
        # Add step config
        input_data.update(step.config)
        
        return input_data
    
    def _process_step_output(
        self, 
        step: WorkflowStep, 
        output_data: Dict[str, Any], 
        execution_id: int
    ) -> None:
        """Process step output and update execution context"""
        context = self.execution_context.get(execution_id, {})
        
        # Apply output mapping
        for output_key, context_key in step.output_mapping.items():
            if output_key in output_data:
                context[context_key] = output_data[output_key]
        
        # Store step output
        context[f"step_{step.id}_output"] = output_data
        
        self.execution_context[execution_id] = context
    
    async def _evaluate_conditions(
        self, 
        conditions: List[Dict[str, Any]], 
        execution_id: int
    ) -> bool:
        """Evaluate step conditions"""
        if not conditions:
            return True
        
        context = self.execution_context.get(execution_id, {})
        
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if field not in context:
                return False
            
            field_value = context[field]
            
            if operator == "equals" and field_value != value:
                return False
            elif operator == "not_equals" and field_value == value:
                return False
            elif operator == "greater_than" and field_value <= value:
                return False
            elif operator == "less_than" and field_value >= value:
                return False
            elif operator == "contains" and value not in str(field_value):
                return False
            elif operator == "not_contains" and value in str(field_value):
                return False
            elif operator == "is_empty" and field_value:
                return False
            elif operator == "is_not_empty" and not field_value:
                return False
            elif operator == "in" and field_value not in value:
                return False
            elif operator == "not_in" and field_value in value:
                return False
        
        return True
    
    # Action implementations
    async def _action_create_task(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task action"""
        db = SessionLocal()
        try:
            from src.backend.schemas.task import TaskCreate
            
            tasks_to_create = config.get("tasks", [])
            if not tasks_to_create:
                # Single task creation
                task_data = {
                    "title": config.get("title", "Workflow Task"),
                    "description": config.get("description", ""),
                    "priority": config.get("priority", "medium"),
                    "workspace_id": input_data.get("workspace_id", 1),
                    "assigned_to": config.get("assigned_to"),
                    "due_date": config.get("due_date")
                }
                tasks_to_create = [task_data]
            
            created_tasks = []
            for task_data in tasks_to_create:
                task_create = TaskCreate(**task_data)
                task_obj = task.create(db, obj_in=task_create)
                created_tasks.append({"id": task.id, "title": task.title})
            
            return {"created_tasks": created_tasks, "count": len(created_tasks)}
            
        finally:
            db.close()
    
    async def _action_update_task(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update task action"""
        db = SessionLocal()
        try:
            task_id = config.get("task_id") or input_data.get("task_id")
            if not task_id:
                raise ValueError("Task ID not provided")
            
            from src.backend.schemas.task import TaskUpdate
            update_data = {k: v for k, v in config.items() if k != "task_id"}
            task_update = TaskUpdate(**update_data)
            
            task_obj = task.update(db, db_obj_id=task_id, obj_in=task_update)
            return {"updated_task": {"id": task.id, "title": task.title}}
            
        finally:
            db.close()
    
    async def _action_assign_task(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign task action"""
        # Implementation depends on task assignment logic
        assignee = config.get("assignee") or config.get("default_assignee")
        task_id = config.get("task_id") or input_data.get("task_id")
        
        return {"assigned_to": assignee, "task_id": task_id}
    
    async def _action_send_email(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email action"""
        # Mock implementation - integrate with actual email service
        to = config.get("to", [])
        subject = config.get("subject", "Workflow Notification")
        template = config.get("template")
        
        logger.info(f"Mock email sent to {to} with subject: {subject}")
        return {"email_sent": True, "recipients": to, "subject": subject}
    
    async def _action_send_notification(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification action"""
        message = config.get("message", "Workflow notification")
        channels = config.get("channels", ["email"])
        
        logger.info(f"Mock notification sent via {channels}: {message}")
        return {"notification_sent": True, "channels": channels, "message": message}
    
    async def _action_create_workspace(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create workspace action"""
        db = SessionLocal()
        try:
            from src.backend.schemas.workspace import WorkspaceCreate
            
            workspace_data = {
                "name": config.get("workspace_name", "New Workspace"),
                "description": config.get("description", ""),
                "owner_id": input_data.get("user_id", 1)
            }
            
            workspace_create = WorkspaceCreate(**workspace_data)
            workspace = crud_workspace.create(db, obj_in=workspace_create)
            
            return {"workspace_created": True, "workspace_id": workspace.id, "name": workspace.name}
            
        finally:
            db.close()
    
    async def _action_move_file(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Move file action"""
        source_path = config.get("source_path")
        destination_path = config.get("destination_path")
        
        # Mock implementation
        logger.info(f"Mock file move from {source_path} to {destination_path}")
        return {"file_moved": True, "source": source_path, "destination": destination_path}
    
    async def _action_generate_report(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report action"""
        report_type = config.get("report_type", "generic")
        format_type = config.get("format", "pdf")
        
        # Mock implementation
        report_id = f"report_{datetime.utcnow().timestamp()}"
        logger.info(f"Mock report generated: {report_id}")
        
        return {"report_generated": True, "report_id": report_id, "type": report_type, "format": format_type}
    
    async def _action_call_api(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call API action"""
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        data = config.get("data", {})
        
        if not url:
            raise ValueError("API URL not provided")
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                params=data if method == "GET" else None
            )
            
            return {
                "api_call_success": True,
                "status_code": response.status_code,
                "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
    
    async def _action_wait(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wait action"""
        wait_seconds = config.get("seconds", 0)
        wait_minutes = config.get("minutes", 0)
        wait_hours = config.get("hours", 0)
        
        total_seconds = wait_seconds + (wait_minutes * 60) + (wait_hours * 3600)
        
        if total_seconds > 0:
            await asyncio.sleep(total_seconds)
        
        return {"waited_seconds": total_seconds}
    
    async def _action_conditional(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conditional action"""
        condition = config.get("condition", "true")
        
        # Simple condition evaluation (could be extended)
        try:
            # Evaluate condition as Python expression (be careful with security)
            result = eval(condition, {"__builtins__": {}}, input_data)
            return {"condition_result": bool(result)}
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return {"condition_result": False, "error": str(e)}
    
    async def _action_approval(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approval action"""
        approver = config.get("approver")
        approval_type = config.get("approval_type", "generic")
        timeout_hours = config.get("timeout_hours", 48)
        
        # Mock implementation - in reality, this would create an approval task
        logger.info(f"Mock approval request sent to {approver} for {approval_type}")
        
        return {
            "approval_requested": True,
            "approver": approver,
            "type": approval_type,
            "timeout_hours": timeout_hours,
            "approval_status": "pending"
        }
    
    async def _action_ai_analysis(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI analysis action"""
        analysis_type = config.get("analysis_type", "generic")
        text_data = input_data.get("text", config.get("text", ""))
        
        try:
            # Use AI service for analysis
            if analysis_type == "sentiment":
                result = await ai_service.analyze_sentiment(text_data)
            elif analysis_type == "classification":
                categories = config.get("categories", [])
                result = await ai_service.classify_text(text_data, categories)
            elif analysis_type == "extraction":
                fields = config.get("extract_fields", [])
                result = await ai_service.extract_entities(text_data, fields)
            else:
                # Generic analysis
                result = await enhanced_ai_service.analyze_text(text_data)
            
            return {"analysis_result": result, "analysis_type": analysis_type}
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {"analysis_result": None, "error": str(e)}
    
    async def _action_webhook_call(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Webhook call action"""
        webhook_url = config.get("webhook_url")
        method = config.get("method", "POST")
        headers = config.get("headers", {"Content-Type": "application/json"})
        payload = config.get("payload", input_data)
        
        if not webhook_url:
            raise ValueError("Webhook URL not provided")
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=webhook_url,
                headers=headers,
                json=payload
            )
            
            return {
                "webhook_call_success": True,
                "status_code": response.status_code,
                "response": response.text
            }
    
    async def pause_execution(self, execution_id: int) -> bool:
        """Pause workflow execution"""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            
            db = SessionLocal()
            try:
                crud_workflow_execution.update_execution_status(
                    db, execution_id=execution_id, status=WorkflowExecutionStatus.CANCELLED
                )
                return True
            finally:
                db.close()
        
        return False
    
    async def cancel_execution(self, execution_id: int) -> bool:
        """Cancel workflow execution"""
        return await self.pause_execution(execution_id)
    
    def get_active_executions(self) -> List[int]:
        """Get list of active execution IDs"""
        return list(self.active_executions.keys())
    
    async def cleanup_stale_executions(self) -> int:
        """Cleanup stale executions that are stuck"""
        db = SessionLocal()
        try:
            # Find executions that have been running for too long
            stale_threshold = datetime.utcnow() - timedelta(hours=24)
            
            stale_executions = db.query(WorkflowExecution).filter(
                and_(
                    WorkflowExecution.status.in_([
                        WorkflowExecutionStatus.PENDING,
                        WorkflowExecutionStatus.RUNNING
                    ]),
                    WorkflowExecution.started_at < stale_threshold
                )
            ).all()
            
            cleanup_count = 0
            for execution in stale_executions:
                crud_workflow_execution.update_execution_status(
                    db, 
                    execution_id=execution.id, 
                    status=WorkflowExecutionStatus.TIMEOUT,
                    error_message="Execution timed out - cleanup"
                )
                cleanup_count += 1
                
                # Cancel if still in active executions
                if execution.id in self.active_executions:
                    self.active_executions[execution.id].cancel()
                    del self.active_executions[execution.id]
                
                if execution.id in self.execution_context:
                    del self.execution_context[execution.id]
            
            logger.info(f"Cleaned up {cleanup_count} stale executions")
            return cleanup_count
            
        finally:
            db.close()


# Create global instance
workflow_execution_engine = WorkflowExecutionEngine()