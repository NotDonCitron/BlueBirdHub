"""
Workflow Template Engine

This service provides pre-built workflow templates for common business processes
and handles template instantiation with variable substitution.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import re

from src.backend.crud.crud_workflow import crud_workflow_template, crud_workflow
from src.backend.models.workflow import WorkflowTemplate, ActionType, TriggerType
from src.backend.schemas.workflow import WorkflowCreate, WorkflowStepCreate, WorkflowTriggerCreate


class WorkflowTemplateEngine:
    """Engine for managing workflow templates and instantiation"""
    
    def __init__(self):
        self.built_in_templates = self._load_built_in_templates()
    
    def _load_built_in_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in workflow templates"""
        return {
            "project_kickoff": self._project_kickoff_template(),
            "sprint_planning": self._sprint_planning_template(),
            "content_creation": self._content_creation_template(),
            "client_onboarding": self._client_onboarding_template(),
            "bug_triage": self._bug_triage_template(),
            "employee_onboarding": self._employee_onboarding_template(),
            "sales_pipeline": self._sales_pipeline_template(),
            "recurring_maintenance": self._recurring_maintenance_template(),
            "expense_approval": self._expense_approval_template(),
            "time_off_approval": self._time_off_approval_template(),
            "invoice_processing": self._invoice_processing_template(),
            "lead_qualification": self._lead_qualification_template(),
            "code_review": self._code_review_template(),
            "marketing_campaign": self._marketing_campaign_template(),
            "customer_support": self._customer_support_template(),
        }
    
    def get_built_in_templates(self) -> List[Dict[str, Any]]:
        """Get all built-in templates metadata"""
        return [
            {
                "id": key,
                "name": template["name"],
                "description": template["description"],
                "category": template["category"],
                "variables": template["variables"],
                "tags": template["tags"]
            }
            for key, template in self.built_in_templates.items()
        ]
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get built-in template by ID"""
        return self.built_in_templates.get(template_id)
    
    def create_workflow_from_template(
        self,
        db: Session,
        *,
        template_id: str,
        workspace_id: int,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        variable_values: Dict[str, Any] = None
    ) -> int:
        """Create workflow from built-in template"""
        template = self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Merge default variables with provided values
        variables = {**template["variables"], **(variable_values or {})}
        
        # Process template data with variable substitution
        workflow_data = self._substitute_variables(template["template_data"], variables)
        
        # Create workflow object
        workflow_create = WorkflowCreate(
            name=name,
            description=description or template["description"],
            workspace_id=workspace_id,
            config=workflow_data.get("config", {}),
            variables=variables,
            timeout_minutes=workflow_data.get("timeout_minutes", 60),
            max_retries=workflow_data.get("max_retries", 3),
            is_parallel=workflow_data.get("is_parallel", False),
            steps=[
                WorkflowStepCreate(**step) for step in workflow_data.get("steps", [])
            ],
            triggers=[
                WorkflowTriggerCreate(**trigger) for trigger in workflow_data.get("triggers", [])
            ]
        )
        
        # Create workflow
        workflow = crud_workflow.create_with_steps_and_triggers(
            db, obj_in=workflow_create, user_id=user_id
        )
        
        return workflow.id
    
    def _substitute_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in template data"""
        if isinstance(data, dict):
            return {key: self._substitute_variables(value, variables) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_variables(item, variables) for item in data]
        elif isinstance(data, str):
            return self._substitute_string_variables(data, variables)
        else:
            return data
    
    def _substitute_string_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in string using {{variable}} syntax"""
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        
        return re.sub(r'\{\{(\w+)\}\}', replace_var, text)
    
    def initialize_built_in_templates(self, db: Session) -> None:
        """Initialize built-in templates in database"""
        for template_id, template_data in self.built_in_templates.items():
            # Check if template already exists
            existing = db.query(WorkflowTemplate).filter(
                WorkflowTemplate.name == template_data["name"]
            ).first()
            
            if not existing:
                db_template = WorkflowTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    category=template_data["category"],
                    version=template_data.get("version", "1.0.0"),
                    template_data=template_data["template_data"],
                    variables=template_data["variables"],
                    tags=template_data["tags"],
                    is_public=True,
                    created_by=None  # System template
                )
                db.add(db_template)
        
        db.commit()
    
    # Built-in template definitions
    def _project_kickoff_template(self) -> Dict[str, Any]:
        """Project kickoff workflow template"""
        return {
            "name": "Project Kickoff",
            "description": "Automated project kickoff workflow with onboarding tasks and setup",
            "category": "project_management",
            "version": "1.0.0",
            "tags": ["project", "kickoff", "onboarding", "setup"],
            "variables": {
                "project_name": "New Project",
                "project_manager": "",
                "team_members": [],
                "deadline": "",
                "project_type": "software"
            },
            "template_data": {
                "config": {"auto_assign": True},
                "timeout_minutes": 120,
                "steps": [
                    {
                        "name": "Create Project Workspace",
                        "description": "Create workspace for {{project_name}}",
                        "step_type": ActionType.CREATE_WORKSPACE,
                        "order": 1,
                        "config": {
                            "workspace_name": "{{project_name}}",
                            "description": "Workspace for {{project_name}} project"
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Send Welcome Email",
                        "description": "Send welcome email to team members",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 2,
                        "config": {
                            "to": "{{team_members}}",
                            "subject": "Welcome to {{project_name}}",
                            "template": "project_welcome"
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Create Initial Tasks",
                        "description": "Create initial project setup tasks",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 3,
                        "config": {
                            "tasks": [
                                {
                                    "title": "Project Charter Review",
                                    "description": "Review and approve project charter",
                                    "priority": "high",
                                    "assigned_to": "{{project_manager}}"
                                },
                                {
                                    "title": "Setup Development Environment",
                                    "description": "Setup development environment for team",
                                    "priority": "medium"
                                },
                                {
                                    "title": "Schedule Kickoff Meeting",
                                    "description": "Schedule project kickoff meeting",
                                    "priority": "high",
                                    "assigned_to": "{{project_manager}}"
                                }
                            ]
                        },
                        "depends_on": [1],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Send Notifications",
                        "description": "Send project start notifications",
                        "step_type": ActionType.SEND_NOTIFICATION,
                        "order": 4,
                        "config": {
                            "message": "{{project_name}} has been kicked off successfully!",
                            "channels": ["slack", "email"]
                        },
                        "depends_on": [2, 3],
                        "position_x": 300,
                        "position_y": 300
                    }
                ],
                "triggers": [
                    {
                        "name": "Manual Start",
                        "trigger_type": TriggerType.MANUAL,
                        "config": {},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _sprint_planning_template(self) -> Dict[str, Any]:
        """Sprint planning workflow template"""
        return {
            "name": "Sprint Planning",
            "description": "Automated sprint planning workflow with backlog grooming and planning poker",
            "category": "project_management",
            "version": "1.0.0",
            "tags": ["sprint", "planning", "agile", "scrum"],
            "variables": {
                "sprint_number": 1,
                "sprint_duration": "2 weeks",
                "team_velocity": 20,
                "scrum_master": ""
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Prepare Backlog",
                        "description": "Prepare and groom product backlog",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "backlog_grooming",
                            "criteria": ["priority", "effort", "dependencies"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Send Planning Invites",
                        "description": "Send sprint planning meeting invites",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 2,
                        "config": {
                            "subject": "Sprint {{sprint_number}} Planning Meeting",
                            "template": "sprint_planning_invite"
                        },
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Create Sprint Tasks",
                        "description": "Create tasks for sprint {{sprint_number}}",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 3,
                        "config": {
                            "sprint_goal": "Complete sprint planning",
                            "capacity": "{{team_velocity}}"
                        },
                        "depends_on": [1],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Generate Sprint Report",
                        "description": "Generate sprint planning report",
                        "step_type": ActionType.GENERATE_REPORT,
                        "order": 4,
                        "config": {
                            "report_type": "sprint_plan",
                            "format": "pdf"
                        },
                        "depends_on": [3],
                        "position_x": 300,
                        "position_y": 300
                    }
                ],
                "triggers": [
                    {
                        "name": "Sprint Schedule",
                        "trigger_type": TriggerType.SCHEDULE,
                        "cron_expression": "0 9 * * MON",
                        "config": {"every": "2 weeks"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _content_creation_template(self) -> Dict[str, Any]:
        """Content creation workflow template"""
        return {
            "name": "Content Creation Workflow",
            "description": "Content creation workflow with draft, review, approve, and publish steps",
            "category": "content_management",
            "version": "1.0.0",
            "tags": ["content", "creation", "review", "publishing"],
            "variables": {
                "content_type": "blog_post",
                "author": "",
                "reviewer": "",
                "publisher": "",
                "publication_date": ""
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Create Content Draft",
                        "description": "Create initial content draft",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 1,
                        "config": {
                            "task_type": "content_creation",
                            "assigned_to": "{{author}}",
                            "content_type": "{{content_type}}"
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "AI Content Analysis",
                        "description": "Analyze content for quality and compliance",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 2,
                        "config": {
                            "analysis_type": "content_quality",
                            "checks": ["grammar", "readability", "seo", "tone"]
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Content Review",
                        "description": "Review content for approval",
                        "step_type": ActionType.APPROVAL,
                        "order": 3,
                        "config": {
                            "approver": "{{reviewer}}",
                            "approval_type": "content_review",
                            "timeout_hours": 48
                        },
                        "depends_on": [2],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Schedule Publication",
                        "description": "Schedule content for publication",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 4,
                        "config": {
                            "task_type": "content_publishing",
                            "assigned_to": "{{publisher}}",
                            "scheduled_date": "{{publication_date}}"
                        },
                        "depends_on": [3],
                        "conditions": [
                            {"field": "approval_status", "operator": "equals", "value": "approved"}
                        ],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Send Publication Notification",
                        "description": "Notify team of content publication",
                        "step_type": ActionType.SEND_NOTIFICATION,
                        "order": 5,
                        "config": {
                            "message": "{{content_type}} has been published",
                            "channels": ["slack"]
                        },
                        "depends_on": [4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Manual Content Creation",
                        "trigger_type": TriggerType.MANUAL,
                        "config": {},
                        "is_enabled": True
                    },
                    {
                        "name": "Content Request",
                        "trigger_type": TriggerType.EVENT,
                        "config": {"event_type": "content_request"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _client_onboarding_template(self) -> Dict[str, Any]:
        """Client onboarding workflow template"""
        return {
            "name": "Client Onboarding",
            "description": "Complete client onboarding process with contracts, setup, and kickoff",
            "category": "client_management",
            "version": "1.0.0",
            "tags": ["client", "onboarding", "contracts", "setup"],
            "variables": {
                "client_name": "",
                "account_manager": "",
                "contract_value": 0,
                "project_start_date": "",
                "services": []
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Send Welcome Package",
                        "description": "Send welcome package to {{client_name}}",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 1,
                        "config": {
                            "template": "client_welcome",
                            "attachments": ["welcome_guide.pdf", "contract_template.pdf"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Contract Review",
                        "description": "Review and process client contract",
                        "step_type": ActionType.APPROVAL,
                        "order": 2,
                        "config": {
                            "approval_type": "contract_review",
                            "approver": "legal_team",
                            "contract_value": "{{contract_value}}"
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Setup Client Account",
                        "description": "Setup client account and access",
                        "step_type": ActionType.CREATE_WORKSPACE,
                        "order": 3,
                        "config": {
                            "workspace_name": "{{client_name}} - Client Portal",
                            "access_level": "client",
                            "services": "{{services}}"
                        },
                        "depends_on": [2],
                        "conditions": [
                            {"field": "contract_status", "operator": "equals", "value": "approved"}
                        ],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Schedule Kickoff Meeting",
                        "description": "Schedule project kickoff meeting",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 4,
                        "config": {
                            "task_type": "meeting",
                            "title": "{{client_name}} Project Kickoff",
                            "assigned_to": "{{account_manager}}",
                            "due_date": "{{project_start_date}}"
                        },
                        "depends_on": [3],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Send Access Credentials",
                        "description": "Send client portal access credentials",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 5,
                        "config": {
                            "template": "client_access",
                            "secure": True
                        },
                        "depends_on": [3],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "New Client Signup",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "crm_system"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _bug_triage_template(self) -> Dict[str, Any]:
        """Bug triage workflow template"""
        return {
            "name": "Bug Triage Workflow",
            "description": "Automated bug triage process with report, assign, fix, test, and deploy steps",
            "category": "development",
            "version": "1.0.0",
            "tags": ["bug", "triage", "development", "testing"],
            "variables": {
                "developer": "",
                "tester": "",
                "severity_threshold": "medium",
                "auto_assign": True
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Analyze Bug Report",
                        "description": "AI analysis of bug report",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "bug_classification",
                            "extract": ["severity", "component", "reproduction_steps"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Assign to Developer",
                        "description": "Assign bug to appropriate developer",
                        "step_type": ActionType.ASSIGN_TASK,
                        "order": 2,
                        "config": {
                            "assignment_criteria": "expertise",
                            "default_assignee": "{{developer}}"
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Create Fix Task",
                        "description": "Create task for bug fix",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 3,
                        "config": {
                            "task_type": "bug_fix",
                            "priority_mapping": {
                                "critical": "urgent",
                                "high": "high",
                                "medium": "medium",
                                "low": "low"
                            }
                        },
                        "depends_on": [2],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Schedule Testing",
                        "description": "Schedule testing after fix completion",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 4,
                        "config": {
                            "task_type": "testing",
                            "assigned_to": "{{tester}}",
                            "depends_on_fix": True
                        },
                        "depends_on": [3],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Send Resolution Notification",
                        "description": "Notify stakeholders of bug resolution",
                        "step_type": ActionType.SEND_NOTIFICATION,
                        "order": 5,
                        "config": {
                            "condition": "fix_verified",
                            "message": "Bug has been resolved and verified"
                        },
                        "depends_on": [4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Bug Report Submitted",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "bug_tracker"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _employee_onboarding_template(self) -> Dict[str, Any]:
        """Employee onboarding workflow template"""
        return {
            "name": "Employee Onboarding",
            "description": "Complete employee onboarding with paperwork, training, and equipment setup",
            "category": "human_resources",
            "version": "1.0.0",
            "tags": ["hr", "onboarding", "employee", "training"],
            "variables": {
                "employee_name": "",
                "position": "",
                "department": "",
                "manager": "",
                "start_date": "",
                "equipment_needed": []
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Send Welcome Email",
                        "description": "Send welcome email to new employee",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 1,
                        "config": {
                            "template": "employee_welcome",
                            "to": "{{employee_name}}",
                            "cc": "{{manager}}"
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Create HR Tasks",
                        "description": "Create HR onboarding tasks",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 2,
                        "config": {
                            "tasks": [
                                {
                                    "title": "Prepare Employment Contract",
                                    "assigned_to": "hr_team",
                                    "due_date": "{{start_date}}"
                                },
                                {
                                    "title": "Setup Payroll",
                                    "assigned_to": "payroll_team"
                                },
                                {
                                    "title": "Prepare ID Badge",
                                    "assigned_to": "security_team"
                                }
                            ]
                        },
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Order Equipment",
                        "description": "Order required equipment for employee",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 3,
                        "config": {
                            "task_type": "equipment_order",
                            "items": "{{equipment_needed}}",
                            "assigned_to": "it_team"
                        },
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Schedule Training",
                        "description": "Schedule orientation and training sessions",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 4,
                        "config": {
                            "task_type": "training_schedule",
                            "position": "{{position}}",
                            "department": "{{department}}"
                        },
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "First Day Checklist",
                        "description": "Create first day checklist for manager",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 5,
                        "config": {
                            "task_type": "checklist",
                            "assigned_to": "{{manager}}",
                            "due_date": "{{start_date}}"
                        },
                        "depends_on": [2, 3, 4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "New Hire Added",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "hr_system"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _sales_pipeline_template(self) -> Dict[str, Any]:
        """Sales pipeline workflow template"""
        return {
            "name": "Sales Pipeline",
            "description": "Sales pipeline workflow with lead qualification, demo, and closing steps",
            "category": "sales",
            "version": "1.0.0",
            "tags": ["sales", "pipeline", "lead", "demo", "closing"],
            "variables": {
                "lead_source": "",
                "sales_rep": "",
                "qualification_criteria": [],
                "demo_duration": 60,
                "follow_up_days": 3
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Lead Qualification",
                        "description": "Qualify lead based on criteria",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "lead_qualification",
                            "criteria": "{{qualification_criteria}}",
                            "score_threshold": 7
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Assign Sales Rep",
                        "description": "Assign qualified lead to sales rep",
                        "step_type": ActionType.ASSIGN_TASK,
                        "order": 2,
                        "config": {
                            "assignment_type": "round_robin",
                            "default_assignee": "{{sales_rep}}"
                        },
                        "depends_on": [1],
                        "conditions": [
                            {"field": "qualification_score", "operator": "greater_than", "value": 6}
                        ],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Schedule Demo",
                        "description": "Schedule product demonstration",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 3,
                        "config": {
                            "task_type": "demo_meeting",
                            "duration_minutes": "{{demo_duration}}",
                            "calendar_integration": True
                        },
                        "depends_on": [2],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Follow-up Sequence",
                        "description": "Schedule follow-up communications",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 4,
                        "config": {
                            "task_type": "follow_up",
                            "sequence": [
                                {"delay_days": 1, "type": "email", "template": "demo_followup"},
                                {"delay_days": "{{follow_up_days}}", "type": "call"},
                                {"delay_days": 7, "type": "email", "template": "proposal"}
                            ]
                        },
                        "depends_on": [3],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Proposal Generation",
                        "description": "Generate customized proposal",
                        "step_type": ActionType.GENERATE_REPORT,
                        "order": 5,
                        "config": {
                            "report_type": "proposal",
                            "template": "sales_proposal",
                            "auto_send": True
                        },
                        "depends_on": [4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "New Lead Created",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "crm"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _recurring_maintenance_template(self) -> Dict[str, Any]:
        """Recurring maintenance workflow template"""
        return {
            "name": "Recurring Maintenance",
            "description": "Automated recurring maintenance workflow for backups, updates, and reviews",
            "category": "maintenance",
            "version": "1.0.0",
            "tags": ["maintenance", "backup", "updates", "monitoring"],
            "variables": {
                "maintenance_type": "weekly",
                "systems": [],
                "notification_channels": ["email"],
                "backup_retention_days": 30
            },
            "template_data": {
                "steps": [
                    {
                        "name": "System Health Check",
                        "description": "Perform system health checks",
                        "step_type": ActionType.CALL_API,
                        "order": 1,
                        "config": {
                            "api_type": "health_check",
                            "systems": "{{systems}}",
                            "metrics": ["cpu", "memory", "disk", "network"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Backup Systems",
                        "description": "Perform system backups",
                        "step_type": ActionType.CALL_API,
                        "order": 2,
                        "config": {
                            "api_type": "backup",
                            "retention_days": "{{backup_retention_days}}",
                            "verify_backup": True
                        },
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Update Dependencies",
                        "description": "Check and update system dependencies",
                        "step_type": ActionType.CALL_API,
                        "order": 3,
                        "config": {
                            "api_type": "update_check",
                            "auto_update": False,
                            "security_only": True
                        },
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Generate Maintenance Report",
                        "description": "Generate maintenance summary report",
                        "step_type": ActionType.GENERATE_REPORT,
                        "order": 4,
                        "config": {
                            "report_type": "maintenance_summary",
                            "include_metrics": True,
                            "format": "html"
                        },
                        "depends_on": [1, 2, 3],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Send Maintenance Report",
                        "description": "Send maintenance report to stakeholders",
                        "step_type": ActionType.SEND_NOTIFICATION,
                        "order": 5,
                        "config": {
                            "channels": "{{notification_channels}}",
                            "include_report": True
                        },
                        "depends_on": [4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Weekly Maintenance",
                        "trigger_type": TriggerType.SCHEDULE,
                        "cron_expression": "0 2 * * SUN",
                        "config": {"description": "Weekly maintenance at 2 AM Sunday"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _expense_approval_template(self) -> Dict[str, Any]:
        """Expense approval workflow template"""
        return {
            "name": "Expense Approval",
            "description": "Automated expense approval workflow with multi-level approval",
            "category": "finance",
            "version": "1.0.0",
            "tags": ["expense", "approval", "finance", "reimbursement"],
            "variables": {
                "approval_threshold_1": 100,
                "approval_threshold_2": 500,
                "manager": "",
                "finance_team": "finance@company.com",
                "auto_approve_limit": 50
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Validate Expense",
                        "description": "Validate expense submission",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "expense_validation",
                            "checks": ["receipt_present", "policy_compliance", "amount_reasonable"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Auto Approval Check",
                        "description": "Check if expense qualifies for auto approval",
                        "step_type": ActionType.CONDITIONAL,
                        "order": 2,
                        "config": {
                            "condition": "amount <= {{auto_approve_limit}} AND validation_score > 8"
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Manager Approval",
                        "description": "Request manager approval",
                        "step_type": ActionType.APPROVAL,
                        "order": 3,
                        "config": {
                            "approver": "{{manager}}",
                            "approval_type": "expense",
                            "timeout_hours": 72
                        },
                        "depends_on": [2],
                        "conditions": [
                            {"field": "auto_approved", "operator": "not_equals", "value": True}
                        ],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Finance Team Approval",
                        "description": "Request finance team approval for large expenses",
                        "step_type": ActionType.APPROVAL,
                        "order": 4,
                        "config": {
                            "approver": "{{finance_team}}",
                            "approval_type": "expense_large",
                            "timeout_hours": 48
                        },
                        "depends_on": [3],
                        "conditions": [
                            {"field": "amount", "operator": "greater_than", "value": "{{approval_threshold_2}}"}
                        ],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Process Reimbursement",
                        "description": "Process approved expense reimbursement",
                        "step_type": ActionType.CALL_API,
                        "order": 5,
                        "config": {
                            "api_type": "payroll_system",
                            "action": "process_reimbursement"
                        },
                        "depends_on": [3, 4],
                        "conditions": [
                            {"field": "approval_status", "operator": "equals", "value": "approved"}
                        ],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Expense Submitted",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "expense_system"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _time_off_approval_template(self) -> Dict[str, Any]:
        """Time off approval workflow template"""
        return {
            "name": "Time Off Approval",
            "description": "Automated time off request approval workflow",
            "category": "human_resources",
            "version": "1.0.0",
            "tags": ["hr", "time_off", "approval", "leave"],
            "variables": {
                "manager": "",
                "hr_team": "hr@company.com",
                "notice_period_days": 14,
                "max_consecutive_days": 30
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Validate Request",
                        "description": "Validate time off request",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "time_off_validation",
                            "checks": ["notice_period", "available_balance", "team_coverage"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Check Team Coverage",
                        "description": "Check if team coverage is available",
                        "step_type": ActionType.CALL_API,
                        "order": 2,
                        "config": {
                            "api_type": "scheduling_system",
                            "check_type": "team_coverage"
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Manager Approval",
                        "description": "Request manager approval",
                        "step_type": ActionType.APPROVAL,
                        "order": 3,
                        "config": {
                            "approver": "{{manager}}",
                            "approval_type": "time_off",
                            "timeout_hours": 48
                        },
                        "depends_on": [1, 2],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "HR Review",
                        "description": "HR review for extended leave",
                        "step_type": ActionType.APPROVAL,
                        "order": 4,
                        "config": {
                            "approver": "{{hr_team}}",
                            "approval_type": "extended_leave"
                        },
                        "depends_on": [3],
                        "conditions": [
                            {"field": "days_requested", "operator": "greater_than", "value": "{{max_consecutive_days}}"}
                        ],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Update Calendar",
                        "description": "Update calendar and scheduling systems",
                        "step_type": ActionType.CALL_API,
                        "order": 5,
                        "config": {
                            "api_type": "calendar_system",
                            "action": "block_time"
                        },
                        "depends_on": [3, 4],
                        "conditions": [
                            {"field": "approval_status", "operator": "equals", "value": "approved"}
                        ],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Time Off Request",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "hr_system"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _invoice_processing_template(self) -> Dict[str, Any]:
        """Invoice processing workflow template"""
        return {
            "name": "Invoice Processing",
            "description": "Automated invoice processing workflow with validation and approval",
            "category": "finance",
            "version": "1.0.0",
            "tags": ["invoice", "processing", "finance", "accounts_payable"],
            "variables": {
                "approval_limit": 1000,
                "department_head": "",
                "accounts_payable": "ap@company.com",
                "payment_terms": 30
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Extract Invoice Data",
                        "description": "Extract data from invoice using AI",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "invoice_extraction",
                            "extract_fields": ["vendor", "amount", "date", "po_number", "line_items"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Validate Invoice",
                        "description": "Validate invoice against purchase order",
                        "step_type": ActionType.CALL_API,
                        "order": 2,
                        "config": {
                            "api_type": "erp_system",
                            "validation_type": "three_way_match"
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Department Approval",
                        "description": "Get department head approval",
                        "step_type": ActionType.APPROVAL,
                        "order": 3,
                        "config": {
                            "approver": "{{department_head}}",
                            "approval_type": "invoice",
                            "timeout_hours": 72
                        },
                        "depends_on": [2],
                        "conditions": [
                            {"field": "amount", "operator": "greater_than", "value": "{{approval_limit}}"}
                        ],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Schedule Payment",
                        "description": "Schedule payment based on terms",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 4,
                        "config": {
                            "task_type": "payment_processing",
                            "assigned_to": "{{accounts_payable}}",
                            "due_date_calculation": "invoice_date + {{payment_terms}} days"
                        },
                        "depends_on": [2, 3],
                        "conditions": [
                            {"field": "validation_status", "operator": "equals", "value": "valid"}
                        ],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Update Accounting System",
                        "description": "Update accounting system with invoice",
                        "step_type": ActionType.CALL_API,
                        "order": 5,
                        "config": {
                            "api_type": "accounting_system",
                            "action": "create_payable"
                        },
                        "depends_on": [4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Invoice Received",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "email_scanner"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _lead_qualification_template(self) -> Dict[str, Any]:
        """Lead qualification workflow template"""
        return {
            "name": "Lead Qualification",
            "description": "AI-powered lead qualification and scoring workflow",
            "category": "sales",
            "version": "1.0.0",
            "tags": ["lead", "qualification", "scoring", "sales"],
            "variables": {
                "qualification_criteria": {
                    "budget": 10,
                    "authority": 8,
                    "need": 9,
                    "timeline": 7
                },
                "minimum_score": 25,
                "sales_team": "sales@company.com"
            },
            "template_data": {
                "steps": [
                    {
                        "name": "AI Lead Scoring",
                        "description": "AI analysis and scoring of lead",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "lead_scoring",
                            "criteria": "{{qualification_criteria}}",
                            "data_sources": ["website_behavior", "form_data", "social_media"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Enrich Lead Data",
                        "description": "Enrich lead with additional data",
                        "step_type": ActionType.CALL_API,
                        "order": 2,
                        "config": {
                            "api_type": "data_enrichment",
                            "providers": ["clearbit", "zoominfo"],
                            "fields": ["company_size", "industry", "technology_stack"]
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Qualification Decision",
                        "description": "Make qualification decision based on score",
                        "step_type": ActionType.CONDITIONAL,
                        "order": 3,
                        "config": {
                            "condition": "lead_score >= {{minimum_score}}"
                        },
                        "depends_on": [1, 2],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Route Qualified Lead",
                        "description": "Route qualified lead to sales team",
                        "step_type": ActionType.ASSIGN_TASK,
                        "order": 4,
                        "config": {
                            "assignment_type": "lead_routing",
                            "criteria": ["territory", "industry", "product_interest"],
                            "default_assignee": "{{sales_team}}"
                        },
                        "depends_on": [3],
                        "conditions": [
                            {"field": "qualified", "operator": "equals", "value": True}
                        ],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Nurture Unqualified Lead",
                        "description": "Add unqualified lead to nurture campaign",
                        "step_type": ActionType.CALL_API,
                        "order": 5,
                        "config": {
                            "api_type": "marketing_automation",
                            "campaign": "lead_nurture",
                            "segment": "unqualified"
                        },
                        "depends_on": [3],
                        "conditions": [
                            {"field": "qualified", "operator": "equals", "value": False}
                        ],
                        "position_x": 500,
                        "position_y": 300
                    }
                ],
                "triggers": [
                    {
                        "name": "New Lead Created",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "marketing_automation"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _code_review_template(self) -> Dict[str, Any]:
        """Code review workflow template"""
        return {
            "name": "Code Review Workflow",
            "description": "Automated code review workflow with AI analysis and peer review",
            "category": "development",
            "version": "1.0.0",
            "tags": ["code", "review", "development", "quality"],
            "variables": {
                "reviewers": [],
                "required_approvals": 2,
                "ai_analysis_enabled": True,
                "auto_merge": False
            },
            "template_data": {
                "steps": [
                    {
                        "name": "AI Code Analysis",
                        "description": "AI analysis of code changes",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "code_review",
                            "checks": ["security", "performance", "style", "complexity", "test_coverage"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Assign Reviewers",
                        "description": "Assign code reviewers",
                        "step_type": ActionType.ASSIGN_TASK,
                        "order": 2,
                        "config": {
                            "reviewers": "{{reviewers}}",
                            "assignment_type": "code_expertise",
                            "required_count": "{{required_approvals}}"
                        },
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Collect Reviews",
                        "description": "Collect peer reviews",
                        "step_type": ActionType.APPROVAL,
                        "order": 3,
                        "config": {
                            "approval_type": "code_review",
                            "required_approvals": "{{required_approvals}}",
                            "timeout_hours": 48
                        },
                        "depends_on": [2],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Run Automated Tests",
                        "description": "Run automated test suite",
                        "step_type": ActionType.CALL_API,
                        "order": 4,
                        "config": {
                            "api_type": "ci_system",
                            "test_suites": ["unit", "integration", "security"]
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Merge Code",
                        "description": "Merge approved code changes",
                        "step_type": ActionType.CALL_API,
                        "order": 5,
                        "config": {
                            "api_type": "version_control",
                            "action": "merge",
                            "auto_merge": "{{auto_merge}}"
                        },
                        "depends_on": [3, 4],
                        "conditions": [
                            {"field": "reviews_approved", "operator": "equals", "value": True},
                            {"field": "tests_passed", "operator": "equals", "value": True}
                        ],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Pull Request Created",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "git_repository"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _marketing_campaign_template(self) -> Dict[str, Any]:
        """Marketing campaign workflow template"""
        return {
            "name": "Marketing Campaign",
            "description": "Complete marketing campaign workflow from planning to analysis",
            "category": "marketing",
            "version": "1.0.0",
            "tags": ["marketing", "campaign", "content", "analytics"],
            "variables": {
                "campaign_name": "",
                "target_audience": "",
                "budget": 0,
                "duration_days": 30,
                "channels": ["email", "social"]
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Campaign Planning",
                        "description": "AI-assisted campaign planning",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "campaign_planning",
                            "inputs": ["target_audience", "budget", "objectives"],
                            "outputs": ["content_strategy", "channel_mix", "timeline"]
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Create Content",
                        "description": "Create campaign content",
                        "step_type": ActionType.CREATE_TASK,
                        "order": 2,
                        "config": {
                            "task_type": "content_creation",
                            "content_types": ["email_templates", "social_posts", "landing_pages"],
                            "brand_guidelines": True
                        },
                        "depends_on": [1],
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Setup Tracking",
                        "description": "Setup campaign tracking and analytics",
                        "step_type": ActionType.CALL_API,
                        "order": 3,
                        "config": {
                            "api_type": "analytics_system",
                            "setup_type": "campaign_tracking",
                            "metrics": ["impressions", "clicks", "conversions", "roi"]
                        },
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Launch Campaign",
                        "description": "Launch marketing campaign",
                        "step_type": ActionType.CALL_API,
                        "order": 4,
                        "config": {
                            "api_type": "marketing_automation",
                            "action": "launch_campaign",
                            "channels": "{{channels}}"
                        },
                        "depends_on": [2, 3],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Monitor Performance",
                        "description": "Monitor campaign performance",
                        "step_type": ActionType.GENERATE_REPORT,
                        "order": 5,
                        "config": {
                            "report_type": "campaign_performance",
                            "frequency": "daily",
                            "auto_optimization": True
                        },
                        "depends_on": [4],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "Campaign Launch Date",
                        "trigger_type": TriggerType.SCHEDULE,
                        "config": {"schedule_type": "campaign_start"},
                        "is_enabled": True
                    }
                ]
            }
        }
    
    def _customer_support_template(self) -> Dict[str, Any]:
        """Customer support workflow template"""
        return {
            "name": "Customer Support Ticket",
            "description": "Automated customer support ticket workflow with routing and escalation",
            "category": "customer_service",
            "version": "1.0.0",
            "tags": ["support", "customer", "ticket", "escalation"],
            "variables": {
                "support_teams": {
                    "technical": "tech_support",
                    "billing": "billing_team",
                    "general": "general_support"
                },
                "escalation_threshold_hours": 24,
                "satisfaction_threshold": 3
            },
            "template_data": {
                "steps": [
                    {
                        "name": "Ticket Classification",
                        "description": "AI classification of support ticket",
                        "step_type": ActionType.AI_ANALYSIS,
                        "order": 1,
                        "config": {
                            "analysis_type": "ticket_classification",
                            "categories": ["technical", "billing", "feature_request", "bug_report"],
                            "priority_detection": True,
                            "sentiment_analysis": True
                        },
                        "position_x": 100,
                        "position_y": 100
                    },
                    {
                        "name": "Auto-Response",
                        "description": "Send automatic acknowledgment to customer",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 2,
                        "config": {
                            "template": "ticket_acknowledgment",
                            "include_ticket_number": True,
                            "estimated_response_time": True
                        },
                        "position_x": 300,
                        "position_y": 100
                    },
                    {
                        "name": "Route to Team",
                        "description": "Route ticket to appropriate support team",
                        "step_type": ActionType.ASSIGN_TASK,
                        "order": 3,
                        "config": {
                            "routing_rules": "{{support_teams}}",
                            "load_balancing": True,
                            "skill_matching": True
                        },
                        "depends_on": [1],
                        "position_x": 100,
                        "position_y": 300
                    },
                    {
                        "name": "Escalation Check",
                        "description": "Check if ticket needs escalation",
                        "step_type": ActionType.CONDITIONAL,
                        "order": 4,
                        "config": {
                            "condition": "hours_open > {{escalation_threshold_hours}} OR priority == 'urgent'"
                        },
                        "depends_on": [3],
                        "position_x": 300,
                        "position_y": 300
                    },
                    {
                        "name": "Follow-up Survey",
                        "description": "Send customer satisfaction survey",
                        "step_type": ActionType.SEND_EMAIL,
                        "order": 5,
                        "config": {
                            "template": "satisfaction_survey",
                            "delay_hours": 24,
                            "condition": "ticket_status == 'resolved'"
                        },
                        "depends_on": [3],
                        "position_x": 200,
                        "position_y": 500
                    }
                ],
                "triggers": [
                    {
                        "name": "New Support Ticket",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "support_system"},
                        "is_enabled": True
                    },
                    {
                        "name": "Email Support",
                        "trigger_type": TriggerType.WEBHOOK,
                        "config": {"source": "email_integration"},
                        "is_enabled": True
                    }
                ]
            }
        }


# Create global instance
workflow_template_engine = WorkflowTemplateEngine()