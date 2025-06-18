#!/usr/bin/env python3
"""
Simple FastAPI backend for OrdnungsHub - NO DOCKER COMPLICATIONS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OrdnungsHub API", version="1.0.0")

# Configure CORS - ALLOW EVERYTHING FOR LOCAL DEV
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "backend": "operational", "database": "operational"}

# Workspaces endpoints
@app.get("/workspaces")
async def get_workspaces():
    return [
        {"id": 1, "name": "Personal", "color": "#3B82F6", "created_at": datetime.now().isoformat()},
        {"id": 2, "name": "Work", "color": "#10B981", "created_at": datetime.now().isoformat()},
        {"id": 3, "name": "Projects", "color": "#F59E0B", "created_at": datetime.now().isoformat()}
    ]

@app.post("/workspaces")
async def create_workspace(workspace_data: dict):
    new_workspace = {
        "id": 4,
        "name": workspace_data.get("name", "New Workspace"),
        "color": workspace_data.get("color", "#6B7280"),
        "created_at": datetime.now().isoformat()
    }
    return new_workspace

# Tasks endpoints
@app.get("/tasks")
async def get_tasks():
    return [
        {"id": 1, "title": "Setup Project", "status": "completed", "priority": "high", "workspace_id": 1},
        {"id": 2, "title": "Create UI Components", "status": "in-progress", "priority": "medium", "workspace_id": 1},
        {"id": 3, "title": "Test Integration", "status": "pending", "priority": "low", "workspace_id": 2}
    ]

# Taskmaster endpoints
@app.get("/tasks/taskmaster/all")
async def get_taskmaster_tasks():
    return {
        "tasks": [
            {
                "id": "T001",
                "title": "Setup Core Application Framework", 
                "description": "Create the foundational structure for OrdnungsHub",
                "status": "done",
                "priority": "high",
                "dependencies": [],
                "completed_at": "2024-06-08T10:00:00Z",
                "workspace_id": 1
            },
            {
                "id": "T002",
                "title": "Implement Frontend Components",
                "description": "Build React components for the user interface",
                "status": "in-progress", 
                "priority": "high",
                "dependencies": ["T001"],
                "workspace_id": 1
            },
            {
                "id": "T003",
                "title": "Add Error Handling",
                "description": "Implement comprehensive error handling and logging",
                "status": "pending",
                "priority": "medium", 
                "dependencies": ["T002"],
                "workspace_id": 1
            }
        ],
        "total": 3,
        "source": "taskmaster"
    }

@app.get("/tasks/taskmaster/next")
async def get_next_task():
    return {
        "task": {
            "id": "T002",
            "title": "Implement Frontend Components",
            "description": "Build React components for the user interface", 
            "status": "in-progress",
            "priority": "high",
            "dependencies": ["T001"],
            "workspace_id": 1
        },
        "message": "Next recommended task: Implement Frontend Components"
    }

@app.get("/tasks/taskmaster/progress")
async def get_progress():
    return {
        "total_tasks": 3,
        "completed_tasks": 1,
        "in_progress_tasks": 1,
        "pending_tasks": 1,
        "completion_percentage": 33.33
    }

# Files endpoints
@app.get("/files")
async def get_files():
    return [
        {"id": 1, "name": "document.pdf", "size": "1.2MB", "type": "pdf"},
        {"id": 2, "name": "image.jpg", "size": "500KB", "type": "image"},
        {"id": 3, "name": "data.csv", "size": "200KB", "type": "csv"}
    ]

# Error logging endpoint
@app.post("/api/logs/frontend-error")
async def log_frontend_error(error_data: dict):
    logger.error(f"Frontend Error: {error_data}")
    return {"status": "logged", "timestamp": datetime.now().isoformat()}

# Catch-all for unimplemented endpoints
@app.get("/{path:path}")
async def catch_all(path: str):
    logger.info(f"Unimplemented endpoint accessed: /{path}")
    return {"message": f"Endpoint /{path} not yet implemented", "status": "ok"}

if __name__ == "__main__":
    print("🚀 Starting OrdnungsHub Simple Backend...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📊 API docs available at: http://localhost:8000/docs")
    print("✅ CORS enabled for all origins")
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )