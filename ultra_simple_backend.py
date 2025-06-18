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
            workspace_id = int(path.split('/')[-1])
            workspace = next((w for w in workspaces_storage if w["id"] == workspace_id), None)
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
        
        elif path == '/' or path == '':
            self._send_json_response({
                "status": "running",
                "message": "OrdnungsHub Backend is operational",
                "version": "1.0.0"
            })
        
        else:
            self._send_json_response({
                "message": f"Endpoint {path} not yet implemented", 
                "status": "ok"
            })

    def do_POST(self):
        """Handle POST requests"""
        path = self.path.split('?')[0]
        
        print(f"📝 POST request: {path}")
        
        if path == '/api/logs/frontend-error':
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
        
        else:
            self._send_json_response({
                "message": f"POST endpoint {path} not yet implemented",
                "status": "ok"
            })

    def do_PUT(self):
        """Handle PUT requests"""
        path = self.path.split('?')[0]
        
        print(f"📝 PUT request: {path}")
        
        if path.startswith('/workspaces/'):
            workspace_id = int(path.split('/')[-1])
            content_length = int(self.headers.get('Content-Length', 0))
            put_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(put_data.decode('utf-8'))
                workspace = next((w for w in workspaces_storage if w["id"] == workspace_id), None)
                if workspace:
                    workspace.update({
                        "name": data.get("name", workspace["name"]),
                        "color": data.get("color", workspace["color"]),
                        "description": data.get("description", workspace.get("description", ""))
                    })
                    print(f"✅ Updated workspace: {workspace['name']}")
                    self._send_json_response(workspace)
                else:
                    self._send_json_response({"error": "Workspace not found"}, 404)
            except Exception as e:
                print(f"❌ Error updating workspace: {e}")
                self._send_json_response({"error": "Failed to update workspace"}, 400)
        
        elif path.startswith('/tasks/taskmaster/'):
            task_id = path.split('/')[-1]
            content_length = int(self.headers.get('Content-Length', 0))
            put_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(put_data.decode('utf-8'))
                task = next((t for t in tasks_storage if t["id"] == task_id), None)
                if task:
                    task.update({
                        "title": data.get("title", task["title"]),
                        "description": data.get("description", task["description"]),
                        "status": data.get("status", task["status"]),
                        "priority": data.get("priority", task["priority"]),
                        "workspace_id": data.get("workspace_id", task["workspace_id"]),
                        "tags": data.get("tags", task.get("tags", []))
                    })
                    if data.get("status") == "done" and task.get("status") != "done":
                        task["completed_at"] = datetime.now().isoformat()
                    
                    # Auto-update parent task status if this is a subtask
                    if task.get("parent_task_id"):
                        update_parent_task_status(task["parent_task_id"])
                    
                    print(f"✅ Updated task: {task['title']}")
                    self._send_json_response(task)
                else:
                    self._send_json_response({"error": "Task not found"}, 404)
            except Exception as e:
                print(f"❌ Error updating task: {e}")
                self._send_json_response({"error": "Failed to update task"}, 400)
        
        elif path == '/tasks/bulk':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                task_ids = data.get('task_ids', [])
                updates = data.get('updates', {})
                
                updated_count = 0
                for task_id in task_ids:
                    task = next((t for t in tasks_storage if t["id"] == task_id), None)
                    if task:
                        # Apply updates
                        if 'status' in updates:
                            task['status'] = updates['status']
                            if updates['status'] == 'done' and task.get('status') != 'done':
                                task['completed_at'] = datetime.now().isoformat()
                        
                        if 'priority' in updates:
                            task['priority'] = updates['priority']
                        
                        if 'tags' in updates:
                            if updates.get('tag_operation') == 'add':
                                current_tags = task.get('tags', [])
                                new_tags = list(set(current_tags + updates['tags']))
                                task['tags'] = new_tags
                            elif updates.get('tag_operation') == 'remove':
                                current_tags = task.get('tags', [])
                                task['tags'] = [tag for tag in current_tags if tag not in updates['tags']]
                            else:
                                task['tags'] = updates['tags']
                        
                        updated_count += 1
                        print(f"✅ Bulk updated task: {task['title']}")
                
                self._send_json_response({
                    "message": f"Updated {updated_count} tasks successfully",
                    "updated_count": updated_count
                })
            else:
                self._send_json_response({"error": "No task data provided"}, 400)
        
        else:
            self._send_json_response({
                "message": f"PUT endpoint {path} not yet implemented",
                "status": "ok"
            })

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
                "message": f"DELETE endpoint {path} not yet implemented",
                "status": "ok"
            })

    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

if __name__ == "__main__":
    print("🚀 Starting ULTRA SIMPLE OrdnungsHub Backend...")
    print("📍 Backend running at: http://localhost:8000")
    print("✅ CORS enabled for all origins")
    print("🔧 No dependencies required!")
    print("")
    
    server = HTTPServer(('localhost', 8000), CORSHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")
        server.server_close()