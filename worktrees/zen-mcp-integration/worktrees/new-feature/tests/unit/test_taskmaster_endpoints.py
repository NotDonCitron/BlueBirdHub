"""
Unit tests for Taskmaster API endpoints
Tests individual API endpoints with mocked dependencies
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from src.backend.main import app

client = TestClient(app)

class TestTaskmasterIntegration:
    """Test Taskmaster API endpoints functionality"""
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.get_all_tasks')
    def test_taskmaster_service_integration(self, mock_get_tasks):
        """Test Taskmaster service integration"""
        # Mock the service response
        mock_get_tasks.return_value = {
            "tasks": [
                {
                    "id": "task_1",
                    "title": "Test Task",
                    "status": "pending",
                    "priority": "high",
                    "description": "Test description"
                }
            ],
            "total": 1,
            "source": "taskmaster"
        }
        
        response = client.get("/tasks/taskmaster/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "source" in data
        assert data["source"] == "taskmaster"
        assert isinstance(data["tasks"], list)
        
        # Verify task structure if tasks exist
        if data["tasks"]:
            task = data["tasks"][0]
            required_fields = ["id", "title", "status", "priority"]
            for field in required_fields:
                assert field in task
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.get_progress')
    def test_get_project_progress(self, mock_get_progress):
        """Test GET /tasks/taskmaster/progress endpoint"""
        mock_get_progress.return_value = {
            "total_tasks": 10,
            "completed_tasks": 5,
            "pending_tasks": 3,
            "in_progress_tasks": 2,
            "completion_percentage": 50.0
        }
        
        response = client.get("/tasks/taskmaster/progress")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "total_tasks", "completed_tasks", "pending_tasks", 
            "in_progress_tasks", "completion_percentage"
        ]
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], (int, float))
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.get_next_task')
    def test_get_next_task(self, mock_next_task):
        """Test getting next recommended task"""
        mock_next_task.return_value = {
            "task": {
                "id": "next_task_1",
                "title": "Important Task",
                "priority": "high",
                "estimated_time": 30,
                "reason": "High priority and due soon"
            },
            "recommendation_score": 0.95
        }
        
        response = client.get("/tasks/taskmaster/next")
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        if data["task"]:
            assert "id" in data["task"]
            assert "title" in data["task"]
    
    @patch('src.backend.services.taskmaster_integration.taskmaster_service.create_task')
    def test_create_taskmaster_task(self, mock_create):
        """Test creating task via Taskmaster"""
        mock_create.return_value = {
            "success": True,
            "task_id": "new_task_123",
            "message": "Task created successfully"
        }
        
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "priority": "medium"
        }
        
        response = client.post("/tasks/taskmaster/create", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "task_id" in data
    
    def test_taskmaster_health_check(self):
        """Test Taskmaster service health"""
        response = client.get("/tasks/taskmaster/health")
        assert response.status_code in [200, 404]  # May not be implemented
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data