"""
Workflow models for automated business processes

This module contains SQLAlchemy models for the workflow automation system,
including workflows, templates, executions, triggers, actions, and conditions.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey,
    Enum, Float, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum
from typing import Optional, Dict, Any, List

from src.backend.models.base import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowExecutionStatus(str, enum.Enum):
    """Individual workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, enum.Enum):
    """Types of workflow triggers"""
    MANUAL = "manual"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    EVENT = "event"
    API_CALL = "api_call"
    FILE_UPLOAD = "file_upload"
    TASK_STATUS = "task_status"
    TIME_BASED = "time_based"


class ActionType(str, enum.Enum):
    """Types of workflow actions"""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    ASSIGN_TASK = "assign_task"
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    CREATE_WORKSPACE = "create_workspace"
    MOVE_FILE = "move_file"
    GENERATE_REPORT = "generate_report"
    CALL_API = "call_api"
    WAIT = "wait"
    CONDITIONAL = "conditional"
    APPROVAL = "approval"
    AI_ANALYSIS = "ai_analysis"
    WEBHOOK_CALL = "webhook_call"


class ConditionOperator(str, enum.Enum):
    """Condition operators for workflow logic"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN = "in"
    NOT_IN = "not_in"


class WorkflowTemplate(Base):
    """Pre-built workflow templates for common business processes"""
    
    __tablename__ = "workflow_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)  # e.g., "project_management", "hr", "sales"
    version = Column(String(20), default="1.0.0")
    template_data = Column(JSON, nullable=False)  # Complete workflow structure
    variables = Column(JSON, default=dict)  # Template variables and defaults
    tags = Column(JSON, default=list)  # Searchable tags
    is_public = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", backref="created_templates")
    workflows = relationship("Workflow", back_populates="template")
    
    __table_args__ = (
        Index("idx_template_category_name", "category", "name"),
        Index("idx_template_public_rating", "is_public", "rating"),
    )


class Workflow(Base):
    """Main workflow definition"""
    
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=True)
    
    # Ownership and sharing
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Configuration
    config = Column(JSON, default=dict)  # Workflow-level configuration
    variables = Column(JSON, default=dict)  # Workflow variables
    
    # Execution settings
    timeout_minutes = Column(Integer, default=60)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=30)
    is_parallel = Column(Boolean, default=False)
    
    # Analytics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_executed_at = Column(DateTime, nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", backref="workflows")
    creator = relationship("User", backref="created_workflows")
    template = relationship("WorkflowTemplate", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    triggers = relationship("WorkflowTrigger", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    versions = relationship("WorkflowVersion", back_populates="workflow", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_workflow_workspace_status", "workspace_id", "status"),
        Index("idx_workflow_creator_updated", "created_by", "updated_at"),
        UniqueConstraint("workspace_id", "name", "version", name="uq_workflow_name_version"),
    )


class WorkflowStep(Base):
    """Individual steps within a workflow"""
    
    __tablename__ = "workflow_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    step_type = Column(Enum(ActionType), nullable=False)
    order = Column(Integer, nullable=False)  # Execution order
    
    # Configuration
    config = Column(JSON, default=dict)  # Step-specific configuration
    input_mapping = Column(JSON, default=dict)  # Map workflow variables to step inputs
    output_mapping = Column(JSON, default=dict)  # Map step outputs to workflow variables
    
    # Dependencies and flow control
    depends_on = Column(JSON, default=list)  # List of step IDs that must complete first
    conditions = Column(JSON, default=list)  # Conditions for step execution
    
    # Error handling
    on_error = Column(String(50), default="fail")  # "fail", "continue", "retry"
    retry_count = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=300)
    
    # UI positioning for visual designer
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    executions = relationship("WorkflowStepExecution", back_populates="step")
    
    __table_args__ = (
        Index("idx_step_workflow_order", "workflow_id", "order"),
        UniqueConstraint("workflow_id", "order", name="uq_step_order"),
    )


class WorkflowTrigger(Base):
    """Triggers that start workflow executions"""
    
    __tablename__ = "workflow_triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    name = Column(String(200), nullable=False)
    trigger_type = Column(Enum(TriggerType), nullable=False)
    
    # Trigger configuration
    config = Column(JSON, default=dict)  # Type-specific configuration
    conditions = Column(JSON, default=list)  # Conditions for trigger activation
    
    # Schedule configuration (for scheduled triggers)
    cron_expression = Column(String(100), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    # Status and control
    is_enabled = Column(Boolean, default=True)
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="triggers")
    
    __table_args__ = (
        Index("idx_trigger_workflow_type", "workflow_id", "trigger_type"),
        Index("idx_trigger_enabled_type", "is_enabled", "trigger_type"),
    )


class WorkflowExecution(Base):
    """Individual workflow execution instances"""
    
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    trigger_id = Column(Integer, ForeignKey("workflow_triggers.id"), nullable=True)
    
    # Execution details
    status = Column(Enum(WorkflowExecutionStatus), default=WorkflowExecutionStatus.PENDING)
    started_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Context and variables
    input_data = Column(JSON, default=dict)  # Input data for this execution
    variables = Column(JSON, default=dict)  # Runtime variables
    context = Column(JSON, default=dict)  # Execution context
    
    # Results and errors
    output_data = Column(JSON, default=dict)  # Final output data
    error_message = Column(Text, nullable=True)
    error_step_id = Column(Integer, nullable=True)
    
    # Performance metrics
    execution_time_seconds = Column(Float, nullable=True)
    steps_completed = Column(Integer, default=0)
    steps_total = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    trigger = relationship("WorkflowTrigger")
    starter = relationship("User")
    step_executions = relationship("WorkflowStepExecution", back_populates="execution", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_execution_workflow_status", "workflow_id", "status"),
        Index("idx_execution_started_at", "started_at"),
        Index("idx_execution_status_updated", "status", "updated_at"),
    )


class WorkflowStepExecution(Base):
    """Individual step execution within a workflow execution"""
    
    __tablename__ = "workflow_step_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=False)
    
    # Execution details
    status = Column(Enum(WorkflowExecutionStatus), default=WorkflowExecutionStatus.PENDING)
    attempt_number = Column(Integer, default=1)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Data
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    
    # Performance
    execution_time_seconds = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="step_executions")
    step = relationship("WorkflowStep", back_populates="executions")
    
    __table_args__ = (
        Index("idx_step_exec_execution_step", "execution_id", "step_id"),
        Index("idx_step_exec_status", "status"),
        UniqueConstraint("execution_id", "step_id", "attempt_number", name="uq_step_execution_attempt"),
    )


class WorkflowVersion(Base):
    """Workflow version history for rollback capabilities"""
    
    __tablename__ = "workflow_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Versioned data
    name = Column(String(200), nullable=False)
    description = Column(Text)
    config = Column(JSON, default=dict)
    steps_data = Column(JSON, default=list)  # Complete steps configuration
    triggers_data = Column(JSON, default=list)  # Complete triggers configuration
    
    # Version metadata
    change_description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=False)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="versions")
    creator = relationship("User")
    
    __table_args__ = (
        Index("idx_version_workflow_number", "workflow_id", "version_number"),
        UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version"),
    )


class WorkflowSchedule(Base):
    """Scheduled workflow executions"""
    
    __tablename__ = "workflow_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    trigger_id = Column(Integer, ForeignKey("workflow_triggers.id"), nullable=False)
    
    # Schedule details
    name = Column(String(200), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    
    # Status and control
    is_enabled = Column(Boolean, default=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    
    # Configuration
    input_data = Column(JSON, default=dict)  # Input data for scheduled executions
    max_runs = Column(Integer, nullable=True)  # Maximum number of runs (None = unlimited)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow")
    trigger = relationship("WorkflowTrigger")
    
    __table_args__ = (
        Index("idx_schedule_next_run", "is_enabled", "next_run_at"),
        Index("idx_schedule_workflow", "workflow_id"),
    )


class WorkflowWebhook(Base):
    """Webhook endpoints for triggering workflows"""
    
    __tablename__ = "workflow_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    trigger_id = Column(Integer, ForeignKey("workflow_triggers.id"), nullable=False)
    
    # Webhook details
    name = Column(String(200), nullable=False)
    webhook_url = Column(String(500), nullable=False, unique=True)
    secret_key = Column(String(100), nullable=True)  # For webhook verification
    
    # Configuration
    allowed_methods = Column(JSON, default=["POST"])  # HTTP methods
    content_type = Column(String(100), default="application/json")
    headers = Column(JSON, default=dict)  # Expected headers
    
    # Security
    is_enabled = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # Requests per hour
    ip_whitelist = Column(JSON, default=list)  # Allowed IP addresses
    
    # Analytics
    request_count = Column(Integer, default=0)
    last_request_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow")
    trigger = relationship("WorkflowTrigger")
    
    __table_args__ = (
        Index("idx_webhook_url", "webhook_url"),
        Index("idx_webhook_workflow", "workflow_id"),
    )


class WorkflowAnalytics(Base):
    """Analytics and performance metrics for workflows"""
    
    __tablename__ = "workflow_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    
    # Time period
    date = Column(DateTime, nullable=False)  # Daily aggregation
    
    # Execution metrics
    executions_total = Column(Integer, default=0)
    executions_successful = Column(Integer, default=0)
    executions_failed = Column(Integer, default=0)
    executions_cancelled = Column(Integer, default=0)
    
    # Performance metrics
    avg_execution_time = Column(Float, default=0.0)
    min_execution_time = Column(Float, default=0.0)
    max_execution_time = Column(Float, default=0.0)
    total_execution_time = Column(Float, default=0.0)
    
    # Error metrics
    timeout_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    most_common_error = Column(String(500), nullable=True)
    
    # Resource usage
    cpu_usage_avg = Column(Float, default=0.0)
    memory_usage_avg = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow")
    
    __table_args__ = (
        Index("idx_analytics_workflow_date", "workflow_id", "date"),
        UniqueConstraint("workflow_id", "date", name="uq_workflow_analytics_date"),
    )


class WorkflowShare(Base):
    """Workflow sharing and collaboration"""
    
    __tablename__ = "workflow_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, nullable=True)  # For team sharing
    
    # Permissions
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_execute = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    
    # Sharing details
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_public_link = Column(Boolean, default=False)
    public_token = Column(String(100), nullable=True, unique=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow")
    sharer = relationship("User", foreign_keys=[shared_by])
    recipient = relationship("User", foreign_keys=[shared_with])
    
    __table_args__ = (
        Index("idx_share_workflow_recipient", "workflow_id", "shared_with"),
        Index("idx_share_public_token", "public_token"),
        CheckConstraint("shared_with IS NOT NULL OR team_id IS NOT NULL OR is_public_link = true", 
                       name="check_share_target"),
    )