"""
Workflow Pydantic schemas for API validation and serialization

This module contains Pydantic models for the workflow automation system,
providing request/response validation and documentation.
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

from src.backend.models.workflow import (
    WorkflowStatus, WorkflowExecutionStatus, TriggerType, ActionType, 
    ConditionOperator
)


# Base schemas for common fields
class WorkflowBase(BaseModel):
    """Base schema for workflow fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    config: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow variables")
    timeout_minutes: int = Field(60, ge=1, le=1440, description="Workflow timeout in minutes")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(30, ge=0, le=3600, description="Delay between retries")
    is_parallel: bool = Field(False, description="Enable parallel step execution")


class WorkflowStepBase(BaseModel):
    """Base schema for workflow step fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Step name")
    description: Optional[str] = Field(None, description="Step description")
    step_type: ActionType = Field(..., description="Type of action this step performs")
    order: int = Field(..., ge=0, description="Execution order of the step")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration")
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="Input variable mapping")
    output_mapping: Dict[str, str] = Field(default_factory=dict, description="Output variable mapping")
    depends_on: List[int] = Field(default_factory=list, description="Step dependencies")
    conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Execution conditions")
    on_error: str = Field("fail", pattern="^(fail|continue|retry)$", description="Error handling strategy")
    retry_count: int = Field(0, ge=0, le=5, description="Step-specific retry count")
    timeout_seconds: int = Field(300, ge=1, le=3600, description="Step timeout")
    position_x: float = Field(0, description="X position in visual designer")
    position_y: float = Field(0, description="Y position in visual designer")


class WorkflowTriggerBase(BaseModel):
    """Base schema for workflow trigger fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Trigger name")
    trigger_type: TriggerType = Field(..., description="Type of trigger")
    config: Dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")
    conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Trigger conditions")
    cron_expression: Optional[str] = Field(None, description="Cron expression for scheduled triggers")
    timezone: str = Field("UTC", description="Timezone for scheduled triggers")
    is_enabled: bool = Field(True, description="Whether trigger is enabled")


# Template schemas
class WorkflowTemplateBase(BaseModel):
    """Base schema for workflow templates"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(..., min_length=1, max_length=100, description="Template category")
    version: str = Field("1.0.0", description="Template version")
    template_data: Dict[str, Any] = Field(..., description="Complete workflow structure")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    is_public: bool = Field(True, description="Whether template is publicly available")


class WorkflowTemplateCreate(WorkflowTemplateBase):
    """Schema for creating workflow templates"""
    pass


class WorkflowTemplateUpdate(BaseModel):
    """Schema for updating workflow templates"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class WorkflowTemplate(WorkflowTemplateBase):
    """Schema for workflow template responses"""
    id: int
    usage_count: int
    rating: float
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Step schemas
class WorkflowStepCreate(WorkflowStepBase):
    """Schema for creating workflow steps"""
    pass


class WorkflowStepUpdate(BaseModel):
    """Schema for updating workflow steps"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    step_type: Optional[ActionType] = None
    order: Optional[int] = Field(None, ge=0)
    config: Optional[Dict[str, Any]] = None
    input_mapping: Optional[Dict[str, str]] = None
    output_mapping: Optional[Dict[str, str]] = None
    depends_on: Optional[List[int]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    on_error: Optional[str] = Field(None, pattern="^(fail|continue|retry)$")
    retry_count: Optional[int] = Field(None, ge=0, le=5)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600)
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class WorkflowStep(WorkflowStepBase):
    """Schema for workflow step responses"""
    id: int
    workflow_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Trigger schemas
class WorkflowTriggerCreate(WorkflowTriggerBase):
    """Schema for creating workflow triggers"""
    pass


class WorkflowTriggerUpdate(BaseModel):
    """Schema for updating workflow triggers"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    trigger_type: Optional[TriggerType] = None
    config: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_enabled: Optional[bool] = None


class WorkflowTrigger(WorkflowTriggerBase):
    """Schema for workflow trigger responses"""
    id: int
    workflow_id: int
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Main workflow schemas
class WorkflowCreate(WorkflowBase):
    """Schema for creating workflows"""
    workspace_id: int = Field(..., description="ID of the workspace")
    template_id: Optional[int] = Field(None, description="Template to create from")
    steps: List[WorkflowStepCreate] = Field(default_factory=list, description="Workflow steps")
    triggers: List[WorkflowTriggerCreate] = Field(default_factory=list, description="Workflow triggers")


class WorkflowUpdate(BaseModel):
    """Schema for updating workflows"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    config: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    timeout_minutes: Optional[int] = Field(None, ge=1, le=1440)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0, le=3600)
    is_parallel: Optional[bool] = None


class Workflow(WorkflowBase):
    """Schema for workflow responses"""
    id: int
    status: WorkflowStatus
    version: int
    is_template: bool
    template_id: Optional[int]
    workspace_id: int
    created_by: int
    execution_count: int
    success_count: int
    failure_count: int
    avg_execution_time: float
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime]
    
    # Related objects
    steps: List[WorkflowStep] = Field(default_factory=list)
    triggers: List[WorkflowTrigger] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


# Execution schemas
class WorkflowExecutionCreate(BaseModel):
    """Schema for creating workflow executions"""
    workflow_id: int = Field(..., description="ID of the workflow to execute")
    trigger_id: Optional[int] = Field(None, description="ID of the trigger that started execution")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for execution")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")


class WorkflowExecution(BaseModel):
    """Schema for workflow execution responses"""
    id: int
    workflow_id: int
    trigger_id: Optional[int]
    status: WorkflowExecutionStatus
    started_by: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    input_data: Dict[str, Any]
    variables: Dict[str, Any]
    context: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    error_step_id: Optional[int]
    execution_time_seconds: Optional[float]
    steps_completed: int
    steps_total: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowStepExecution(BaseModel):
    """Schema for workflow step execution responses"""
    id: int
    execution_id: int
    step_id: int
    status: WorkflowExecutionStatus
    attempt_number: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    logs: Optional[str]
    execution_time_seconds: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Version schemas
class WorkflowVersionCreate(BaseModel):
    """Schema for creating workflow versions"""
    workflow_id: int
    change_description: str = Field(..., min_length=1, description="Description of changes")


class WorkflowVersion(BaseModel):
    """Schema for workflow version responses"""
    id: int
    workflow_id: int
    version_number: int
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    steps_data: List[Dict[str, Any]]
    triggers_data: List[Dict[str, Any]]
    change_description: str
    created_by: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# Schedule schemas
class WorkflowScheduleCreate(BaseModel):
    """Schema for creating workflow schedules"""
    workflow_id: int = Field(..., description="ID of the workflow to schedule")
    trigger_id: int = Field(..., description="ID of the trigger to use")
    name: str = Field(..., min_length=1, max_length=200, description="Schedule name")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field("UTC", description="Timezone for schedule")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for executions")
    max_runs: Optional[int] = Field(None, ge=1, description="Maximum number of runs")


class WorkflowScheduleUpdate(BaseModel):
    """Schema for updating workflow schedules"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_enabled: Optional[bool] = None
    input_data: Optional[Dict[str, Any]] = None
    max_runs: Optional[int] = Field(None, ge=1)


class WorkflowSchedule(BaseModel):
    """Schema for workflow schedule responses"""
    id: int
    workflow_id: int
    trigger_id: int
    name: str
    cron_expression: str
    timezone: str
    is_enabled: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    run_count: int
    input_data: Dict[str, Any]
    max_runs: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Webhook schemas
class WorkflowWebhookCreate(BaseModel):
    """Schema for creating workflow webhooks"""
    workflow_id: int = Field(..., description="ID of the workflow")
    trigger_id: int = Field(..., description="ID of the trigger")
    name: str = Field(..., min_length=1, max_length=200, description="Webhook name")
    secret_key: Optional[str] = Field(None, description="Secret key for verification")
    allowed_methods: List[str] = Field(["POST"], description="Allowed HTTP methods")
    content_type: str = Field("application/json", description="Expected content type")
    headers: Dict[str, str] = Field(default_factory=dict, description="Expected headers")
    rate_limit: int = Field(100, ge=1, le=10000, description="Requests per hour limit")
    ip_whitelist: List[str] = Field(default_factory=list, description="Allowed IP addresses")


class WorkflowWebhookUpdate(BaseModel):
    """Schema for updating workflow webhooks"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    secret_key: Optional[str] = None
    allowed_methods: Optional[List[str]] = None
    content_type: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    is_enabled: Optional[bool] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    ip_whitelist: Optional[List[str]] = None


class WorkflowWebhook(BaseModel):
    """Schema for workflow webhook responses"""
    id: int
    workflow_id: int
    trigger_id: int
    name: str
    webhook_url: str
    secret_key: Optional[str]
    allowed_methods: List[str]
    content_type: str
    headers: Dict[str, str]
    is_enabled: bool
    rate_limit: int
    ip_whitelist: List[str]
    request_count: int
    last_request_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Analytics schemas
class WorkflowAnalytics(BaseModel):
    """Schema for workflow analytics responses"""
    id: int
    workflow_id: int
    date: datetime
    executions_total: int
    executions_successful: int
    executions_failed: int
    executions_cancelled: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    total_execution_time: float
    timeout_count: int
    retry_count: int
    most_common_error: Optional[str]
    cpu_usage_avg: float
    memory_usage_avg: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Share schemas
class WorkflowShareCreate(BaseModel):
    """Schema for creating workflow shares"""
    workflow_id: int = Field(..., description="ID of the workflow to share")
    shared_with: Optional[int] = Field(None, description="User ID to share with")
    team_id: Optional[int] = Field(None, description="Team ID to share with")
    can_view: bool = Field(True, description="View permission")
    can_edit: bool = Field(False, description="Edit permission")
    can_execute: bool = Field(False, description="Execute permission")
    can_share: bool = Field(False, description="Share permission")
    message: Optional[str] = Field(None, description="Message to recipient")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    is_public_link: bool = Field(False, description="Create public link")
    
    @root_validator(skip_on_failure=True)
    def validate_share_target(cls, values):
        shared_with = values.get('shared_with')
        team_id = values.get('team_id')
        is_public_link = values.get('is_public_link')
        
        if not any([shared_with, team_id, is_public_link]):
            raise ValueError('Must specify shared_with, team_id, or is_public_link')
        
        return values


class WorkflowShareUpdate(BaseModel):
    """Schema for updating workflow shares"""
    can_view: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_execute: Optional[bool] = None
    can_share: Optional[bool] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_public_link: Optional[bool] = None


class WorkflowShare(BaseModel):
    """Schema for workflow share responses"""
    id: int
    workflow_id: int
    shared_by: int
    shared_with: Optional[int]
    team_id: Optional[int]
    can_view: bool
    can_edit: bool
    can_execute: bool
    can_share: bool
    message: Optional[str]
    expires_at: Optional[datetime]
    is_public_link: bool
    public_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Complex operation schemas
class WorkflowFromTemplate(BaseModel):
    """Schema for creating workflow from template"""
    template_id: int = Field(..., description="ID of the template to use")
    workspace_id: int = Field(..., description="ID of the target workspace")
    name: str = Field(..., min_length=1, max_length=200, description="New workflow name")
    description: Optional[str] = Field(None, description="New workflow description")
    variable_values: Dict[str, Any] = Field(default_factory=dict, description="Values for template variables")


class WorkflowDuplicate(BaseModel):
    """Schema for duplicating workflow"""
    name: str = Field(..., min_length=1, max_length=200, description="New workflow name")
    workspace_id: Optional[int] = Field(None, description="Target workspace (default: same as original)")
    include_executions: bool = Field(False, description="Copy execution history")


class WorkflowBulkExecute(BaseModel):
    """Schema for bulk workflow execution"""
    workflow_ids: List[int] = Field(..., min_items=1, max_items=50, description="Workflow IDs to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Common input data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Common execution context")


class WorkflowExecutionControl(BaseModel):
    """Schema for controlling workflow execution"""
    action: str = Field(..., pattern="^(pause|resume|cancel|retry)$", description="Control action")
    reason: Optional[str] = Field(None, description="Reason for the action")


# Response schemas for lists and pagination
class WorkflowListResponse(BaseModel):
    """Schema for paginated workflow list responses"""
    items: List[Workflow]
    total: int
    page: int
    per_page: int
    pages: int


class WorkflowTemplateListResponse(BaseModel):
    """Schema for paginated workflow template list responses"""
    items: List[WorkflowTemplate]
    total: int
    page: int
    per_page: int
    pages: int


class WorkflowExecutionListResponse(BaseModel):
    """Schema for paginated workflow execution list responses"""
    items: List[WorkflowExecution]
    total: int
    page: int
    per_page: int
    pages: int


# Status and statistics schemas
class WorkflowStatistics(BaseModel):
    """Schema for workflow statistics"""
    total_workflows: int
    active_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time: float
    most_used_templates: List[Dict[str, Any]]
    execution_trends: List[Dict[str, Any]]


class WorkflowHealthCheck(BaseModel):
    """Schema for workflow system health check"""
    status: str
    active_executions: int
    pending_schedules: int
    failed_webhooks: int
    system_load: float
    last_cleanup: datetime