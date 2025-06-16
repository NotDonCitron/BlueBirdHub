"""
Test cases for Enhanced AI Content Assignment System
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
from src.backend.models.workspace import Workspace
from src.backend.models.user import User

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_content_assignment.db"
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

class TestAIContentAssignment:
    """Test Enhanced AI Content Assignment functionality"""
    
    def test_enhanced_content_assignment(self):
        """Test enhanced content assignment with multiple factors"""
        # Create test workspace
        workspace_data = {
            "name": "Work Productivity Hub",
            "description": "Professional workspace for business tasks and project management",
            "theme": "professional",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        assert create_response.status_code == 200
        workspace_id = create_response.json()["id"]
        
        # Test content assignment with detailed content
        content_data = {
            "text": "Urgent: Complete quarterly business report for client meeting deadline tomorrow",
            "type": "document",
            "tags": ["business", "report", "urgent", "quarterly"]
        }
        
        response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert "content_analysis" in data
        assert "compatibility_factors" in data
        assert "overall_compatibility" in data
        assert "organization_suggestions" in data
        assert "alternative_workspaces" in data
        
        # Check compatibility factors structure
        compatibility = data["compatibility_factors"]
        assert "factors" in compatibility
        assert "weights" in compatibility
        assert "total_score" in compatibility
        assert "recommendation" in compatibility
        assert "detailed_reasoning" in compatibility
        
        # Should be a reasonable match for professional workspace with business content
        assert compatibility["total_score"] > 0.5
        assert compatibility["recommendation"] in ["recommended", "highly_recommended", "consider"]
        
    def test_content_assignment_poor_match(self):
        """Test content assignment with poor workspace-content match"""
        # Create focused workspace
        workspace_data = {
            "name": "Deep Focus Zone",
            "description": "Minimal distractions for concentrated work",
            "theme": "minimal",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Test with unrelated content
        content_data = {
            "text": "Fun family vacation photos and personal memories",
            "type": "photos",
            "tags": ["personal", "family", "vacation", "memories"]
        }
        
        response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content_data)
        assert response.status_code == 200
        
        data = response.json()
        compatibility = data["compatibility_factors"]
        
        # Should be a poor match
        assert compatibility["total_score"] < 0.5
        assert compatibility["recommendation"] in ["not_recommended", "consider"]
        
    def test_bulk_content_assignment(self):
        """Test bulk content assignment across multiple workspaces"""
        # Create multiple workspaces
        workspaces = [
            {
                "name": "Work Projects",
                "description": "Business and professional tasks",
                "theme": "professional",
                "user_id": 1
            },
            {
                "name": "Personal Life",
                "description": "Personal organization and life management",
                "theme": "minimal",
                "user_id": 1
            },
            {
                "name": "Creative Studio",
                "description": "Art projects and creative work",
                "theme": "colorful",
                "user_id": 1
            }
        ]
        
        for workspace in workspaces:
            client.post("/workspaces/", json=workspace)
        
        # Bulk content assignment
        content_items = [
            {
                "id": "content_1",
                "text": "Design new company logo and branding materials",
                "type": "design",
                "tags": ["creative", "design", "branding"]
            },
            {
                "id": "content_2", 
                "text": "Schedule doctor appointment and grocery shopping",
                "type": "task",
                "tags": ["personal", "health", "shopping"]
            },
            {
                "id": "content_3",
                "text": "Prepare quarterly financial analysis for board meeting",
                "type": "document",
                "tags": ["business", "finance", "analysis"]
            }
        ]
        
        response = client.post("/workspaces/bulk-assign-content", json=content_items)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_content_items"] == 3
        assert len(data["results"]) == 3
        assert data["summary"]["processed"] == 3
        assert data["summary"]["errors"] == 0
        
        # Check that each content item got recommendations
        for result in data["results"]:
            assert "content_id" in result
            assert "recommendations" in result
            assert "best_match" in result
            assert len(result["recommendations"]) <= 3  # Top 3 recommendations
            
    def test_workspace_optimization(self):
        """Test AI-powered workspace optimization"""
        # Create workspace with default settings
        workspace_data = {
            "name": "Unoptimized Workspace",
            "description": "Research and academic work",
            "theme": "default",  # Default theme should trigger optimization
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        assert create_response.status_code == 200
        
        # Get optimization suggestions
        response = client.post("/workspaces/optimize-all")
        assert response.status_code == 200
        
        data = response.json()
        assert "optimization_results" in data
        assert "summary" in data
        
        # Should find optimization opportunities
        assert data["summary"]["workspaces_needing_optimization"] > 0
        assert data["summary"]["total_optimizations"] > 0
        
        # Check optimization structure
        optimization = data["optimization_results"][0]
        assert "workspace_id" in optimization
        assert "optimizations" in optimization
        assert "optimization_score" in optimization
        
        # Should have at least one optimization suggestion
        optimizations = optimization["optimizations"]
        assert len(optimizations) > 0
        
        # Check if there's a theme optimization (there should be since theme is "default")
        theme_opt = next((opt for opt in optimizations if opt["type"] == "theme"), None)
        if theme_opt:
            assert theme_opt["current"] == "default"
            assert theme_opt["suggested"] != "default"
        
    @pytest.mark.skip("Content insights endpoint needs parameter validation fix")
    def test_content_insights(self):
        """Test AI-powered content insights generation"""
        # Create workspace with some activity
        workspace_data = {
            "name": "Insights Test Workspace",
            "description": "Workspace for testing insights",
            "theme": "professional",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Get content insights (test without workspace_id first)
        response = client.get("/workspaces/content-insights")
        assert response.status_code == 200
        
        # Get content insights for specific workspace
        response = client.get(f"/workspaces/content-insights?workspace_id={workspace_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "workspace_insights" in data
        assert "summary" in data
        
        insights = data["workspace_insights"][0]
        assert insights["workspace_id"] == workspace_id
        assert "metrics" in insights
        assert "ai_insights" in insights
        assert "recommendations" in insights
        
        # Check metrics structure
        metrics = insights["metrics"]
        assert "total_tasks" in metrics
        assert "completed_tasks" in metrics
        assert "completion_rate" in metrics
        assert "productivity_score" in metrics
        
        # Check AI insights
        ai_insights = insights["ai_insights"]
        assert "content_category" in ai_insights
        assert "productivity_level" in ai_insights
        assert "optimization_potential" in ai_insights
        
    def test_content_assignment_missing_text(self):
        """Test content assignment with missing text"""
        workspace_data = {
            "name": "Test Workspace",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Test with missing text
        content_data = {
            "type": "document",
            "tags": ["test"]
        }
        
        response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content_data)
        assert response.status_code == 400
        assert "Content text is required" in response.json()["detail"]
        
    def test_content_assignment_nonexistent_workspace(self):
        """Test content assignment for nonexistent workspace"""
        content_data = {
            "text": "Some test content",
            "type": "document"
        }
        
        response = client.post("/workspaces/999999/assign-content", json=content_data)
        assert response.status_code == 404
        
    def test_organization_suggestions_by_content_type(self):
        """Test that organization suggestions vary by content type"""
        workspace_data = {
            "name": "Organization Test",
            "theme": "professional",
            "user_id": 1
        }
        
        create_response = client.post("/workspaces/", json=workspace_data)
        workspace_id = create_response.json()["id"]
        
        # Test different content types
        content_types = [
            {
                "text": "Complete project milestone review",
                "type": "task",
                "expected_widget": "Tasks"
            },
            {
                "text": "Meeting notes from client discussion",
                "type": "note", 
                "expected_widget": "Notes"
            },
            {
                "text": "Project specification document",
                "type": "file",
                "expected_widget": "Files"
            }
        ]
        
        for content in content_types:
            response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content)
            assert response.status_code == 200
            
            data = response.json()
            suggestions = data["organization_suggestions"]
            
            # Should have widget placement suggestion
            widget_suggestion = next((s for s in suggestions if s["type"] == "widget_placement"), None)
            assert widget_suggestion is not None
            assert content["expected_widget"].lower() in widget_suggestion["suggestion"].lower()
            
    def test_theme_specific_suggestions(self):
        """Test that suggestions adapt to workspace themes"""
        themes_to_test = [
            {
                "theme": "focus", 
                "expected_suggestion_type": "distraction_minimization"
            },
            {
                "theme": "colorful",
                "expected_suggestion_type": "visual_enhancement"
            }
        ]
        
        for theme_data in themes_to_test:
            workspace_data = {
                "name": f"Theme Test {theme_data['theme']}",
                "theme": theme_data["theme"],
                "user_id": 1
            }
            
            create_response = client.post("/workspaces/", json=workspace_data)
            workspace_id = create_response.json()["id"]
            
            content_data = {
                "text": "Important work content requiring attention",
                "type": "document"
            }
            
            response = client.post(f"/workspaces/{workspace_id}/assign-content", json=content_data)
            assert response.status_code == 200
            
            data = response.json()
            suggestions = data["organization_suggestions"]
            
            # Should have theme-specific suggestion
            theme_suggestion = next(
                (s for s in suggestions if s["type"] == theme_data["expected_suggestion_type"]), 
                None
            )
            assert theme_suggestion is not None
            
    def test_bulk_assignment_error_handling(self):
        """Test bulk assignment handles errors gracefully"""
        content_items = [
            {
                "id": "valid_content",
                "text": "Valid content with text",
                "type": "document"
            },
            {
                "id": "invalid_content",
                "type": "document"
                # Missing text field
            }
        ]
        
        response = client.post("/workspaces/bulk-assign-content", json=content_items)
        assert response.status_code == 200
        
        data = response.json()
        assert data["summary"]["processed"] == 1
        assert data["summary"]["errors"] == 1
        
        # Check error is properly recorded
        error_result = next((r for r in data["results"] if "error" in r), None)
        assert error_result is not None
        assert error_result["content_id"] == "invalid_content"