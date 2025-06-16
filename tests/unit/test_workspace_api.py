"""
Test cases for Workspace API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.backend.main import app
from src.backend.database.database import Base, get_db
from src.backend.models.task import Task, TaskStatus, TaskPriority
from src.backend.models.workspace import Workspace
from src.backend.models.user import User

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workspace.db"
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

class TestWorkspaceAPI:
    """Test Workspace API endpoints"""
    
    def test_get_workspaces_empty(self):
        """Test getting workspaces when none exist"""
        response = client.get("/workspaces/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_create_workspace(self):
        """Test creating a new workspace"""
        workspace_data = {
            "name": "Test Workspace",
            "description": "A test workspace for work tasks",
            "theme": "professional",
            "color": "#4a9eff",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Workspace"
        assert data["theme"] == "professional"
        assert data["user_id"] == 1
        assert "id" in data

    def test_create_workspace_with_ai_suggestion(self):
        """Test creating workspace with AI theme suggestion"""
        workspace_data = {
            "name": "Work Project",
            "description": "Important business project with urgent deadlines",
            "user_id": 1
        }
        
        response = client.post("/workspaces/", json=workspace_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Work Project"
        # AI should suggest professional theme for work content
        assert data["theme"] == "professional"

    def test_get_workspace_by_id(self):
        """Test getting a specific workspace"""
        # First create a workspace
        workspace_data = {
            "name": "Test Workspace 2",
            "description": "Another test workspace",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Then get it by ID
        response = client.get(f"/workspaces/{workspace_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == workspace_id
        assert data["name"] == "Test Workspace 2"

    def test_get_nonexistent_workspace(self):
        """Test getting a workspace that doesn't exist"""
        response = client.get("/workspaces/999999")
        assert response.status_code == 404

    def test_update_workspace(self):
        """Test updating a workspace"""
        # Create workspace first
        workspace_data = {
            "name": "Original Name",
            "description": "Original description",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Update it
        update_data = {
            "name": "Updated Name",
            "theme": "dark"
        }
        
        response = client.put(f"/workspaces/{workspace_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["theme"] == "dark"

    def test_switch_workspace(self):
        """Test switching to a workspace"""
        # Create workspace first
        workspace_data = {
            "name": "Switch Test Workspace",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Switch to it
        response = client.post(f"/workspaces/{workspace_id}/switch")
        assert response.status_code == 200
        
        data = response.json()
        assert "workspace" in data
        assert data["workspace"]["id"] == workspace_id
        assert "message" in data

    def test_update_workspace_state(self):
        """Test updating workspace state"""
        # Create workspace first
        workspace_data = {
            "name": "State Test Workspace",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Update state
        state_data = {
            "state": {
                "widgets": ["calendar", "tasks", "notes"],
                "sidebar_collapsed": True,
                "theme_settings": {"dark_mode": True}
            }
        }
        
        response = client.put(f"/workspaces/{workspace_id}/state", json=state_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert "widgets" in data["state"]

    def test_get_workspace_state(self):
        """Test getting workspace state"""
        # Create workspace with state
        workspace_data = {
            "name": "State Get Test",
            "user_id": 1,
            "state": {"initial": "state"}
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Get state
        response = client.get(f"/workspaces/{workspace_id}/state")
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert "state" in data

    def test_assign_content_to_workspace(self):
        """Test AI content assignment to workspace"""
        # Create workspace
        workspace_data = {
            "name": "Work Tasks",
            "description": "Professional workspace for business tasks",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Test content assignment
        content_data = {
            "text": "Urgent business meeting with client about project deadline"
        }
        
        response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert "overall_compatibility" in data
        assert "recommendation" in data
        assert data["overall_compatibility"] > 0.5  # Should be compatible

    def test_get_workspace_suggestions(self):
        """Test getting AI workspace suggestions"""
        # Create workspace
        workspace_data = {
            "name": "Learning Space",
            "description": "Educational workspace for studying and learning",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Get suggestions
        response = client.get(f"/workspaces/{workspace_id}/suggestions")
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    def test_create_workspace_from_template(self):
        """Test creating workspace from template"""
        response = client.post(
            "/workspaces/create-from-template",
            params={
                "template_name": "work",
                "workspace_name": "My Work Space"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace"]["name"] == "My Work Space"
        assert data["template_used"] == "work"
        assert data["workspace"]["theme"] == "professional"

    def test_create_workspace_invalid_template(self):
        """Test creating workspace with invalid template"""
        response = client.post(
            "/workspaces/create-from-template",
            params={
                "template_name": "nonexistent",
                "workspace_name": "Test"
            }
        )
        assert response.status_code == 400

    def test_delete_workspace(self):
        """Test deleting a workspace"""
        # Create workspace first
        workspace_data = {
            "name": "Delete Test Workspace",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/workspaces/{workspace_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
        # Verify it's deleted
        get_response = client.get(f"/workspaces/{workspace_id}")
        assert get_response.status_code == 404

    def test_assign_content_missing_text(self):
        """Test content assignment with missing text"""
        # Create workspace first
        workspace_data = {
            "name": "Test Workspace",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Try to assign content without text
        content_data = {}
        
        response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content_data)
        assert response.status_code == 400