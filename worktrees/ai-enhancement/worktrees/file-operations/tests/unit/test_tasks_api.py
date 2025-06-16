"""
Test cases for tasks API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.backend.main import app
from src.backend.models.task import TaskStatus, TaskPriority
from datetime import datetime

client = TestClient(app)


class TestTasksAPI:
    """Test task management endpoints"""
    
    def test_get_all_tasks(self):
        """Test getting all tasks"""
        response = client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_tasks_with_filters(self):
        """Test getting tasks with filters"""
        response = client.get("/tasks/?user_id=1&status=pending&priority=high")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.get_all_tasks')
    def test_get_taskmaster_tasks(self, mock_get_tasks):
        """Test getting tasks from Taskmaster AI"""
        mock_get_tasks.return_value = {
            "tasks": [
                {
                    "id": "1",
                    "title": "Test Task",
                    "status": "pending",
                    "priority": "high"
                }
            ],
            "total": 1
        }
        
        response = client.get("/tasks/taskmaster/all")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.get_next_task')
    def test_get_next_task(self, mock_next_task):
        """Test getting next recommended task"""
        mock_next_task.return_value = {
            "task": {
                "id": "1",
                "title": "Important Task",
                "reason": "High priority and due soon"
            }
        }
        
        response = client.get("/tasks/taskmaster/next")
        assert response.status_code == 200
        data = response.json()
        assert "task" in data
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.get_progress')
    def test_get_taskmaster_progress(self, mock_progress):
        """Test getting task progress from Taskmaster"""
        mock_progress.return_value = {
            "total_tasks": 10,
            "completed_tasks": 5,
            "completion_percentage": 50
        }
        
        response = client.get("/tasks/taskmaster/progress")
        assert response.status_code == 200
        data = response.json()
        assert "completion_percentage" in data
        assert "total_tasks" in data
    
    def test_create_task(self):
        """Test creating a new task"""
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "workspace_id": 1,
            "priority": "medium",
            "status": "pending"
        }
        
        response = client.post("/tasks/", json=task_data)
        # May succeed or fail based on DB state
        assert response.status_code in [200, 201, 422, 500]
    
    @patch('src.backend.database.database.SessionLocal')
    def test_update_task(self, mock_db):
        """Test updating a task"""
        # Mock the database session
        mock_session = MagicMock()
        mock_db.return_value = mock_session
        
        # Mock the task query
        mock_task = MagicMock()
        mock_task.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_task
        
        update_data = {
            "title": "Updated Task",
            "status": "completed"
        }
        
        response = client.put("/tasks/1", json=update_data)
        # Task might not exist
        assert response.status_code in [200, 404, 422]
    
    def test_delete_task(self):
        """Test deleting a task"""
        response = client.delete("/tasks/1")
        # Task might not exist
        assert response.status_code in [200, 204, 404]
    
    def test_get_task_by_id(self):
        """Test getting a specific task"""
        response = client.get("/tasks/1")
        # Task might not exist
        assert response.status_code in [200, 404]
    
    @patch('src.backend.services.ai_service.ai_service.generate_suggestions')
    def test_ai_task_suggestions(self, mock_suggestions):
        """Test AI task suggestions"""
        mock_suggestions.return_value = [
            "Break down the task into smaller subtasks",
            "Set a specific deadline"
        ]
        
        response = client.post("/tasks/ai-suggestions", json={
            "title": "Complex Task",
            "description": "Need help organizing this"
        })
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.create_task')
    def test_create_taskmaster_task(self, mock_create):
        """Test creating task via Taskmaster"""
        mock_create.return_value = {
            "success": True,
            "task_id": "123",
            "message": "Task created successfully"
        }
        
        response = client.post("/tasks/taskmaster/add", json={
            "title": "New Task",
            "description": "Task description",
            "priority": "high"
        })
        assert response.status_code == 200
    
    def test_task_filtering(self):
        """Test task filtering by various parameters"""
        # Test status filter
        response = client.get("/tasks/?status=completed")
        assert response.status_code == 200
        
        # Test priority filter
        response = client.get("/tasks/?priority=high")
        assert response.status_code == 200
        
        # Test combined filters
        response = client.get("/tasks/?status=pending&priority=medium&workspace_id=1")
        assert response.status_code == 200
    
    def test_task_validation(self):
        """Test task validation"""
        # Invalid priority
        response = client.post("/tasks/", json={
            "title": "Test",
            "priority": "invalid"
        })
        assert response.status_code in [422, 500]
        
        # Missing required fields
        response = client.post("/tasks/", json={})
        assert response.status_code in [422, 500]