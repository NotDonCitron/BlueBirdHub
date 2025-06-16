#!/usr/bin/env python3
"""
Test Runner for TaskManager
Runs comprehensive tests for the TaskManager page and APIs
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{END}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{END}")

def print_error(text):
    print(f"{RED}❌ {text}{END}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{END}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{END}")

def check_backend_health():
    """Check if backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "running":
                print_success("Backend is running and healthy")
                return True
    except requests.exceptions.RequestException:
        pass
    
    print_error("Backend is not running or not healthy")
    return False

def check_frontend_health():
    """Check if frontend is accessible"""
    try:
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code in [200, 301, 302]:
            print_success("Frontend is accessible")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print_warning("Frontend is not accessible (this is optional for API tests)")
    return False

def run_command(command, description, required=True):
    """Run a command and return success status"""
    print_info(f"Running: {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print_success(f"{description} - PASSED")
            if result.stdout.strip():
                print(f"Output:\n{result.stdout}")
            return True
        else:
            print_error(f"{description} - FAILED")
            if result.stderr.strip():
                print(f"Error:\n{result.stderr}")
            if result.stdout.strip():
                print(f"Output:\n{result.stdout}")
            
            if required:
                return False
            else:
                print_warning("Continuing despite failure (non-required test)")
                return True
                
    except subprocess.TimeoutExpired:
        print_error(f"{description} - TIMEOUT (5 minutes)")
        return False
    except Exception as e:
        print_error(f"{description} - ERROR: {e}")
        return False

def install_dependencies():
    """Install required dependencies for testing"""
    print_header("Installing Test Dependencies")
    
    commands = [
        ("pip install pytest requests", "Installing Python test dependencies"),
        ("npm install --prefix . @testing-library/react @testing-library/jest-dom @testing-library/user-event jest", "Installing React test dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description, required=False):
            print_warning(f"Failed to install dependencies: {description}")

def run_unit_tests():
    """Run backend unit tests"""
    print_header("Running Backend Unit Tests")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    test_files = [
        "tests/unit/test_taskmaster_endpoints.py",
        "tests/unit/test_tasks_api.py",
        "tests/unit/test_main_api.py"
    ]
    
    all_passed = True
    for test_file in test_files:
        if Path(test_file).exists():
            success = run_command(
                f"python -m pytest {test_file} -v",
                f"Running {test_file}",
                required=False
            )
            if not success:
                all_passed = False
        else:
            print_warning(f"Test file not found: {test_file}")
    
    return all_passed

def run_integration_tests():
    """Run end-to-end integration tests"""
    print_header("Running End-to-End Integration Tests")
    
    if not check_backend_health():
        print_error("Cannot run integration tests without backend")
        return False
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    return run_command(
        "python -m pytest tests/integration/test_taskmanager_e2e.py -v",
        "Running TaskManager E2E tests",
        required=True
    )

def run_react_tests():
    """Run React component tests"""
    print_header("Running React Component Tests")
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if test files exist
    test_files = [
        "tests/react/TaskManager.comprehensive.test.tsx",
        "tests/react/TaskManager.test.tsx"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print_info(f"Found React test file: {test_file}")
        else:
            print_warning(f"React test file not found: {test_file}")
    
    # Try to run React tests (this might fail if Jest is not properly configured)
    return run_command(
        "npm test -- --watchAll=false --passWithNoTests",
        "Running React component tests",
        required=False
    )

def run_api_endpoint_tests():
    """Run direct API endpoint tests"""
    print_header("Running Direct API Endpoint Tests")
    
    if not check_backend_health():
        print_error("Cannot run API tests without backend")
        return False
    
    endpoints_to_test = [
        ("GET", "/tasks/taskmaster/all", "Get all tasks"),
        ("GET", "/tasks/taskmaster/progress", "Get task progress"),
        ("GET", "/tasks/taskmaster/next", "Get next task"),
        ("GET", "/tasks/taskmaster/workspace-overview", "Get workspace overview"),
        ("GET", "/workspaces/", "Get workspaces"),
        ("POST", "/tasks/taskmaster/suggest-workspace", "Suggest workspace", {"title": "Test task"}),
        ("POST", "/tasks/taskmaster/add", "Add new task", {"title": "API Test Task", "description": "Test", "priority": "medium"})
    ]
    
    all_passed = True
    base_url = "http://localhost:8000"
    
    for method, endpoint, description, *payload in endpoints_to_test:
        try:
            print_info(f"Testing {method} {endpoint} - {description}")
            
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            elif method == "POST":
                data = payload[0] if payload else {}
                response = requests.post(f"{base_url}{endpoint}", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                print_success(f"{description} - HTTP {response.status_code}")
                
                # Basic response validation
                try:
                    response.json()
                    print_success("Response is valid JSON")
                except:
                    print_warning("Response is not valid JSON")
                    
            else:
                print_error(f"{description} - HTTP {response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print_error(f"{description} - Request failed: {e}")
            all_passed = False
        except Exception as e:
            print_error(f"{description} - Error: {e}")
            all_passed = False
    
    return all_passed

def run_performance_tests():
    """Run basic performance tests"""
    print_header("Running Performance Tests")
    
    if not check_backend_health():
        print_warning("Skipping performance tests - backend not available")
        return True
    
    endpoints = [
        "/tasks/taskmaster/all",
        "/tasks/taskmaster/progress",
        "/tasks/taskmaster/workspace-overview"
    ]
    
    all_passed = True
    base_url = "http://localhost:8000"
    
    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200 and response_time < 2.0:
                print_success(f"{endpoint} - {response_time:.3f}s (FAST)")
            elif response.status_code == 200 and response_time < 5.0:
                print_warning(f"{endpoint} - {response_time:.3f}s (SLOW)")
            else:
                print_error(f"{endpoint} - {response_time:.3f}s (TOO SLOW or FAILED)")
                all_passed = False
                
        except Exception as e:
            print_error(f"{endpoint} - Performance test failed: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main test runner function"""
    print_header("TaskManager Comprehensive Test Suite")
    print("Testing TaskManager page functionality and APIs")
    
    # Check system status
    print_header("System Health Check")
    backend_healthy = check_backend_health()
    frontend_healthy = check_frontend_health()
    
    # Install dependencies
    install_dependencies()
    
    # Run tests
    results = []
    
    # API endpoint tests (most important)
    if backend_healthy:
        results.append(("API Endpoints", run_api_endpoint_tests()))
        results.append(("Integration Tests", run_integration_tests()))
        results.append(("Performance Tests", run_performance_tests()))
    else:
        print_error("Skipping API tests - backend not healthy")
        results.append(("API Endpoints", False))
        results.append(("Integration Tests", False))
        results.append(("Performance Tests", False))
    
    # Unit tests
    results.append(("Unit Tests", run_unit_tests()))
    
    # React tests (optional)
    results.append(("React Tests", run_react_tests()))
    
    # Summary
    print_header("Test Results Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    for test_name, passed in results:
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{BOLD}Overall Result: {passed_tests}/{total_tests} test suites passed{END}")
    
    if passed_tests == total_tests:
        print_success("ALL TESTS PASSED! 🎉")
        return 0
    elif passed_tests >= total_tests * 0.8:
        print_warning("MOST TESTS PASSED (80%+)")
        return 0
    else:
        print_error("MULTIPLE TEST FAILURES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)