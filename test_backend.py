#!/usr/bin/env python3
"""
Test script to diagnose backend import issues
"""

import sys
import traceback

print("Testing backend imports...")

try:
    print("1. Testing FastAPI import...")
    from fastapi import FastAPI
    print("   ✅ FastAPI import successful")
except Exception as e:
    print(f"   ❌ FastAPI import failed: {e}")
    traceback.print_exc()

try:
    print("2. Testing basic imports...")
    import uvicorn
    from loguru import logger
    print("   ✅ Basic imports successful")
except Exception as e:
    print(f"   ❌ Basic imports failed: {e}")
    traceback.print_exc()

try:
    print("3. Testing database import...")
    from src.backend.database.database import init_db
    print("   ✅ Database import successful")
except Exception as e:
    print(f"   ❌ Database import failed: {e}")
    traceback.print_exc()

try:
    print("4. Testing API router imports...")
    from src.backend.api.ai import router as ai_router
    print("   ✅ AI router import successful")
except Exception as e:
    print(f"   ❌ AI router import failed: {e}")
    traceback.print_exc()

try:
    print("5. Testing auth router import...")
    from src.backend.routes.auth import router as auth_router
    print("   ✅ Auth router import successful")
except Exception as e:
    print(f"   ❌ Auth router import failed: {e}")
    traceback.print_exc()

try:
    print("6. Testing docs import...")
    from src.backend.docs.swagger_ui import setup_custom_swagger_ui
    print("   ✅ Docs import successful")
except Exception as e:
    print(f"   ❌ Docs import failed: {e}")
    traceback.print_exc()

try:
    print("7. Testing full main import...")
    from src.backend.main import app
    print("   ✅ Main app import successful")
    print("   🎉 All imports working!")
except Exception as e:
    print(f"   ❌ Main app import failed: {e}")
    traceback.print_exc()

print("\nTest completed!") 