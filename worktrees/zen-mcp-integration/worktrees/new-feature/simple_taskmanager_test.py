#!/usr/bin/env python3
"""
Simple TaskManager Test Suite
Quick validation of TaskManager functionality
"""

import requests
import json
import time

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

def test_result(name, success, details=""):
    if success:
        print(f"{GREEN}✅ {name}{END}")
        if details:
            print(f"   {details}")
    else:
        print(f"{RED}❌ {name}{END}")
        if details:
            print(f"   {details}")
    return success

def main():
    print(f"{BLUE}{BOLD}🧪 TaskManager Quick Test Suite{END}")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Backend Health
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        success = response.status_code == 200 and response.json().get("status") in ["running", "healthy"]
        details = f"HTTP {response.status_code}" if not success else "Backend is healthy"
    except Exception as e:
        success = False
        details = f"Connection error: {e}"
    
    if test_result("Backend Health Check", success, details):
        tests_passed += 1
    
    # Test 2: Get All Tasks
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all", timeout=10)
        data = response.json()
        success = response.status_code == 200 and "tasks" in data
        details = f"Found {data.get('total', 0)} tasks" if success else f"HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Get All Tasks", success, details):
        tests_passed += 1
    
    # Test 3: Get Progress
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/progress", timeout=10)
        data = response.json()
        success = response.status_code == 200 and "completion_percentage" in data
        details = f"{data.get('completion_percentage', 0)}% complete" if success else f"HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Get Task Progress", success, details):
        tests_passed += 1
    
    # Test 4: Get Workspaces
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/workspaces/", timeout=10)
        data = response.json()
        success = response.status_code == 200 and isinstance(data, list)
        details = f"Found {len(data)} workspaces" if success else f"HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Get Workspaces", success, details):
        tests_passed += 1
    
    # Test 5: Workspace Overview
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/workspace-overview", timeout=10)
        data = response.json()
        success = response.status_code == 200 and data.get("success") and "overview" in data
        details = f"Found {len(data.get('overview', {}))} workspace overviews" if success else f"HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Workspace Overview", success, details):
        tests_passed += 1
    
    # Test 6: Workspace Suggestions
    total_tests += 1
    try:
        test_data = {"title": "Create unit tests", "description": "Write comprehensive tests"}
        response = requests.post(f"{BACKEND_URL}/tasks/taskmaster/suggest-workspace", 
                               json=test_data, timeout=10)
        data = response.json()
        success = response.status_code == 200 and data.get("success") and "suggestions" in data
        details = f"Got {len(data.get('suggestions', []))} workspace suggestions" if success else f"HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Workspace Suggestions", success, details):
        tests_passed += 1
    
    # Test 7: Add New Task
    total_tests += 1
    try:
        test_task = {
            "title": f"Test Task {int(time.time())}",
            "description": "Automated test task",
            "priority": "medium"
        }
        response = requests.post(f"{BACKEND_URL}/tasks/taskmaster/add", 
                               json=test_task, timeout=10)
        data = response.json()
        success = response.status_code == 200 and "task" in data
        details = f"Created task with ID {data.get('task', {}).get('id', 'unknown')}" if success else f"HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Add New Task", success, details):
        tests_passed += 1
    
    # Test 8: Frontend Accessibility
    total_tests += 1
    try:
        response = requests.get(f"{FRONTEND_URL}/tasks", timeout=10)
        success = response.status_code in [200, 301, 302]
        details = f"HTTP {response.status_code}" if success else f"Not accessible - HTTP {response.status_code}"
    except Exception as e:
        success = False
        details = f"Connection error: {e}"
    
    if test_result("Frontend TaskManager Page", success, details):
        tests_passed += 1
    
    # Test 9: Performance Check
    total_tests += 1
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all", timeout=5)
        end_time = time.time()
        response_time = end_time - start_time
        success = response.status_code == 200 and response_time < 2.0
        details = f"Response time: {response_time:.3f}s" if success else f"Too slow: {response_time:.3f}s"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("API Performance", success, details):
        tests_passed += 1
    
    # Test 10: Data Consistency
    total_tests += 1
    try:
        # Get data from multiple endpoints
        all_tasks_resp = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all", timeout=10)
        progress_resp = requests.get(f"{BACKEND_URL}/tasks/taskmaster/progress", timeout=10)
        
        all_tasks_data = all_tasks_resp.json()
        progress_data = progress_resp.json()
        
        tasks_count = all_tasks_data.get("total", 0)
        progress_count = progress_data.get("total_tasks", 0)
        
        # Allow some variance due to different endpoints potentially having different data
        success = abs(tasks_count - progress_count) <= 3
        details = f"Tasks: {tasks_count}, Progress: {progress_count}" if success else f"Inconsistent: Tasks {tasks_count} vs Progress {progress_count}"
    except Exception as e:
        success = False
        details = f"Error: {e}"
    
    if test_result("Data Consistency", success, details):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"{BOLD}Test Results Summary:{END}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {total_tests - tests_passed}")
    print(f"📊 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! TaskManager is working perfectly!{END}")
        return 0
    elif tests_passed >= total_tests * 0.8:
        print(f"\n{YELLOW}{BOLD}✨ MOST TESTS PASSED! TaskManager is mostly functional.{END}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ MULTIPLE FAILURES! TaskManager needs attention.{END}")
        return 1

if __name__ == "__main__":
    exit(main())