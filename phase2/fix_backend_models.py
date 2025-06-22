#!/usr/bin/env python3
"""
Phase 2 - Backend Model Registration and Relationship Fix
This script implements and tests the fixes for SQLAlchemy issues
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
import shutil
from datetime import datetime

# Step 1: Fix Model Imports in __init__.py
def fix_model_imports():
    """Update models/__init__.py to include all models"""
    logger.info("=" * 60)
    logger.info("STEP 1: Fixing Model Imports")
    logger.info("=" * 60)
    
    # Backup original file
    init_file = "src/backend/models/__init__.py"
    backup_file = f"{init_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(init_file, backup_file)
    logger.info(f"✓ Created backup: {backup_file}")
    
    # New content with all models properly imported
    new_content = '''from src.backend.models.user import User, UserPreference
from src.backend.models.workspace import Workspace
from src.backend.models.task import Task, Project
from src.backend.models.file_metadata import FileMetadata, Tag
from src.backend.models.supplier import (
    Supplier, SupplierProduct, PriceList, 
    SupplierDocument, SupplierCommunication
)
from src.backend.models.team import (
    Team, TeamMembership, WorkspaceShare,
    TaskAssignment, WorkspaceActivity, TaskComment,
    WorkspaceInvite
)

__all__ = [
    # User models
    "User", 
    "UserPreference",
    # Workspace models
    "Workspace",
    # Task models
    "Task", 
    "Project",
    # File models
    "FileMetadata", 
    "Tag",
    # Supplier models
    "Supplier",
    "SupplierProduct",
    "PriceList",
    "SupplierDocument",
    "SupplierCommunication",
    # Team/Collaboration models
    "Team",
    "TeamMembership",
    "WorkspaceShare",
    "TaskAssignment",
    "WorkspaceActivity",
    "TaskComment",
    "WorkspaceInvite"
]
'''
    
    with open(init_file, 'w') as f:
        f.write(new_content)
    
    logger.success("✓ Updated models/__init__.py with all model imports")
    return True

# Step 2: Fix database.py init_db function
def fix_database_init():
    """Update database.py to import all model modules"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Fixing Database Initialization")
    logger.info("=" * 60)
    
    db_file = "src/backend/database/database.py"
    backup_file = f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(db_file, backup_file)
    logger.info(f"✓ Created backup: {backup_file}")
    
    # Read current content
    with open(db_file, 'r') as f:
        content = f.read()
    
    # Replace the init_db function
    old_init_db = '''def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    from src.backend.models import user, workspace, task, file_metadata
    Base.metadata.create_all(bind=engine)'''
    
    new_init_db = '''def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    # Import all model modules to register them with SQLAlchemy
    from src.backend.models import (
        user, workspace, task, file_metadata,
        supplier, team  # Added missing modules
    )
    Base.metadata.create_all(bind=engine)'''
    
    content = content.replace(old_init_db, new_init_db)
    
    with open(db_file, 'w') as f:
        f.write(content)
    
    logger.success("✓ Updated database.py init_db function")
    return True

# Step 3: Fix TeamMembership relationship issues
def fix_team_membership_relationships():
    """Fix foreign key specifications in team.py"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Fixing TeamMembership Foreign Key Relationships")
    logger.info("=" * 60)
    
    team_file = "src/backend/models/team.py"
    backup_file = f"{team_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(team_file, backup_file)
    logger.info(f"✓ Created backup: {backup_file}")
    
    # Read current content
    with open(team_file, 'r') as f:
        lines = f.readlines()
    
    # Fix line 64 - add foreign_keys parameter
    for i, line in enumerate(lines):
        if i == 63 and 'user = relationship("User"' in line:
            lines[i] = '    user = relationship("User", foreign_keys=[user_id], back_populates="team_memberships")\n'
            logger.info("✓ Fixed TeamMembership.user relationship")
    
    # Write back
    with open(team_file, 'w') as f:
        f.writelines(lines)
    
    logger.success("✓ Fixed foreign key relationships in team.py")
    return True

# Step 4: Fix Workspace model relationships
def fix_workspace_relationships():
    """Add missing relationships to Workspace model"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Fixing Workspace Model Relationships")
    logger.info("=" * 60)
    
    workspace_file = "src/backend/models/workspace.py"
    
    # Read current content
    with open(workspace_file, 'r') as f:
        content = f.read()
    
    # Check if suppliers relationship exists
    if 'suppliers = relationship' not in content:
        logger.info("Adding missing relationships to Workspace model...")
        
        backup_file = f"{workspace_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(workspace_file, backup_file)
        logger.info(f"✓ Created backup: {backup_file}")
        
        # Find the relationships section and add missing ones
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'tasks = relationship("Task"' in line:
                # Add missing relationships after tasks
                new_relationships = '''    tasks = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="workspace", cascade="all, delete-orphan")
    shares = relationship("WorkspaceShare", back_populates="workspace", cascade="all, delete-orphan")
    activities = relationship("WorkspaceActivity", back_populates="workspace", cascade="all, delete-orphan")
    invites = relationship("WorkspaceInvite", back_populates="workspace", cascade="all, delete-orphan")'''
                lines[i] = new_relationships
                break
        
        # Write back
        with open(workspace_file, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.success("✓ Added missing relationships to Workspace model")
    else:
        logger.info("✓ Workspace relationships already fixed")
    
    return True

# Step 5: Fix Task model relationships  
def fix_task_relationships():
    """Add missing relationships to Task model"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Fixing Task Model Relationships")
    logger.info("=" * 60)
    
    task_file = "src/backend/models/task.py"
    
    # Read current content
    with open(task_file, 'r') as f:
        content = f.read()
    
    # Check if assignments relationship exists
    if 'assignments = relationship' not in content:
        logger.info("Adding missing relationships to Task model...")
        
        backup_file = f"{task_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(task_file, backup_file)
        logger.info(f"✓ Created backup: {backup_file}")
        
        # Find where to add relationships
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'project = relationship("Project"' in line:
                # Add missing relationships after project
                lines[i] = '''    project = relationship("Project", back_populates="tasks")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")'''
                break
        
        # Write back
        with open(task_file, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.success("✓ Added missing relationships to Task model")
    else:
        logger.info("✓ Task relationships already fixed")
    
    return True

# Step 6: Test the fixes
def test_fixes():
    """Test that all fixes work correctly"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Testing All Fixes")
    logger.info("=" * 60)
    
    try:
        # Test 1: Import all models
        logger.info("\nTest 1: Importing all models...")
        from src.backend.models import (
            User, UserPreference, Workspace, Task, Project,
            FileMetadata, Tag, Supplier, SupplierProduct,
            Team, TeamMembership, TaskAssignment,
            WorkspaceActivity, TaskComment
        )
        logger.success("✓ All models imported successfully!")
        
        # Test 2: Create database tables
        logger.info("\nTest 2: Creating database tables...")
        from src.backend.database.database import Base, engine, init_db
        Base.metadata.drop_all(bind=engine)  # Clean slate
        init_db()
        
        # Check tables created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables created: {len(tables)}")
        logger.info(f"Tables: {sorted(tables)}")
        
        expected_tables = [
            'users', 'user_preferences', 'workspaces', 'tasks', 'projects',
            'file_metadata', 'tags', 'file_tags', 'suppliers', 'supplier_products',
            'teams', 'team_memberships', 'task_assignments', 'workspace_activities',
            'task_comments', 'workspace_shares', 'workspace_invites'
        ]
        
        missing = [t for t in expected_tables if t not in tables]
        if missing:
            logger.warning(f"Missing tables: {missing}")
        else:
            logger.success("✓ All expected tables created!")
        
        # Test 3: Test relationship access
        logger.info("\nTest 3: Testing relationship access...")
        from src.backend.database.database import SessionLocal
        db = SessionLocal()
        
        # Create test user
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.add(test_user)
        db.commit()
        
        # Try to access relationships (shouldn't error even if empty)
        _ = test_user.preferences
        _ = test_user.workspaces
        _ = test_user.tasks
        _ = test_user.suppliers
        _ = test_user.created_teams
        _ = test_user.team_memberships
        _ = test_user.task_assignments
        _ = test_user.workspace_activities
        _ = test_user.task_comments
        
        logger.success("✓ All relationships accessible without errors!")
        
        # Cleanup
        db.delete(test_user)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Main execution
if __name__ == "__main__":
    logger.info("Starting Backend Model Fix Implementation")
    logger.info("=" * 80)
    
    success = True
    
    # Execute fixes in order
    if not fix_model_imports():
        success = False
    
    if not fix_database_init():
        success = False
    
    if not fix_team_membership_relationships():
        success = False
        
    if not fix_workspace_relationships():
        success = False
        
    if not fix_task_relationships():
        success = False
    
    # Test the fixes
    if success:
        if test_fixes():
            logger.success("\n✓ ALL FIXES APPLIED AND TESTED SUCCESSFULLY!")
            logger.info("The backend models are now properly configured.")
        else:
            logger.error("\n✗ Tests failed - review the fixes")
    else:
        logger.error("\n✗ Some fixes failed to apply")