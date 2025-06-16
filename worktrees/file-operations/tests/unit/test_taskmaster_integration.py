"""
Test cases for Taskmaster AI Integration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.backend.main import app
from src.backend.database.database import Base, get_db
from src.backend.models.task import Task, TaskStatus, TaskPriority
from src.backend.models.user import User
from src.backend.services.taskmaster_integration import TaskmasterService

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_taskmaster_integration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestTaskmasterIntegration:
    """Test Taskmaster AI Integration functionality"""
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService._run_taskmaster_command')
    def test_taskmaster_service_initialization(self, mock_command):
        """Test TaskmasterService initialization"""
        service = TaskmasterService()
        assert service.project_root is not None
        assert service.taskmaster_dir.name == ".taskmaster"
        assert service.tasks_file.name == "tasks.json"
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_all_tasks')
    @pytest.mark.asyncio
    async def test_get_taskmaster_tasks_endpoint(self, mock_get_tasks):
        """Test getting tasks from Taskmaster system"""
        # Mock Taskmaster tasks
        mock_tasks = [
            {
                "id": "1",
                "title": "Setup Core Application Framework",
                "description": "Create the foundational structure",
                "status": "done",
                "priority": "high",
                "dependencies": []
            },
            {
                "id": "2", 
                "title": "Implement Database Layer",
                "description": "Setup SQLite with SQLAlchemy",
                "status": "done",
                "priority": "high",
                "dependencies": ["1"]
            }
        ]
        mock_get_tasks.return_value = mock_tasks
        
        response = client.get("/tasks/taskmaster/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert data["total"] == 2
        assert data["source"] == "taskmaster"
        assert len(data["tasks"]) == 2
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_next_task')
    @pytest.mark.asyncio
    async def test_get_next_task_endpoint(self, mock_get_next):
        """Test getting next recommended task"""
        mock_next_task = {
            "id": "4",
            "title": "Integrate Local AI Engine",
            "description": "Implement privacy-focused AI",
            "status": "pending",
            "priority": "high",
            "dependencies": ["3"]
        }
        mock_get_next.return_value = mock_next_task
        
        response = client.get("/tasks/taskmaster/next")
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert "message" in data
        assert data["task"]["id"] == "4"
        assert "Next recommended task" in data["message"]
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_next_task')
    @pytest.mark.asyncio
    async def test_get_next_task_no_available(self, mock_get_next):
        """Test getting next task when none available"""
        mock_get_next.return_value = None
        
        response = client.get("/tasks/taskmaster/next")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task"] is None
        assert "No available tasks found" in data["message"]
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_project_progress')
    @pytest.mark.asyncio
    async def test_get_project_progress_endpoint(self, mock_get_progress):
        """Test getting project progress"""
        mock_progress = {
            "total_tasks": 10,
            "completed_tasks": 3,
            "pending_tasks": 5,
            "in_progress_tasks": 2,
            "completion_percentage": 30.0
        }
        mock_get_progress.return_value = mock_progress
        
        response = client.get("/tasks/taskmaster/progress")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_tasks"] == 10
        assert data["completed_tasks"] == 3
        assert data["completion_percentage"] == 30.0
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_task_dependencies_graph')
    @pytest.mark.asyncio
    async def test_get_task_dependencies_endpoint(self, mock_get_deps):
        """Test getting task dependency graph"""
        mock_graph = {
            "nodes": [
                {"id": "1", "title": "Task 1", "status": "done", "priority": "high"},
                {"id": "2", "title": "Task 2", "status": "pending", "priority": "medium"}
            ],
            "edges": [
                {"from": "1", "to": "2"}
            ]
        }
        mock_get_deps.return_value = mock_graph
        
        response = client.get("/tasks/taskmaster/dependencies")
        assert response.status_code == 200
        
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_task_by_id')
    @pytest.mark.asyncio
    async def test_get_specific_taskmaster_task(self, mock_get_task):
        """Test getting specific task by ID"""
        mock_task = {
            "id": "1",
            "title": "Setup Core Application Framework",
            "description": "Create the foundational structure",
            "status": "done",
            "priority": "high",
            "details": "Detailed implementation notes...",
            "testStrategy": "Testing approach..."
        }
        mock_get_task.return_value = mock_task
        
        response = client.get("/tasks/taskmaster/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "1"
        assert data["title"] == "Setup Core Application Framework"
        assert "details" in data
        assert "testStrategy" in data
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.get_task_by_id')
    @pytest.mark.asyncio
    async def test_get_nonexistent_taskmaster_task(self, mock_get_task):
        """Test getting nonexistent task"""
        mock_get_task.return_value = None
        
        response = client.get("/tasks/taskmaster/999")
        assert response.status_code == 404
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.add_task')
    @pytest.mark.asyncio
    async def test_add_taskmaster_task(self, mock_add_task):
        """Test adding new task via Taskmaster AI"""
        mock_new_task = {
            "id": "11",
            "title": "New AI Feature",
            "description": "Implement new AI functionality",
            "status": "pending",
            "priority": "medium"
        }
        mock_add_task.return_value = mock_new_task
        
        task_data = {
            "title": "New AI Feature",
            "description": "Implement new AI functionality",
            "priority": "medium"
        }
        
        response = client.post("/tasks/taskmaster/add", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert "message" in data
        assert data["task"]["title"] == "New AI Feature"
        assert "created successfully" in data["message"]
    
    def test_add_taskmaster_task_missing_title(self):
        """Test adding task without title"""
        task_data = {
            "description": "Description without title"
        }
        
        response = client.post("/tasks/taskmaster/add", json=task_data)
        assert response.status_code == 400
        assert "Task title is required" in response.json()["detail"]
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.update_task_status')
    @pytest.mark.asyncio
    async def test_update_taskmaster_task_status(self, mock_update_status):
        """Test updating task status"""
        mock_update_status.return_value = True
        
        status_data = {"status": "in-progress"}
        
        response = client.put("/tasks/taskmaster/1/status", json=status_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "1"
        assert data["status"] == "in-progress"
        assert "status updated" in data["message"]
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.update_task_status')
    @pytest.mark.asyncio
    async def test_update_taskmaster_task_status_failure(self, mock_update_status):
        """Test updating task status failure"""
        mock_update_status.return_value = False
        
        status_data = {"status": "done"}
        
        response = client.put("/tasks/taskmaster/1/status", json=status_data)
        assert response.status_code == 500
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.expand_task')
    @pytest.mark.asyncio
    async def test_expand_taskmaster_task(self, mock_expand_task):
        """Test expanding task into subtasks"""
        mock_expanded_task = {
            "id": "4",
            "title": "Complex Task",
            "subtasks": [
                {"id": "4.1", "title": "Subtask 1"},
                {"id": "4.2", "title": "Subtask 2"}
            ]
        }
        mock_expand_task.return_value = mock_expanded_task
        
        expand_data = {"num_subtasks": 2}
        
        response = client.post("/tasks/taskmaster/4/expand", json=expand_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert "expanded into subtasks" in data["message"]
        assert len(data["task"]["subtasks"]) == 2
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.update_task_with_context')
    @pytest.mark.asyncio
    async def test_update_task_with_context(self, mock_update_task):
        """Test updating task with additional context"""
        mock_updated_task = {
            "id": "1",
            "title": "Updated Task",
            "description": "Updated with new context"
        }
        mock_update_task.return_value = mock_updated_task
        
        update_data = {"context": "New requirements and context"}
        
        response = client.put("/tasks/taskmaster/1/update", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert "updated with new context" in data["message"]
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.analyze_task_complexity')
    @pytest.mark.asyncio
    async def test_analyze_task_complexity(self, mock_analyze):
        """Test analyzing task complexity"""
        mock_complexity_report = {
            "analysis_date": "2024-06-10",
            "tasks_analyzed": 10,
            "high_complexity_tasks": ["4", "7", "9"],
            "recommendations": ["Expand task 4", "Break down task 7"]
        }
        mock_analyze.return_value = mock_complexity_report
        
        response = client.post("/tasks/taskmaster/analyze-complexity")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks_analyzed" in data
        assert "high_complexity_tasks" in data
        assert "recommendations" in data
    
    @patch('src.backend.services.taskmaster_integration.TaskmasterService.sync_with_ordnungshub_tasks')
    @pytest.mark.asyncio
    async def test_sync_with_taskmaster(self, mock_sync):
        """Test syncing OrdnungsHub tasks with Taskmaster"""
        # Create test OrdnungsHub task
        task_data = {
            "title": "Test Task",
            "description": "Test sync functionality",
            "user_id": 1
        }
        
        create_response = client.post("/tasks/", json=task_data)
        assert create_response.status_code == 200
        
        mock_sync_result = {
            "synced_tasks": 1,
            "new_tasks_added": 0,
            "conflicts": [],
            "recommendations": []
        }
        mock_sync.return_value = mock_sync_result
        
        response = client.post("/tasks/sync-with-taskmaster")
        assert response.status_code == 200
        
        data = response.json()
        assert "sync_result" in data
        assert "message" in data
        assert data["sync_result"]["synced_tasks"] == 1
    
    def test_create_enhanced_task_with_ai(self):
        """Test creating task with AI enhancement"""
        task_data = {
            "title": "Urgent Bug Fix",
            "description": "Critical security vulnerability needs immediate attention",
            "user_id": 1,
            "priority": "HIGH"
        }
        
        response = client.post("/tasks/?enhance_with_ai=true", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Urgent Bug Fix"
        assert data["ai_suggested_priority"] is not None
        # Should be high priority score due to "urgent" and "critical" keywords
        assert data["ai_suggested_priority"] >= 70
    
    def test_create_task_without_ai_enhancement(self):
        """Test creating task without AI enhancement"""
        task_data = {
            "title": "Regular Task",
            "description": "Normal task description",
            "user_id": 1
        }
        
        response = client.post("/tasks/?enhance_with_ai=false", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Regular Task"
        assert data["ai_suggested_priority"] is None
    
    def test_get_task_ai_insights(self):
        """Test getting AI insights for a task"""
        # Create test task first
        task_data = {
            "title": "Complex Implementation Task",
            "description": "Implement advanced machine learning algorithm with high complexity",
            "user_id": 1
        }
        
        create_response = client.post("/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        response = client.get(f"/tasks/ai-insights/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == task_id
        assert "ai_analysis" in data
        assert "suggested_priority" in data
        assert "estimated_complexity" in data
        assert "recommended_approach" in data
    
    def test_get_ai_insights_nonexistent_task(self):
        """Test getting AI insights for nonexistent task"""
        response = client.get("/tasks/ai-insights/999999")
        assert response.status_code == 404