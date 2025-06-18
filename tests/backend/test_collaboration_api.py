"""
Comprehensive tests for collaborative workspace API endpoints
Following SPARC methodology: Specification -> Pseudocode -> Architecture -> Refinement -> Completion
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Import API components to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from backend.api.collaboration import router as collaboration_router
from backend.models.base import Base
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.task import Task
from backend.models.team import Team, TeamMembership, TeamRole
from fastapi import FastAPI
from backend.database import get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_collaboration_api.db"

@pytest.fixture(scope="module")
def test_db():
    """Create test database engine and session"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def app(db_session):
    """Create FastAPI test app"""
    app = FastAPI()
    app.include_router(collaboration_router, prefix="/collaboration")
    
    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def mock_current_user():
    """Mock current user for authentication"""
    user = Mock()
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    return user

@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing"""
    users = []
    for i in range(5):
        user = User(
            username=f"user_{i}",
            email=f"user_{i}@example.com",
            full_name=f"User {i}"
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    
    return users

@pytest.fixture
def sample_workspace(db_session, sample_users):
    """Create a sample workspace for testing"""
    workspace = Workspace(
        name="Test Workspace",
        description="A test workspace",
        user_id=sample_users[0].id
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)
    return workspace

@pytest.fixture
def sample_task(db_session, sample_users, sample_workspace):
    """Create a sample task for testing"""
    task = Task(
        title="Test Task",
        description="A test task",
        status="pending",
        priority="medium",
        user_id=sample_users[0].id,
        workspace_id=sample_workspace.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task

@pytest.fixture
def sample_team(db_session, sample_users):
    """Create a sample team for testing"""
    team = Team(
        name="Test Team",
        description="A test team",
        created_by=sample_users[0].id,
        max_members=10,
        is_public=False
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    
    # Add owner membership
    membership = TeamMembership(
        team_id=team.id,
        user_id=sample_users[0].id,
        role=TeamRole.OWNER
    )
    db_session.add(membership)
    db_session.commit()
    
    return team

class TestTeamEndpoints:
    """Test team management API endpoints"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_create_team(self, mock_get_current_user, client, mock_current_user, sample_users):
        """Test POST /teams - Create team"""
        mock_get_current_user.return_value = mock_current_user
        
        team_data = {
            "name": "API Test Team",
            "description": "Created via API",
            "max_members": 20,
            "is_public": True
        }
        
        response = client.post("/collaboration/teams", json=team_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test Team"
        assert data["description"] == "Created via API"
        assert data["max_members"] == 20
        assert data["is_public"] is True
        assert "invite_code" in data
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_user_teams(self, mock_get_current_user, client, mock_current_user, sample_team):
        """Test GET /teams - Get user teams"""
        mock_get_current_user.return_value = mock_current_user
        
        response = client.get("/collaboration/teams")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(team["name"] == "Test Team" for team in data)
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_team_members(self, mock_get_current_user, client, mock_current_user, sample_team):
        """Test GET /teams/{team_id}/members - Get team members"""
        mock_get_current_user.return_value = mock_current_user
        
        response = client.get(f"/collaboration/teams/{sample_team.id}/members")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1  # Owner
        assert data[0]["role"] == "owner"
    
    @patch('backend.api.collaboration.get_current_user')
    def test_invite_team_member(self, mock_get_current_user, client, mock_current_user, sample_team, sample_users):
        """Test POST /teams/{team_id}/invite - Invite team member"""
        mock_get_current_user.return_value = mock_current_user
        
        invite_data = {
            "user_id": sample_users[1].id,
            "role": "member"
        }
        
        response = client.post(f"/collaboration/teams/{sample_team.id}/invite", json=invite_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["team_id"] == sample_team.id
        assert data["user_id"] == sample_users[1].id
        assert data["role"] == "member"

class TestWorkspaceEndpoints:
    """Test workspace sharing API endpoints"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_accessible_workspaces(self, mock_get_current_user, client, mock_current_user, sample_workspace):
        """Test GET /workspaces - Get accessible workspaces"""
        mock_get_current_user.return_value = mock_current_user
        
        response = client.get("/collaboration/workspaces")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item["workspace"]["name"] == "Test Workspace" for item in data)
    
    @patch('backend.api.collaboration.get_current_user')
    def test_share_workspace(self, mock_get_current_user, client, mock_current_user, sample_workspace, sample_users):
        """Test POST /workspaces/{workspace_id}/share - Share workspace"""
        mock_get_current_user.return_value = mock_current_user
        
        share_data = {
            "user_id": sample_users[1].id,
            "permissions": ["read", "write"],
            "expires_in_days": 30
        }
        
        response = client.post(f"/collaboration/workspaces/{sample_workspace.id}/share", json=share_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == sample_workspace.id
        assert data["shared_with_user_id"] == sample_users[1].id
        assert data["permissions"] == '["read", "write"]'
    
    @patch('backend.api.collaboration.get_current_user')
    def test_share_workspace_with_team(self, mock_get_current_user, client, mock_current_user, sample_workspace, sample_team):
        """Test sharing workspace with team"""
        mock_get_current_user.return_value = mock_current_user
        
        share_data = {
            "team_id": sample_team.id,
            "permissions": ["read"]
        }
        
        response = client.post(f"/collaboration/workspaces/{sample_workspace.id}/share", json=share_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == sample_workspace.id
        assert data["shared_with_team_id"] == sample_team.id
        assert data["permissions"] == '["read"]'
    
    @patch('backend.api.collaboration.get_current_user')
    def test_create_workspace_invite(self, mock_get_current_user, client, mock_current_user, sample_workspace):
        """Test POST /workspaces/{workspace_id}/invite - Create workspace invite"""
        mock_get_current_user.return_value = mock_current_user
        
        invite_data = {
            "invited_email": "newuser@example.com",
            "permissions": ["read", "write"],
            "expires_in_days": 7,
            "message": "Welcome!"
        }
        
        response = client.post(f"/collaboration/workspaces/{sample_workspace.id}/invite", json=invite_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == sample_workspace.id
        assert data["invited_email"] == "newuser@example.com"
        assert data["message"] == "Welcome!"
        assert "invite_code" in data
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_workspace_activity(self, mock_get_current_user, client, mock_current_user, sample_workspace):
        """Test GET /workspaces/{workspace_id}/activity - Get workspace activity"""
        mock_get_current_user.return_value = mock_current_user
        
        response = client.get(f"/collaboration/workspaces/{sample_workspace.id}/activity")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestTaskEndpoints:
    """Test task collaboration API endpoints"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_assign_task(self, mock_get_current_user, client, mock_current_user, sample_task, sample_users):
        """Test POST /tasks/{task_id}/assign - Assign task"""
        mock_get_current_user.return_value = mock_current_user
        
        assign_data = {
            "assigned_to": sample_users[1].id,
            "role": "collaborator",
            "estimated_hours": 8
        }
        
        response = client.post(f"/collaboration/tasks/{sample_task.id}/assign", json=assign_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == sample_task.id
        assert data["assigned_to"] == sample_users[1].id
        assert data["role"] == "collaborator"
        assert data["estimated_hours"] == 8
    
    @patch('backend.api.collaboration.get_current_user')
    def test_update_task_progress(self, mock_get_current_user, client, mock_current_user, sample_task, sample_users, db_session):
        """Test PUT /tasks/{task_id}/progress - Update task progress"""
        mock_get_current_user.return_value = mock_current_user
        
        # First assign the task
        from backend.crud.crud_collaboration import assign_task_to_user
        assign_task_to_user(db_session, sample_task.id, mock_current_user.id, mock_current_user.id, "owner")
        
        progress_data = {
            "completion_percentage": 75,
            "actual_hours": 6
        }
        
        response = client.put(f"/collaboration/tasks/{sample_task.id}/progress", json=progress_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["completion_percentage"] == 75
        assert data["actual_hours"] == 6
    
    @patch('backend.api.collaboration.get_current_user')
    def test_add_task_comment(self, mock_get_current_user, client, mock_current_user, sample_task):
        """Test POST /tasks/{task_id}/comments - Add task comment"""
        mock_get_current_user.return_value = mock_current_user
        
        comment_data = {
            "content": "This is a test comment",
            "comment_type": "comment",
            "mentions": [2, 3]
        }
        
        response = client.post(f"/collaboration/tasks/{sample_task.id}/comments", json=comment_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == sample_task.id
        assert data["content"] == "This is a test comment"
        assert data["comment_type"] == "comment"
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_task_comments(self, mock_get_current_user, client, mock_current_user, sample_task, db_session):
        """Test GET /tasks/{task_id}/comments - Get task comments"""
        mock_get_current_user.return_value = mock_current_user
        
        # Add a comment first
        from backend.crud.crud_collaboration import add_task_comment
        add_task_comment(db_session, sample_task.id, mock_current_user.id, "Test comment")
        
        response = client.get(f"/collaboration/tasks/{sample_task.id}/comments")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(comment["content"] == "Test comment" for comment in data)
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_assigned_tasks(self, mock_get_current_user, client, mock_current_user, sample_task, db_session):
        """Test GET /tasks/assigned - Get assigned tasks"""
        mock_get_current_user.return_value = mock_current_user
        
        # Assign task to current user
        from backend.crud.crud_collaboration import assign_task_to_user
        assign_task_to_user(db_session, sample_task.id, mock_current_user.id, mock_current_user.id, "owner")
        
        response = client.get("/collaboration/tasks/assigned")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item["task"]["id"] == sample_task.id for item in data)

class TestAnalyticsEndpoints:
    """Test analytics and metrics API endpoints"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_get_workspace_metrics(self, mock_get_current_user, client, mock_current_user, sample_workspace, db_session):
        """Test GET /analytics/workspace/{workspace_id}/metrics - Get workspace metrics"""
        mock_get_current_user.return_value = mock_current_user
        
        # Add some test data
        from backend.crud.crud_collaboration import log_workspace_activity
        log_workspace_activity(db_session, sample_workspace.id, mock_current_user.id, "test_action", "Test")
        
        response = client.get(f"/collaboration/analytics/workspace/{sample_workspace.id}/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_activities" in data
        assert "total_shares" in data
        assert "total_tasks" in data
        assert "activity_by_type" in data
        assert data["total_activities"] >= 1

class TestErrorHandling:
    """Test API error handling"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_create_team_invalid_data(self, mock_get_current_user, client, mock_current_user):
        """Test creating team with invalid data"""
        mock_get_current_user.return_value = mock_current_user
        
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "max_members": -1  # Negative number should fail
        }
        
        response = client.post("/collaboration/teams", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('backend.api.collaboration.get_current_user')
    def test_share_nonexistent_workspace(self, mock_get_current_user, client, mock_current_user):
        """Test sharing workspace that doesn't exist"""
        mock_get_current_user.return_value = mock_current_user
        
        share_data = {
            "user_id": 999,
            "permissions": ["read"]
        }
        
        response = client.post("/collaboration/workspaces/99999/share", json=share_data)
        
        assert response.status_code == 404  # Not found
    
    @patch('backend.api.collaboration.get_current_user')
    def test_assign_nonexistent_task(self, mock_get_current_user, client, mock_current_user):
        """Test assigning task that doesn't exist"""
        mock_get_current_user.return_value = mock_current_user
        
        assign_data = {
            "assigned_to": 1,
            "role": "collaborator"
        }
        
        response = client.post("/collaboration/tasks/99999/assign", json=assign_data)
        
        assert response.status_code == 404  # Not found
    
    @patch('backend.api.collaboration.get_current_user')
    def test_unauthorized_access(self, mock_get_current_user, client):
        """Test unauthorized access to protected endpoints"""
        mock_get_current_user.side_effect = Exception("Unauthorized")
        
        response = client.get("/collaboration/teams")
        
        assert response.status_code == 500  # Internal server error due to auth failure

class TestPermissions:
    """Test permission-based access control"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_team_owner_permissions(self, mock_get_current_user, client, mock_current_user, sample_team, sample_users):
        """Test team owner can invite members"""
        mock_get_current_user.return_value = mock_current_user
        
        invite_data = {
            "user_id": sample_users[1].id,
            "role": "member"
        }
        
        response = client.post(f"/collaboration/teams/{sample_team.id}/invite", json=invite_data)
        
        assert response.status_code == 200
    
    @patch('backend.api.collaboration.get_current_user')
    def test_workspace_sharing_permissions(self, mock_get_current_user, client, mock_current_user, sample_workspace, sample_users):
        """Test workspace owner can share workspace"""
        mock_get_current_user.return_value = mock_current_user
        
        share_data = {
            "user_id": sample_users[1].id,
            "permissions": ["read"]
        }
        
        response = client.post(f"/collaboration/workspaces/{sample_workspace.id}/share", json=share_data)
        
        assert response.status_code == 200

class TestIntegrationScenarios:
    """Test complete API integration scenarios"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_complete_collaboration_workflow(self, mock_get_current_user, client, mock_current_user, sample_workspace, sample_task, sample_users):
        """Test complete collaboration workflow via API"""
        mock_get_current_user.return_value = mock_current_user
        
        # 1. Create team
        team_data = {"name": "API Workflow Team", "description": "Test team"}
        team_response = client.post("/collaboration/teams", json=team_data)
        assert team_response.status_code == 200
        team = team_response.json()
        
        # 2. Invite team member
        invite_data = {"user_id": sample_users[1].id, "role": "member"}
        invite_response = client.post(f"/collaboration/teams/{team['id']}/invite", json=invite_data)
        assert invite_response.status_code == 200
        
        # 3. Share workspace with team
        share_data = {"team_id": team["id"], "permissions": ["read", "write"]}
        share_response = client.post(f"/collaboration/workspaces/{sample_workspace.id}/share", json=share_data)
        assert share_response.status_code == 200
        
        # 4. Assign task
        assign_data = {"assigned_to": sample_users[1].id, "role": "collaborator"}
        assign_response = client.post(f"/collaboration/tasks/{sample_task.id}/assign", json=assign_data)
        assert assign_response.status_code == 200
        
        # 5. Add comment
        comment_data = {"content": "Task assigned via API workflow", "comment_type": "comment"}
        comment_response = client.post(f"/collaboration/tasks/{sample_task.id}/comments", json=comment_data)
        assert comment_response.status_code == 200
        
        # 6. Check workspace activity
        activity_response = client.get(f"/collaboration/workspaces/{sample_workspace.id}/activity")
        assert activity_response.status_code == 200
        
        # Verify workflow completed
        assert all([
            team_response.status_code == 200,
            invite_response.status_code == 200,
            share_response.status_code == 200,
            assign_response.status_code == 200,
            comment_response.status_code == 200,
            activity_response.status_code == 200
        ])

class TestPerformance:
    """Test API performance characteristics"""
    
    @patch('backend.api.collaboration.get_current_user')
    def test_bulk_operations_performance(self, mock_get_current_user, client, mock_current_user, sample_workspace, sample_users):
        """Test API performance with multiple operations"""
        mock_get_current_user.return_value = mock_current_user
        
        # Create multiple teams
        teams = []
        for i in range(5):
            team_data = {"name": f"Perf Team {i}", "description": f"Performance test team {i}"}
            response = client.post("/collaboration/teams", json=team_data)
            assert response.status_code == 200
            teams.append(response.json())
        
        # Share workspace with all teams
        for team in teams:
            share_data = {"team_id": team["id"], "permissions": ["read"]}
            response = client.post(f"/collaboration/workspaces/{sample_workspace.id}/share", json=share_data)
            assert response.status_code == 200
        
        # Verify all shares created
        workspaces_response = client.get("/collaboration/workspaces")
        assert workspaces_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])