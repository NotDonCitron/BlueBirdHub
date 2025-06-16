#!/usr/bin/env python3
"""
Test script to verify that all absolute imports are working correctly.
This script tests the conversion from relative to absolute imports.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test key imports to verify the conversion worked."""
    
    print("Testing absolute imports...")
    
    try:
        # Test database import
        from src.backend.database.database import Base, get_db
        print("✅ Database imports working")
        
        # Test model imports
        from src.backend.models.workspace import Workspace
        from src.backend.models.task import Task, TaskStatus
        from src.backend.models.user import User
        print("✅ Model imports working")
        
        # Test CRUD imports (skip email-dependent parts)
        from src.backend.crud.base import CRUDBase
        print("✅ CRUD base import working")
        
        # Test API imports
        from src.backend.api.workspaces_enhanced import get_workspace_template_context
        print("✅ API imports working")
        
        # Test services
        from src.backend.services.ai_service import ai_service
        print("✅ Service imports working")
        
        print("\n🎉 All absolute imports are working correctly!")
        print("✅ Successfully converted from relative imports (..module) to absolute imports (src.backend.module)")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)