"""
Comprehensive tests for collaborative workspace models
Following SPARC methodology: Specification -> Pseudocode -> Architecture -> Refinement -> Completion
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Import models to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_collaboration.db"

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
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        username="test_user",
        email="test@example.com",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_workspace(db_session, sample_user):
    """Create a sample workspace for testing"""
    workspace = Workspace(
        name="Test Workspace",
        description="A test workspace",
        user_id=sample_user.id
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)
    return workspace

@pytest.fixture
def sample_task(db_session, sample_user, sample_workspace):
    """Create a sample task for testing"""
    task = Task(
        title="Test Task",
        description="A test task",
        status="pending",
        priority="medium",
        user_id=sample_user.id,
        workspace_id=sample_workspace.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task

class TestTeamModel:
    """Test Team model functionality"""
    
    def test_team_creation(self, db_session, sample_user):
        """Test creating a new team"""
        # Specification: A team should be created with basic information
        team = Team(
            name="Test Team",
            description="A test team for collaboration",
            created_by=sample_user.id,
            max_members=10,
            is_public=False
        )
        
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        # Verification
        assert team.id is not None
        assert team.name == "Test Team"
        assert team.description == "A test team for collaboration"
        assert team.created_by == sample_user.id
        assert team.max_members == 10
        assert team.is_public is False
        assert team.is_active is True
        assert team.invite_code is not None
    
    def test_team_relationships(self, db_session, sample_user):
        """Test team relationships with memberships"""
        # Create team
        team = Team(
            name="Relationship Test Team",
            created_by=sample_user.id
        )
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        # Create membership
        membership = TeamMembership(
            team_id=team.id,
            user_id=sample_user.id,
            role=TeamRole.OWNER
        )
        db_session.add(membership)
        db_session.commit()
        
        # Test relationships
        assert len(team.memberships) == 1
        assert team.memberships[0].user_id == sample_user.id
        assert team.memberships[0].role == TeamRole.OWNER

class TestTeamMembership:
    """Test TeamMembership model functionality"""
    
    def test_membership_creation(self, db_session, sample_user):
        """Test creating team membership"""
        team = Team(name="Membership Team", created_by=sample_user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        membership = TeamMembership(
            team_id=team.id,
            user_id=sample_user.id,
            role=TeamRole.ADMIN,
            invited_by=sample_user.id
        )
        
        db_session.add(membership)
        db_session.commit()
        db_session.refresh(membership)
        
        assert membership.id is not None
        assert membership.team_id == team.id
        assert membership.user_id == sample_user.id
        assert membership.role == TeamRole.ADMIN
        assert membership.invited_by == sample_user.id
        assert membership.is_active is True
    
    def test_membership_roles(self, db_session, sample_user):
        """Test different membership roles"""
        team = Team(name="Role Test Team", created_by=sample_user.id)
        db_session.add(team)
        db_session.commit()
        
        # Test all roles
        roles = [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER]
        
        for role in roles:
            membership = TeamMembership(
                team_id=team.id,
                user_id=sample_user.id,
                role=role
            )
            db_session.add(membership)
        
        db_session.commit()
        
        # Verify roles were stored correctly
        memberships = db_session.query(TeamMembership).filter_by(team_id=team.id).all()
        stored_roles = [m.role for m in memberships]
        
        assert TeamRole.OWNER in stored_roles
        assert TeamRole.ADMIN in stored_roles
        assert TeamRole.MEMBER in stored_roles
        assert TeamRole.VIEWER in stored_roles

class TestWorkspaceShare:
    """Test WorkspaceShare model functionality"""
    
    def test_workspace_share_creation(self, db_session, sample_user, sample_workspace):
        """Test creating workspace share"""
        # Create another user to share with
        user2 = User(username="user2", email="user2@example.com")
        db_session.add(user2)
        db_session.commit()
        db_session.refresh(user2)
        
        share = WorkspaceShare(
            workspace_id=sample_workspace.id,
            shared_with_user_id=user2.id,
            permissions='["read", "write"]',
            shared_by=sample_user.id,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add(share)
        db_session.commit()
        db_session.refresh(share)
        
        assert share.id is not None
        assert share.workspace_id == sample_workspace.id
        assert share.shared_with_user_id == user2.id
        assert share.shared_by == sample_user.id
        assert share.permissions == '["read", "write"]'
        assert share.is_active is True
        assert share.expires_at is not None
    
    def test_team_workspace_share(self, db_session, sample_user, sample_workspace):
        """Test sharing workspace with team"""
        # Create team
        team = Team(name="Share Team", created_by=sample_user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        share = WorkspaceShare(
            workspace_id=sample_workspace.id,
            shared_with_team_id=team.id,
            permissions='["read"]',
            shared_by=sample_user.id
        )
        
        db_session.add(share)
        db_session.commit()
        db_session.refresh(share)
        
        assert share.shared_with_team_id == team.id
        assert share.shared_with_user_id is None
        assert share.permissions == '["read"]'

class TestTaskAssignment:
    """Test TaskAssignment model functionality"""
    
    def test_task_assignment_creation(self, db_session, sample_user, sample_task):
        """Test creating task assignment"""
        # Create assignee
        assignee = User(username="assignee", email="assignee@example.com")
        db_session.add(assignee)
        db_session.commit()
        db_session.refresh(assignee)
        
        assignment = TaskAssignment(
            task_id=sample_task.id,
            assigned_to=assignee.id,
            assigned_by=sample_user.id,
            role="collaborator",
            estimated_hours=8,
            completion_percentage=25
        )
        
        db_session.add(assignment)
        db_session.commit()
        db_session.refresh(assignment)
        
        assert assignment.id is not None
        assert assignment.task_id == sample_task.id
        assert assignment.assigned_to == assignee.id
        assert assignment.assigned_by == sample_user.id
        assert assignment.role == "collaborator"
        assert assignment.estimated_hours == 8
        assert assignment.completion_percentage == 25
        assert assignment.is_active is True
    
    def test_task_assignment_progress(self, db_session, sample_user, sample_task):
        """Test task assignment progress tracking"""
        assignee = User(username="progress_user", email="progress@example.com")
        db_session.add(assignee)
        db_session.commit()
        
        assignment = TaskAssignment(
            task_id=sample_task.id,
            assigned_to=assignee.id,
            assigned_by=sample_user.id,
            role="owner",
            completion_percentage=0
        )
        
        db_session.add(assignment)
        db_session.commit()
        
        # Update progress
        assignment.completion_percentage = 100
        assignment.completed_at = datetime.utcnow()
        assignment.actual_hours = 10
        
        db_session.commit()
        db_session.refresh(assignment)
        
        assert assignment.completion_percentage == 100
        assert assignment.completed_at is not None
        assert assignment.actual_hours == 10

class TestTaskComment:
    """Test TaskComment model functionality"""
    
    def test_comment_creation(self, db_session, sample_user, sample_task):
        """Test creating task comment"""
        comment = TaskComment(
            task_id=sample_task.id,
            user_id=sample_user.id,
            content="This is a test comment",
            comment_type="comment",
            mentions='[1, 2, 3]'
        )
        
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        assert comment.id is not None
        assert comment.task_id == sample_task.id
        assert comment.user_id == sample_user.id
        assert comment.content == "This is a test comment"
        assert comment.comment_type == "comment"
        assert comment.mentions == '[1, 2, 3]'
        assert comment.is_deleted is False
    
    def test_threaded_comments(self, db_session, sample_user, sample_task):
        """Test threaded comment functionality"""
        # Parent comment
        parent_comment = TaskComment(
            task_id=sample_task.id,
            user_id=sample_user.id,
            content="Parent comment"
        )
        db_session.add(parent_comment)
        db_session.commit()
        db_session.refresh(parent_comment)
        
        # Reply comment
        reply_comment = TaskComment(
            task_id=sample_task.id,
            user_id=sample_user.id,
            content="Reply to parent",
            parent_comment_id=parent_comment.id
        )
        db_session.add(reply_comment)
        db_session.commit()
        db_session.refresh(reply_comment)
        
        assert reply_comment.parent_comment_id == parent_comment.id
        assert len(parent_comment.replies) == 1
        assert parent_comment.replies[0].content == "Reply to parent"

class TestWorkspaceActivity:
    """Test WorkspaceActivity model functionality"""
    
    def test_activity_logging(self, db_session, sample_user, sample_workspace):
        """Test workspace activity logging"""
        activity = WorkspaceActivity(
            workspace_id=sample_workspace.id,
            user_id=sample_user.id,
            action_type="task_created",
            action_description="Created a new task",
            entity_type="task",
            entity_id=123,
            metadata='{"task_title": "Test Task"}'
        )
        
        db_session.add(activity)
        db_session.commit()
        db_session.refresh(activity)
        
        assert activity.id is not None
        assert activity.workspace_id == sample_workspace.id
        assert activity.user_id == sample_user.id
        assert activity.action_type == "task_created"
        assert activity.action_description == "Created a new task"
        assert activity.entity_type == "task"
        assert activity.entity_id == 123
        assert activity.metadata == '{"task_title": "Test Task"}'
    
    def test_activity_timestamp(self, db_session, sample_user, sample_workspace):
        """Test activity timestamp functionality"""
        before_creation = datetime.utcnow()
        
        activity = WorkspaceActivity(
            workspace_id=sample_workspace.id,
            user_id=sample_user.id,
            action_type="test_action",
            action_description="Test action"
        )
        
        db_session.add(activity)
        db_session.commit()
        db_session.refresh(activity)
        
        after_creation = datetime.utcnow()
        
        assert before_creation <= activity.created_at <= after_creation

class TestWorkspaceInvite:
    """Test WorkspaceInvite model functionality"""
    
    def test_invite_creation(self, db_session, sample_user, sample_workspace):
        """Test creating workspace invitation"""
        invite = WorkspaceInvite(
            workspace_id=sample_workspace.id,
            invited_by=sample_user.id,
            invited_email="invite@example.com",
            permissions='["read", "write"]',
            invite_code="TEST123456",
            expires_at=datetime.utcnow() + timedelta(days=7),
            message="Welcome to our workspace!"
        )
        
        db_session.add(invite)
        db_session.commit()
        db_session.refresh(invite)
        
        assert invite.id is not None
        assert invite.workspace_id == sample_workspace.id
        assert invite.invited_by == sample_user.id
        assert invite.invited_email == "invite@example.com"
        assert invite.permissions == '["read", "write"]'
        assert invite.invite_code == "TEST123456"
        assert invite.status == "pending"
        assert invite.message == "Welcome to our workspace!"
    
    def test_invite_acceptance(self, db_session, sample_user, sample_workspace):
        """Test invite acceptance workflow"""
        # Create invitee
        invitee = User(username="invitee", email="invitee@example.com")
        db_session.add(invitee)
        db_session.commit()
        db_session.refresh(invitee)
        
        invite = WorkspaceInvite(
            workspace_id=sample_workspace.id,
            invited_by=sample_user.id,
            invited_user_id=invitee.id,
            permissions='["read"]',
            invite_code="ACCEPT123",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db_session.add(invite)
        db_session.commit()
        
        # Accept invite
        invite.status = "accepted"
        invite.accepted_at = datetime.utcnow()
        
        db_session.commit()
        db_session.refresh(invite)
        
        assert invite.status == "accepted"
        assert invite.accepted_at is not None

class TestModelIntegration:
    """Test integration between different models"""
    
    def test_complete_collaboration_workflow(self, db_session, sample_user):
        """Test complete collaboration workflow"""
        # 1. Create team
        team = Team(name="Integration Team", created_by=sample_user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        # 2. Add team membership
        membership = TeamMembership(
            team_id=team.id,
            user_id=sample_user.id,
            role=TeamRole.OWNER
        )
        db_session.add(membership)
        db_session.commit()
        
        # 3. Create workspace
        workspace = Workspace(
            name="Integration Workspace",
            user_id=sample_user.id
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        
        # 4. Share workspace with team
        share = WorkspaceShare(
            workspace_id=workspace.id,
            shared_with_team_id=team.id,
            permissions='["read", "write"]',
            shared_by=sample_user.id
        )
        db_session.add(share)
        db_session.commit()
        
        # 5. Create task
        task = Task(
            title="Integration Task",
            description="Test task for integration",
            user_id=sample_user.id,
            workspace_id=workspace.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        # 6. Assign task
        assignment = TaskAssignment(
            task_id=task.id,
            assigned_to=sample_user.id,
            assigned_by=sample_user.id,
            role="owner"
        )
        db_session.add(assignment)
        db_session.commit()
        
        # 7. Add comment
        comment = TaskComment(
            task_id=task.id,
            user_id=sample_user.id,
            content="Integration test comment"
        )
        db_session.add(comment)
        db_session.commit()
        
        # 8. Log activity
        activity = WorkspaceActivity(
            workspace_id=workspace.id,
            user_id=sample_user.id,
            action_type="workflow_completed",
            action_description="Completed integration test workflow"
        )
        db_session.add(activity)
        db_session.commit()
        
        # Verify complete workflow
        assert team.id is not None
        assert len(team.memberships) == 1
        assert workspace.id is not None
        assert len(workspace.shares) == 1
        assert task.id is not None
        assert len(task.assignments) == 1
        assert len(task.comments) == 1
        assert len(workspace.activities) == 1

# Performance and stress tests
class TestModelPerformance:
    """Test model performance with larger datasets"""
    
    def test_bulk_team_creation(self, db_session, sample_user):
        """Test creating multiple teams efficiently"""
        teams = []
        for i in range(100):
            team = Team(
                name=f"Team {i}",
                description=f"Description for team {i}",
                created_by=sample_user.id
            )
            teams.append(team)
        
        db_session.add_all(teams)
        db_session.commit()
        
        # Verify all teams were created
        team_count = db_session.query(Team).count()
        assert team_count >= 100
    
    def test_bulk_task_assignments(self, db_session, sample_user, sample_task):
        """Test creating multiple task assignments"""
        # Create multiple users
        users = []
        for i in range(10):
            user = User(
                username=f"user_{i}",
                email=f"user_{i}@example.com"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Create assignments for all users
        assignments = []
        for user in users:
            assignment = TaskAssignment(
                task_id=sample_task.id,
                assigned_to=user.id,
                assigned_by=sample_user.id,
                role="collaborator"
            )
            assignments.append(assignment)
        
        db_session.add_all(assignments)
        db_session.commit()
        
        # Verify assignments
        assignment_count = db_session.query(TaskAssignment).filter_by(task_id=sample_task.id).count()
        assert assignment_count == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])