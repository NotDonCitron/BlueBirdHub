"""
Database seeding script for OrdnungsHub
Creates initial data for development and testing
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from database.database import SessionLocal, init_db
from models.user import User, UserPreference
from models.workspace import Workspace, WorkspaceTheme
from models.task import Task, Project, TaskStatus, TaskPriority
from models.file_metadata import Tag
from crud.crud_user import user as crud_user
from crud.crud_workspace import workspace as crud_workspace
from crud.crud_task import task as crud_task, project as crud_project
from schemas.user import UserCreate
from schemas.workspace import WorkspaceCreate
from schemas.task import TaskCreate, ProjectCreate

def create_default_themes(db: Session):
    """Create default workspace themes"""
    themes = [
        {
            "name": "modern_light",
            "display_name": "Modern Light",
            "description": "Clean and modern light theme",
            "primary_color": "#2563eb",
            "secondary_color": "#64748b",
            "accent_color": "#3b82f6",
            "background_color": "#ffffff",
            "text_color": "#1e293b",
            "is_dark_mode": False,
            "is_system": True
        },
        {
            "name": "modern_dark",
            "display_name": "Modern Dark",
            "description": "Sleek dark theme for night work",
            "primary_color": "#3b82f6",
            "secondary_color": "#94a3b8",
            "accent_color": "#60a5fa",
            "background_color": "#0f172a",
            "text_color": "#f1f5f9",
            "is_dark_mode": True,
            "is_system": True
        },
        {
            "name": "forest",
            "display_name": "Forest",
            "description": "Calming green theme inspired by nature",
            "primary_color": "#059669",
            "secondary_color": "#6b7280",
            "accent_color": "#10b981",
            "background_color": "#f0fdf4",
            "text_color": "#065f46",
            "is_dark_mode": False,
            "is_system": True
        },
        {
            "name": "sunset",
            "display_name": "Sunset",
            "description": "Warm orange and pink sunset theme",
            "primary_color": "#ea580c",
            "secondary_color": "#78716c",
            "accent_color": "#f97316",
            "background_color": "#fff7ed",
            "text_color": "#9a3412",
            "is_dark_mode": False,
            "is_system": True
        }
    ]
    
    for theme_data in themes:
        existing_theme = db.query(WorkspaceTheme).filter(
            WorkspaceTheme.name == theme_data["name"]
        ).first()
        
        if not existing_theme:
            theme = WorkspaceTheme(**theme_data)
            db.add(theme)
    
    db.commit()

def create_default_tags(db: Session):
    """Create default system tags"""
    tags = [
        {"name": "work", "color": "#3b82f6", "is_system": True},
        {"name": "personal", "color": "#10b981", "is_system": True},
        {"name": "important", "color": "#ef4444", "is_system": True},
        {"name": "archive", "color": "#6b7280", "is_system": True},
        {"name": "project", "color": "#8b5cf6", "is_system": True},
        {"name": "document", "color": "#f59e0b", "is_system": True},
        {"name": "image", "color": "#ec4899", "is_system": True},
        {"name": "code", "color": "#06b6d4", "is_system": True},
        {"name": "media", "color": "#84cc16", "is_system": True},
        {"name": "reference", "color": "#64748b", "is_system": True}
    ]
    
    for tag_data in tags:
        existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
        if not existing_tag:
            tag = Tag(**tag_data)
            db.add(tag)
    
    db.commit()

def create_demo_user(db: Session) -> User:
    """Create a demo user for development"""
    # Check if demo user already exists
    existing_user = crud_user.get_by_username(db, username="demo")
    if existing_user:
        return existing_user
    
    # Create demo user
    user_data = UserCreate(
        username="demo",
        email="demo@example.com",
        is_active=True
    )
    demo_user = crud_user.create(db, obj_in=user_data)
    
    # Create user preferences
    preferences = [
        {"preference_key": "theme", "preference_value": "modern_light"},
        {"preference_key": "sidebar_collapsed", "preference_value": False},
        {"preference_key": "notifications_enabled", "preference_value": True},
        {"preference_key": "auto_organize", "preference_value": True},
        {"preference_key": "ai_suggestions", "preference_value": True}
    ]
    
    for pref in preferences:
        user_pref = UserPreference(
            user_id=demo_user.id,
            preference_key=pref["preference_key"],
            preference_value=pref["preference_value"]
        )
        db.add(user_pref)
    
    db.commit()
    return demo_user

def create_demo_workspaces(db: Session, user: User):
    """Create demo workspaces"""
    workspaces_data = [
        {
            "name": "Personal Organization",
            "description": "My personal files and tasks organization workspace",
            "theme": "modern_light",
            "is_default": True,
            "icon": "🏠",
            "color": "#3b82f6",
            "layout_config": {
                "widgets": ["files", "tasks", "calendar"],
                "layout": "grid"
            }
        },
        {
            "name": "Work Projects",
            "description": "Professional work and project management",
            "theme": "modern_dark",
            "is_default": False,
            "icon": "💼",
            "color": "#059669",
            "layout_config": {
                "widgets": ["projects", "tasks", "files"],
                "layout": "sidebar"
            }
        },
        {
            "name": "Learning & Research",
            "description": "Educational materials and research workspace",
            "theme": "forest",
            "is_default": False,
            "icon": "📚",
            "color": "#8b5cf6",
            "layout_config": {
                "widgets": ["notes", "files", "bookmarks"],
                "layout": "column"
            }
        }
    ]
    
    for ws_data in workspaces_data:
        ws_data["user_id"] = user.id
        workspace_create = WorkspaceCreate(**ws_data)
        workspace = crud_workspace.create(db, obj_in=workspace_create)
        
        # Mark as accessed recently
        workspace.last_accessed_at = datetime.utcnow() - timedelta(
            days=random.randint(0, 7)
        )
        db.add(workspace)
    
    db.commit()

def create_demo_projects_and_tasks(db: Session, user: User):
    """Create demo projects and tasks"""
    # Get workspaces
    workspaces = crud_workspace.get_by_user(db, user_id=user.id)
    work_workspace = next((ws for ws in workspaces if "Work" in ws.name), workspaces[0])
    
    # Create projects
    projects_data = [
        {
            "name": "OrdnungsHub Development",
            "description": "AI-powered file organization application",
            "color": "#3b82f6",
            "is_active": True,
            "start_date": datetime.utcnow() - timedelta(days=30)
        },
        {
            "name": "Home Organization",
            "description": "Organize and digitize home documents",
            "color": "#10b981",
            "is_active": True,
            "start_date": datetime.utcnow() - timedelta(days=14)
        }
    ]
    
    created_projects = []
    for proj_data in projects_data:
        proj_data["user_id"] = user.id
        # Convert datetime objects to avoid serialization issues
        if "start_date" in proj_data:
            proj_data["start_date"] = proj_data["start_date"]
        project_create = ProjectCreate(**proj_data)
        project = crud_project.create(db, obj_in=project_create)
        created_projects.append(project)
    
    # Create tasks
    tasks_data = [
        # OrdnungsHub Development tasks
        {
            "title": "Implement file scanning algorithm",
            "description": "Create efficient file system scanning with metadata extraction",
            "status": TaskStatus.COMPLETED,
            "priority": TaskPriority.HIGH,
            "project_id": created_projects[0].id,
            "workspace_id": work_workspace.id,
            "estimated_hours": 8,
            "actual_hours": 6,
            "completed_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "title": "Design AI categorization system",
            "description": "Implement machine learning for automatic file categorization",
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.HIGH,
            "project_id": created_projects[0].id,
            "workspace_id": work_workspace.id,
            "estimated_hours": 12,
            "due_date": datetime.utcnow() + timedelta(days=7)
        },
        {
            "title": "Create user interface",
            "description": "Build React-based user interface for file management",
            "status": TaskStatus.PENDING,
            "priority": TaskPriority.MEDIUM,
            "project_id": created_projects[0].id,
            "workspace_id": work_workspace.id,
            "estimated_hours": 16,
            "due_date": datetime.utcnow() + timedelta(days=14)
        },
        # Home Organization tasks
        {
            "title": "Scan important documents",
            "description": "Digitize birth certificates, passports, and insurance documents",
            "status": TaskStatus.COMPLETED,
            "priority": TaskPriority.HIGH,
            "project_id": created_projects[1].id,
            "workspace_id": workspaces[0].id,
            "completed_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "title": "Organize photo collection",
            "description": "Sort and tag family photos by date and event",
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.MEDIUM,
            "project_id": created_projects[1].id,
            "workspace_id": workspaces[0].id,
            "due_date": datetime.utcnow() + timedelta(days=10)
        },
        # General tasks
        {
            "title": "Review monthly expenses",
            "description": "Analyze spending patterns and update budget",
            "status": TaskStatus.PENDING,
            "priority": TaskPriority.MEDIUM,
            "workspace_id": workspaces[0].id,
            "due_date": datetime.utcnow() + timedelta(days=3)
        }
    ]
    
    for task_data in tasks_data:
        task_data["user_id"] = user.id
        task_create = TaskCreate(**task_data)
        crud_task.create(db, obj_in=task_create)
    
    db.commit()

def seed_database():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    # Initialize database
    init_db()
    
    # Get database session
    db = SessionLocal()
    
    try:
        print("📚 Creating default themes...")
        create_default_themes(db)
        
        print("🏷️  Creating default tags...")
        create_default_tags(db)
        
        print("👤 Creating demo user...")
        demo_user = create_demo_user(db)
        
        print("🏠 Creating demo workspaces...")
        create_demo_workspaces(db, demo_user)
        
        print("📋 Creating demo projects and tasks...")
        create_demo_projects_and_tasks(db, demo_user)
        
        print("✅ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()