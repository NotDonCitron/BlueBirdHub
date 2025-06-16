import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backend.database.database import Base, get_db
from src.backend.models.user import User, UserPreference
from src.backend.models.workspace import Workspace
from src.backend.models.task import Task, Project, TaskStatus, TaskPriority
from src.backend.crud.crud_user import user as crud_user, user_preference as crud_user_preference
from src.backend.crud.crud_workspace import workspace as crud_workspace
from src.backend.crud.crud_task import task as crud_task, project as crud_project
from src.backend.schemas.user import UserCreate, UserPreferenceCreate
from src.backend.schemas.workspace import WorkspaceCreate
from src.backend.schemas.task import TaskCreate, ProjectCreate

@pytest.fixture
def db_session():
    """Create a test database session"""
    # Create a temporary SQLite database
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    os.close(db_fd)
    os.unlink(db_path)

class TestUserCRUD:
    def test_create_user(self, db_session):
        """Test creating a new user"""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        created_user = crud_user.create_user(db_session, obj_in=user_data)
        
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        assert created_user.is_active == True
        assert created_user.id is not None

    def test_get_user_by_username(self, db_session):
        """Test getting user by username"""
        # Create user first
        user_data = UserCreate(username="testuser2", email="test2@example.com")
        created_user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Retrieve user
        retrieved_user = crud_user.get_by_username(db_session, username="testuser2")
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == "testuser2"

    def test_user_preferences(self, db_session):
        """Test user preferences CRUD"""
        # Create user first
        user_data = UserCreate(username="prefuser", email="pref@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Set preference
        preference = crud_user_preference.set_preference(
            db_session,
            user_id=user.id,
            key="theme",
            value="dark"
        )
        
        assert preference.preference_key == "theme"
        assert preference.preference_value == "dark"
        assert preference.user_id == user.id
        
        # Get preference
        retrieved_pref = crud_user_preference.get_by_user_and_key(
            db_session,
            user_id=user.id,
            preference_key="theme"
        )
        
        assert retrieved_pref.preference_value == "dark"

class TestWorkspaceCRUD:
    def test_create_workspace(self, db_session):
        """Test creating a workspace"""
        # Create user first
        user_data = UserCreate(username="workspaceuser", email="ws@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Create workspace
        workspace_data = WorkspaceCreate(
            name="Test Workspace",
            description="A test workspace",
            theme="dark",
            user_id=user.id,
            is_default=True
        )
        
        workspace = crud_workspace.create(db_session, obj_in=workspace_data)
        
        assert workspace.name == "Test Workspace"
        assert workspace.theme == "dark"
        assert workspace.user_id == user.id
        assert workspace.is_default == True

    def test_get_default_workspace(self, db_session):
        """Test getting default workspace"""
        # Create user and workspace
        user_data = UserCreate(username="defaultuser", email="default@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        workspace_data = WorkspaceCreate(
            name="Default Workspace",
            user_id=user.id,
            is_default=True
        )
        workspace = crud_workspace.create(db_session, obj_in=workspace_data)
        
        # Get default workspace
        default_ws = crud_workspace.get_default_workspace(db_session, user_id=user.id)
        
        assert default_ws is not None
        assert default_ws.id == workspace.id
        assert default_ws.is_default == True

class TestTaskCRUD:
    def test_create_task(self, db_session):
        """Test creating a task"""
        # Create user first
        user_data = UserCreate(username="taskuser", email="task@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Create task
        task_data = TaskCreate(
            title="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH,
            user_id=user.id
        )
        
        task = crud_task.create(db_session, obj_in=task_data)
        
        assert task.title == "Test Task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.user_id == user.id

    def test_complete_task(self, db_session):
        """Test completing a task"""
        # Create user and task
        user_data = UserCreate(username="completeuser", email="complete@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        task_data = TaskCreate(
            title="Task to Complete",
            user_id=user.id
        )
        task = crud_task.create(db_session, obj_in=task_data)
        
        # Complete task
        completed_task = crud_task.complete_task(db_session, task_id=task.id)
        
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None

    def test_get_tasks_by_status(self, db_session):
        """Test getting tasks by status"""
        # Create user
        user_data = UserCreate(username="statususer", email="status@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Create tasks with different statuses
        task1_data = TaskCreate(title="Pending Task", user_id=user.id)
        task1 = crud_task.create(db_session, obj_in=task1_data)
        
        task2_data = TaskCreate(title="In Progress Task", user_id=user.id)
        task2 = crud_task.create(db_session, obj_in=task2_data)
        crud_task.update(db_session, db_obj=task2, obj_in={"status": TaskStatus.IN_PROGRESS})
        
        # Get pending tasks
        pending_tasks = crud_task.get_by_status(
            db_session,
            user_id=user.id,
            status=TaskStatus.PENDING
        )
        
        assert len(pending_tasks) == 1
        assert pending_tasks[0].title == "Pending Task"

class TestProjectCRUD:
    def test_create_project(self, db_session):
        """Test creating a project"""
        # Create user
        user_data = UserCreate(username="projectuser", email="project@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Create project
        project_data = ProjectCreate(
            name="Test Project",
            description="A test project",
            user_id=user.id
        )
        
        project = crud_project.create(db_session, obj_in=project_data)
        
        assert project.name == "Test Project"
        assert project.user_id == user.id
        assert project.is_active == True

    def test_get_active_projects(self, db_session):
        """Test getting active projects"""
        # Create user
        user_data = UserCreate(username="activeuser", email="active@example.com")
        user = crud_user.create_user(db_session, obj_in=user_data)
        
        # Create active and inactive projects
        active_project_data = ProjectCreate(name="Active Project", user_id=user.id)
        active_project = crud_project.create(db_session, obj_in=active_project_data)
        
        inactive_project_data = ProjectCreate(name="Inactive Project", user_id=user.id)
        inactive_project = crud_project.create(db_session, obj_in=inactive_project_data)
        crud_project.update(db_session, db_obj=inactive_project, obj_in={"is_active": False})
        
        # Get active projects
        active_projects = crud_project.get_active_projects(db_session, user_id=user.id)
        
        assert len(active_projects) == 1
        assert active_projects[0].name == "Active Project"