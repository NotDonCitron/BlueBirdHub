"""
CRUD operations for workflow management

This module provides database access layer for workflows, including
workflows, templates, executions, triggers, and related entities.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta
import uuid
import json

from src.backend.crud.base import CRUDBase
from src.backend.models.workflow import (
    Workflow, WorkflowTemplate, WorkflowStep, WorkflowExecution,
    WorkflowStepExecution, WorkflowTrigger, WorkflowVersion,
    WorkflowSchedule, WorkflowWebhook, WorkflowAnalytics,
    WorkflowShare, WorkflowStatus, WorkflowExecutionStatus
)
from src.backend.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowTemplateCreate,
    WorkflowTemplateUpdate, WorkflowStepCreate, WorkflowStepUpdate,
    WorkflowTriggerCreate, WorkflowTriggerUpdate,
    WorkflowExecutionCreate, WorkflowScheduleCreate,
    WorkflowWebhookCreate, WorkflowShareCreate
)


class CRUDWorkflow(CRUDBase[Workflow, WorkflowCreate, WorkflowUpdate]):
    """CRUD operations for workflows"""
    
    def create_with_steps_and_triggers(
        self,
        db: Session,
        *,
        obj_in: WorkflowCreate,
        user_id: int
    ) -> Workflow:
        """Create workflow with steps and triggers"""
        # Create main workflow
        workflow_data = obj_in.dict(exclude={"steps", "triggers"})
        workflow_data["created_by"] = user_id
        
        db_workflow = Workflow(**workflow_data)
        db.add(db_workflow)
        db.flush()  # Get the ID
        
        # Create steps
        for step_data in obj_in.steps:
            step_data_dict = step_data.dict()
            step_data_dict["workflow_id"] = db_workflow.id
            db_step = WorkflowStep(**step_data_dict)
            db.add(db_step)
        
        # Create triggers
        for trigger_data in obj_in.triggers:
            trigger_data_dict = trigger_data.dict()
            trigger_data_dict["workflow_id"] = db_workflow.id
            db_trigger = WorkflowTrigger(**trigger_data_dict)
            db.add(db_trigger)
        
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    
    def get_by_workspace(
        self,
        db: Session,
        workspace_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WorkflowStatus] = None,
        include_steps: bool = False,
        include_triggers: bool = False
    ) -> List[Workflow]:
        """Get workflows by workspace"""
        query = db.query(self.model).filter(
            self.model.workspace_id == workspace_id
        )
        
        if status:
            query = query.filter(self.model.status == status)
        
        if include_steps:
            query = query.options(selectinload(self.model.steps))
        
        if include_triggers:
            query = query.options(selectinload(self.model.triggers))
        
        return query.offset(skip).limit(limit).all()
    
    def get_active_workflows(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Workflow]:
        """Get all active workflows"""
        return db.query(self.model).filter(
            self.model.status == WorkflowStatus.ACTIVE
        ).offset(skip).limit(limit).all()
    
    def duplicate_workflow(
        self,
        db: Session,
        *,
        workflow_id: int,
        new_name: str,
        workspace_id: Optional[int] = None,
        user_id: int
    ) -> Workflow:
        """Duplicate a workflow"""
        # Get original workflow with all related data
        original = db.query(self.model).options(
            selectinload(self.model.steps),
            selectinload(self.model.triggers)
        ).filter(self.model.id == workflow_id).first()
        
        if not original:
            raise ValueError("Workflow not found")
        
        # Create new workflow
        new_workflow_data = {
            "name": new_name,
            "description": original.description,
            "workspace_id": workspace_id or original.workspace_id,
            "created_by": user_id,
            "config": original.config,
            "variables": original.variables,
            "timeout_minutes": original.timeout_minutes,
            "max_retries": original.max_retries,
            "retry_delay_seconds": original.retry_delay_seconds,
            "is_parallel": original.is_parallel,
        }
        
        new_workflow = Workflow(**new_workflow_data)
        db.add(new_workflow)
        db.flush()
        
        # Duplicate steps
        step_id_mapping = {}
        for step in original.steps:
            new_step_data = {
                "workflow_id": new_workflow.id,
                "name": step.name,
                "description": step.description,
                "step_type": step.step_type,
                "order": step.order,
                "config": step.config,
                "input_mapping": step.input_mapping,
                "output_mapping": step.output_mapping,
                "depends_on": step.depends_on,  # Will update IDs later
                "conditions": step.conditions,
                "on_error": step.on_error,
                "retry_count": step.retry_count,
                "timeout_seconds": step.timeout_seconds,
                "position_x": step.position_x,
                "position_y": step.position_y,
            }
            new_step = WorkflowStep(**new_step_data)
            db.add(new_step)
            db.flush()
            step_id_mapping[step.id] = new_step.id
        
        # Update step dependencies with new IDs
        for step in new_workflow.steps:
            if step.depends_on:
                new_depends_on = [
                    step_id_mapping.get(old_id, old_id) 
                    for old_id in step.depends_on
                ]
                step.depends_on = new_depends_on
        
        # Duplicate triggers
        for trigger in original.triggers:
            new_trigger_data = {
                "workflow_id": new_workflow.id,
                "name": trigger.name,
                "trigger_type": trigger.trigger_type,
                "config": trigger.config,
                "conditions": trigger.conditions,
                "cron_expression": trigger.cron_expression,
                "timezone": trigger.timezone,
                "is_enabled": False,  # Start disabled for safety
            }
            new_trigger = WorkflowTrigger(**new_trigger_data)
            db.add(new_trigger)
        
        db.commit()
        db.refresh(new_workflow)
        return new_workflow
    
    def search_workflows(
        self,
        db: Session,
        *,
        query: str,
        workspace_id: Optional[int] = None,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Workflow]:
        """Search workflows by name and description"""
        search_query = db.query(self.model)
        
        # Text search
        search_query = search_query.filter(
            or_(
                self.model.name.ilike(f"%{query}%"),
                self.model.description.ilike(f"%{query}%")
            )
        )
        
        # Filter by workspace
        if workspace_id:
            search_query = search_query.filter(
                self.model.workspace_id == workspace_id
            )
        
        # Filter by user
        if user_id:
            search_query = search_query.filter(
                self.model.created_by == user_id
            )
        
        return search_query.offset(skip).limit(limit).all()


class CRUDWorkflowTemplate(CRUDBase[WorkflowTemplate, WorkflowTemplateCreate, WorkflowTemplateUpdate]):
    """CRUD operations for workflow templates"""
    
    def get_by_category(
        self,
        db: Session,
        category: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowTemplate]:
        """Get templates by category"""
        return db.query(self.model).filter(
            self.model.category == category,
            self.model.is_public == True
        ).order_by(desc(self.model.rating)).offset(skip).limit(limit).all()
    
    def get_popular_templates(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20
    ) -> List[WorkflowTemplate]:
        """Get popular templates by usage count"""
        return db.query(self.model).filter(
            self.model.is_public == True
        ).order_by(desc(self.model.usage_count)).offset(skip).limit(limit).all()
    
    def search_templates(
        self,
        db: Session,
        *,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowTemplate]:
        """Search templates"""
        search_query = db.query(self.model).filter(
            self.model.is_public == True
        )
        
        # Text search
        search_query = search_query.filter(
            or_(
                self.model.name.ilike(f"%{query}%"),
                self.model.description.ilike(f"%{query}%")
            )
        )
        
        # Category filter
        if category:
            search_query = search_query.filter(
                self.model.category == category
            )
        
        # Tags filter
        if tags:
            for tag in tags:
                search_query = search_query.filter(
                    func.json_contains(self.model.tags, f'"{tag}"')
                )
        
        return search_query.order_by(desc(self.model.rating)).offset(skip).limit(limit).all()
    
    def increment_usage(self, db: Session, *, template_id: int) -> WorkflowTemplate:
        """Increment template usage count"""
        template = self.get(db, id=template_id)
        if template:
            template.usage_count += 1
            db.commit()
            db.refresh(template)
        return template


class CRUDWorkflowExecution(CRUDBase[WorkflowExecution, WorkflowExecutionCreate, Any]):
    """CRUD operations for workflow executions"""
    
    def create_execution(
        self,
        db: Session,
        *,
        obj_in: WorkflowExecutionCreate,
        user_id: Optional[int] = None
    ) -> WorkflowExecution:
        """Create a new workflow execution"""
        execution_data = obj_in.dict()
        execution_data["started_by"] = user_id
        
        # Get workflow to set initial variables and steps count
        workflow = db.query(Workflow).filter(
            Workflow.id == obj_in.workflow_id
        ).first()
        
        if not workflow:
            raise ValueError("Workflow not found")
        
        # Merge workflow variables with input data
        execution_data["variables"] = {**workflow.variables, **obj_in.input_data}
        execution_data["steps_total"] = len(workflow.steps)
        
        db_execution = WorkflowExecution(**execution_data)
        db.add(db_execution)
        db.commit()
        db.refresh(db_execution)
        
        # Update workflow execution count
        workflow.execution_count += 1
        db.commit()
        
        return db_execution
    
    def get_by_workflow(
        self,
        db: Session,
        workflow_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WorkflowExecutionStatus] = None
    ) -> List[WorkflowExecution]:
        """Get executions by workflow"""
        query = db.query(self.model).filter(
            self.model.workflow_id == workflow_id
        )
        
        if status:
            query = query.filter(self.model.status == status)
        
        return query.order_by(desc(self.model.started_at)).offset(skip).limit(limit).all()
    
    def get_active_executions(self, db: Session) -> List[WorkflowExecution]:
        """Get all currently running executions"""
        return db.query(self.model).filter(
            self.model.status.in_([
                WorkflowExecutionStatus.PENDING,
                WorkflowExecutionStatus.RUNNING
            ])
        ).all()
    
    def update_execution_status(
        self,
        db: Session,
        *,
        execution_id: int,
        status: WorkflowExecutionStatus,
        error_message: Optional[str] = None,
        output_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Update execution status"""
        execution = self.get(db, id=execution_id)
        if not execution:
            raise ValueError("Execution not found")
        
        execution.status = status
        if error_message:
            execution.error_message = error_message
        if output_data:
            execution.output_data = output_data
        
        # Set completion time for final statuses
        if status in [WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.FAILED, WorkflowExecutionStatus.CANCELLED]:
            execution.completed_at = datetime.utcnow()
            
            # Calculate execution time
            if execution.started_at:
                execution.execution_time_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
            
            # Update workflow statistics
            workflow = db.query(Workflow).filter(
                Workflow.id == execution.workflow_id
            ).first()
            
            if workflow:
                if status == WorkflowExecutionStatus.COMPLETED:
                    workflow.success_count += 1
                elif status == WorkflowExecutionStatus.FAILED:
                    workflow.failure_count += 1
                
                # Update average execution time
                if execution.execution_time_seconds:
                    total_time = (workflow.avg_execution_time * (workflow.execution_count - 1) + 
                                execution.execution_time_seconds)
                    workflow.avg_execution_time = total_time / workflow.execution_count
                
                workflow.last_executed_at = execution.completed_at
        
        db.commit()
        db.refresh(execution)
        return execution


class CRUDWorkflowStep(CRUDBase[WorkflowStep, WorkflowStepCreate, WorkflowStepUpdate]):
    """CRUD operations for workflow steps"""
    
    def get_by_workflow(
        self,
        db: Session,
        workflow_id: int,
        *,
        ordered: bool = True
    ) -> List[WorkflowStep]:
        """Get steps by workflow"""
        query = db.query(self.model).filter(
            self.model.workflow_id == workflow_id
        )
        
        if ordered:
            query = query.order_by(self.model.order)
        
        return query.all()
    
    def reorder_steps(
        self,
        db: Session,
        *,
        workflow_id: int,
        step_orders: Dict[int, int]
    ) -> List[WorkflowStep]:
        """Reorder workflow steps"""
        steps = []
        for step_id, new_order in step_orders.items():
            step = db.query(self.model).filter(
                and_(
                    self.model.id == step_id,
                    self.model.workflow_id == workflow_id
                )
            ).first()
            if step:
                step.order = new_order
                steps.append(step)
        
        db.commit()
        return steps


class CRUDWorkflowTrigger(CRUDBase[WorkflowTrigger, WorkflowTriggerCreate, WorkflowTriggerUpdate]):
    """CRUD operations for workflow triggers"""
    
    def get_by_workflow(
        self,
        db: Session,
        workflow_id: int,
        *,
        enabled_only: bool = False
    ) -> List[WorkflowTrigger]:
        """Get triggers by workflow"""
        query = db.query(self.model).filter(
            self.model.workflow_id == workflow_id
        )
        
        if enabled_only:
            query = query.filter(self.model.is_enabled == True)
        
        return query.all()
    
    def get_scheduled_triggers(self, db: Session) -> List[WorkflowTrigger]:
        """Get all enabled scheduled triggers"""
        return db.query(self.model).filter(
            and_(
                self.model.trigger_type == "schedule",
                self.model.is_enabled == True,
                self.model.cron_expression.isnot(None)
            )
        ).all()


class CRUDWorkflowVersion(CRUDBase[WorkflowVersion, Any, Any]):
    """CRUD operations for workflow versions"""
    
    def create_version(
        self,
        db: Session,
        *,
        workflow_id: int,
        change_description: str,
        user_id: int
    ) -> WorkflowVersion:
        """Create a new workflow version"""
        # Get current workflow with steps and triggers
        workflow = db.query(Workflow).options(
            selectinload(Workflow.steps),
            selectinload(Workflow.triggers)
        ).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise ValueError("Workflow not found")
        
        # Get next version number
        last_version = db.query(WorkflowVersion).filter(
            WorkflowVersion.workflow_id == workflow_id
        ).order_by(desc(WorkflowVersion.version_number)).first()
        
        version_number = (last_version.version_number + 1) if last_version else 1
        
        # Deactivate current active version
        if last_version and last_version.is_active:
            last_version.is_active = False
        
        # Create version data
        steps_data = [
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "step_type": step.step_type.value,
                "order": step.order,
                "config": step.config,
                "input_mapping": step.input_mapping,
                "output_mapping": step.output_mapping,
                "depends_on": step.depends_on,
                "conditions": step.conditions,
                "on_error": step.on_error,
                "retry_count": step.retry_count,
                "timeout_seconds": step.timeout_seconds,
                "position_x": step.position_x,
                "position_y": step.position_y,
            }
            for step in workflow.steps
        ]
        
        triggers_data = [
            {
                "id": trigger.id,
                "name": trigger.name,
                "trigger_type": trigger.trigger_type.value,
                "config": trigger.config,
                "conditions": trigger.conditions,
                "cron_expression": trigger.cron_expression,
                "timezone": trigger.timezone,
                "is_enabled": trigger.is_enabled,
            }
            for trigger in workflow.triggers
        ]
        
        version = WorkflowVersion(
            workflow_id=workflow_id,
            version_number=version_number,
            name=workflow.name,
            description=workflow.description,
            config=workflow.config,
            steps_data=steps_data,
            triggers_data=triggers_data,
            change_description=change_description,
            created_by=user_id,
            is_active=True
        )
        
        db.add(version)
        
        # Update workflow version
        workflow.version = version_number
        
        db.commit()
        db.refresh(version)
        return version
    
    def get_by_workflow(
        self,
        db: Session,
        workflow_id: int,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowVersion]:
        """Get versions by workflow"""
        return db.query(self.model).filter(
            self.model.workflow_id == workflow_id
        ).order_by(desc(self.model.version_number)).offset(skip).limit(limit).all()
    
    def rollback_to_version(
        self,
        db: Session,
        *,
        workflow_id: int,
        version_number: int,
        user_id: int
    ) -> Workflow:
        """Rollback workflow to a specific version"""
        # Get the target version
        version = db.query(self.model).filter(
            and_(
                self.model.workflow_id == workflow_id,
                self.model.version_number == version_number
            )
        ).first()
        
        if not version:
            raise ValueError("Version not found")
        
        # Get current workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")
        
        # Create new version before rollback
        self.create_version(
            db, 
            workflow_id=workflow_id,
            change_description=f"Rollback to version {version_number}",
            user_id=user_id
        )
        
        # Update workflow with version data
        workflow.name = version.name
        workflow.description = version.description
        workflow.config = version.config
        
        # Delete current steps and triggers
        db.query(WorkflowStep).filter(WorkflowStep.workflow_id == workflow_id).delete()
        db.query(WorkflowTrigger).filter(WorkflowTrigger.workflow_id == workflow_id).delete()
        
        # Recreate steps from version data
        for step_data in version.steps_data:
            step_data_copy = step_data.copy()
            step_data_copy.pop("id", None)  # Remove old ID
            step_data_copy["workflow_id"] = workflow_id
            step = WorkflowStep(**step_data_copy)
            db.add(step)
        
        # Recreate triggers from version data
        for trigger_data in version.triggers_data:
            trigger_data_copy = trigger_data.copy()
            trigger_data_copy.pop("id", None)  # Remove old ID
            trigger_data_copy["workflow_id"] = workflow_id
            trigger = WorkflowTrigger(**trigger_data_copy)
            db.add(trigger)
        
        db.commit()
        db.refresh(workflow)
        return workflow


class CRUDWorkflowWebhook(CRUDBase[WorkflowWebhook, WorkflowWebhookCreate, Any]):
    """CRUD operations for workflow webhooks"""
    
    def create_webhook(
        self,
        db: Session,
        *,
        obj_in: WorkflowWebhookCreate
    ) -> WorkflowWebhook:
        """Create webhook with unique URL"""
        webhook_data = obj_in.dict()
        
        # Generate unique webhook URL
        webhook_token = str(uuid.uuid4())
        webhook_data["webhook_url"] = f"/api/webhooks/workflow/{webhook_token}"
        
        webhook = WorkflowWebhook(**webhook_data)
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        return webhook
    
    def get_by_url(self, db: Session, webhook_url: str) -> Optional[WorkflowWebhook]:
        """Get webhook by URL"""
        return db.query(self.model).filter(
            self.model.webhook_url == webhook_url
        ).first()
    
    def increment_request_count(
        self,
        db: Session,
        *,
        webhook_id: int
    ) -> WorkflowWebhook:
        """Increment webhook request count"""
        webhook = self.get(db, id=webhook_id)
        if webhook:
            webhook.request_count += 1
            webhook.last_request_at = datetime.utcnow()
            db.commit()
            db.refresh(webhook)
        return webhook


# Create CRUD instances
crud_workflow = CRUDWorkflow(Workflow)
crud_workflow_template = CRUDWorkflowTemplate(WorkflowTemplate)
crud_workflow_execution = CRUDWorkflowExecution(WorkflowExecution)
crud_workflow_step = CRUDWorkflowStep(WorkflowStep)
crud_workflow_trigger = CRUDWorkflowTrigger(WorkflowTrigger)
crud_workflow_version = CRUDWorkflowVersion(WorkflowVersion)
crud_workflow_webhook = CRUDWorkflowWebhook(WorkflowWebhook)