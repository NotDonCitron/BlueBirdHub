#!/usr/bin/env python3
"""
Integration test to verify the full application setup
"""
import subprocess
import time
import requests
import sys
import os

def test_backend():
    """Test if the backend starts and responds correctly"""
    print("Starting backend test...")
    
    # Start backend
    backend_process = subprocess.Popen(
        [sys.executable, "src/backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for backend to start
    print("Waiting for backend to start...")
    time.sleep(3)
    
    try:
        # Test root endpoint
        response = requests.get("http://127.0.0.1:8000/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        print("✓ Backend root endpoint working")
        
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8000/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Backend health endpoint working")
        
        print("\n✅ Backend tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Backend test failed: {e}")
        return False
        
    finally:
        # Cleanup
        backend_process.terminate()
        backend_process.wait()

def test_project_structure():
    """Verify project structure is correct"""
    print("\nTesting project structure...")
    
    required_dirs = [
        "src/backend",
        "src/frontend", 
        "tests/unit",
        "tests/integration",
        "docs",
        "resources",
        "logs"
    ]
    
    required_files = [
        "src/backend/main.py",
        "src/frontend/main.js",
        "src/frontend/preload.js",
        "src/frontend/renderer.js",
        "src/frontend/index.html",
        "src/frontend/styles.css",
        "package.json",
        "requirements.txt"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Missing directory: {dir_path}")
            all_good = False
            
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ Missing file: {file_path}")
            all_good = False
            
    if all_good:
        print("\n✅ Project structure tests passed!")
    else:
        print("\n❌ Project structure tests failed!")
        
    return all_good

def main():
    """Run all integration tests"""
    print("=== OrdnungsHub Integration Tests ===\n")
    
    # Check if we're in the right directory
    if not os.path.exists("package.json"):
        print("❌ Error: Must run from project root directory")
        sys.exit(1)
    
    # Run tests
    structure_ok = test_project_structure()
    backend_ok = test_backend()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Project Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Backend API: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    
    if structure_ok and backend_ok:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()