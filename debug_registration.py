#!/usr/bin/env python3
"""
Debug script to isolate the registration endpoint issue
"""
import sys
sys.path.append('.')

import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Try importing components one by one to identify the issue
try:
    print("1. Importing database...")
    from src.backend.database.database import init_db, get_db
    print("   ✅ Database imports successful")
    
    print("2. Importing auth services...")
    from src.backend.services.auth import (
        UserCreate, create_user, get_user, get_user_by_email,
        create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    )
    print("   ✅ Auth service imports successful")
    
    print("3. Importing models...")
    from src.backend.models.user import User
    print("   ✅ User model import successful")
    
    print("4. Testing database initialization...")
    init_db()
    print("   ✅ Database initialization successful")
    
    print("5. Testing user creation...")
    # Get a database session
    db_gen = get_db()
    db = next(db_gen)
    
    # Create test user data
    test_user = UserCreate(
        username="debug_test_user",
        email="debug@test.com",
        password="testpass123"
    )
    
    # Check if user already exists
    existing_user = get_user(db, username=test_user.username)
    if existing_user:
        print(f"   User {test_user.username} already exists, skipping creation")
    else:
        # Try to create user
        new_user = create_user(db, test_user)
        print(f"   ✅ User creation successful: {new_user.username} (ID: {new_user.id})")
    
    print("6. Testing token creation...")
    from datetime import timedelta
    access_token = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print(f"   ✅ Token creation successful: {access_token[:50]}...")
    
    print("\n🎉 All components working correctly!")
    print("The issue might be in the FastAPI route handling or middleware.")
    
except Exception as e:
    print(f"\n❌ Error encountered: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Try to identify the specific issue
    if "jose" in str(e):
        print("\n💡 Potential fix: Install python-jose")
        print("   pip install python-jose[cryptography]")
    elif "passlib" in str(e):
        print("\n💡 Potential fix: Install passlib")
        print("   pip install passlib[bcrypt]")
    elif "bcrypt" in str(e):
        print("\n💡 Potential fix: Install bcrypt")
        print("   pip install bcrypt")
    elif "database" in str(e).lower():
        print("\n💡 Potential fix: Database issue - check database file permissions")

if __name__ == "__main__":
    print("Starting registration debug test...\n")