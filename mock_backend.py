#!/usr/bin/env python3
"""
Mock Backend Server for Collaborative Workspace Demo
Provides REST API endpoints without external dependencies
"""

import json
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import uuid

class MockAPIHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _set_cors_headers(self):
        """Set CORS headers to allow frontend access"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Access-Control-Allow-Credentials', 'true')
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _get_request_data(self):
        """Get JSON data from request body"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except:
            return {}
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]  # Remove query parameters
        
        # Remove /api prefix if present to support both /api/endpoint and /endpoint
        if path.startswith('/api/'):
            path = path[4:]  # Remove '/api' prefix
        
        # Root endpoint
        if path == '/':
            self._send_json_response({
                "status": "running",
                "message": "OrdnungsHub Mock API is operational",
                "version": "0.1.0",
                "features": ["collaboration", "workspace-management", "task-assignment"]
            })
        
        # Health check
        elif path == '/health':
            self._send_json_response({
                "status": "healthy",
                "backend": "operational",
                "database": "mock",
                "collaboration_features": "enabled"
            })
        
        # Tasks endpoints
        elif path == '/tasks':
            self._send_json_response({
                "tasks": [
                    {
                        "id": "1",
                        "title": "Implement collaborative features",
                        "description": "Add team management and workspace sharing",
                        "status": "completed",
                        "priority": "high",
                        "workspace_id": 1,
                        "created_at": "2025-06-17T10:00:00Z",
                        "assignments": [
                            {
                                "user": {"username": "john_doe", "email": "john@example.com"},
                                "role": "owner",
                                "completion_percentage": 100
                            }
                        ]
                    },
                    {
                        "id": "2", 
                        "title": "Setup team collaboration",
                        "description": "Configure team roles and permissions",
                        "status": "in-progress",
                        "priority": "medium",
                        "workspace_id": 1,
                        "created_at": "2025-06-17T11:00:00Z",
                        "assignments": [
                            {
                                "user": {"username": "jane_smith", "email": "jane@example.com"},
                                "role": "collaborator", 
                                "completion_percentage": 75
                            }
                        ]
                    }
                ],
                "total": 2
            })
        
        elif path == '/tasks/taskmaster/all':
            self._send_json_response({
                "tasks": [
                    {
                        "id": "1",
                        "title": "Collaborative Workspace Implementation",
                        "description": "Implement team management, workspace sharing, and task collaboration features",
                        "status": "completed",
                        "priority": "high",
                        "workspace_id": 1,
                        "created_at": "2025-06-17T10:00:00Z"
                    },
                    {
                        "id": "2",
                        "title": "API Endpoint Development", 
                        "description": "Create REST APIs for all collaborative features",
                        "status": "completed",
                        "priority": "high",
                        "workspace_id": 1,
                        "created_at": "2025-06-17T11:00:00Z"
                    },
                    {
                        "id": "3",
                        "title": "React UI Components",
                        "description": "Build collaborative workspace and enhanced task manager components",
                        "status": "completed", 
                        "priority": "medium",
                        "workspace_id": 1,
                        "created_at": "2025-06-17T12:00:00Z"
                    }
                ]
            })
        
        # Collaboration endpoints
        elif path == '/collaboration/teams':
            self._send_json_response([
                {
                    "id": 1,
                    "name": "Development Team",
                    "description": "Main development team for collaborative features",
                    "is_public": False,
                    "created_at": "2025-06-17T09:00:00Z",
                    "member_count": 3
                },
                {
                    "id": 2,
                    "name": "Design Team", 
                    "description": "UI/UX design team",
                    "is_public": True,
                    "created_at": "2025-06-17T09:30:00Z",
                    "member_count": 2
                }
            ])
        
        elif path == '/collaboration/workspaces':
            self._send_json_response([
                {
                    "workspace": {
                        "id": 1,
                        "name": "Collaborative Workspace Demo",
                        "description": "Demo workspace showcasing all collaborative features",
                        "created_at": "2025-06-17T08:00:00Z"
                    },
                    "access_type": "owner",
                    "permissions": ["read", "write", "delete", "share", "admin"],
                    "shared_at": None
                },
                {
                    "workspace": {
                        "id": 2,
                        "name": "Shared Project Workspace", 
                        "description": "Workspace shared with team members",
                        "created_at": "2025-06-17T08:30:00Z"
                    },
                    "access_type": "shared",
                    "permissions": ["read", "write"],
                    "shared_at": "2025-06-17T09:00:00Z"
                }
            ])
        
        elif path == '/collaboration/tasks/assigned':
            self._send_json_response([
                {
                    "task": {
                        "id": 1,
                        "title": "Implement team management",
                        "description": "Create database models and APIs for team management",
                        "status": "completed",
                        "priority": "high",
                        "workspace_id": 1
                    },
                    "assignment": {
                        "role": "owner",
                        "assigned_at": "2025-06-17T10:00:00Z",
                        "completion_percentage": 100
                    }
                },
                {
                    "task": {
                        "id": 2,
                        "title": "Build React components",
                        "description": "Develop collaborative workspace UI components", 
                        "status": "in-progress",
                        "priority": "medium",
                        "workspace_id": 1
                    },
                    "assignment": {
                        "role": "collaborator",
                        "assigned_at": "2025-06-17T11:00:00Z",
                        "completion_percentage": 85
                    }
                }
            ])
        
        # AI endpoints
        elif path == '/ai/workspace-suggestions':
            self._send_json_response({
                "suggestions": [
                    {
                        "type": "workspace",
                        "title": "Team Collaboration Hub",
                        "description": "Create a dedicated space for team collaboration with shared tasks and documents",
                        "priority": "high",
                        "features": ["team-management", "task-sharing", "document-collaboration"]
                    },
                    {
                        "type": "workspace",
                        "title": "Project Management Space", 
                        "description": "Organize project tasks with timeline tracking and milestone management",
                        "priority": "medium",
                        "features": ["project-tracking", "milestone-management", "progress-analytics"]
                    }
                ]
            })
        
        # Workspaces endpoints
        elif path == '/workspaces':
            self._send_json_response({
                "workspaces": [
                    {
                        "id": 1,
                        "name": "Collaborative Workspace Demo",
                        "description": "Demo workspace with all collaborative features",
                        "created_at": "2025-06-17T08:00:00Z",
                        "file_count": 15,
                        "task_count": 8,
                        "collaboration_enabled": True
                    },
                    {
                        "id": 2,
                        "name": "Development Workspace",
                        "description": "Main development workspace for the team",
                        "created_at": "2025-06-17T07:00:00Z", 
                        "file_count": 42,
                        "task_count": 23,
                        "collaboration_enabled": True
                    }
                ],
                "total": 2
            })
        
        # Dashboard endpoint
        elif path == '/dashboard/stats':
            self._send_json_response({
                "total_workspaces": 2,
                "total_tasks": 8,
                "completed_tasks": 5,
                "team_members": 3,
                "active_collaborations": 4,
                "recent_activity": [
                    {
                        "action": "Task completed",
                        "description": "Collaborative features implementation",
                        "timestamp": "2025-06-17T16:00:00Z",
                        "user": "john_doe"
                    },
                    {
                        "action": "Team member added",
                        "description": "Added jane_smith to Development Team",
                        "timestamp": "2025-06-17T15:30:00Z", 
                        "user": "admin"
                    }
                ]
            })
        
        # Task progress endpoint
        elif path == '/tasks/taskmaster/progress':
            self._send_json_response({
                "progress": {
                    "completed": 8,
                    "total": 15,
                    "percentage": 53.3,
                    "recent_completions": [
                        {"task": "Collaborative features implementation", "completed_at": "2025-06-17T16:00:00Z"},
                        {"task": "API endpoint development", "completed_at": "2025-06-17T15:30:00Z"}
                    ]
                }
            })
        
        # Next task endpoint
        elif path == '/tasks/taskmaster/next':
            self._send_json_response({
                "next_task": {
                    "id": "next-1",
                    "title": "Implement advanced search features",
                    "description": "Add full-text search and filtering capabilities",
                    "priority": "medium",
                    "estimated_time": "4 hours",
                    "tags": ["search", "ui", "backend"]
                }
            })
        
        # Automation endpoints
        elif path == '/automation/dashboard':
            self._send_json_response({
                "success": True,
                "statistics": {
                    "rules": {
                        "total": 5,
                        "enabled": 3,
                        "total_triggers": 127
                    },
                    "scheduled_tasks": {
                        "total": 3,
                        "enabled": 2,
                        "total_runs": 45
                    }
                },
                "most_active_rules": [
                    {
                        "id": "rule-1",
                        "name": "Auto-organize Documents",
                        "description": "Automatically organize PDF files by date",
                        "trigger_count": 45,
                        "enabled": True,
                        "created_at": "2025-06-01T10:00:00Z"
                    },
                    {
                        "id": "rule-2", 
                        "name": "Image Compression",
                        "description": "Compress large images automatically",
                        "trigger_count": 32,
                        "enabled": True,
                        "created_at": "2025-06-05T14:30:00Z"
                    }
                ],
                "upcoming_tasks": [
                    {
                        "id": "task-1",
                        "name": "Weekly Cleanup",
                        "description": "Clean up temporary files",
                        "next_run": "2025-06-18T09:00:00Z",
                        "schedule": {"type": "weekly", "time": "09:00"},
                        "enabled": True
                    }
                ],
                "recent_activity": [
                    {
                        "timestamp": "2025-06-17T16:30:00Z",
                        "type": "rule_triggered",
                        "message": "Auto-organize Documents rule processed 3 files"
                    },
                    {
                        "timestamp": "2025-06-17T15:45:00Z", 
                        "type": "task_completed",
                        "message": "Weekly Cleanup task completed successfully"
                    }
                ]
            })
        
        elif path == '/automation/rules':
            self._send_json_response({
                "success": True,
                "rules": [
                    {
                        "id": "rule-1",
                        "name": "Auto-organize Documents",
                        "description": "Automatically organize PDF files by date",
                        "conditions": {
                            "file_extension": ["pdf", "doc", "docx"],
                            "filename_contains": [],
                            "file_size_mb": {"min": 0, "max": 50}
                        },
                        "actions": {
                            "move_to_workspace": 1,
                            "add_tags": ["document", "auto-organized"],
                            "notify": True
                        },
                        "enabled": True,
                        "created_at": "2025-06-01T10:00:00Z",
                        "last_triggered": "2025-06-17T16:30:00Z",
                        "trigger_count": 45
                    },
                    {
                        "id": "rule-2",
                        "name": "Image Compression", 
                        "description": "Compress large images automatically",
                        "conditions": {
                            "file_extension": ["jpg", "jpeg", "png"],
                            "file_size_mb": {"min": 5}
                        },
                        "actions": {
                            "compress": True,
                            "move_to_folder": "compressed_images",
                            "add_tags": ["compressed"]
                        },
                        "enabled": True,
                        "created_at": "2025-06-05T14:30:00Z",
                        "last_triggered": "2025-06-17T14:20:00Z",
                        "trigger_count": 32
                    }
                ]
            })
        
        elif path == '/automation/scheduled-tasks':
            self._send_json_response({
                "success": True,
                "tasks": [
                    {
                        "id": "task-1",
                        "name": "Weekly Cleanup",
                        "description": "Clean up temporary files and empty folders",
                        "schedule": {
                            "type": "weekly",
                            "time": "09:00",
                            "timezone": "Europe/Berlin",
                            "day": "Monday"
                        },
                        "actions": [
                            "cleanup_temp_files",
                            "remove_empty_folders",
                            "optimize_database"
                        ],
                        "enabled": True,
                        "last_run": "2025-06-10T09:00:00Z",
                        "next_run": "2025-06-17T09:00:00Z",
                        "run_count": 12,
                        "status": "active"
                    },
                    {
                        "id": "task-2",
                        "name": "Daily Backup",
                        "description": "Create daily backup of important files",
                        "schedule": {
                            "type": "daily",
                            "time": "02:00",
                            "timezone": "Europe/Berlin"
                        },
                        "actions": [
                            "backup_user_data",
                            "backup_configurations"
                        ],
                        "enabled": True,
                        "last_run": "2025-06-17T02:00:00Z",
                        "next_run": "2025-06-18T02:00:00Z",
                        "run_count": 45,
                        "status": "active"
                    }
                ]
            })
        
        # API logs endpoint for frontend errors
        elif path == '/logs/frontend-error':
            self._send_json_response({"message": "Error logged successfully"})
        
        # File search endpoint
        elif path.startswith('/search/files'):
            self._send_json_response({
                "files": [
                    {
                        "id": "file-1",
                        "name": "Project Proposal.pdf",
                        "type": "pdf",
                        "size": "2.5 MB",
                        "modified": "2025-06-17T14:30:00Z",
                        "tags": ["important", "client"],
                        "category": "documents",
                        "priority": "high",
                        "workspace_id": 1,
                        "workspace_name": "Collaborative Workspace Demo",
                        "folder": "/Documents/Proposals"
                    },
                    {
                        "id": "file-2",
                        "name": "Meeting Notes.docx",
                        "type": "docx",
                        "size": "156 KB",
                        "modified": "2025-06-17T16:00:00Z",
                        "tags": ["meeting", "team"],
                        "category": "documents",
                        "priority": "medium",
                        "workspace_id": 2,
                        "workspace_name": "Development Workspace",
                        "folder": "/Documents/Meetings"
                    },
                    {
                        "id": "file-3",
                        "name": "Budget Report.xlsx",
                        "type": "xlsx",
                        "size": "3.8 MB",
                        "modified": "2025-06-17T12:00:00Z",
                        "tags": ["finance", "quarterly"],
                        "category": "business",
                        "priority": "high",
                        "workspace_id": 1,
                        "workspace_name": "Collaborative Workspace Demo",
                        "folder": "/Finance/Reports"
                    }
                ],
                "total": 3,
                "page": 1,
                "per_page": 20
            })
        
        # File stats endpoint
        elif path == '/files/stats':
            self._send_json_response({
                "total_files": 150,
                "total_size_gb": 25.6,
                "category_stats": {
                    "documents": {"count": 45, "size": 8.2},
                    "business": {"count": 30, "size": 5.5},
                    "design": {"count": 25, "size": 6.8},
                    "marketing": {"count": 20, "size": 3.1},
                    "other": {"count": 30, "size": 2.0}
                },
                "insights": [
                    {
                        "type": "storage",
                        "message": "25% of storage used by design files",
                        "action": "Consider archiving old design files"
                    },
                    {
                        "type": "organization",
                        "message": "30 files without proper categorization",
                        "action": "Review and categorize uncategorized files"
                    }
                ],
                "large_files": [
                    {
                        "path": "/Design/UI Mockups.psd",
                        "size_mb": 450,
                        "category": "design"
                    }
                ]
            })
        
        # Quick actions endpoint
        elif path == '/files/quick-actions':
            self._send_json_response({
                "actions": [
                    {
                        "action": "organize_duplicates",
                        "title": "Remove Duplicate Files",
                        "description": "Found 12 duplicate files taking up 1.2GB",
                        "priority": "high",
                        "estimated_savings_mb": 1200
                    },
                    {
                        "action": "archive_old_files",
                        "title": "Archive Old Files",
                        "description": "45 files haven't been accessed in over 6 months",
                        "priority": "medium",
                        "estimated_savings_mb": 3500
                    },
                    {
                        "action": "categorize_files",
                        "title": "Categorize Uncategorized Files",
                        "description": "30 files need proper categorization",
                        "priority": "low"
                    }
                ]
            })
        
        # File filter options endpoint
        elif path == '/files/filter-options':
            self._send_json_response({
                "types": ["pdf", "docx", "xlsx", "pptx", "jpg", "png", "mp4", "zip"],
                "categories": ["documents", "business", "design", "marketing", "development", "other"],
                "workspaces": [
                    {"id": 1, "name": "Collaborative Workspace Demo"},
                    {"id": 2, "name": "Development Workspace"}
                ],
                "tags": ["important", "client", "meeting", "team", "finance", "quarterly", "review", "draft"]
            })
        
        # 404 for unknown endpoints
        else:
            self._send_json_response({
                "error": "Endpoint not found",
                "path": path,
                "available_endpoints": [
                    "/", "/health", "/tasks", "/collaboration/teams", 
                    "/collaboration/workspaces", "/ai/workspace-suggestions",
                    "/workspaces", "/dashboard/stats", "/api/logs/frontend-error",
                    "/search/files", "/files/stats", "/files/quick-actions", 
                    "/files/filter-options"
                ]
            }, 404)
    
    def do_POST(self):
        """Handle POST requests"""
        path = self.path
        
        # Remove /api prefix if present to support both /api/endpoint and /endpoint
        if path.startswith('/api/'):
            path = path[4:]  # Remove '/api' prefix
            
        data = self._get_request_data()
        
        # Create team
        if path == '/collaboration/teams':
            team_id = len(MockAPIHandler.teams) + 1
            team = {
                "id": team_id,
                "name": data.get("name", "New Team"),
                "description": data.get("description", ""),
                "is_public": data.get("is_public", False),
                "created_at": datetime.now().isoformat() + "Z",
                "invite_code": str(uuid.uuid4())[:10].upper()
            }
            self._send_json_response(team, 201)
        
        # Assign task
        elif path.startswith('/collaboration/tasks/') and path.endswith('/assign'):
            task_id = path.split('/')[-2]
            assignment = {
                "id": len(MockAPIHandler.assignments) + 1,
                "task_id": task_id,
                "assigned_to": data.get("assigned_to"),
                "role": data.get("role", "collaborator"),
                "estimated_hours": data.get("estimated_hours"),
                "completion_percentage": 0,
                "assigned_at": datetime.now().isoformat() + "Z"
            }
            self._send_json_response(assignment, 201)
        
        # Add comment
        elif path.startswith('/collaboration/tasks/') and path.endswith('/comments'):
            task_id = path.split('/')[-2]
            comment = {
                "id": len(MockAPIHandler.comments) + 1,
                "task_id": task_id,
                "content": data.get("content"),
                "comment_type": data.get("comment_type", "comment"),
                "created_at": datetime.now().isoformat() + "Z",
                "user": {
                    "id": 1,
                    "username": "current_user"
                }
            }
            self._send_json_response(comment, 201)
        
        # Share workspace
        elif path.startswith('/collaboration/workspaces/') and path.endswith('/share'):
            workspace_id = path.split('/')[-2]
            share = {
                "id": len(MockAPIHandler.shares) + 1,
                "workspace_id": workspace_id,
                "shared_with_user_id": data.get("user_id"),
                "shared_with_team_id": data.get("team_id"),
                "permissions": json.dumps(data.get("permissions", [])),
                "shared_at": datetime.now().isoformat() + "Z"
            }
            self._send_json_response(share, 201)
        
        # Automation rule endpoints
        elif path == '/automation/rules':
            rule = {
                "id": f"rule-{len(MockAPIHandler.automation_rules) + 1}",
                "name": data.get("name", "New Rule"),
                "description": data.get("description", ""),
                "conditions": data.get("conditions", {}),
                "actions": data.get("actions", {}),
                "enabled": data.get("enabled", True),
                "created_at": datetime.now().isoformat() + "Z",
                "trigger_count": 0
            }
            MockAPIHandler.automation_rules.append(rule)
            self._send_json_response({"success": True, "rule": rule}, 201)
        
        elif path.startswith('/automation/rules/') and path.endswith('/toggle'):
            rule_id = path.split('/')[-2]
            self._send_json_response({"success": True, "rule_id": rule_id, "toggled": True}, 200)
        
        elif path == '/automation/scheduled-tasks':
            task = {
                "id": f"task-{len(MockAPIHandler.scheduled_tasks) + 1}",
                "name": data.get("name", "New Task"),
                "description": data.get("description", ""),
                "schedule": data.get("schedule", {}),
                "actions": data.get("actions", []),
                "enabled": data.get("enabled", True),
                "created_at": datetime.now().isoformat() + "Z",
                "next_run": datetime.now().isoformat() + "Z",
                "run_count": 0,
                "status": "active"
            }
            MockAPIHandler.scheduled_tasks.append(task)
            self._send_json_response({"success": True, "task": task}, 201)
        
        elif path.startswith('/automation/scheduled-tasks/') and path.endswith('/toggle'):
            task_id = path.split('/')[-2]
            self._send_json_response({"success": True, "task_id": task_id, "toggled": True}, 200)
        
        elif path.startswith('/automation/scheduled-tasks/') and path.endswith('/run'):
            task_id = path.split('/')[-2]
            self._send_json_response({
                "success": True, 
                "task": {"id": task_id, "name": "Test Task", "status": "completed"}
            }, 200)
        
        # Frontend error logging
        elif path == '/logs/frontend-error':
            self._send_json_response({"message": "Frontend error logged successfully"}, 201)
        
        else:
            self._send_json_response({"error": "POST endpoint not found", "path": path}, 404)
    
    def do_PUT(self):
        """Handle PUT requests"""
        path = self.path
        
        # Remove /api prefix if present to support both /api/endpoint and /endpoint
        if path.startswith('/api/'):
            path = path[4:]  # Remove '/api' prefix
            
        data = self._get_request_data()
        
        # Update task progress
        if path.startswith('/collaboration/tasks/') and path.endswith('/progress'):
            task_id = path.split('/')[-2]
            update = {
                "task_id": task_id,
                "completion_percentage": data.get("completion_percentage", 0),
                "actual_hours": data.get("actual_hours"),
                "updated_at": datetime.now().isoformat() + "Z"
            }
            self._send_json_response(update)
        
        # Delete automation rule
        elif path.startswith('/automation/rules/') and not path.endswith('/toggle'):
            rule_id = path.split('/')[-1]
            self._send_json_response({"success": True, "deleted_rule_id": rule_id}, 200)
        
        # Delete scheduled task  
        elif path.startswith('/automation/scheduled-tasks/') and not path.endswith(('/toggle', '/run')):
            task_id = path.split('/')[-1]
            self._send_json_response({"success": True, "deleted_task_id": task_id}, 200)
        
        else:
            self._send_json_response({"error": "PUT endpoint not found", "path": path}, 404)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        path = self.path
        
        # Remove /api prefix if present to support both /api/endpoint and /endpoint
        if path.startswith('/api/'):
            path = path[4:]  # Remove '/api' prefix
        
        # Delete automation rule
        if path.startswith('/automation/rules/'):
            rule_id = path.split('/')[-1]
            self._send_json_response({"success": True, "deleted_rule_id": rule_id}, 200)
        
        # Delete scheduled task
        elif path.startswith('/automation/scheduled-tasks/'):
            task_id = path.split('/')[-1]
            self._send_json_response({"success": True, "deleted_task_id": task_id}, 200)
        
        else:
            self._send_json_response({"error": "DELETE endpoint not found", "path": path}, 404)
    
    def log_message(self, format, *args):
        """Custom log message to show requests"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

# Class variables to simulate database
MockAPIHandler.teams = []
MockAPIHandler.assignments = []
MockAPIHandler.comments = []
MockAPIHandler.shares = []
MockAPIHandler.automation_rules = []
MockAPIHandler.scheduled_tasks = []

def start_mock_backend(port=8001):
    """Start the mock backend server"""
    try:
        with socketserver.TCPServer(("", port), MockAPIHandler) as httpd:
            print("OrdnungsHub Mock Backend Server")
            print("=" * 60)
            print(f"Server running on: http://localhost:{port}")
            print(f"API endpoints: http://localhost:{port}/")
            print(f"Health check: http://localhost:{port}/health")
            print("Collaborative features: ENABLED")
            print("Press Ctrl+C to stop the server")
            print("=" * 60)
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n\nMock backend stopped")
                print("Session completed")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Port {port} is already in use. Trying port {port + 1}...")
            start_mock_backend(port + 1)
        else:
            print(f"Failed to start server: {e}")

if __name__ == "__main__":
    start_mock_backend()