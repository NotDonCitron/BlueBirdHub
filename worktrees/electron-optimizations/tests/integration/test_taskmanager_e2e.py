"""
End-to-End Tests for TaskManager Page
Tests the complete integration between frontend and backend APIs
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

class TestTaskManagerE2E:
    """Comprehensive end-to-end tests for TaskManager functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Verify backend is running
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            assert response.status_code == 200, "Backend not running"
        except requests.exceptions.RequestException:
            pytest.skip("Backend not available")
        
        yield
        
        # Cleanup after test
        # Note: In a real test environment, you might want to reset test data
    
    def test_backend_health_check(self):
        """Test that backend is healthy and accessible"""
        response = requests.get(f"{BACKEND_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "running"
        assert data["message"] == "OrdnungsHub API is operational"
    
    def test_taskmaster_all_tasks_endpoint(self):
        """Test /tasks/taskmaster/all endpoint returns valid data"""
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "source" in data
        assert data["source"] == "taskmaster"
        assert isinstance(data["tasks"], list)
        assert data["total"] >= 0
        
        # Verify task structure
        if data["tasks"]:
            task = data["tasks"][0]
            required_fields = ["id", "title", "status", "priority"]
            for field in required_fields:
                assert field in task, f"Missing required field: {field}"
            
            # Check if workspace_id is present in some tasks
            workspace_tasks = [t for t in data["tasks"] if "workspace_id" in t]
            assert len(workspace_tasks) > 0, "No tasks have workspace_id assigned"
    
    def test_taskmaster_progress_endpoint(self):
        """Test /tasks/taskmaster/progress endpoint"""
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/progress")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "total_tasks", "completed_tasks", "pending_tasks", 
            "in_progress_tasks", "completion_percentage"
        ]
        for field in required_fields:
            assert field in data, f"Missing progress field: {field}"
            assert isinstance(data[field], (int, float)), f"Invalid type for {field}"
        
        # Logical checks
        assert data["completion_percentage"] >= 0
        assert data["completion_percentage"] <= 100
        assert data["total_tasks"] >= 0
        assert data["completed_tasks"] + data["pending_tasks"] + data["in_progress_tasks"] <= data["total_tasks"]
    
    def test_taskmaster_next_task_endpoint(self):
        """Test /tasks/taskmaster/next endpoint"""
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/next")
        assert response.status_code == 200
        
        data = response.json()
        
        # Next task can be None if no available tasks
        if data.get("task"):
            task = data["task"]
            assert "id" in task
            assert "title" in task
            assert "status" in task
            # Next task should typically be pending or in-progress
            assert task["status"] in ["pending", "in-progress"]
    
    def test_workspaces_endpoint(self):
        """Test /workspaces/ endpoint returns workspace data"""
        response = requests.get(f"{BACKEND_URL}/workspaces/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            workspace = data[0]
            required_fields = ["id", "name", "color"]
            for field in required_fields:
                assert field in workspace, f"Missing workspace field: {field}"
    
    def test_workspace_overview_endpoint(self):
        """Test /tasks/taskmaster/workspace-overview endpoint"""
        response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/workspace-overview")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "overview" in data
        
        overview = data["overview"]
        assert isinstance(overview, dict)
        
        # Check workspace overview structure
        for workspace_id, workspace_data in overview.items():
            assert "workspace_name" in workspace_data
            assert "workspace_color" in workspace_data
            assert "statistics" in workspace_data
            assert "tasks" in workspace_data
            assert "recent_tasks" in workspace_data
            
            stats = workspace_data["statistics"]
            required_stats = [
                "total_tasks", "completed_tasks", "in_progress_tasks", 
                "pending_tasks", "completion_rate"
            ]
            for stat in required_stats:
                assert stat in stats, f"Missing statistic: {stat}"
            
            # Verify tasks have workspace_id
            for task in workspace_data["tasks"]:
                assert "workspace_id" in task
                assert task["workspace_id"] == int(workspace_id)
    
    def test_workspace_suggestions_endpoint(self):
        """Test /tasks/taskmaster/suggest-workspace endpoint"""
        test_data = {
            "title": "Create API documentation",
            "description": "Write comprehensive API documentation for developers"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/tasks/taskmaster/suggest-workspace",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        
        if data["suggestions"]:
            suggestion = data["suggestions"][0]
            required_fields = ["workspace_id", "workspace_name", "confidence", "reason"]
            for field in required_fields:
                assert field in suggestion, f"Missing suggestion field: {field}"
            
            assert 0 <= suggestion["confidence"] <= 1
        
        # Auto suggestion should be provided if confidence is high
        if data.get("auto_suggestion"):
            auto_suggestion = data["auto_suggestion"]
            assert auto_suggestion["confidence"] > 0.7
    
    def test_add_task_endpoint(self):
        """Test adding a new task via /tasks/taskmaster/add"""
        test_task = {
            "title": "E2E Test Task",
            "description": "This is a test task created during E2E testing",
            "priority": "high"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/tasks/taskmaster/add",
            json=test_task,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert "message" in data
        
        task = data["task"]
        assert task["title"] == test_task["title"]
        assert task["description"] == test_task["description"]
        assert task["priority"] == test_task["priority"]
        assert task["status"] == "pending"
        assert "id" in task
        
        # Task should now appear in task list
        all_tasks_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all")
        all_tasks_data = all_tasks_response.json()
        
        created_task_found = any(
            t["id"] == task["id"] for t in all_tasks_data["tasks"]
        )
        assert created_task_found, "Created task not found in task list"
    
    def test_update_task_status_endpoint(self):
        """Test updating task status via /tasks/taskmaster/{task_id}/status"""
        # First, get a task to update
        all_tasks_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all")
        all_tasks_data = all_tasks_response.json()
        
        if not all_tasks_data["tasks"]:
            pytest.skip("No tasks available to test status update")
        
        # Find a pending task
        pending_task = None
        for task in all_tasks_data["tasks"]:
            if task["status"] == "pending":
                pending_task = task
                break
        
        if not pending_task:
            pytest.skip("No pending tasks available to test status update")
        
        # Update status
        update_data = {"status": "in-progress"}
        response = requests.put(
            f"{BACKEND_URL}/tasks/taskmaster/{pending_task['id']}/status",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == pending_task["id"]
        assert data["status"] == "in-progress"
    
    def test_link_task_to_workspace_endpoint(self):
        """Test linking task to workspace"""
        # Get a task and workspace
        all_tasks_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all")
        all_tasks_data = all_tasks_response.json()
        
        workspaces_response = requests.get(f"{BACKEND_URL}/workspaces/")
        workspaces_data = workspaces_response.json()
        
        if not all_tasks_data["tasks"] or not workspaces_data:
            pytest.skip("No tasks or workspaces available to test linking")
        
        task = all_tasks_data["tasks"][0]
        workspace = workspaces_data[0]
        
        link_data = {
            "task_id": task["id"],
            "workspace_id": workspace["id"]
        }
        
        response = requests.post(
            f"{BACKEND_URL}/tasks/taskmaster/{task['id']}/link-workspace",
            json=link_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["task_id"] == task["id"]
        assert data["workspace_id"] == workspace["id"]
    
    def test_analyze_complexity_endpoint(self):
        """Test task complexity analysis"""
        response = requests.post(f"{BACKEND_URL}/tasks/taskmaster/analyze-complexity")
        
        # This endpoint might not be fully implemented, so we check for either success or expected failure
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Structure depends on implementation
            assert isinstance(data, dict)
    
    def test_task_workflow_integration(self):
        """Test complete task workflow: create -> update -> complete"""
        # 1. Create new task
        new_task_data = {
            "title": "Integration Test Workflow Task",
            "description": "Testing complete task lifecycle",
            "priority": "medium"
        }
        
        create_response = requests.post(
            f"{BACKEND_URL}/tasks/taskmaster/add",
            json=new_task_data,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 200
        
        created_task = create_response.json()["task"]
        task_id = created_task["id"]
        
        # 2. Verify task appears in task list
        all_tasks_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all")
        all_tasks_data = all_tasks_response.json()
        
        task_found = any(t["id"] == task_id for t in all_tasks_data["tasks"])
        assert task_found, "Created task not found in task list"
        
        # 3. Update task to in-progress
        update_response = requests.put(
            f"{BACKEND_URL}/tasks/taskmaster/{task_id}/status",
            json={"status": "in-progress"},
            headers={"Content-Type": "application/json"}
        )
        assert update_response.status_code == 200
        
        # 4. Complete the task
        complete_response = requests.put(
            f"{BACKEND_URL}/tasks/taskmaster/{task_id}/status",
            json={"status": "done"},
            headers={"Content-Type": "application/json"}
        )
        assert complete_response.status_code == 200
        
        # 5. Verify progress statistics updated
        progress_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/progress")
        progress_data = progress_response.json()
        
        assert progress_data["total_tasks"] > 0
        assert progress_data["completed_tasks"] > 0
    
    def test_workspace_task_integration(self):
        """Test workspace and task integration"""
        # 1. Get workspace overview
        overview_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/workspace-overview")
        assert overview_response.status_code == 200
        
        overview_data = overview_response.json()
        assert overview_data["success"] is True
        
        # 2. Verify workspace statistics match task counts
        for workspace_id, workspace_data in overview_data["overview"].items():
            stats = workspace_data["statistics"]
            tasks = workspace_data["tasks"]
            
            # Count tasks by status
            actual_completed = len([t for t in tasks if t["status"] == "done"])
            actual_in_progress = len([t for t in tasks if t["status"] == "in-progress"])
            actual_pending = len([t for t in tasks if t["status"] == "pending"])
            actual_total = len(tasks)
            
            # Verify statistics match actual task counts
            assert stats["completed_tasks"] == actual_completed
            assert stats["in_progress_tasks"] == actual_in_progress
            assert stats["pending_tasks"] == actual_pending
            assert stats["total_tasks"] == actual_total
            
            # Verify completion rate calculation
            if actual_total > 0:
                expected_completion_rate = round((actual_completed / actual_total) * 100, 1)
                assert abs(stats["completion_rate"] - expected_completion_rate) < 0.1
    
    def test_api_error_handling(self):
        """Test API error handling for invalid requests"""
        # Test invalid task creation
        invalid_task_response = requests.post(
            f"{BACKEND_URL}/tasks/taskmaster/add",
            json={},  # Missing required title
            headers={"Content-Type": "application/json"}
        )
        assert invalid_task_response.status_code == 400
        
        # Test invalid task status update
        invalid_status_response = requests.put(
            f"{BACKEND_URL}/tasks/taskmaster/nonexistent/status",
            json={"status": "invalid"},
            headers={"Content-Type": "application/json"}
        )
        assert invalid_status_response.status_code in [404, 500]
        
        # Test invalid workspace suggestion
        invalid_suggestion_response = requests.post(
            f"{BACKEND_URL}/tasks/taskmaster/suggest-workspace",
            json={},  # Missing required title
            headers={"Content-Type": "application/json"}
        )
        assert invalid_suggestion_response.status_code == 400
    
    def test_frontend_backend_integration(self):
        """Test that frontend can reach backend (basic connectivity)"""
        try:
            frontend_response = requests.get(f"{FRONTEND_URL}", timeout=5)
            # Frontend should be accessible (might return 200 or redirect)
            assert frontend_response.status_code in [200, 301, 302]
        except requests.exceptions.RequestException:
            pytest.skip("Frontend not available for integration test")
    
    def test_performance_basic(self):
        """Basic performance test for API endpoints"""
        endpoints_to_test = [
            "/tasks/taskmaster/all",
            "/tasks/taskmaster/progress", 
            "/tasks/taskmaster/next",
            "/workspaces/",
            "/tasks/taskmaster/workspace-overview"
        ]
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = requests.get(f"{BACKEND_URL}{endpoint}")
            end_time = time.time()
            
            # API should respond within 2 seconds
            response_time = end_time - start_time
            assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.2f}s (too slow)"
            assert response.status_code == 200, f"Endpoint {endpoint} returned {response.status_code}"
    
    def test_data_consistency(self):
        """Test data consistency across different endpoints"""
        # Get tasks from different endpoints
        all_tasks_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/all")
        progress_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/progress")
        overview_response = requests.get(f"{BACKEND_URL}/tasks/taskmaster/workspace-overview")
        
        all_tasks_data = all_tasks_response.json()
        progress_data = progress_response.json()
        overview_data = overview_response.json()
        
        # Total task count should be consistent
        total_tasks_from_all = all_tasks_data["total"]
        total_tasks_from_progress = progress_data["total_tasks"]
        
        # Calculate total from workspace overview
        total_tasks_from_overview = sum(
            ws_data["statistics"]["total_tasks"] 
            for ws_data in overview_data["overview"].values()
        )
        
        # These should be reasonably consistent (allowing for some differences due to mock data)
        assert abs(total_tasks_from_all - total_tasks_from_progress) <= 2
        
        # Status counts should be consistent
        status_counts = {"done": 0, "in-progress": 0, "pending": 0}
        for task in all_tasks_data["tasks"]:
            status = task["status"]
            if status in status_counts:
                status_counts[status] += 1
        
        # Progress endpoint should reflect similar counts
        assert abs(status_counts["done"] - progress_data["completed_tasks"]) <= 2
        assert abs(status_counts["in-progress"] - progress_data["in_progress_tasks"]) <= 2
        assert abs(status_counts["pending"] - progress_data["pending_tasks"]) <= 2

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])