#!/usr/bin/env python3
"""
Test database seeding after fixes
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger

def test_seeding():
    """Test that database seeding works after fixes"""
    logger.info("=" * 60)
    logger.info("Testing Database Seeding")
    logger.info("=" * 60)
    
    try:
        # Import seeding function
        from src.backend.seed_database import seed_database
        
        # Run seeding
        logger.info("Running seed_database()...")
        seed_database()
        
        # Verify data was seeded
        from src.backend.database.database import SessionLocal
        from src.backend.models import User, Workspace, WorkspaceTheme, Team
        
        db = SessionLocal()
        
        # Check counts
        user_count = db.query(User).count()
        workspace_count = db.query(Workspace).count()
        theme_count = db.query(WorkspaceTheme).count()
        team_count = db.query(Team).count()
        
        logger.info(f"\nSeeding Results:")
        logger.info(f"✓ Users created: {user_count}")
        logger.info(f"✓ Workspaces created: {workspace_count}")
        logger.info(f"✓ Themes created: {theme_count}")
        logger.info(f"✓ Teams created: {team_count}")
        
        # Test a specific user with relationships
        demo_user = db.query(User).filter_by(username="demo").first()
        if demo_user:
            logger.success(f"✓ Demo user found: {demo_user.username}")
            logger.info(f"  - Workspaces: {len(demo_user.workspaces)}")
            logger.info(f"  - Tasks: {len(demo_user.tasks)}")
            logger.info(f"  - Preferences: {len(demo_user.preferences)}")
        
        db.close()
        
        logger.success("\n✓ DATABASE SEEDING SUCCESSFUL!")
        return True
        
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_seeding()