#!/usr/bin/env python3
"""
ULTRA SIMPLE Backend - NO DEPENDENCIES NEEDED
Uses only Python standard library
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import urllib.parse
import os
import uuid
import mimetypes
import base64

# In-memory storage for demo purposes
workspaces_storage = [
    {"id": 1, "name": "Personal", "color": "#3B82F6", "created_at": datetime.now().isoformat(), "description": "Personal tasks and projects"},
    {"id": 2, "name": "Work", "color": "#10B981", "created_at": datetime.now().isoformat(), "description": "Work-related tasks and meetings"},
    {"id": 3, "name": "Projects", "color": "#F59E0B", "created_at": datetime.now().isoformat(), "description": "Side projects and learning"}
]

# Agent System Storage
agents_storage = [
    {
        "id": "a2a-google",
        "name": "Google A2A Agent",
        "description": "Google's Agent-to-Agent communication protocol implementation",
        "capabilities": ["task-delegation", "communication", "protocol-translation"],
        "status": "active",
        "type": "a2a",
        "version": "0.2.8",
        "endpoint": "http://localhost:8002/a2a"
    },
    {
        "id": "anubis-workflow",
        "name": "Anubis Workflow Manager",
        "description": "Intelligent workflow guidance and role-based task management",
        "capabilities": ["workflow-management", "role-guidance", "reporting"],
        "status": "active",
        "type": "anubis",
        "version": "1.0.0",
        "endpoint": "http://localhost:8003/anubis"
    },
    {
        "id": "serena-coder",
        "name": "Serena Code Assistant",
        "description": "Semantic code analysis and editing toolkit",
        "capabilities": ["code-analysis", "semantic-search", "refactoring", "lsp-integration"],
        "status": "active",
        "type": "serena",
        "version": "latest",
        "endpoint": "http://localhost:8004/serena"
    }
]

agent_tasks_storage = []
agent_workflows_storage = []
agent_messages_storage = []
next_agent_task_id = 1
next_workflow_id = 1
next_message_id = 1

# User storage and authentication
import hashlib
import secrets

users_storage = [
    {
        "id": 1,
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),  # Password: admin123
        "created_at": datetime.now().isoformat(),
        "last_login": None
    },
    {
        "id": 2, 
        "username": "user",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),  # Password: user123
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
]

# Active sessions storage (token -> user_id)
sessions_storage = {}

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def authenticate_user(username, password):
    """Authenticate user and return user data if valid"""
    password_hash = hash_password(password)
    user = next((u for u in users_storage if u["username"] == username and u["password_hash"] == password_hash), None)
    if user:
        # Update last login
        user["last_login"] = datetime.now().isoformat()
        return user
    return None

def get_user_from_token(token):
    """Get user from session token"""
    if not token:
        return None
    user_id = sessions_storage.get(token)
    if user_id:
        return next((u for u in users_storage if u["id"] == user_id), None)
    return None

def require_auth(handler_method):
    """Decorator to require authentication for endpoints"""
    def wrapper(self):
        # Get token from Authorization header
        auth_header = self.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        user = get_user_from_token(token)
        if not user:
            self._send_json_response({"error": "Authentication required"}, 401)
            return
        
        # Add user to self for use in handler
        self.current_user = user
        return handler_method(self)
    return wrapper

tasks_storage = [
    {"id": "T001", "title": "Setup Core Application Framework", "description": "Create the foundational structure for OrdnungsHub", "status": "done", "priority": "high", "dependencies": [], "completed_at": "2024-06-08T10:00:00Z", "workspace_id": 1, "due_date": "2024-06-10T12:00:00Z", "created_at": "2024-06-08T09:00:00Z", "tags": ["setup", "backend", "foundation"], "parent_task_id": None, "subtasks": [], "attachments": []},
    {"id": "T002", "title": "Implement Frontend Components", "description": "Build React components for the user interface", "status": "in-progress", "priority": "high", "dependencies": ["T001"], "workspace_id": 1, "due_date": "2024-06-20T18:00:00Z", "created_at": "2024-06-08T11:00:00Z", "tags": ["frontend", "ui", "react", "feature"], "parent_task_id": None, "subtasks": ["T002-1", "T002-2", "T002-3"], "attachments": []},
    {"id": "T003", "title": "Add Error Handling", "description": "Implement comprehensive error handling and logging", "status": "pending", "priority": "medium", "dependencies": ["T002"], "workspace_id": 1, "due_date": "2024-06-25T16:00:00Z", "created_at": "2024-06-08T12:00:00Z", "tags": ["bug", "enhancement", "logging"], "parent_task_id": None, "subtasks": [], "attachments": []},
    {"id": "T002-1", "title": "Create Navigation Component", "description": "Build the main navigation bar", "status": "done", "priority": "medium", "dependencies": [], "workspace_id": 1, "created_at": "2024-06-08T13:00:00Z", "tags": ["frontend", "ui"], "parent_task_id": "T002", "subtasks": [], "attachments": []},
    {"id": "T002-2", "title": "Implement Task List View", "description": "Create the task listing component", "status": "in-progress", "priority": "medium", "dependencies": ["T002-1"], "workspace_id": 1, "created_at": "2024-06-08T14:00:00Z", "tags": ["frontend", "ui"], "parent_task_id": "T002", "subtasks": [], "attachments": []},
    {"id": "T002-3", "title": "Add Task Creation Form", "description": "Build form for creating new tasks", "status": "pending", "priority": "medium", "dependencies": ["T002-2"], "workspace_id": 1, "created_at": "2024-06-08T15:00:00Z", "tags": ["frontend", "ui"], "parent_task_id": "T002", "subtasks": [], "attachments": []}
]

next_workspace_id = 4
next_task_id = 4

# File storage
files_storage = []
next_file_id = 1

# Ensure upload directories exist
os.makedirs('uploads/tasks', exist_ok=True)
os.makedirs('uploads/workspaces', exist_ok=True)

def get_file_type_icon(mime_type):
    """Get emoji icon for file type"""
    if mime_type.startswith('image/'):
        return '🖼️'
    elif mime_type.startswith('video/'):
        return '🎥'
    elif mime_type.startswith('audio/'):
        return '🎵'
    elif 'pdf' in mime_type:
        return '📄'
    elif any(x in mime_type for x in ['word', 'doc']):
        return '📝'
    elif any(x in mime_type for x in ['excel', 'sheet']):
        return '📊'
    elif any(x in mime_type for x in ['powerpoint', 'presentation']):
        return '📺'
    elif 'text' in mime_type:
        return '📃'
    elif 'zip' in mime_type or 'compressed' in mime_type:
        return '📦'
    else:
        return '📎'

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def is_allowed_file_type(filename, mime_type):
    """Check if file type is allowed"""
    allowed_extensions = {
        '.pdf', '.doc', '.docx', '.txt', '.md',
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp4', '.mov', '.avi', '.webm',
        '.mp3', '.wav', '.m4a',
        '.zip', '.rar', '.tar', '.gz',
        '.xlsx', '.xls', '.csv',
        '.pptx', '.ppt'
    }
    
    file_ext = os.path.splitext(filename.lower())[1]
    return file_ext in allowed_extensions

def save_uploaded_file(file_data, filename, task_id=None, workspace_id=None):
    """Save uploaded file and return file metadata"""
    global next_file_id
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(filename)[1]
    stored_filename = f"{file_id}{file_ext}"
    
    # Determine storage path
    if task_id:
        file_path = os.path.join('uploads', 'tasks', stored_filename)
        entity_type = 'task'
        entity_id = task_id
    elif workspace_id:
        file_path = os.path.join('uploads', 'workspaces', stored_filename)
        entity_type = 'workspace'
        entity_id = workspace_id
    else:
        file_path = os.path.join('uploads', stored_filename)
        entity_type = 'general'
        entity_id = None
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    # Get file info
    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    # Create file metadata
    file_metadata = {
        'id': next_file_id,
        'file_id': file_id,
        'original_name': filename,
        'stored_name': stored_filename,
        'file_path': file_path,
        'size': file_size,
        'size_formatted': format_file_size(file_size),
        'mime_type': mime_type,
        'icon': get_file_type_icon(mime_type),
        'entity_type': entity_type,
        'entity_id': entity_id,
        'uploaded_at': datetime.now().isoformat()
    }
    
    files_storage.append(file_metadata)
    next_file_id += 1
    
    return file_metadata

def update_parent_task_status(parent_task_id):
    """Auto-update parent task status based on subtasks"""
    if not parent_task_id:
        return
    
    parent_task = next((t for t in tasks_storage if t["id"] == parent_task_id), None)
    if not parent_task:
        return
    
    subtasks = [t for t in tasks_storage if t.get("parent_task_id") == parent_task_id]
    if not subtasks:
        return
    
    # Count subtask statuses
    done_count = len([st for st in subtasks if st["status"] == "done"])
    total_count = len(subtasks)
    
    # Update parent status based on subtask progress
    if done_count == 0:
        new_status = "pending"
    elif done_count == total_count:
        new_status = "done"
        parent_task["completed_at"] = datetime.now().isoformat()
    else:
        new_status = "in-progress"
    
    parent_task["status"] = new_status
    print(f"🔄 Auto-updated parent task {parent_task_id} status to {new_status} ({done_count}/{total_count} subtasks done)")

class CORSHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers to allow all requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')

    def _send_json_response(self, data, status=200):
        """Send JSON response with CORS headers"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]  # Remove query parameters
        
        print(f"🔍 GET request: {path}")
        
        if path == '/health':
            self._send_json_response({
                "status": "healthy", 
                "backend": "operational", 
                "database": "operational"
            })
        
        elif path == '/workspaces':
            self._send_json_response(workspaces_storage)
        
        elif path.startswith('/workspaces/'):
            workspace_id_str = path.split('/')[-1]
            if workspace_id_str and workspace_id_str.isdigit():
                workspace_id = int(workspace_id_str)
                workspace = next((w for w in workspaces_storage if w["id"] == workspace_id), None)
            else:
                self._send_json_response({"error": "Invalid workspace ID"}, 400)
                return
            if workspace:
                self._send_json_response(workspace)
            else:
                self._send_json_response({"error": "Workspace not found"}, 404)
        
        elif path == '/tasks':
            self._send_json_response([
                {"id": 1, "title": "Setup Project", "status": "completed", "priority": "high", "workspace_id": 1},
                {"id": 2, "title": "Create UI Components", "status": "in-progress", "priority": "medium", "workspace_id": 1},
                {"id": 3, "title": "Test Integration", "status": "pending", "priority": "low", "workspace_id": 2}
            ])
        
        elif path == '/tasks/taskmaster/all':
            # Parse query parameters for filtering
            query_params = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
            status_filter = query_params.get('status', [None])[0]
            priority_filter = query_params.get('priority', [None])[0]
            workspace_filter = query_params.get('workspace', [None])[0]
            
            filtered_tasks = tasks_storage.copy()
            
            if status_filter:
                filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]
            if priority_filter:
                filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority_filter]
            if workspace_filter:
                filtered_tasks = [t for t in filtered_tasks if t["workspace_id"] == int(workspace_filter)]
            
            self._send_json_response({
                "tasks": filtered_tasks,
                "total": len(filtered_tasks),
                "source": "taskmaster"
            })
        
        elif path == '/tasks/taskmaster/next':
            # Find next task (first non-done task with highest priority)
            pending_tasks = [t for t in tasks_storage if t["status"] != "done"]
            if pending_tasks:
                priority_order = {"high": 3, "medium": 2, "low": 1}
                next_task = max(pending_tasks, key=lambda t: priority_order.get(t["priority"], 0))
                self._send_json_response({
                    "task": next_task,
                    "message": f"Next recommended task: {next_task['title']}"
                })
            else:
                self._send_json_response({
                    "task": None,
                    "message": "All tasks completed!"
                })
        
        elif path == '/tasks/taskmaster/progress':
            total_tasks = len(tasks_storage)
            completed_tasks = len([t for t in tasks_storage if t["status"] == "done"])
            in_progress_tasks = len([t for t in tasks_storage if t["status"] == "in-progress"])
            pending_tasks = len([t for t in tasks_storage if t["status"] == "pending"])
            completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate overdue tasks
            from datetime import datetime
            now = datetime.now().isoformat()
            overdue_tasks = len([t for t in tasks_storage if t.get("due_date") and t["due_date"] < now and t["status"] != "done"])
            
            self._send_json_response({
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_percentage": round(completion_percentage, 2)
            })
        
        elif path == '/tasks/taskmaster/overdue':
            # Get overdue tasks
            from datetime import datetime
            now = datetime.now().isoformat()
            overdue_tasks = [t for t in tasks_storage if t.get("due_date") and t["due_date"] < now and t["status"] != "done"]
            
            self._send_json_response({
                "tasks": overdue_tasks,
                "total": len(overdue_tasks),
                "source": "taskmaster_overdue"
            })
        
        elif path == '/tasks/taskmaster/upcoming':
            # Get tasks due in the next 7 days
            from datetime import datetime, timedelta
            now = datetime.now()
            week_from_now = (now + timedelta(days=7)).isoformat()
            now_iso = now.isoformat()
            
            upcoming_tasks = [t for t in tasks_storage 
                            if t.get("due_date") and 
                               now_iso <= t["due_date"] <= week_from_now and 
                               t["status"] != "done"]
            
            self._send_json_response({
                "tasks": upcoming_tasks,
                "total": len(upcoming_tasks),
                "source": "taskmaster_upcoming"
            })
        
        elif path == '/tasks/tags/all':
            # Get all unique tags from all tasks
            all_tags = set()
            for task in tasks_storage:
                if task.get("tags"):
                    all_tags.update(task["tags"])
            
            # Convert to list and add predefined popular tags
            predefined_tags = ["bug", "feature", "enhancement", "urgent", "backend", "frontend", "ui", "api", "testing", "documentation"]
            all_tags.update(predefined_tags)
            
            self._send_json_response({
                "tags": sorted(list(all_tags)),
                "total": len(all_tags),
                "source": "all_tags"
            })
        
        elif path.startswith('/tasks/tags/'):
            # Get tasks by tag
            tag = path.split('/')[-1]
            tagged_tasks = [t for t in tasks_storage if t.get("tags") and tag in t["tags"]]
            
            self._send_json_response({
                "tasks": tagged_tasks,
                "tag": tag,
                "total": len(tagged_tasks),
                "source": "tasks_by_tag"
            })
        
        elif path.startswith('/tasks/') and path.endswith('/subtasks'):
            # Get subtasks for a parent task
            parent_task_id = path.split('/')[2]
            subtasks = [t for t in tasks_storage if t.get("parent_task_id") == parent_task_id]
            
            self._send_json_response({
                "subtasks": subtasks,
                "parent_task_id": parent_task_id,
                "total": len(subtasks),
                "source": "subtasks"
            })
        
        elif path == '/tasks/main':
            # Get only main tasks (no subtasks)
            main_tasks = [t for t in tasks_storage if not t.get("parent_task_id")]
            
            self._send_json_response({
                "tasks": main_tasks,
                "total": len(main_tasks),
                "source": "main_tasks"
            })
        
        elif path == '/files':
            # Get all files
            self._send_json_response({
                "files": files_storage,
                "total": len(files_storage),
                "source": "all_files"
            })
        
        elif path.startswith('/files/') and not path.startswith('/files/upload'):
            # File download or metadata
            parts = path.split('/')
            if len(parts) >= 3:
                file_id_or_action = parts[2]
                
                if file_id_or_action.isdigit():
                    # Get file by ID
                    file_id = int(file_id_or_action)
                    file_metadata = next((f for f in files_storage if f["id"] == file_id), None)
                    
                    if not file_metadata:
                        self._send_json_response({"error": "File not found"}, 404)
                        return
                    
                    if len(parts) >= 4 and parts[3] == 'download':
                        # Download file
                        try:
                            file_path = file_metadata['file_path']
                            if not os.path.exists(file_path):
                                self._send_json_response({"error": "File not found on disk"}, 404)
                                return
                            
                            # Send file
                            self.send_response(200)
                            self.send_header('Content-Type', file_metadata['mime_type'])
                            self.send_header('Content-Disposition', f'attachment; filename="{file_metadata["original_name"]}"')
                            self.send_header('Content-Length', str(file_metadata['size']))
                            self._set_cors_headers()
                            self.end_headers()
                            
                            with open(file_path, 'rb') as f:
                                self.wfile.write(f.read())
                            return
                            
                        except Exception as e:
                            print(f"❌ Error downloading file: {e}")
                            self._send_json_response({"error": "Failed to download file"}, 500)
                            return
                    else:
                        # Get file metadata
                        self._send_json_response(file_metadata)
                        return
        
        elif path == '/agents':
            # Get all agents
            self._send_json_response(agents_storage)
        
        elif path == '/agents/system':
            # Get agent system status
            self._send_json_response({
                "agents": agents_storage,
                "activeWorkflows": agent_workflows_storage,
                "tasks": agent_tasks_storage,
                "messages": agent_messages_storage[-50:],  # Last 50 messages
                "status": "ready"
            })
        
        elif path.startswith('/agents/') and path.endswith('/status'):
            # Get specific agent status
            agent_id = path.split('/')[2]
            agent = next((a for a in agents_storage if a["id"] == agent_id), None)
            if agent:
                self._send_json_response(agent)
            else:
                self._send_json_response({"error": "Agent not found"}, 404)
        
        elif path == '/agents/tasks':
            # Get all agent tasks
            self._send_json_response(agent_tasks_storage)
        
        elif path == '/agents/messages':
            # Get agent messages (optionally filtered by agent)
            query_params = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
            agent_id_filter = query_params.get('agentId', [None])[0]
            
            filtered_messages = agent_messages_storage
            if agent_id_filter:
                filtered_messages = [m for m in agent_messages_storage if m["agentId"] == agent_id_filter]
            
            self._send_json_response(filtered_messages[-100:])  # Last 100 messages
        
        elif path.startswith('/agents/anubis/workflows/') and '/report' in path:
            # Generate workflow report
            workflow_id = path.split('/')[4]
            workflow = next((w for w in agent_workflows_storage if w["id"] == workflow_id), None)
            if workflow:
                # Generate a simple HTML report
                html_report = f"""
                <html>
                <head><title>Workflow Report: {workflow['name']}</title></head>
                <body>
                    <h1>🧠 Anubis Workflow Report</h1>
                    <h2>{workflow['name']}</h2>
                    <p><strong>Status:</strong> {workflow['status']}</p>
                    <p><strong>Current Role:</strong> {workflow['currentRole']}</p>
                    <p><strong>Progress:</strong> {len(workflow['completedSteps'])} steps completed</p>
                    <h3>Decisions Made:</h3>
                    <ul>{''.join(f'<li>{decision}</li>' for decision in workflow['context']['decisions'])}</ul>
                    <h3>Next Steps:</h3>
                    <ul>{''.join(f'<li>{step}</li>' for step in workflow['context']['nextSteps'])}</ul>
                </body>
                </html>
                """
                self._send_json_response({"html": html_report})
            else:
                self._send_json_response({"error": "Workflow not found"}, 404)
        
        elif path.startswith('/tasks/') and '/files' in path:
            # Get files for a specific task
            parts = path.split('/')
            if len(parts) >= 4 and parts[3] == 'files':
                task_id = parts[2]
                task = next((t for t in tasks_storage if t["id"] == task_id), None)
                if task:
                    task_files = []
                    if "attachments" in task:
                        task_files = [f for f in files_storage if f["id"] in task["attachments"]]
                    
                    self._send_json_response({
                        "files": task_files,
                        "task_id": task_id,
                        "total": len(task_files),
                        "source": "task_files"
                    })
                else:
                    self._send_json_response({"error": "Task not found"}, 404)
        
        elif path == '/auth/me':
            # Get current user info
            auth_header = self.headers.get('Authorization', '')
            token = None
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            
            user = get_user_from_token(token)
            if user:
                self._send_json_response({
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "last_login": user["last_login"],
                        "created_at": user["created_at"]
                    }
                })
            else:
                self._send_json_response({"error": "Not authenticated"}, 401)
        
        elif path == '/' or path == '':
            self._send_json_response({
                "status": "running",
                "message": "OrdnungsHub Backend is operational",
                "version": "1.0.0"
            })
        
        elif self.path.startswith('/api/ai/suggest-workspaces'):
            self.handle_suggest_workspaces()
        elif self.path == '/api/progress/stats':
            self.handle_get_progress_stats()
        elif self.path == '/api/searchable-data':
            self.handle_get_searchable_data()
        # File serving
        elif self.path.startswith('/uploads/'):
            self.serve_static_file()
        
        else:
            self._send_json_response({
                "error": f"Endpoint {path} not found", 
                "message": "The requested endpoint does not exist",
                "available_endpoints": [
                    "/health", "/workspaces", "/tasks/taskmaster/all", 
                    "/agents", "/files", "/auth/me"
                ]
            }, 404)

    def do_POST(self):
        """Handle POST requests"""
        global next_message_id  # Declare at method level to avoid scope issues
        path = self.path.split('?')[0]
        
        print(f"📝 POST request: {path}")
        
        if path == '/auth/login':
            # User login
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                username = data.get('username', '').strip()
                password = data.get('password', '')
                
                if not username or not password:
                    self._send_json_response({"error": "Username and password required"}, 400)
                    return
                
                user = authenticate_user(username, password)
                if user:
                    # Generate session token
                    token = generate_session_token()
                    sessions_storage[token] = user["id"]
                    
                    print(f"✅ User logged in: {username}")
                    self._send_json_response({
                        "success": True,
                        "message": "Login successful",
                        "token": token,
                        "user": {
                            "id": user["id"],
                            "username": user["username"],
                            "last_login": user["last_login"]
                        }
                    })
                else:
                    print(f"❌ Failed login attempt: {username}")
                    self._send_json_response({"error": "Invalid username or password"}, 401)
            except Exception as e:
                print(f"❌ Login error: {e}")
                self._send_json_response({"error": "Login failed"}, 500)
        
        elif path == '/auth/logout':
            # User logout
            auth_header = self.headers.get('Authorization', '')
            token = None
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            
            if token and token in sessions_storage:
                user_id = sessions_storage[token]
                user = next((u for u in users_storage if u["id"] == user_id), None)
                username = user["username"] if user else "Unknown"
                
                del sessions_storage[token]
                print(f"👋 User logged out: {username}")
                self._send_json_response({"success": True, "message": "Logout successful"})
            else:
                self._send_json_response({"error": "Invalid session"}, 401)
        
        elif path == '/api/logs/frontend-error':
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                error_data = json.loads(post_data.decode('utf-8'))
                print(f"🚨 Frontend Error Logged: {error_data}")
            except:
                print("🚨 Error logging request received (could not parse JSON)")
            
            self._send_json_response({
                "status": "logged", 
                "timestamp": datetime.now().isoformat()
            })
        
        elif path == '/workspaces':
            # Create new workspace
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                global next_workspace_id
                data = json.loads(post_data.decode('utf-8'))
                new_workspace = {
                    "id": next_workspace_id,
                    "name": data.get("name", "New Workspace"),
                    "color": data.get("color", "#6B7280"),
                    "description": data.get("description", ""),
                    "created_at": datetime.now().isoformat()
                }
                workspaces_storage.append(new_workspace)
                next_workspace_id += 1
                
                print(f"✅ Created workspace: {new_workspace['name']}")
                self._send_json_response(new_workspace, 201)
            except Exception as e:
                print(f"❌ Error creating workspace: {e}")
                self._send_json_response({"error": "Failed to create workspace"}, 400)
        
        elif path == '/tasks/taskmaster/suggest-workspace':
            # AI workspace suggestion for task
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                title = data.get("title", "").lower()
                description = data.get("description", "").lower()
                
                # Simple AI workspace matching logic
                suggestions = []
                
                # Check each workspace and calculate confidence
                for workspace in workspaces_storage:
                    confidence = 0.0
                    reason = ""
                    
                    # Match based on keywords
                    workspace_name = workspace["name"].lower()
                    workspace_desc = workspace.get("description", "").lower()
                    
                    # Direct name matching
                    if workspace_name in title or workspace_name in description:
                        confidence += 0.8
                        reason = f"Strong match with workspace name '{workspace['name']}'"
                    elif any(word in title or word in description for word in workspace_name.split()):
                        confidence += 0.4
                        reason = f"Partial match with workspace '{workspace['name']}'"
                    
                    # Description matching
                    if workspace_desc and (workspace_desc in title or workspace_desc in description):
                        confidence += 0.3
                        reason += f" and description similarity"
                    
                    # Category-based matching
                    if "work" in title or "job" in title or "meeting" in title:
                        if "work" in workspace_name:
                            confidence += 0.6
                            reason = "Work-related task detected"
                    
                    if "personal" in title or "home" in title or "family" in title:
                        if "personal" in workspace_name:
                            confidence += 0.6
                            reason = "Personal task detected"
                    
                    if "project" in title or "development" in title or "code" in title:
                        if "project" in workspace_name:
                            confidence += 0.6
                            reason = "Development project detected"
                    
                    # Add suggestion if confidence is meaningful
                    if confidence > 0.2:
                        suggestions.append({
                            "workspace_id": workspace["id"],
                            "workspace_name": workspace["name"],
                            "confidence": min(confidence, 1.0),  # Cap at 1.0
                            "reason": reason or "General compatibility match"
                        })
                
                # Sort by confidence and limit to top 3
                suggestions.sort(key=lambda x: x["confidence"], reverse=True)
                suggestions = suggestions[:3]
                
                # Determine auto-suggestion (highest confidence above threshold)
                auto_suggestion = None
                if suggestions and suggestions[0]["confidence"] > 0.65:
                    auto_suggestion = suggestions[0]
                
                print(f"✅ Generated {len(suggestions)} workspace suggestions for task: {title}")
                self._send_json_response({
                    "success": True,
                    "suggestions": suggestions,
                    "auto_suggestion": auto_suggestion,
                    "task_title": title
                })
            except Exception as e:
                print(f"❌ Error generating workspace suggestions: {e}")
                self._send_json_response({"error": "Failed to generate suggestions"}, 400)

        elif path == '/tasks/taskmaster':
            # Create new task
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                global next_task_id
                data = json.loads(post_data.decode('utf-8'))
                parent_task_id = data.get("parent_task_id")
                if parent_task_id:
                    # Creating a subtask
                    parent_task = next((t for t in tasks_storage if t["id"] == parent_task_id), None)
                    if parent_task:
                        subtask_count = len([t for t in tasks_storage if t.get("parent_task_id") == parent_task_id])
                        task_id = f"{parent_task_id}-{subtask_count + 1}"
                    else:
                        task_id = f"T{next_task_id:03d}"
                        next_task_id += 1
                else:
                    # Creating a main task
                    task_id = f"T{next_task_id:03d}"
                    next_task_id += 1

                new_task = {
                    "id": task_id,
                    "title": data.get("title", "New Task"),
                    "description": data.get("description", ""),
                    "status": data.get("status", "pending"),
                    "priority": data.get("priority", "medium"),
                    "dependencies": data.get("dependencies", []),
                    "workspace_id": data.get("workspace_id", 1),
                    "due_date": data.get("due_date"),
                    "tags": data.get("tags", []),
                    "parent_task_id": parent_task_id,
                    "subtasks": [],
                    "attachments": [],
                    "created_at": datetime.now().isoformat()
                }
                
                # Add to parent's subtasks list if it's a subtask
                if parent_task_id:
                    parent_task = next((t for t in tasks_storage if t["id"] == parent_task_id), None)
                    if parent_task and task_id not in parent_task.get("subtasks", []):
                        parent_task["subtasks"].append(task_id)
                tasks_storage.append(new_task)
                
                print(f"✅ Created task: {new_task['title']}")
                self._send_json_response(new_task, 201)
            except Exception as e:
                print(f"❌ Error creating task: {e}")
                self._send_json_response({"error": "Failed to create task"}, 400)
        
        elif path.startswith('/files/upload'):
            # File upload endpoint
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_json_response({"error": "No file data"}, 400)
                return
            
            try:
                # Parse multipart form data manually (simplified)
                boundary = None
                content_type = self.headers.get('Content-Type', '')
                if 'boundary=' in content_type:
                    boundary = content_type.split('boundary=')[1].encode()
                
                if not boundary:
                    # Handle JSON upload (base64 encoded)
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    file_data = base64.b64decode(data['file_data'])
                    filename = data['filename']
                    task_id = data.get('task_id')
                    workspace_id = data.get('workspace_id')
                    
                    # Validate file
                    if not is_allowed_file_type(filename, ''):
                        self._send_json_response({"error": "File type not allowed"}, 400)
                        return
                    
                    if len(file_data) > 50 * 1024 * 1024:  # 50MB limit
                        self._send_json_response({"error": "File too large (max 50MB)"}, 400)
                        return
                    
                    # Save file
                    file_metadata = save_uploaded_file(file_data, filename, task_id, workspace_id)
                    
                    # Update task with attachment
                    if task_id:
                        task = next((t for t in tasks_storage if t["id"] == task_id), None)
                        if task:
                            if "attachments" not in task:
                                task["attachments"] = []
                            task["attachments"].append(file_metadata["id"])
                    
                    print(f"✅ File uploaded: {filename} ({file_metadata['size_formatted']})")
                    self._send_json_response({
                        "file": file_metadata,
                        "message": "File uploaded successfully"
                    }, 201)
                else:
                    self._send_json_response({"error": "Multipart upload not implemented yet"}, 400)
                    
            except Exception as e:
                print(f"❌ Error uploading file: {e}")
                self._send_json_response({"error": "Failed to upload file"}, 400)
        
        # --- SUBTASK ENDPOINTS ---
        elif self.path.endswith('/subtasks') and self.command == 'POST':
            task_id = self.path.split('/')[-2]
            self.handle_create_subtask(task_id)
        # --- END SUBTASK ENDPOINTS ---
        
        # --- AGENT SYSTEM ENDPOINTS ---
        elif path == '/agents/tasks':
            # Create new agent task
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                global next_agent_task_id
                data = json.loads(post_data.decode('utf-8'))
                
                new_task = {
                    "id": str(next_agent_task_id),
                    "title": data.get("title", "New Agent Task"),
                    "description": data.get("description", ""),
                    "assignedAgent": data.get("assignedAgent", ""),
                    "status": data.get("status", "pending"),
                    "priority": data.get("priority", "medium"),
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                    "result": None
                }
                
                agent_tasks_storage.append(new_task)
                next_agent_task_id += 1
                
                # Log agent message
                agent_messages_storage.append({
                    "id": str(next_message_id),
                    "agentId": "system",
                    "content": f"New task created: {new_task['title']}",
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                })
                next_message_id += 1
                
                print(f"✅ Created agent task: {new_task['title']}")
                self._send_json_response(new_task, 201)
            except Exception as e:
                print(f"❌ Error creating agent task: {e}")
                self._send_json_response({"error": "Failed to create agent task"}, 400)
        
        elif path == '/agents/anubis/init':
            # Initialize Anubis workflow
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                global next_workflow_id
                data = json.loads(post_data.decode('utf-8'))
                
                new_workflow = {
                    "id": str(next_workflow_id),
                    "name": data.get("projectName", "New Project"),
                    "currentRole": "boomerang",
                    "completedSteps": [],
                    "context": {
                        "decisions": [],
                        "rationale": "Project initialization",
                        "nextSteps": ["Analyze requirements", "Create system architecture"]
                    },
                    "status": "active",
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat()
                }
                
                agent_workflows_storage.append(new_workflow)
                next_workflow_id += 1
                
                # Log agent message
                agent_messages_storage.append({
                    "id": str(next_message_id),
                    "agentId": "anubis-workflow",
                    "content": f"Initialized workflow for project: {new_workflow['name']}",
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                })
                next_message_id += 1
                
                print(f"✅ Initialized Anubis workflow: {new_workflow['name']}")
                self._send_json_response(new_workflow, 201)
            except Exception as e:
                print(f"❌ Error initializing workflow: {e}")
                self._send_json_response({"error": "Failed to initialize workflow"}, 400)
        
        elif path == '/agents/broadcast':
            # Broadcast message to agents
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get("message", "")
                target_agents = data.get("targetAgents", [])
                
                # If no target agents specified, broadcast to all
                if not target_agents:
                    target_agents = [agent["id"] for agent in agents_storage]
                
                for agent_id in target_agents:
                    agent_messages_storage.append({
                        "id": str(next_message_id),
                        "agentId": agent_id,
                        "content": f"Broadcast: {message}",
                        "type": "text",
                        "timestamp": datetime.now().isoformat()
                    })
                    next_message_id += 1
                
                print(f"✅ Broadcast message to {len(target_agents)} agents")
                self._send_json_response({"message": "Broadcast sent successfully"})
            except Exception as e:
                print(f"❌ Error broadcasting message: {e}")
                self._send_json_response({"error": "Failed to broadcast message"}, 400)
        
        elif path.startswith('/agents/a2a/') and path.endswith('/message'):
            # Send message to A2A agent
            agent_id = path.split('/')[3]
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get("message", "")
                
                # Simulate A2A agent response
                response_message = {
                    "id": str(next_message_id),
                    "agentId": agent_id,
                    "content": f"Received: {message}. Processing via A2A protocol...",
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                }
                
                agent_messages_storage.append(response_message)
                next_message_id += 1
                
                print(f"✅ Sent message to A2A agent: {agent_id}")
                self._send_json_response(response_message, 201)
            except Exception as e:
                print(f"❌ Error sending A2A message: {e}")
                self._send_json_response({"error": "Failed to send A2A message"}, 400)
        
        elif path == '/ai/suggest-workspaces':
            # AI workspace suggestions for new workspace creation
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                task_title = data.get("task_title", "").lower()
                task_description = data.get("task_description", "").lower()
                existing_workspaces = data.get("existing_workspaces", [])
                
                # Generate AI suggestions for new workspaces
                suggestions = []
                
                # Predefined workspace templates based on task content
                templates = [
                    {
                        "name": "Development Projects",
                        "description": "Software development and coding projects",
                        "icon": "💻",
                        "color": "#3b82f6",
                        "theme": "modern_dark",
                        "keywords": ["code", "development", "programming", "software", "app", "web", "api", "system"],
                        "confidence_boost": 0.9
                    },
                    {
                        "name": "Personal Tasks",
                        "description": "Personal errands and daily activities",
                        "icon": "🏠",
                        "color": "#10b981",
                        "theme": "modern_light",
                        "keywords": ["personal", "home", "family", "life", "daily", "routine"],
                        "confidence_boost": 0.8
                    },
                    {
                        "name": "Work & Business",
                        "description": "Professional work and business tasks",
                        "icon": "💼",
                        "color": "#f59e0b",
                        "theme": "professional",
                        "keywords": ["work", "business", "meeting", "professional", "office", "job", "career"],
                        "confidence_boost": 0.8
                    },
                    {
                        "name": "Learning & Research",
                        "description": "Educational content and research projects",
                        "icon": "📚",
                        "color": "#8b5cf6",
                        "theme": "academic",
                        "keywords": ["learn", "study", "research", "education", "course", "tutorial", "knowledge"],
                        "confidence_boost": 0.7
                    },
                    {
                        "name": "Creative Projects",
                        "description": "Art, design, and creative endeavors",
                        "icon": "🎨",
                        "color": "#ef4444",
                        "theme": "creative",
                        "keywords": ["design", "art", "creative", "draw", "paint", "music", "video", "photo"],
                        "confidence_boost": 0.7
                    }
                ]
                
                # Calculate suggestions based on task content
                for template in templates:
                    confidence = 0.0
                    matched_keywords = []
                    
                    # Check keyword matches
                    for keyword in template["keywords"]:
                        if keyword in task_title or keyword in task_description:
                            confidence += template["confidence_boost"] / len(template["keywords"])
                            matched_keywords.append(keyword)
                    
                    # Boost confidence if multiple keywords match
                    if len(matched_keywords) > 1:
                        confidence *= 1.3
                    
                    # Check if similar workspace already exists
                    workspace_exists = any(
                        template["name"].lower() in ws.get("name", "").lower() or
                        any(kw in ws.get("name", "").lower() for kw in template["keywords"][:2])
                        for ws in existing_workspaces
                    )
                    
                    if workspace_exists:
                        confidence *= 0.3  # Reduce confidence if similar workspace exists
                    
                    # Add suggestion if confidence is meaningful
                    if confidence > 0.3:
                        suggestion = template.copy()
                        suggestion["confidence"] = min(confidence, 1.0)
                        suggestion["suggested_categories"] = matched_keywords[:3]
                        suggestions.append(suggestion)
                
                # Sort by confidence
                suggestions.sort(key=lambda x: x["confidence"], reverse=True)
                suggestions = suggestions[:3]  # Limit to top 3
                
                print(f"✅ Generated {len(suggestions)} AI workspace suggestions")
                self._send_json_response({
                    "success": True,
                    "suggestions": suggestions,
                    "task_context": {
                        "title": task_title,
                        "description": task_description
                    }
                })
            except Exception as e:
                print(f"❌ Error generating AI workspace suggestions: {e}")
                self._send_json_response({"error": "Failed to generate AI suggestions"}, 400)

        elif path == '/agents/serena/activate':
            # Activate Serena project
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                project_path = data.get("projectPath", "")
                
                # Simulate Serena project activation
                agent_messages_storage.append({
                    "id": str(next_message_id),
                    "agentId": "serena-coder",
                    "content": f"Activated project: {project_path}. Language servers initialized.",
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                })
                next_message_id += 1
                
                print(f"✅ Activated Serena project: {project_path}")
                self._send_json_response({"message": "Project activated successfully"})
            except Exception as e:
                print(f"❌ Error activating Serena project: {e}")
                self._send_json_response({"error": "Failed to activate project"}, 400)
        # --- END AGENT SYSTEM ENDPOINTS ---
        
        else:
            self._send_json_response({"error": "Endpoint not found"}, 404)

    def do_PUT(self):
        """Handle PUT requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        print(f"📝 PUT request: {path}")

        if path.startswith('/api/tasks/taskmaster/'):
            task_id = path.split('/')[-1]
            self.handle_update_task(task_id)
        elif path.startswith('/api/workspaces/'):
            workspace_id = int(path.split('/')[-1])
            self.handle_update_workspace(workspace_id)
        # --- SUBTASK ENDPOINTS ---
        elif path.startswith('/api/subtasks/'):
            subtask_id = path.split('/')[-1]
            self.handle_update_subtask(subtask_id)
        # --- END SUBTASK ENDPOINTS ---
        else:
            self._send_json_response({"error": "Endpoint not found"}, 404)

    def do_DELETE(self):
        """Handle DELETE requests"""
        path = self.path.split('?')[0]
        
        print(f"🗑️ DELETE request: {path}")
        
        if path.startswith('/workspaces/'):
            workspace_id = int(path.split('/')[-1])
            workspace = next((w for w in workspaces_storage if w["id"] == workspace_id), None)
            if workspace:
                workspaces_storage.remove(workspace)
                print(f"✅ Deleted workspace: {workspace['name']}")
                self._send_json_response({"message": "Workspace deleted successfully"})
            else:
                self._send_json_response({"error": "Workspace not found"}, 404)
        
        elif path.startswith('/tasks/taskmaster/'):
            task_id = path.split('/')[-1]
            task = next((t for t in tasks_storage if t["id"] == task_id), None)
            if task:
                tasks_storage.remove(task)
                print(f"✅ Deleted task: {task['title']}")
                self._send_json_response({"message": "Task deleted successfully"})
            else:
                self._send_json_response({"error": "Task not found"}, 404)
        
        elif path == '/tasks/bulk':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                task_ids = data.get('task_ids', [])
                
                deleted_count = 0
                for task_id in task_ids:
                    task = next((t for t in tasks_storage if t["id"] == task_id), None)
                    if task:
                        tasks_storage.remove(task)
                        deleted_count += 1
                        print(f"✅ Bulk deleted task: {task['title']}")
                
                self._send_json_response({
                    "message": f"Deleted {deleted_count} tasks successfully",
                    "deleted_count": deleted_count
                })
            else:
                self._send_json_response({"error": "No task IDs provided"}, 400)
        
        else:
            self._send_json_response({
                "error": f"DELETE endpoint {path} not found",
                "message": "The requested DELETE endpoint does not exist"
            }, 404)

    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

    def handle_create_task(self):
        """Handle creating a new task"""
        global next_task_id
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # Generate a unique ID for the task
        task_id = f"T{next_task_id:03d}"
        next_task_id += 1

        new_task = {
            "id": task_id,
            "title": data.get("title", "New Task"),
            "description": data.get("description", ""),
            "status": data.get("status", "pending"),
            "priority": data.get("priority", "medium"),
            "dependencies": data.get("dependencies", []),
            "workspace_id": data.get("workspace_id", 1),
            "due_date": data.get("due_date"),
            "tags": data.get("tags", []),
            "parent_task_id": None,
            "subtasks": [],
            "attachments": [],
            "created_at": datetime.now().isoformat()
        }
        
        tasks_storage.append(new_task)
        self._send_json_response(new_task, 201)

    def handle_create_subtask(self, parent_task_id):
        """Handles creating a new subtask for a parent task"""
        parent_task = next((t for t in tasks_storage if t["id"] == parent_task_id), None)
        if not parent_task:
            self._send_json_response({"error": "Parent task not found"}, 404)
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # Generate a unique ID for the subtask
        subtask_num = len([t for t in tasks_storage if t.get("parent_task_id") == parent_task_id]) + 1
        new_subtask_id = f"{parent_task_id}-{subtask_num}"

        new_subtask = {
            "id": new_subtask_id,
            "title": data.get("title", "New Subtask"),
            "description": data.get("description", ""),
            "status": "pending",
            "priority": data.get("priority", "medium"),
            "parent_task_id": parent_task_id,
            "workspace_id": parent_task.get("workspace_id"),
            "created_at": datetime.now().isoformat(),
            "dependencies": [],
            "subtasks": [],
            "tags": ["subtask"],
            "attachments": []
        }
        
        tasks_storage.append(new_subtask)

        # Add subtask ID to parent
        if "subtasks" not in parent_task:
            parent_task["subtasks"] = []
        parent_task["subtasks"].append(new_subtask_id)
        
        # Update parent task status automatically
        update_parent_task_status(parent_task_id)

        print(f"✅ Created subtask: {new_subtask['title']} for task {parent_task_id}")
        self._send_json_response(new_subtask, 201)

    def handle_update_task(self, task_id):
        """Handle updating an existing task"""
        task = next((t for t in tasks_storage if t["id"] == task_id), None)
        if not task:
            self._send_json_response({"error": "Task not found"}, 404)
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # Prevent changing parentage
        if 'parent_task_id' in data and data['parent_task_id'] != task.get('parent_task_id'):
            self._send_json_response({"error": "Cannot change the parent of a task"}, 400)
            return
            
        task.update(data)
        print(f"✅ Updated task: {task['title']}")
        self._send_json_response(task)

    def handle_update_subtask(self, subtask_id):
        """Handles updating an existing subtask"""
        subtask = next((t for t in tasks_storage if t["id"] == subtask_id), None)
        if not subtask:
            self._send_json_response({"error": "Subtask not found"}, 404)
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # Prevent changing parentage
        if 'parent_task_id' in data and data['parent_task_id'] != subtask.get('parent_task_id'):
            self._send_json_response({"error": "Cannot change the parent of a subtask"}, 400)
            return
            
        subtask.update(data)
        
        # If status is updated, check parent task
        if 'status' in data and subtask.get("parent_task_id"):
            update_parent_task_status(subtask["parent_task_id"])

        print(f"✅ Updated subtask: {subtask['title']}")
        self._send_json_response(subtask)

    def handle_delete_task(self, task_id):
        """Handle deleting a task"""
        task = next((t for t in tasks_storage if t["id"] == task_id), None)
        if not task:
            self._send_json_response({"error": "Task not found"}, 404)
            return

        tasks_storage.remove(task)
        print(f"✅ Deleted task: {task['title']}")
        self._send_json_response({"message": "Task deleted successfully"})

    def handle_get_progress_stats(self):
        """
        Handles GET requests for progress statistics.
        Returns mock data for charting.
        """
        # In a real app, this would query and calculate from the database
        mock_stats = {
            "task_completion_over_time": [
                {"date": "2024-06-01", "completed": 5},
                {"date": "2024-06-02", "completed": 7},
                {"date": "2024-06-03", "completed": 3},
                {"date": "2024-06-04", "completed": 8},
                {"date": "2024-06-05", "completed": 6},
                {"date": "2024-06-06", "completed": 10},
                {"date": "2024-06-07", "completed": 12}
            ],
            "tasks_by_workspace": [
                {"workspace_id": 1, "name": "Personal", "task_count": 25},
                {"workspace_id": 2, "name": "Work", "task_count": 40},
                {"workspace_id": 3, "name": "Projects", "task_count": 15}
            ],
            "tasks_by_priority": {
                "high": 30,
                "medium": 40,
                "low": 10
            },
            "overall_progress": {
                "completed": 150,
                "in-progress": 45,
                "pending": 20
            }
        }
        self._send_json_response(mock_stats)

    def handle_get_searchable_data(self):
        """
        Handles GET requests for all data that can be searched.
        Combines tasks, workspaces, and files into a single list.
        """
        searchable_data = []

        # Add tasks
        for task in tasks_storage:
            searchable_data.append({
                "id": f"task-{task['id']}",
                "title": task.get('title', 'Untitled Task'),
                "type": "task",
                "description": task.get('description', ''),
                "tags": task.get('tags', []),
                "status": task.get('status', 'pending')
            })

        # Add workspaces
        for workspace in workspaces_storage:
            searchable_data.append({
                "id": f"workspace-{workspace['id']}",
                "title": workspace.get('name', 'Untitled Workspace'),
                "type": "workspace",
                "description": workspace.get('description', '')
            })

        # Add files
        for file_item in files_storage:
            searchable_data.append({
                "id": f"file-{file_item['id']}",
                "title": file_item.get('filename', 'Untitled File'),
                "type": "file",
                "mime_type": file_item.get('mime_type', ''),
                "size": file_item.get('size', 0)
            })
            
        self._send_json_response(searchable_data)

if __name__ == "__main__":
    print("Starting ULTRA SIMPLE OrdnungsHub Backend...")
    print("Backend running at: http://localhost:8002")
    print("CORS enabled for all origins")
    print("No dependencies required!")
    print("")
    
    server = HTTPServer(('localhost', 8002), CORSHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")
        server.server_close()