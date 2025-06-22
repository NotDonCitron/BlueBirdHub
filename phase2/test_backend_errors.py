#!/usr/bin/env python3
"""
Test script to reproduce and fix backend SQLAlchemy errors
Phase 2 - Backend Implementation Testing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
import traceback

# Test 1: Reproduce Model Import Errors
def test_model_import_errors():
    """Test current model import and identify missing models"""
    logger.info("=" * 60)
    logger.info("TEST 1: Reproducing Model Import Errors")
    logger.info("=" * 60)
    
    try:
        from src.backend.database.database import Base, engine
        logger.success("✓ Database engine imported successfully")
        
        # Try to import all models mentioned in relationships
        models_to_test = [
            "User", "UserPreference", "Workspace", "Task", "Project",
            "FileMetadata", "Tag", "Supplier", "Team", "TeamMembership",
            "TaskAssignment", "WorkspaceActivity", "TaskComment"
        ]
        
        imported = []
        missing = []
        
        for model_name in models_to_test:
            try:
                # Try to import from models package
                exec(f"from src.backend.models import {model_name}")
                imported.append(model_name)
                logger.info(f"✓ Successfully imported: {model_name}")
            except ImportError as e:
                missing.append(model_name)
                logger.error(f"✗ Failed to import {model_name}: {str(e)}")
        
        logger.info(f"\nSummary: {len(imported)} imported, {len(missing)} missing")
        logger.info(f"Missing models: {missing}")
        
        return missing
        
    except Exception as e:
        logger.error(f"Error during import test: {str(e)}")
        traceback.print_exc()
        return None

# Test 2: Reproduce Database Creation Errors
def test_database_creation_errors():
    """Test database table creation with current state"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Reproducing Database Creation Errors")
    logger.info("=" * 60)
    
    try:
        from src.backend.database.database import Base, engine, init_db
        
        # Drop all tables first for clean test
        logger.info("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Try to create tables using init_db
        logger.info("Attempting to create tables with init_db()...")
        try:
            init_db()
            logger.success("✓ init_db() completed without error")
        except Exception as e:
            logger.error(f"✗ init_db() failed: {str(e)}")
            traceback.print_exc()
            
        # Check which tables were actually created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"\nTables created: {tables}")
        
        # Check for foreign key constraint errors
        logger.info("\nChecking foreign key constraints...")
        for table in tables:
            fks = inspector.get_foreign_keys(table)
            for fk in fks:
                ref_table = fk['referred_table']
                if ref_table not in tables:
                    logger.error(f"✗ Table '{table}' references missing table '{ref_table}'")
        
        return tables
        
    except Exception as e:
        logger.error(f"Error during database creation test: {str(e)}")
        traceback.print_exc()
        return []

# Test 3: Test SQLAlchemy Relationship Loading
def test_relationship_loading():
    """Test if relationships can be loaded without errors"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Testing SQLAlchemy Relationship Loading")
    logger.info("=" * 60)
    
    try:
        from src.backend.database.database import SessionLocal
        from src.backend.models import User
        
        db = SessionLocal()
        
        # Try to query users and access relationships
        logger.info("Attempting to query User model...")
        try:
            user = db.query(User).first()
            if user:
                # Try to access each relationship
                relationships = [
                    "preferences", "workspaces", "tasks", "suppliers",
                    "created_teams", "team_memberships", "task_assignments",
                    "workspace_activities", "task_comments"
                ]
                
                for rel in relationships:
                    try:
                        getattr(user, rel)
                        logger.success(f"✓ Relationship '{rel}' accessible")
                    except Exception as e:
                        logger.error(f"✗ Relationship '{rel}' failed: {str(e)}")
            else:
                logger.info("No users in database to test relationships")
                
        except Exception as e:
            logger.error(f"✗ Query failed: {str(e)}")
            traceback.print_exc()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error during relationship test: {str(e)}")
        traceback.print_exc()

# Test 4: Check Model Files
def check_model_files():
    """Check which model files actually exist"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Checking Model Files")
    logger.info("=" * 60)
    
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'models')
    
    expected_models = [
        "user.py", "workspace.py", "task.py", "file_metadata.py",
        "supplier.py", "team.py", "activity.py", "comment.py"
    ]
    
    existing = []
    missing = []
    
    for model_file in expected_models:
        file_path = os.path.join(models_dir, model_file)
        if os.path.exists(file_path):
            existing.append(model_file)
            logger.info(f"✓ Found: {model_file}")
        else:
            missing.append(model_file)
            logger.warning(f"✗ Missing: {model_file}")
    
    # Check what files are actually in the models directory
    actual_files = [f for f in os.listdir(models_dir) if f.endswith('.py')]
    logger.info(f"\nActual files in models directory: {actual_files}")
    
    return existing, missing

# Main test execution
if __name__ == "__main__":
    logger.info("Starting Backend Error Reproduction Tests")
    logger.info("=" * 80)
    
    # Run all tests
    missing_models = test_model_import_errors()
    check_model_files()
    tables = test_database_creation_errors()
    test_relationship_loading()
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Missing models need to be created or imported: {missing_models}")
    logger.info(f"Tables created: {len(tables)}")
    logger.info("\nNext steps: Create missing model files and fix imports")