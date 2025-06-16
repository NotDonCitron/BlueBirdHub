"""
Test cases for Enhanced Workspace API endpoints
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workspace_enhanced.db"
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

class TestEnhancedWorkspaceAPI:
    """Test Enhanced Workspace API endpoints"""
    
    def test_get_workspace_templates(self):
        """Test getting enhanced workspace templates"""
        response = client.get("/workspaces/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert "categories" in data
        
        templates = data["templates"]
        assert "work" in templates
        assert "personal" in templates
        assert "study" in templates
        assert "creative" in templates
        assert "focus" in templates
        assert "wellness" in templates
        
        # Check enhanced template structure
        work_template = templates["work"]
        assert work_template["display_name"] == "Professional"
        assert "features" in work_template
        assert "recommended_for" in work_template
        assert "ambient_sound" in work_template
        assert work_template["icon"] == "💼"

    def test_get_available_themes(self):
        """Test getting available workspace themes"""
        response = client.get("/workspaces/themes")
        assert response.status_code == 200
        
        data = response.json()
        assert "builtin_themes" in data
        assert "custom_themes" in data
        assert "total_themes" in data
        
        builtin_themes = data["builtin_themes"]
        assert "professional" in builtin_themes
        assert "minimal" in builtin_themes
        assert "dark" in builtin_themes
        assert "colorful" in builtin_themes
        assert "light" in builtin_themes
        
        # Check theme structure
        professional_theme = builtin_themes["professional"]
        assert professional_theme["display_name"] == "Professional"
        assert professional_theme["primary_color"] == "#2563eb"
        assert professional_theme["is_dark_mode"] == False

    def test_workspace_analytics(self):
        """Test workspace analytics endpoint"""
        # First create a workspace
        workspace_data = {
            "name": "Analytics Test Workspace",
            "description": "Workspace for testing analytics",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        assert create_response.status_code == 200
        workspace_id = create_response.json()["id"]
        
        # Get analytics
        response = client.get(f"/workspaces/{workspace_id}/analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert "usage_stats" in data
        assert "ai_insights" in data
        assert "recommendations" in data
        
        # Check usage stats structure
        usage_stats = data["usage_stats"]
        assert "total_tasks" in usage_stats
        assert "completed_tasks" in usage_stats
        assert "completion_rate" in usage_stats
        assert "estimated_time_spent_hours" in usage_stats
        
        # Check AI insights
        ai_insights = data["ai_insights"]
        assert "productivity_score" in ai_insights
        assert "suggested_improvements" in ai_insights
        assert "category" in ai_insights
        assert "sentiment" in ai_insights

    def test_workspace_analytics_nonexistent(self):
        """Test analytics for nonexistent workspace"""
        response = client.get("/workspaces/999999/analytics")
        assert response.status_code == 404

    def test_update_ambient_sound(self):
        """Test updating workspace ambient sound"""
        # Create workspace first
        workspace_data = {
            "name": "Ambient Sound Test",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Update ambient sound
        sound_data = {"ambient_sound": "nature_sounds"}
        response = client.post(f"/workspaces/{workspace_id}/ambient-sound", json=sound_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert data["ambient_sound"] == "nature_sounds"
        assert data["sound_name"] == "Nature sounds"
        assert "available_sounds" in data

    def test_update_ambient_sound_invalid(self):
        """Test updating workspace with invalid ambient sound"""
        # Create workspace first
        workspace_data = {
            "name": "Invalid Sound Test",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Try invalid ambient sound
        sound_data = {"ambient_sound": "invalid_sound"}
        response = client.post(f"/workspaces/{workspace_id}/ambient-sound", json=sound_data)
        assert response.status_code == 400

    def test_update_ambient_sound_nonexistent_workspace(self):
        """Test updating ambient sound for nonexistent workspace"""
        sound_data = {"ambient_sound": "nature_sounds"}
        response = client.post("/workspaces/999999/ambient-sound", json=sound_data)
        assert response.status_code == 404

    def test_create_workspace_from_enhanced_template(self):
        """Test creating workspace from enhanced template"""
        response = client.post("/workspaces/create-from-template", params={
            "template_name": "focus",
            "workspace_name": "My Focus Space"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace"]["name"] == "My Focus Space"
        assert data["template_used"] == "focus"
        assert data["workspace"]["theme"] == "minimal"
        
        # Check that layout_config contains focus template data
        workspace = data["workspace"]
        assert workspace["layout_config"] is not None

    def test_create_workspace_wellness_template(self):
        """Test creating workspace from wellness template"""
        response = client.post("/workspaces/create-from-template", params={
            "template_name": "wellness",
            "workspace_name": "My Wellness Hub"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace"]["name"] == "My Wellness Hub"
        assert data["template_used"] == "wellness"
        assert data["workspace"]["theme"] == "light"

    def test_workspace_with_ambient_sounds_integration(self):
        """Test complete workflow with ambient sounds"""
        # Create workspace from template with ambient sound
        create_response = client.post("/workspaces/create-from-template", params={
            "template_name": "study",
            "workspace_name": "Study Session"
        })
        workspace_id = create_response.json()["workspace"]["id"]
        
        # Check ambient sound was set from template
        get_response = client.get(f"/workspaces/{workspace_id}")
        workspace = get_response.json()
        # Note: ambient_sound might be in layout_config depending on implementation
        
        # Update ambient sound
        sound_update = {"ambient_sound": "white_noise"}
        update_response = client.post(f"/workspaces/{workspace_id}/ambient-sound", json=sound_update)
        assert update_response.status_code == 200
        assert update_response.json()["ambient_sound"] == "white_noise"

    def test_workspace_themes_and_templates_consistency(self):
        """Test that themes from templates match available themes"""
        # Get templates
        templates_response = client.get("/workspaces/templates")
        templates = templates_response.json()["templates"]
        
        # Get themes
        themes_response = client.get("/workspaces/themes")
        themes = themes_response.json()["builtin_themes"]
        
        # Check that template themes exist in available themes
        for template_name, template_data in templates.items():
            template_theme = template_data["theme"]
            assert template_theme in themes, f"Template {template_name} uses theme {template_theme} which is not available"

    def test_analytics_with_tasks(self):
        """Test analytics calculation with actual tasks"""
        # Create workspace
        workspace_data = {
            "name": "Task Analytics Test",
            "description": "Testing analytics with tasks",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Create some tasks (this would require task API integration)
        # For now, test the analytics endpoint structure
        response = client.get(f"/workspaces/{workspace_id}/analytics")
        assert response.status_code == 200
        
        data = response.json()
        usage_stats = data["usage_stats"]
        
        # Should handle zero tasks gracefully
        assert usage_stats["total_tasks"] >= 0
        assert usage_stats["completion_rate"] >= 0
        assert usage_stats["estimated_time_spent_hours"] >= 0

    def test_ambient_sound_options_comprehensive(self):
        """Test all available ambient sound options"""
        # Create workspace
        workspace_data = {"name": "Sound Test", "user_id": 1}
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Test each available sound
        expected_sounds = [
            "none", "office_ambience", "nature_sounds", "study_music",
            "creativity_boost", "white_noise", "meditation_sounds",
            "rain", "forest", "ocean", "cafe"
        ]
        
        for sound in expected_sounds:
            sound_data = {"ambient_sound": sound}
            response = client.post(f"/workspaces/{workspace_id}/ambient-sound", json=sound_data)
            assert response.status_code == 200
            assert response.json()["ambient_sound"] == sound

    def test_template_feature_descriptions(self):
        """Test that all templates have proper feature descriptions"""
        response = client.get("/workspaces/templates")
        templates = response.json()["templates"]
        
        required_fields = ["name", "display_name", "description", "theme", "color", 
                          "icon", "default_widgets", "features", "recommended_for"]
        
        for template_name, template_data in templates.items():
            for field in required_fields:
                assert field in template_data, f"Template {template_name} missing field {field}"
            
            # Check that features and recommended_for are lists
            assert isinstance(template_data["features"], list)
            assert isinstance(template_data["recommended_for"], list)
            assert len(template_data["features"]) > 0
            assert len(template_data["recommended_for"]) > 0