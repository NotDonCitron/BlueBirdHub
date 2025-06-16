"""
End-to-end tests for Create Workspace functionality
Tests the complete user flow from UI to backend
"""

import pytest
from fastapi.testclient import TestClient
import json

from src.backend.main import app
from src.backend.database.database import get_db, init_db

client = TestClient(app)


class TestCreateWorkspaceE2E:
    """End-to-end tests for workspace creation flow"""

    def setup_method(self):
        """Setup test database before each test"""
        init_db()

    def test_complete_workspace_creation_flow(self):
        """Test the complete flow from UI interaction to database persistence"""
        # Step 1: User loads task manager and gets workspaces
        response = client.get("/workspaces/")
        assert response.status_code == 200
        initial_workspaces = response.json()
        
        # Step 2: User clicks "Create New Workspace" (simulated by direct API call)
        # In real flow, this would open a modal/form
        new_workspace_data = {
            "name": "E2E Test Workspace",
            "description": "Created during E2E testing",
            "theme": "modern_light",
            "color": "#3b82f6",
            "icon": "🧪",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=new_workspace_data)
        assert response.status_code == 200
        created_workspace = response.json()
        
        # Step 3: Verify workspace appears in the list
        response = client.get("/workspaces/")
        assert response.status_code == 200
        updated_workspaces = response.json()
        assert len(updated_workspaces) == len(initial_workspaces) + 1
        
        # Find the new workspace
        new_workspace = next(
            (w for w in updated_workspaces if w["id"] == created_workspace["id"]),
            None
        )
        assert new_workspace is not None
        assert new_workspace["name"] == "E2E Test Workspace"
        
        # Step 4: User creates a task in the new workspace
        task_data = {
            "title": "First task in E2E workspace",
            "description": "Testing the complete flow",
            "priority": "medium",
            "workspace_id": created_workspace["id"],
            "user_id": 1
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 200
        created_task = response.json()
        
        # Step 5: Verify task is associated with workspace
        assert created_task["workspace_id"] == created_workspace["id"]
        
        # Step 6: Load workspace overview to see the task
        response = client.get("/tasks/taskmaster/workspace-overview")
        assert response.status_code == 200
        overview = response.json()
        
        if overview.get("success") and overview.get("overview"):
            workspace_data = overview["overview"].get(str(created_workspace["id"]))
            if workspace_data:
                assert workspace_data["workspace_name"] == "E2E Test Workspace"
                assert workspace_data["statistics"]["total_tasks"] >= 1

    def test_workspace_creation_with_validation_errors(self):
        """Test UI validation scenarios when creating workspace"""
        # Scenario 1: Empty workspace name
        invalid_data = {
            "name": "",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=invalid_data)
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("name" in str(error).lower() for error in errors)
        
        # Scenario 2: Workspace name too long
        long_name_data = {
            "name": "A" * 256,  # Exceeds typical length limit
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=long_name_data)
        # Should either truncate or reject
        assert response.status_code in [200, 422]
        
        # Scenario 3: Special characters in name
        special_char_data = {
            "name": "Test/Workspace\\With<Special>Chars",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=special_char_data)
        assert response.status_code == 200  # Should handle special chars
        
    def test_workspace_creation_from_different_contexts(self):
        """Test creating workspace from different parts of the application"""
        # Context 1: From task manager
        task_manager_workspace = {
            "name": "Task Manager Workspace",
            "description": "Created from task manager",
            "theme": "modern_light",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=task_manager_workspace)
        assert response.status_code == 200
        tm_workspace = response.json()
        
        # Context 2: From workspace manager (with more options)
        workspace_manager_data = {
            "name": "Workspace Manager Creation",
            "description": "Created with full options",
            "theme": "ocean",
            "color": "#0891b2",
            "icon": "🌊",
            "layout_config": {
                "widgets": ["tasks", "calendar", "notes"],
                "layout": "grid"
            },
            "ambient_sound": "ocean_waves",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_manager_data)
        assert response.status_code == 200
        wm_workspace = response.json()
        assert wm_workspace["ambient_sound"] == "ocean_waves"
        
        # Context 3: Quick create (minimal data)
        quick_create_data = {
            "name": "Quick Workspace",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=quick_create_data)
        assert response.status_code == 200
        quick_workspace = response.json()
        assert quick_workspace["theme"] is not None  # Defaults applied

    def test_workspace_creation_and_immediate_switch(self):
        """Test creating a workspace and immediately switching to it"""
        # Create workspace
        workspace_data = {
            "name": "Switch Test Workspace",
            "color": "#7c3aed",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        workspace = response.json()
        workspace_id = workspace["id"]
        
        # Switch to the new workspace
        response = client.post(f"/workspaces/{workspace_id}/switch")
        assert response.status_code == 200
        switch_response = response.json()
        
        assert switch_response["workspace"]["id"] == workspace_id
        assert "Switched to workspace" in switch_response["message"]
        
        # Verify workspace is marked as accessed
        response = client.get(f"/workspaces/{workspace_id}")
        assert response.status_code == 200
        workspace_details = response.json()
        assert workspace_details["last_accessed_at"] is not None

    def test_bulk_task_creation_after_workspace(self):
        """Test creating multiple tasks immediately after workspace creation"""
        # Create workspace
        workspace_data = {
            "name": "Bulk Task Workspace",
            "description": "For testing bulk operations",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        workspace = response.json()
        workspace_id = workspace["id"]
        
        # Create multiple tasks
        tasks_to_create = [
            {
                "title": "Task 1: Setup",
                "priority": "high",
                "workspace_id": workspace_id,
                "user_id": 1
            },
            {
                "title": "Task 2: Development",
                "priority": "medium",
                "workspace_id": workspace_id,
                "user_id": 1
            },
            {
                "title": "Task 3: Testing",
                "priority": "medium",
                "workspace_id": workspace_id,
                "user_id": 1
            }
        ]
        
        created_tasks = []
        for task_data in tasks_to_create:
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 200
            created_tasks.append(response.json())
        
        # Verify all tasks are in the workspace
        response = client.get(f"/tasks/?workspace_id={workspace_id}")
        assert response.status_code == 200
        workspace_tasks = response.json()
        assert len(workspace_tasks) >= 3
        
        task_titles = [t["title"] for t in workspace_tasks]
        assert "Task 1: Setup" in task_titles
        assert "Task 2: Development" in task_titles
        assert "Task 3: Testing" in task_titles

    def test_workspace_template_suggestions(self):
        """Test getting template suggestions when creating workspace"""
        # Get available templates
        response = client.get("/workspaces/templates")
        assert response.status_code == 200
        templates_response = response.json()
        
        assert "templates" in templates_response
        templates = templates_response["templates"]
        assert len(templates) > 0
        
        # Verify template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "theme" in template
            assert "suggested_widgets" in template
        
        # Create workspace from a template
        template_name = templates[0]["id"]
        response = client.post(
            "/workspaces/create-from-template",
            params={
                "template_name": template_name,
                "workspace_name": "From Template Test",
                "user_id": 1
            }
        )
        assert response.status_code == 200
        
        created = response.json()
        assert created["workspace"]["name"] == "From Template Test"
        assert created["message"] == f"Workspace created from template: {template_name}"

    def test_concurrent_workspace_creation(self):
        """Test handling concurrent workspace creation requests"""
        # This simulates multiple users or tabs creating workspaces
        workspace_names = [
            "Concurrent Workspace 1",
            "Concurrent Workspace 2",
            "Concurrent Workspace 3"
        ]
        
        created_workspaces = []
        for name in workspace_names:
            workspace_data = {
                "name": name,
                "user_id": 1
            }
            response = client.post("/workspaces/", json=workspace_data)
            assert response.status_code == 200
            created_workspaces.append(response.json())
        
        # Verify all were created with unique IDs
        ids = [w["id"] for w in created_workspaces]
        assert len(ids) == len(set(ids))  # All IDs are unique
        
        # Verify all appear in workspace list
        response = client.get("/workspaces/")
        assert response.status_code == 200
        all_workspaces = response.json()
        
        workspace_names_in_db = [w["name"] for w in all_workspaces]
        for name in workspace_names:
            assert name in workspace_names_in_db