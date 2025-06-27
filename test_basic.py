#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

try:
    # Test basic imports
    from src.backend.database.database import SessionLocal, init_db
    print("✅ Database imports work")
    
    # Test session creation
    db = SessionLocal()
    print("✅ Database session creation works")
    
    # Test user model import
    from src.backend.models.user import User
    print("✅ User model import works")
    
    # Test creating tables
    init_db()
    print("✅ Database initialization works")
    
    # Test creating a user manually
    from src.backend.schemas.user import UserCreate
    from src.backend.crud.crud_user import user
    
    user_data = UserCreate(
        username="testuser", 
        email="test@example.com", 
        password="password123"
    )
    
    db_user = user.create(db, obj_in=user_data)
    print(f"✅ User created successfully: {db_user.username}")
    
    db.close()
    print("✅ All basic operations work!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)