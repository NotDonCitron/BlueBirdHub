"""
Comprehensive tests for collaborative workspace CRUD operations
Following SPARC methodology: Specification -> Pseudocode -> Architecture -> Refinement -> Completion
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Import CRUD operations to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from backend.crud.crud_collaboration import (
    create_team, add_team_member, get_user_teams,
    share_workspace_with_user, share_workspace_with_team,
    assign_task_to_user, update_task_progress, add_task_comment,
    log_workspace_activity, get_workspace_activity,
    create_workspace_invite, accept_workspace_invite
)
from backend.models.team import (
    Team, TeamMembership, WorkspaceShare, TaskAssignment,
    WorkspaceActivity, TaskComment, WorkspaceInvite,
    TeamRole, WorkspacePermission
)
from backend.models.base import Base
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.task import Task

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_collaboration_crud.db"

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

class TestTeamCrud:
    """Test team CRUD operations"""
    
    def test_create_team(self, db_session, sample_users):
        """Test creating a new team"""
        # Specification: Create team with owner
        team_data = {
            "name": "Test Team",
            "description": "A test team",
            "max_members": 10,
            "is_public": False
        }
        
        team = create_team(db_session, team_data, sample_users[0].id)
        
        assert team.id is not None
        assert team.name == "Test Team"
        assert team.created_by == sample_users[0].id
        assert team.max_members == 10
        assert team.is_public is False
        assert team.invite_code is not None
        
        # Verify owner membership was created
        memberships = db_session.query(TeamMembership).filter_by(team_id=team.id).all()
        assert len(memberships) == 1
        assert memberships[0].role == TeamRole.OWNER
    
    def test_add_team_member(self, db_session, sample_users):
        """Test adding member to team"""
        # Create team first
        team_data = {"name": "Member Test Team", "description": "Test"}
        team = create_team(db_session, team_data, sample_users[0].id)
        
        # Add member
        membership = add_team_member(
            db_session, 
            team.id, 
            sample_users[1].id, 
            sample_users[0].id, 
            TeamRole.MEMBER
        )
        
        assert membership.team_id == team.id
        assert membership.user_id == sample_users[1].id
        assert membership.role == TeamRole.MEMBER
        assert membership.invited_by == sample_users[0].id
        assert membership.is_active is True
    
    def test_get_user_teams(self, db_session, sample_users):
        """Test getting teams for a user"""
        # Create multiple teams
        team1 = create_team(db_session, {"name": "Team 1"}, sample_users[0].id)
        team2 = create_team(db_session, {"name": "Team 2"}, sample_users[1].id)
        
        # Add user to second team
        add_team_member(db_session, team2.id, sample_users[0].id, sample_users[1].id, TeamRole.MEMBER)
        
        # Get teams for user
        teams = get_user_teams(db_session, sample_users[0].id)
        
        assert len(teams) == 2
        team_names = [team.name for team in teams]
        assert "Team 1" in team_names
        assert "Team 2" in team_names

class TestWorkspaceSharing:
    """Test workspace sharing CRUD operations"""
    
    def test_share_workspace_with_user(self, db_session, sample_users, sample_workspace):
        """Test sharing workspace with individual user"""
        permissions = ["read", "write"]
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        share = share_workspace_with_user(
            db_session,
            sample_workspace.id,
            sample_users[1].id,
            sample_users[0].id,
            permissions,
            expires_at
        )
        
        assert share.workspace_id == sample_workspace.id
        assert share.shared_with_user_id == sample_users[1].id
        assert share.shared_by == sample_users[0].id
        assert share.permissions == '["read", "write"]'
        assert share.expires_at == expires_at
        assert share.is_active is True
    
    def test_share_workspace_with_team(self, db_session, sample_users, sample_workspace):
        """Test sharing workspace with team"""
        # Create team first
        team = create_team(db_session, {"name": "Share Team"}, sample_users[0].id)
        
        permissions = ["read"]
        
        share = share_workspace_with_team(
            db_session,
            sample_workspace.id,
            team.id,
            sample_users[0].id,
            permissions
        )
        
        assert share.workspace_id == sample_workspace.id
        assert share.shared_with_team_id == team.id
        assert share.shared_by == sample_users[0].id
        assert share.permissions == '["read"]'
        assert share.is_active is True

class TestTaskAssignments:
    """Test task assignment CRUD operations"""
    
    def test_assign_task_to_user(self, db_session, sample_users, sample_task):
        """Test assigning task to user"""
        assignment = assign_task_to_user(
            db_session,
            sample_task.id,
            sample_users[1].id,
            sample_users[0].id,
            "collaborator",
            estimated_hours=8
        )
        
        assert assignment.task_id == sample_task.id
        assert assignment.assigned_to == sample_users[1].id
        assert assignment.assigned_by == sample_users[0].id
        assert assignment.role == "collaborator"
        assert assignment.estimated_hours == 8
        assert assignment.completion_percentage == 0
        assert assignment.is_active is True
    
    def test_update_task_progress(self, db_session, sample_users, sample_task):
        """Test updating task progress"""
        # Create assignment first
        assignment = assign_task_to_user(
            db_session,
            sample_task.id,
            sample_users[1].id,
            sample_users[0].id,
            "owner"
        )
        
        # Update progress
        updated_assignment = update_task_progress(
            db_session,
            sample_task.id,
            sample_users[1].id,
            75,
            actual_hours=6
        )
        
        assert updated_assignment.completion_percentage == 75
        assert updated_assignment.actual_hours == 6
        assert updated_assignment.completed_at is None  # Not 100% yet
        
        # Complete the task
        completed_assignment = update_task_progress(
            db_session,
            sample_task.id,
            sample_users[1].id,
            100
        )
        
        assert completed_assignment.completion_percentage == 100
        assert completed_assignment.completed_at is not None

class TestTaskComments:
    """Test task comment CRUD operations"""
    
    def test_add_task_comment(self, db_session, sample_users, sample_task):
        """Test adding comment to task"""
        comment = add_task_comment(
            db_session,
            sample_task.id,
            sample_users[0].id,
            "This is a test comment",
            comment_type="comment",
            mentions=[sample_users[1].id, sample_users[2].id]
        )
        
        assert comment.task_id == sample_task.id
        assert comment.user_id == sample_users[0].id
        assert comment.content == "This is a test comment"
        assert comment.comment_type == "comment"
        assert comment.mentions == f'[{sample_users[1].id}, {sample_users[2].id}]'
        assert comment.is_deleted is False
    
    def test_add_threaded_comment(self, db_session, sample_users, sample_task):
        """Test adding reply to comment"""
        # Create parent comment
        parent_comment = add_task_comment(
            db_session,
            sample_task.id,
            sample_users[0].id,
            "Parent comment"
        )
        
        # Add reply
        reply_comment = add_task_comment(
            db_session,
            sample_task.id,
            sample_users[1].id,
            "Reply to parent",
            parent_comment_id=parent_comment.id
        )
        
        assert reply_comment.parent_comment_id == parent_comment.id
        assert len(parent_comment.replies) == 1
        assert parent_comment.replies[0].content == "Reply to parent"

class TestWorkspaceActivity:
    """Test workspace activity logging"""
    
    def test_log_workspace_activity(self, db_session, sample_users, sample_workspace):
        """Test logging workspace activity"""
        activity = log_workspace_activity(
            db_session,
            sample_workspace.id,
            sample_users[0].id,
            "task_created",
            "User created a new task",
            entity_type="task",
            entity_id=123,
            metadata={"task_title": "Test Task"}
        )
        
        assert activity.workspace_id == sample_workspace.id
        assert activity.user_id == sample_users[0].id
        assert activity.action_type == "task_created"
        assert activity.action_description == "User created a new task"
        assert activity.entity_type == "task"
        assert activity.entity_id == 123
        assert activity.metadata == '{"task_title": "Test Task"}'
    
    def test_get_workspace_activity(self, db_session, sample_users, sample_workspace):
        """Test retrieving workspace activity"""
        # Log multiple activities
        for i in range(5):
            log_workspace_activity(
                db_session,
                sample_workspace.id,
                sample_users[0].id,
                f"action_{i}",
                f"Action {i} description"
            )
        
        # Get activities
        activities = get_workspace_activity(db_session, sample_workspace.id, limit=3)
        
        assert len(activities) == 3
        # Should be in reverse chronological order
        assert activities[0].action_type == "action_4"
        assert activities[1].action_type == "action_3"
        assert activities[2].action_type == "action_2"

class TestWorkspaceInvites:
    """Test workspace invitation system"""
    
    def test_create_workspace_invite(self, db_session, sample_users, sample_workspace):
        """Test creating workspace invitation"""
        invite = create_workspace_invite(
            db_session,
            sample_workspace.id,
            sample_users[0].id,
            invited_email="invite@example.com",
            permissions=["read", "write"],
            expires_in_days=7,
            message="Welcome to our workspace!"
        )
        
        assert invite.workspace_id == sample_workspace.id
        assert invite.invited_by == sample_users[0].id
        assert invite.invited_email == "invite@example.com"
        assert invite.permissions == '["read", "write"]'
        assert invite.status == "pending"
        assert invite.message == "Welcome to our workspace!"
        assert invite.invite_code is not None
        assert len(invite.invite_code) >= 10  # Should be random string
        
        # Check expiration date
        expected_expiry = datetime.utcnow() + timedelta(days=7)
        time_diff = abs((invite.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_create_invite_for_user(self, db_session, sample_users, sample_workspace):
        """Test creating invite for specific user"""
        invite = create_workspace_invite(
            db_session,
            sample_workspace.id,
            sample_users[0].id,
            invited_user_id=sample_users[1].id,
            permissions=["read"]
        )
        
        assert invite.invited_user_id == sample_users[1].id
        assert invite.invited_email is None
    
    def test_accept_workspace_invite(self, db_session, sample_users, sample_workspace):
        """Test accepting workspace invitation"""
        # Create invite
        invite = create_workspace_invite(
            db_session,
            sample_workspace.id,
            sample_users[0].id,
            invited_user_id=sample_users[1].id,
            permissions=["read", "write"]
        )
        
        # Accept invite
        share = accept_workspace_invite(db_session, invite.invite_code, sample_users[1].id)
        
        # Verify invite was accepted
        db_session.refresh(invite)
        assert invite.status == "accepted"
        assert invite.accepted_at is not None
        
        # Verify workspace share was created
        assert share.workspace_id == sample_workspace.id
        assert share.shared_with_user_id == sample_users[1].id
        assert share.permissions == '["read", "write"]'
        assert share.is_active is True

class TestIntegrationWorkflows:
    """Test complete collaboration workflows"""
    
    def test_complete_team_workflow(self, db_session, sample_users, sample_workspace, sample_task):
        """Test complete team collaboration workflow"""
        # 1. Create team
        team = create_team(
            db_session,
            {"name": "Workflow Team", "description": "Test workflow"},
            sample_users[0].id
        )
        
        # 2. Add team members
        member1 = add_team_member(db_session, team.id, sample_users[1].id, sample_users[0].id, TeamRole.ADMIN)
        member2 = add_team_member(db_session, team.id, sample_users[2].id, sample_users[0].id, TeamRole.MEMBER)
        
        # 3. Share workspace with team
        workspace_share = share_workspace_with_team(
            db_session,
            sample_workspace.id,
            team.id,
            sample_users[0].id,
            ["read", "write"]
        )
        
        # 4. Assign task to team member
        assignment = assign_task_to_user(
            db_session,
            sample_task.id,
            sample_users[1].id,
            sample_users[0].id,
            "owner"
        )
        
        # 5. Add comment
        comment = add_task_comment(
            db_session,
            sample_task.id,
            sample_users[0].id,
            "Task assigned to team",
            mentions=[sample_users[1].id]
        )
        
        # 6. Log activity
        activity = log_workspace_activity(
            db_session,
            sample_workspace.id,
            sample_users[0].id,
            "workflow_completed",
            "Completed team workflow setup"
        )
        
        # Verify complete workflow
        assert team.id is not None
        assert len(team.memberships) == 3  # Owner + 2 members
        assert workspace_share.shared_with_team_id == team.id
        assert assignment.assigned_to == sample_users[1].id
        assert comment.mentions == f'[{sample_users[1].id}]'
        assert activity.action_type == "workflow_completed"
    
    def test_invitation_workflow(self, db_session, sample_users, sample_workspace):
        """Test complete invitation workflow"""
        # 1. Create invitation
        invite = create_workspace_invite(
            db_session,
            sample_workspace.id,
            sample_users[0].id,
            invited_email="newuser@example.com",
            permissions=["read"],
            message="Join our project!"
        )
        
        # 2. Simulate new user accepting invite
        new_user = User(
            username="newuser",
            email="newuser@example.com",
            full_name="New User"
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        
        # 3. Accept invitation
        share = accept_workspace_invite(db_session, invite.invite_code, new_user.id)
        
        # 4. Log activity
        activity = log_workspace_activity(
            db_session,
            sample_workspace.id,
            new_user.id,
            "user_joined",
            "New user joined workspace via invitation"
        )
        
        # Verify workflow
        assert invite.status == "accepted"
        assert share.shared_with_user_id == new_user.id
        assert activity.action_type == "user_joined"

class TestErrorHandling:
    """Test error handling in CRUD operations"""
    
    def test_add_member_to_nonexistent_team(self, db_session, sample_users):
        """Test adding member to team that doesn't exist"""
        with pytest.raises(Exception):
            add_team_member(db_session, 99999, sample_users[0].id, sample_users[1].id, TeamRole.MEMBER)
    
    def test_share_nonexistent_workspace(self, db_session, sample_users):
        """Test sharing workspace that doesn't exist"""
        with pytest.raises(Exception):
            share_workspace_with_user(
                db_session, 99999, sample_users[0].id, sample_users[1].id, ["read"]
            )
    
    def test_assign_nonexistent_task(self, db_session, sample_users):
        """Test assigning task that doesn't exist"""
        with pytest.raises(Exception):
            assign_task_to_user(db_session, 99999, sample_users[0].id, sample_users[1].id, "owner")
    
    def test_accept_invalid_invite_code(self, db_session, sample_users):
        """Test accepting invite with invalid code"""
        result = accept_workspace_invite(db_session, "INVALID_CODE", sample_users[0].id)
        assert result is None

class TestPerformance:
    """Test performance of CRUD operations"""
    
    def test_bulk_team_operations(self, db_session, sample_users):
        """Test performance with multiple team operations"""
        # Create multiple teams
        teams = []
        for i in range(10):
            team = create_team(
                db_session,
                {"name": f"Bulk Team {i}", "description": f"Team {i}"},
                sample_users[0].id
            )
            teams.append(team)
        
        # Add members to each team
        for team in teams:
            for user in sample_users[1:4]:  # Add 3 members to each team
                add_team_member(db_session, team.id, user.id, sample_users[0].id, TeamRole.MEMBER)
        
        # Verify all operations completed
        user_teams = get_user_teams(db_session, sample_users[0].id)
        assert len(user_teams) == 10
        
        # Check team memberships
        for team in teams:
            memberships = db_session.query(TeamMembership).filter_by(team_id=team.id).count()
            assert memberships == 4  # Owner + 3 members

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])