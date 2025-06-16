"""
Tests for Create Workspace Integration
Tests the complete flow of creating a workspace from the task manager
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.main import app
from src.backend.database.database import get_db, init_db
from src.backend.models.workspace import Workspace
from src.backend.models.task import Task

client = TestClient(app)


class TestCreateWorkspaceIntegration:
    """Test suite for create workspace integration"""

    def setup_method(self):
        """Setup test database before each test"""
        init_db()

    def test_create_workspace_from_task_manager_flow(self):
        """Test the full flow of creating a workspace when adding a task"""
        # Step 1: Get current workspaces
        response = client.get("/workspaces/")
        assert response.status_code == 200
        initial_workspaces = response.json()
        initial_count = len(initial_workspaces)

        # Step 2: Create a new workspace
        workspace_data = {
            "name": "New Project Workspace",
            "description": "Created from task manager",
            "theme": "modern_light",
            "color": "#9333ea",
            "icon": "🚀",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        new_workspace = response.json()
        assert new_workspace["name"] == "New Project Workspace"
        assert new_workspace["id"] is not None
        
        # Step 3: Verify workspace was created
        response = client.get("/workspaces/")
        assert response.status_code == 200
        updated_workspaces = response.json()
        assert len(updated_workspaces) == initial_count + 1
        
        # Step 4: Create a task in the new workspace
        task_data = {
            "title": "First task in new workspace",
            "description": "Testing workspace creation flow",
            "priority": "HIGH",
            "status": "PENDING", 
            "workspace_id": new_workspace["id"],
            "user_id": 1
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 200
        new_task = response.json()
        assert new_task["workspace_id"] == new_workspace["id"]
        
        # Step 5: Verify task appears in workspace
        response = client.get(f"/tasks/?workspace_id={new_workspace['id']}")
        assert response.status_code == 200
        workspace_tasks = response.json()
        assert len(workspace_tasks) == 1
        assert workspace_tasks[0]["title"] == "First task in new workspace"

    def test_create_workspace_with_template_from_task_manager(self):
        """Test creating a workspace from a template when adding a task"""
        # Step 1: Get available templates
        response = client.get("/workspaces/templates")
        assert response.status_code == 200
        templates = response.json()
        assert len(templates["templates"]) > 0
        
        # Step 2: Create workspace from template
        response = client.post(
            "/workspaces/create-from-template",
            params={
                "template_name": "project_management",
                "workspace_name": "My New Project",
                "user_id": 1
            }
        )
        assert response.status_code == 200
        workspace = response.json()["workspace"]
        assert workspace["name"] == "My New Project"
        assert workspace["theme"] == "modern_light"  # From template
        
        # Step 3: Add task to the templated workspace
        task_data = {
            "title": "Project kickoff meeting",
            "description": "Initial planning session",
            "priority": "high",
            "workspace_id": workspace["id"],
            "user_id": 1
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 200

    def test_workspace_creation_validation(self):
        """Test validation when creating workspace from task manager"""
        # Test duplicate workspace name
        workspace_data = {
            "name": "Duplicate Test Workspace",
            "user_id": 1
        }
        
        # Create first workspace
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        
        # Try to create duplicate
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
        
        # Test invalid workspace data
        invalid_data = {
            "name": "",  # Empty name
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_workspace_quick_create_minimal_data(self):
        """Test creating workspace with minimal data (quick create from task manager)"""
        # Minimal workspace data - just name and user
        minimal_data = {
            "name": "Quick Workspace",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=minimal_data)
        assert response.status_code == 200
        workspace = response.json()
        
        # Check defaults were applied
        assert workspace["name"] == "Quick Workspace"
        assert workspace["theme"] is not None  # Default theme applied
        assert workspace["color"] is not None  # Default color applied
        assert workspace["icon"] is not None   # Default icon applied
        assert workspace["is_active"] is True
        assert workspace["is_default"] is False

    def test_create_workspace_and_set_as_default(self):
        """Test creating a workspace and setting it as default"""
        # Create workspace
        workspace_data = {
            "name": "New Default Workspace",
            "user_id": 1,
            "is_default": True
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        new_workspace = response.json()
        
        # Verify it's set as default
        assert new_workspace["is_default"] is True
        
        # Verify other workspaces are not default
        response = client.get("/workspaces/?user_id=1")
        assert response.status_code == 200
        all_workspaces = response.json()
        
        default_count = sum(1 for w in all_workspaces if w["is_default"])
        assert default_count == 1  # Only one default workspace

    def test_workspace_creation_with_ai_suggestions(self):
        """Test workspace creation with AI-suggested properties"""
        # Create workspace with AI suggestions endpoint
        content_data = {
            "text": "Software development project with Python and React",
            "content_type": "project_description"
        }
        
        # First get AI suggestions for the workspace
        response = client.post(
            f"/workspaces/1/assign-content",
            json=content_data
        )
        assert response.status_code == 200
        
        # Create workspace based on content
        workspace_data = {
            "name": "Software Dev Project",
            "description": "Python and React project workspace",
            "theme": "modern_dark",  # AI might suggest dark theme for coding
            "color": "#059669",      # Green for tech projects
            "icon": "💻",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        workspace = response.json()
        assert workspace["theme"] == "modern_dark"
        assert workspace["icon"] == "💻"

    def test_create_workspace_and_immediately_add_task(self):
        """Test the immediate task creation after workspace creation"""
        # Step 1: Create workspace
        workspace_data = {
            "name": "Urgent Project",
            "description": "Time-sensitive project",
            "color": "#ef4444",  # Red for urgent
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        workspace = response.json()
        workspace_id = workspace["id"]
        
        # Step 2: Immediately create a task
        task_data = {
            "title": "Setup project structure",
            "description": "Initialize the project repository and basic structure",
            "priority": "high",
            "status": "PENDING",
            "workspace_id": workspace_id,
            "user_id": 1
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 200
        task = response.json()
        
        # Step 3: Verify task is in the new workspace
        assert task["workspace_id"] == workspace_id
        
        # Step 4: Check workspace has the task
        response = client.get(f"/tasks/?workspace_id={workspace_id}")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task["id"]

    def test_workspace_creation_error_handling(self):
        """Test error handling during workspace creation from task manager"""
        # Test with invalid user
        workspace_data = {
            "name": "Invalid User Workspace",
            "user_id": 99999  # Non-existent user
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        # Should still create (no foreign key constraint in test)
        assert response.status_code in [200, 400]
        
        # Test with missing required field
        incomplete_data = {
            # Missing name
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=incomplete_data)
        assert response.status_code == 422
        
        # Test with invalid color format
        invalid_color_data = {
            "name": "Bad Color Workspace",
            "color": "not-a-color",  # Invalid color format
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=invalid_color_data)
        # Should either accept or validate
        assert response.status_code in [200, 422]