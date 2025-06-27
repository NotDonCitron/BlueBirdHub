"""
Workflow API endpoints

This module provides REST API endpoints for workflow management,
including CRUD operations, execution, templates, and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.backend.database.database import get_db
from src.backend.schemas.workflow import (
    Workflow, WorkflowCreate, WorkflowUpdate, WorkflowListResponse,
    WorkflowTemplate, WorkflowTemplateCreate, WorkflowTemplateUpdate, WorkflowTemplateListResponse,
    WorkflowExecution, WorkflowExecutionCreate, WorkflowExecutionListResponse,
    WorkflowStep, WorkflowStepCreate, WorkflowStepUpdate,
    WorkflowTrigger, WorkflowTriggerCreate, WorkflowTriggerUpdate,
    WorkflowVersion, WorkflowVersionCreate,
    WorkflowSchedule, WorkflowScheduleCreate, WorkflowScheduleUpdate,
    WorkflowWebhook, WorkflowWebhookCreate, WorkflowWebhookUpdate,
    WorkflowShare, WorkflowShareCreate, WorkflowShareUpdate,
    WorkflowFromTemplate, WorkflowDuplicate, WorkflowBulkExecute,
    WorkflowExecutionControl, WorkflowStatistics, WorkflowHealthCheck
)
from src.backend.crud.crud_workflow import (
    crud_workflow, crud_workflow_template, crud_workflow_execution,
    crud_workflow_step, crud_workflow_trigger, crud_workflow_version,
    crud_workflow_webhook
)
from src.backend.services.workflow_template_engine import workflow_template_engine
from src.backend.services.workflow_execution_engine import workflow_execution_engine
from src.backend.models.workflow import WorkflowStatus, WorkflowExecutionStatus

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# Workflow CRUD endpoints
@router.post("/", response_model=Workflow, summary="Create Workflow")
async def create_workflow(
    *,
    db: Session = Depends(get_db),
    workflow_in: WorkflowCreate,
    current_user_id: int = 1  # TODO: Get from auth
) -> Workflow:
    """
    Create a new workflow with steps and triggers.
    
    - **name**: Workflow name (required)
    - **description**: Workflow description
    - **workspace_id**: Target workspace ID (required)
    - **steps**: List of workflow steps
    - **triggers**: List of workflow triggers
    """
    try:
        workflow = crud_workflow.create_with_steps_and_triggers(
            db, obj_in=workflow_in, user_id=current_user_id
        )
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=WorkflowListResponse, summary="List Workflows")
async def list_workflows(
    *,
    db: Session = Depends(get_db),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of workflows to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of workflows to return"),
    include_steps: bool = Query(False, description="Include workflow steps"),
    include_triggers: bool = Query(False, description="Include workflow triggers"),
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowListResponse:
    """
    List workflows with optional filtering and pagination.
    """
    if workspace_id:
        workflows = crud_workflow.get_by_workspace(
            db, 
            workspace_id=workspace_id, 
            skip=skip, 
            limit=limit, 
            status=status,
            include_steps=include_steps,
            include_triggers=include_triggers
        )
    else:
        workflows = crud_workflow.get_multi(db, skip=skip, limit=limit)
    
    total = len(workflows)  # TODO: Implement proper count
    
    return WorkflowListResponse(
        items=workflows,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{workflow_id}", response_model=Workflow, summary="Get Workflow")
async def get_workflow(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    include_steps: bool = Query(True, description="Include workflow steps"),
    include_triggers: bool = Query(True, description="Include workflow triggers"),
    current_user_id: int = 1  # TODO: Get from auth
) -> Workflow:
    """
    Get a specific workflow by ID.
    """
    workflow = crud_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # TODO: Check user permissions
    return workflow


@router.put("/{workflow_id}", response_model=Workflow, summary="Update Workflow")
async def update_workflow(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    workflow_in: WorkflowUpdate,
    current_user_id: int = 1  # TODO: Get from auth
) -> Workflow:
    """
    Update a workflow.
    """
    workflow = crud_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # TODO: Check user permissions
    workflow = crud_workflow.update(db, db_obj=workflow, obj_in=workflow_in)
    return workflow


@router.delete("/{workflow_id}", summary="Delete Workflow")
async def delete_workflow(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, str]:
    """
    Delete a workflow.
    """
    workflow = crud_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # TODO: Check user permissions
    crud_workflow.remove(db, id=workflow_id)
    return {"message": "Workflow deleted successfully"}


# Workflow execution endpoints
@router.post("/{workflow_id}/execute", summary="Execute Workflow")
async def execute_workflow(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    workflow_id: int,
    execution_data: Optional[Dict[str, Any]] = None,
    trigger_id: Optional[int] = None,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, Any]:
    """
    Execute a workflow asynchronously.
    """
    workflow = crud_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status != WorkflowStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Workflow is not active")
    
    try:
        execution_id = await workflow_execution_engine.execute_workflow(
            workflow_id=workflow_id,
            trigger_id=trigger_id,
            input_data=execution_data or {},
            user_id=current_user_id
        )
        
        return {
            "execution_id": execution_id,
            "status": "started",
            "message": "Workflow execution started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions", response_model=WorkflowExecutionListResponse, summary="List Workflow Executions")
async def list_workflow_executions(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    status: Optional[WorkflowExecutionStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of executions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of executions to return"),
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowExecutionListResponse:
    """
    List executions for a specific workflow.
    """
    executions = crud_workflow_execution.get_by_workflow(
        db, workflow_id=workflow_id, skip=skip, limit=limit, status=status
    )
    
    total = len(executions)  # TODO: Implement proper count
    
    return WorkflowExecutionListResponse(
        items=executions,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/executions/{execution_id}", response_model=WorkflowExecution, summary="Get Workflow Execution")
async def get_workflow_execution(
    *,
    db: Session = Depends(get_db),
    execution_id: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowExecution:
    """
    Get a specific workflow execution.
    """
    execution = crud_workflow_execution.get(db, id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution


@router.post("/executions/{execution_id}/control", summary="Control Workflow Execution")
async def control_workflow_execution(
    *,
    db: Session = Depends(get_db),
    execution_id: int,
    control: WorkflowExecutionControl,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, str]:
    """
    Control workflow execution (pause, resume, cancel, retry).
    """
    execution = crud_workflow_execution.get(db, id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    try:
        if control.action == "pause":
            await workflow_execution_engine.pause_execution(execution_id)
            return {"message": "Execution paused"}
        elif control.action == "cancel":
            await workflow_execution_engine.cancel_execution(execution_id)
            return {"message": "Execution cancelled"}
        elif control.action == "retry":
            # Restart failed execution
            new_execution_id = await workflow_execution_engine.execute_workflow(
                workflow_id=execution.workflow_id,
                input_data=execution.input_data,
                user_id=current_user_id
            )
            return {"message": "Execution restarted", "new_execution_id": new_execution_id}
        else:
            raise HTTPException(status_code=400, detail="Invalid control action")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Workflow template endpoints
@router.get("/templates", response_model=WorkflowTemplateListResponse, summary="List Workflow Templates")
async def list_workflow_templates(
    *,
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search templates"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of templates to return"),
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowTemplateListResponse:
    """
    List workflow templates with optional filtering.
    """
    if search:
        templates = crud_workflow_template.search_templates(
            db, query=search, category=category, tags=tags, skip=skip, limit=limit
        )
    elif category:
        templates = crud_workflow_template.get_by_category(
            db, category=category, skip=skip, limit=limit
        )
    else:
        templates = crud_workflow_template.get_multi(db, skip=skip, limit=limit)
    
    total = len(templates)  # TODO: Implement proper count
    
    return WorkflowTemplateListResponse(
        items=templates,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/templates/built-in", summary="Get Built-in Templates")
async def get_built_in_templates() -> List[Dict[str, Any]]:
    """
    Get all built-in workflow templates.
    """
    return workflow_template_engine.get_built_in_templates()


@router.get("/templates/{template_id}", response_model=WorkflowTemplate, summary="Get Workflow Template")
async def get_workflow_template(
    *,
    db: Session = Depends(get_db),
    template_id: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowTemplate:
    """
    Get a specific workflow template.
    """
    template = crud_workflow_template.get(db, id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("/templates", response_model=WorkflowTemplate, summary="Create Workflow Template")
async def create_workflow_template(
    *,
    db: Session = Depends(get_db),
    template_in: WorkflowTemplateCreate,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowTemplate:
    """
    Create a new workflow template.
    """
    template_data = template_in.dict()
    template_data["created_by"] = current_user_id
    
    template = crud_workflow_template.create(db, obj_in=template_data)
    return template


@router.post("/from-template", summary="Create Workflow from Template")
async def create_workflow_from_template(
    *,
    db: Session = Depends(get_db),
    template_data: WorkflowFromTemplate,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, Any]:
    """
    Create a workflow from a template (built-in or custom).
    """
    try:
        # Check if it's a built-in template
        if isinstance(template_data.template_id, str):
            workflow_id = workflow_template_engine.create_workflow_from_template(
                db,
                template_id=template_data.template_id,
                workspace_id=template_data.workspace_id,
                user_id=current_user_id,
                name=template_data.name,
                description=template_data.description,
                variable_values=template_data.variable_values
            )
        else:
            # Custom template from database
            template = crud_workflow_template.get(db, id=template_data.template_id)
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Increment usage count
            crud_workflow_template.increment_usage(db, template_id=template.id)
            
            # Create workflow from template data
            # TODO: Implement custom template instantiation
            raise HTTPException(status_code=501, detail="Custom template instantiation not yet implemented")
        
        return {
            "workflow_id": workflow_id,
            "message": "Workflow created from template successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/duplicate", summary="Duplicate Workflow")
async def duplicate_workflow(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    duplicate_data: WorkflowDuplicate,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, Any]:
    """
    Duplicate an existing workflow.
    """
    try:
        new_workflow = crud_workflow.duplicate_workflow(
            db,
            workflow_id=workflow_id,
            new_name=duplicate_data.name,
            workspace_id=duplicate_data.workspace_id,
            user_id=current_user_id
        )
        
        return {
            "workflow_id": new_workflow.id,
            "message": "Workflow duplicated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Workflow step endpoints
@router.get("/{workflow_id}/steps", response_model=List[WorkflowStep], summary="List Workflow Steps")
async def list_workflow_steps(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> List[WorkflowStep]:
    """
    List steps for a specific workflow.
    """
    steps = crud_workflow_step.get_by_workflow(db, workflow_id=workflow_id)
    return steps


@router.post("/{workflow_id}/steps", response_model=WorkflowStep, summary="Create Workflow Step")
async def create_workflow_step(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    step_in: WorkflowStepCreate,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowStep:
    """
    Create a new workflow step.
    """
    step_data = step_in.dict()
    step_data["workflow_id"] = workflow_id
    
    step = crud_workflow_step.create(db, obj_in=step_data)
    return step


@router.put("/steps/{step_id}", response_model=WorkflowStep, summary="Update Workflow Step")
async def update_workflow_step(
    *,
    db: Session = Depends(get_db),
    step_id: int,
    step_in: WorkflowStepUpdate,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowStep:
    """
    Update a workflow step.
    """
    step = crud_workflow_step.get(db, id=step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    step = crud_workflow_step.update(db, db_obj=step, obj_in=step_in)
    return step


@router.delete("/steps/{step_id}", summary="Delete Workflow Step")
async def delete_workflow_step(
    *,
    db: Session = Depends(get_db),
    step_id: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, str]:
    """
    Delete a workflow step.
    """
    step = crud_workflow_step.get(db, id=step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    crud_workflow_step.remove(db, id=step_id)
    return {"message": "Step deleted successfully"}


@router.post("/{workflow_id}/steps/reorder", summary="Reorder Workflow Steps")
async def reorder_workflow_steps(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    step_orders: Dict[int, int],
    current_user_id: int = 1  # TODO: Get from auth
) -> List[WorkflowStep]:
    """
    Reorder workflow steps.
    """
    steps = crud_workflow_step.reorder_steps(
        db, workflow_id=workflow_id, step_orders=step_orders
    )
    return steps


# Workflow trigger endpoints
@router.get("/{workflow_id}/triggers", response_model=List[WorkflowTrigger], summary="List Workflow Triggers")
async def list_workflow_triggers(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    enabled_only: bool = Query(False, description="Only return enabled triggers"),
    current_user_id: int = 1  # TODO: Get from auth
) -> List[WorkflowTrigger]:
    """
    List triggers for a specific workflow.
    """
    triggers = crud_workflow_trigger.get_by_workflow(
        db, workflow_id=workflow_id, enabled_only=enabled_only
    )
    return triggers


@router.post("/{workflow_id}/triggers", response_model=WorkflowTrigger, summary="Create Workflow Trigger")
async def create_workflow_trigger(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    trigger_in: WorkflowTriggerCreate,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowTrigger:
    """
    Create a new workflow trigger.
    """
    trigger_data = trigger_in.dict()
    trigger_data["workflow_id"] = workflow_id
    
    trigger = crud_workflow_trigger.create(db, obj_in=trigger_data)
    return trigger


@router.put("/triggers/{trigger_id}", response_model=WorkflowTrigger, summary="Update Workflow Trigger")
async def update_workflow_trigger(
    *,
    db: Session = Depends(get_db),
    trigger_id: int,
    trigger_in: WorkflowTriggerUpdate,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowTrigger:
    """
    Update a workflow trigger.
    """
    trigger = crud_workflow_trigger.get(db, id=trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    trigger = crud_workflow_trigger.update(db, db_obj=trigger, obj_in=trigger_in)
    return trigger


@router.delete("/triggers/{trigger_id}", summary="Delete Workflow Trigger")
async def delete_workflow_trigger(
    *,
    db: Session = Depends(get_db),
    trigger_id: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, str]:
    """
    Delete a workflow trigger.
    """
    trigger = crud_workflow_trigger.get(db, id=trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    crud_workflow_trigger.remove(db, id=trigger_id)
    return {"message": "Trigger deleted successfully"}


# Workflow version endpoints
@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersion], summary="List Workflow Versions")
async def list_workflow_versions(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user_id: int = 1  # TODO: Get from auth
) -> List[WorkflowVersion]:
    """
    List versions for a specific workflow.
    """
    versions = crud_workflow_version.get_by_workflow(
        db, workflow_id=workflow_id, skip=skip, limit=limit
    )
    return versions


@router.post("/{workflow_id}/versions", response_model=WorkflowVersion, summary="Create Workflow Version")
async def create_workflow_version(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    version_in: WorkflowVersionCreate,
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowVersion:
    """
    Create a new workflow version (snapshot).
    """
    try:
        version = crud_workflow_version.create_version(
            db,
            workflow_id=workflow_id,
            change_description=version_in.change_description,
            user_id=current_user_id
        )
        return version
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/rollback/{version_number}", summary="Rollback Workflow")
async def rollback_workflow(
    *,
    db: Session = Depends(get_db),
    workflow_id: int,
    version_number: int,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, str]:
    """
    Rollback workflow to a specific version.
    """
    try:
        workflow = crud_workflow_version.rollback_to_version(
            db,
            workflow_id=workflow_id,
            version_number=version_number,
            user_id=current_user_id
        )
        return {"message": f"Workflow rolled back to version {version_number}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Bulk operations
@router.post("/bulk/execute", summary="Bulk Execute Workflows")
async def bulk_execute_workflows(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    execution_data: WorkflowBulkExecute,
    current_user_id: int = 1  # TODO: Get from auth
) -> Dict[str, Any]:
    """
    Execute multiple workflows at once.
    """
    try:
        execution_ids = []
        for workflow_id in execution_data.workflow_ids:
            workflow = crud_workflow.get(db, id=workflow_id)
            if workflow and workflow.status == WorkflowStatus.ACTIVE:
                execution_id = await workflow_execution_engine.execute_workflow(
                    workflow_id=workflow_id,
                    input_data=execution_data.input_data,
                    context=execution_data.context,
                    user_id=current_user_id
                )
                execution_ids.append(execution_id)
        
        return {
            "execution_ids": execution_ids,
            "count": len(execution_ids),
            "message": f"Started {len(execution_ids)} workflow executions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Search and analytics
@router.get("/search", response_model=WorkflowListResponse, summary="Search Workflows")
async def search_workflows(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., description="Search query"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowListResponse:
    """
    Search workflows by name and description.
    """
    workflows = crud_workflow.search_workflows(
        db, query=q, workspace_id=workspace_id, user_id=current_user_id, skip=skip, limit=limit
    )
    
    total = len(workflows)  # TODO: Implement proper count
    
    return WorkflowListResponse(
        items=workflows,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/statistics", response_model=WorkflowStatistics, summary="Get Workflow Statistics")
async def get_workflow_statistics(
    *,
    db: Session = Depends(get_db),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace"),
    current_user_id: int = 1  # TODO: Get from auth
) -> WorkflowStatistics:
    """
    Get workflow system statistics.
    """
    # TODO: Implement actual statistics calculation
    return WorkflowStatistics(
        total_workflows=0,
        active_workflows=0,
        total_executions=0,
        successful_executions=0,
        failed_executions=0,
        avg_execution_time=0.0,
        most_used_templates=[],
        execution_trends=[]
    )


@router.get("/health", response_model=WorkflowHealthCheck, summary="Workflow System Health")
async def get_workflow_health(
    *,
    db: Session = Depends(get_db)
) -> WorkflowHealthCheck:
    """
    Get workflow system health status.
    """
    active_executions = len(workflow_execution_engine.get_active_executions())
    
    return WorkflowHealthCheck(
        status="healthy",
        active_executions=active_executions,
        pending_schedules=0,  # TODO: Implement
        failed_webhooks=0,  # TODO: Implement
        system_load=0.5,  # TODO: Implement
        last_cleanup=datetime.utcnow()
    )