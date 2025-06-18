#!/usr/bin/env python3
"""
Simple test runner for collaboration features without requiring pytest
Following SPARC methodology: Specification -> Pseudocode -> Architecture -> Refinement -> Completion
"""

import sys
import os
import traceback
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from backend.models.base import Base
    from backend.models.user import User
    from backend.models.workspace import Workspace
    from backend.models.task import Task
    from backend.models.team import (
        Team, TeamMembership, WorkspaceShare, TaskAssignment,
        WorkspaceActivity, TaskComment, WorkspaceInvite,
        TeamRole, WorkspacePermission
    )
    print("✓ Successfully imported all collaboration models")
except ImportError as e:
    print(f"✗ Failed to import collaboration models: {e}")
    sys.exit(1)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_collaboration_simple.db"

def create_test_db():
    """Create test database and session"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return TestingSessionLocal

def cleanup_test_db():
    """Cleanup test database"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)

def test_team_creation():
    """Test creating a new team"""
    print("Testing team creation...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create a user first
        user = User(
            username="test_user",
            email="test@example.com",
            full_name="Test User"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create team
        team = Team(
            name="Test Team",
            description="A test team for collaboration",
            created_by=user.id,
            max_members=10,
            is_public=False
        )
        
        session.add(team)
        session.commit()
        session.refresh(team)
        
        # Verify team creation
        assert team.id is not None
        assert team.name == "Test Team"
        assert team.description == "A test team for collaboration"
        assert team.created_by == user.id
        assert team.max_members == 10
        assert team.is_public is False
        assert team.is_active is True
        assert team.invite_code is not None
        
        print("✓ Team creation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Team creation test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_team_membership():
    """Test team membership functionality"""
    print("Testing team membership...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create users
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)
        
        # Create team
        team = Team(name="Membership Test Team", created_by=user1.id)
        session.add(team)
        session.commit()
        session.refresh(team)
        
        # Create membership
        membership = TeamMembership(
            team_id=team.id,
            user_id=user2.id,
            role=TeamRole.MEMBER,
            invited_by=user1.id
        )
        session.add(membership)
        session.commit()
        
        # Verify membership
        assert membership.id is not None
        assert membership.team_id == team.id
        assert membership.user_id == user2.id
        assert membership.role == TeamRole.MEMBER
        assert membership.invited_by == user1.id
        assert membership.is_active is True
        
        print("✓ Team membership test passed")
        return True
        
    except Exception as e:
        print(f"✗ Team membership test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_workspace_sharing():
    """Test workspace sharing functionality"""
    print("Testing workspace sharing...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create users
        user1 = User(username="owner", email="owner@example.com")
        user2 = User(username="collaborator", email="collaborator@example.com")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)
        
        # Create workspace
        workspace = Workspace(
            name="Test Workspace",
            description="A test workspace",
            user_id=user1.id
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        
        # Share workspace
        share = WorkspaceShare(
            workspace_id=workspace.id,
            shared_with_user_id=user2.id,
            permissions='["read", "write"]',
            shared_by=user1.id,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        session.add(share)
        session.commit()
        
        # Verify sharing
        assert share.id is not None
        assert share.workspace_id == workspace.id
        assert share.shared_with_user_id == user2.id
        assert share.shared_by == user1.id
        assert share.permissions == '["read", "write"]'
        assert share.is_active is True
        assert share.expires_at is not None
        
        print("✓ Workspace sharing test passed")
        return True
        
    except Exception as e:
        print(f"✗ Workspace sharing test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_task_assignment():
    """Test task assignment functionality"""
    print("Testing task assignment...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create users
        user1 = User(username="assigner", email="assigner@example.com")
        user2 = User(username="assignee", email="assignee@example.com")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)
        
        # Create workspace
        workspace = Workspace(name="Test Workspace", user_id=user1.id)
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        
        # Create task
        task = Task(
            title="Test Task",
            description="A test task",
            status="pending",
            priority="medium",
            user_id=user1.id,
            workspace_id=workspace.id
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Create assignment
        assignment = TaskAssignment(
            task_id=task.id,
            assigned_to=user2.id,
            assigned_by=user1.id,
            role="collaborator",
            estimated_hours=8,
            completion_percentage=25
        )
        session.add(assignment)
        session.commit()
        
        # Verify assignment
        assert assignment.id is not None
        assert assignment.task_id == task.id
        assert assignment.assigned_to == user2.id
        assert assignment.assigned_by == user1.id
        assert assignment.role == "collaborator"
        assert assignment.estimated_hours == 8
        assert assignment.completion_percentage == 25
        assert assignment.is_active is True
        
        print("✓ Task assignment test passed")
        return True
        
    except Exception as e:
        print(f"✗ Task assignment test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_task_comments():
    """Test task comments functionality"""
    print("Testing task comments...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create user
        user = User(username="commenter", email="commenter@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create workspace
        workspace = Workspace(name="Test Workspace", user_id=user.id)
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        
        # Create task
        task = Task(
            title="Test Task",
            description="A test task",
            user_id=user.id,
            workspace_id=workspace.id
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Create comment
        comment = TaskComment(
            task_id=task.id,
            user_id=user.id,
            content="This is a test comment",
            comment_type="comment",
            mentions='[1, 2, 3]'
        )
        session.add(comment)
        session.commit()
        
        # Verify comment
        assert comment.id is not None
        assert comment.task_id == task.id
        assert comment.user_id == user.id
        assert comment.content == "This is a test comment"
        assert comment.comment_type == "comment"
        assert comment.mentions == '[1, 2, 3]'
        assert comment.is_deleted is False
        
        print("✓ Task comments test passed")
        return True
        
    except Exception as e:
        print(f"✗ Task comments test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_workspace_activity():
    """Test workspace activity logging"""
    print("Testing workspace activity...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create user
        user = User(username="activity_user", email="activity@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create workspace
        workspace = Workspace(name="Activity Workspace", user_id=user.id)
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        
        # Create activity
        activity = WorkspaceActivity(
            workspace_id=workspace.id,
            user_id=user.id,
            action_type="task_created",
            action_description="Created a new task",
            entity_type="task",
            entity_id=123,
            metadata='{"task_title": "Test Task"}'
        )
        session.add(activity)
        session.commit()
        
        # Verify activity
        assert activity.id is not None
        assert activity.workspace_id == workspace.id
        assert activity.user_id == user.id
        assert activity.action_type == "task_created"
        assert activity.action_description == "Created a new task"
        assert activity.entity_type == "task"
        assert activity.entity_id == 123
        assert activity.metadata == '{"task_title": "Test Task"}'
        
        print("✓ Workspace activity test passed")
        return True
        
    except Exception as e:
        print(f"✗ Workspace activity test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_workspace_invites():
    """Test workspace invitation system"""
    print("Testing workspace invites...")
    
    SessionLocal = create_test_db()
    session = SessionLocal()
    
    try:
        # Create user
        user = User(username="inviter", email="inviter@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create workspace
        workspace = Workspace(name="Invite Workspace", user_id=user.id)
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        
        # Create invite
        invite = WorkspaceInvite(
            workspace_id=workspace.id,
            invited_by=user.id,
            invited_email="invite@example.com",
            permissions='["read", "write"]',
            invite_code="TEST123456",
            expires_at=datetime.utcnow() + timedelta(days=7),
            message="Welcome to our workspace!"
        )
        session.add(invite)
        session.commit()
        
        # Verify invite
        assert invite.id is not None
        assert invite.workspace_id == workspace.id
        assert invite.invited_by == user.id
        assert invite.invited_email == "invite@example.com"
        assert invite.permissions == '["read", "write"]'
        assert invite.invite_code == "TEST123456"
        assert invite.status == "pending"
        assert invite.message == "Welcome to our workspace!"
        
        print("✓ Workspace invites test passed")
        return True
        
    except Exception as e:
        print(f"✗ Workspace invites test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        session.close()

def run_all_tests():
    """Run all collaboration tests"""
    print("🚀 Starting Collaboration Features Test Suite")
    print("=" * 60)
    
    tests = [
        test_team_creation,
        test_team_membership,
        test_workspace_sharing,
        test_task_assignment,
        test_task_comments,
        test_workspace_activity,
        test_workspace_invites,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        print()
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with exception: {e}")
            failed += 1
        
        # Cleanup between tests
        try:
            cleanup_test_db()
        except:
            pass
    
    print()
    print("=" * 60)
    print(f"📊 Test Results Summary:")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("🎉 All collaboration tests passed successfully!")
        print("🤝 Collaborative workspace management features are working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)