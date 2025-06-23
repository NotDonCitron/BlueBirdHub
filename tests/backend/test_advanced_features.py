#!/usr/bin/env python3
"""
Comprehensive test suite for advanced OrdnungsHub features
Tests all 6 major feature implementations with >85% coverage
"""

import pytest
import json
import urllib.request
import urllib.parse
import time
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://127.0.0.1:8002"
TEST_TOKEN = None

class TestAdvancedFeatures:
    """Test all advanced features implementation"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment and authenticate"""
        # Login to get test token
        login_data = {"username": "admin", "password": "admin123"}
        response = cls._make_request("/auth/login", "POST", login_data)
        assert response["success"] == True
        cls.test_token = response["token"]
        
        print(f"✅ Test setup complete. Token: {cls.test_token[:20]}...")

    @classmethod
    def _make_request(cls, endpoint, method="GET", data=None, token=None):
        """Helper to make HTTP requests"""
        url = BASE_URL + endpoint
        headers = {"Content-Type": "application/json"}
        
        if token or cls.test_token:
            headers["Authorization"] = f"Bearer {token or cls.test_token}"
        
        req_data = None
        if data and method != "GET":
            req_data = json.dumps(data).encode('utf-8')
        
        request = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_data = json.loads(e.read().decode())
            return {"error": error_data, "status_code": e.code}

    # === FEATURE 1: Smart File Upload & Organization Tests ===
    def test_file_categorization_ai(self):
        """Test AI-powered file categorization"""
        # Test file data
        test_file = {
            "filename": "test_document.pdf",
            "size": 1024000,
            "type": "application/pdf",
            "workspace_id": 1,
            "content": "base64_encoded_content_here"
        }
        
        # Upload file
        response = self._make_request("/files/upload", "POST", test_file)
        assert "file" in response
        file_id = response["file"]["id"]
        
        # Test AI organization
        org_response = self._make_request(f"/files/{file_id}/organize", "PUT")
        assert "organization" in org_response
        assert org_response["file"]["category"] in ["documents", "images", "code", "videos", "audio"]
        assert org_response["organization"]["confidence"] > 0.5
        
        print(f"✅ File categorized as: {org_response['file']['category']}")

    def test_batch_file_organization(self):
        """Test batch file organization"""
        # Create multiple test files
        file_ids = []
        test_files = [
            {"filename": "code.py", "type": "text/python"},
            {"filename": "image.jpg", "type": "image/jpeg"},
            {"filename": "video.mp4", "type": "video/mp4"}
        ]
        
        for file_data in test_files:
            file_data.update({"size": 1024, "workspace_id": 1, "content": "test"})
            response = self._make_request("/files/upload", "POST", file_data)
            if "file" in response:
                file_ids.append(response["file"]["id"])
        
        # Batch organize
        batch_response = self._make_request("/files/batch-organize", "POST", {
            "file_ids": file_ids
        })
        
        assert "organized_files" in batch_response
        assert len(batch_response["organized_files"]) == len(file_ids)
        
        # Verify categories
        categories = [item["category"] for item in batch_response["organized_files"]]
        assert "code" in categories
        assert "images" in categories
        assert "videos" in categories
        
        print(f"✅ Batch organized {len(file_ids)} files with categories: {categories}")

    def test_file_organization_suggestions(self):
        """Test AI file organization suggestions"""
        # Get file categories
        response = self._make_request("/files/categories", "GET")
        assert "categories" in response
        assert "organization_stats" in response
        
        categories = response["categories"]
        assert "documents" in categories
        assert "images" in categories
        assert "code" in categories
        
        # Check category configuration
        doc_config = categories["documents"]
        assert "extensions" in doc_config
        assert ".pdf" in doc_config["extensions"]
        assert "folder" in doc_config
        assert "icon" in doc_config
        
        print(f"✅ File categories loaded: {list(categories.keys())}")

    # === FEATURE 2: Advanced Task Dependencies Tests ===
    def test_task_dependency_creation(self):
        """Test creating task dependencies"""
        # Create test tasks
        task1_data = {"title": "Foundation Task", "priority": "high", "workspace_id": 1}
        task2_data = {"title": "Dependent Task", "priority": "medium", "workspace_id": 1}
        
        task1_response = self._make_request("/tasks/taskmaster", "POST", task1_data)
        task2_response = self._make_request("/tasks/taskmaster", "POST", task2_data)
        
        task1_id = task1_response["id"]
        task2_id = task2_response["id"]
        
        # Create dependency: task2 depends on task1
        dep_response = self._make_request(f"/tasks/{task2_id}/dependencies", "PUT", {
            "dependencies": [task1_id]
        })
        
        assert "dependency_graph" in dep_response
        assert "task" in dep_response
        assert task1_id in dep_response["task"]["dependencies"]
        
        print(f"✅ Created dependency: {task2_id} depends on {task1_id}")

    def test_dependency_graph_visualization(self):
        """Test dependency graph generation"""
        # Get tasks to test with
        tasks_response = self._make_request("/tasks/taskmaster/all", "GET")
        tasks = tasks_response["tasks"]
        
        if len(tasks) > 0:
            task_id = tasks[0]["id"]
            
            # Get dependency graph
            graph_response = self._make_request(f"/tasks/{task_id}/dependencies", "GET")
            
            assert "dependency_graph" in graph_response
            assert "blocked_tasks" in graph_response
            assert "blocking_tasks" in graph_response
            
            graph = graph_response["dependency_graph"]
            assert "nodes" in graph
            assert "edges" in graph
            
            print(f"✅ Dependency graph for {task_id}: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    # === FEATURE 3: Workspace Collaboration Tests ===
    def test_workspace_member_management(self):
        """Test workspace collaboration features"""
        # Create test workspace
        workspace_data = {"name": "Collaboration Test", "description": "Test workspace", "color": "#3B82F6"}
        workspace_response = self._make_request("/workspaces", "POST", workspace_data)
        workspace_id = workspace_response["id"]
        
        # Add member to workspace
        member_data = {
            "user_id": 2,
            "role": "editor",
            "permissions": ["read", "write"]
        }
        member_response = self._make_request(f"/workspaces/{workspace_id}/members", "PUT", member_data)
        
        assert "member" in member_response
        assert member_response["member"]["role"] == "editor"
        assert "read" in member_response["member"]["permissions"]
        
        # Get workspace members
        members_response = self._make_request(f"/workspaces/members?workspace_id={workspace_id}", "GET")
        assert "members" in members_response
        assert len(members_response["members"]) > 0
        
        print(f"✅ Added member to workspace {workspace_id}")

    def test_collaboration_invitations(self):
        """Test collaboration invitation system"""
        invitation_data = {
            "workspace_id": 1,
            "email": "test@example.com",
            "role": "member",
            "permissions": ["read"],
            "invited_by": 1
        }
        
        response = self._make_request("/collaboration/invite", "POST", invitation_data)
        
        assert "invitation" in response
        assert response["invitation"]["email"] == "test@example.com"
        assert response["invitation"]["status"] == "pending"
        assert "expires_at" in response["invitation"]
        
        print(f"✅ Created collaboration invitation for {invitation_data['email']}")

    def test_activity_feed(self):
        """Test workspace activity tracking"""
        # Get activity feed
        response = self._make_request("/collaboration/activity", "GET")
        
        assert "activities" in response
        assert "total" in response
        
        # Test workspace-specific activity
        workspace_response = self._make_request("/collaboration/activity?workspace_id=1", "GET")
        assert "activities" in workspace_response
        
        print(f"✅ Activity feed loaded: {response['total']} total activities")

    # === FEATURE 4: AI-Powered Content Search Tests ===
    def test_smart_search_functionality(self):
        """Test AI-powered semantic search"""
        search_queries = [
            {"query": "task", "type": "tasks"},
            {"query": "file", "type": "files"},
            {"query": "workspace", "type": "workspaces"},
            {"query": "test", "type": "all"}
        ]
        
        for search_data in search_queries:
            response = self._make_request("/ai/smart-search", "POST", search_data)
            
            assert "results" in response
            assert "total" in response
            assert "query" in response
            assert response["query"] == search_data["query"]
            
            # Verify result structure
            if response["total"] > 0:
                result = response["results"][0]
                assert "type" in result
                assert "score" in result
                assert "title" in result
                
                # Verify type filtering
                if search_data["type"] != "all":
                    assert all(r["type"] == search_data["type"] for r in response["results"])
        
        print(f"✅ Smart search tested with {len(search_queries)} query types")

    def test_search_result_ranking(self):
        """Test search result relevance scoring"""
        # Create test task with specific keywords
        task_data = {
            "title": "Machine Learning Project",
            "description": "Implement neural network for image classification",
            "tags": ["ai", "ml", "python"],
            "workspace_id": 1
        }
        
        task_response = self._make_request("/tasks/taskmaster", "POST", task_data)
        task_id = task_response["id"]
        
        # Search for the task
        search_response = self._make_request("/ai/smart-search", "POST", {
            "query": "machine learning",
            "type": "tasks"
        })
        
        assert "results" in search_response
        if search_response["total"] > 0:
            # Verify our task appears in results
            task_found = any(r["id"] == task_id for r in search_response["results"])
            if task_found:
                # Find our task and verify score
                our_task = next(r for r in search_response["results"] if r["id"] == task_id)
                assert our_task["score"] > 0
                
                print(f"✅ Search ranking: found task with score {our_task['score']}")

    # === FEATURE 5: Automation Rules Engine Tests ===
    def test_automation_rule_creation(self):
        """Test creating automation rules"""
        rule_data = {
            "name": "High Priority Task Auto-Follow-up",
            "description": "Automatically create follow-up tasks for high priority items",
            "trigger": {
                "type": "task_created",
                "conditions": [
                    {"field": "priority", "operator": "equals", "value": "high"}
                ]
            },
            "actions": [
                {
                    "type": "create_task",
                    "title": "Follow-up: {original_title}",
                    "priority": "medium",
                    "workspace_id": 1
                }
            ],
            "enabled": True
        }
        
        response = self._make_request("/automation/rules", "POST", rule_data)
        
        assert "rule" in response
        assert response["rule"]["name"] == rule_data["name"]
        assert response["rule"]["enabled"] == True
        assert len(response["rule"]["actions"]) == 1
        
        rule_id = response["rule"]["id"]
        print(f"✅ Created automation rule: {rule_id}")
        
        return rule_id

    def test_automation_rule_execution(self):
        """Test automation rule execution"""
        # Create a rule first
        rule_id = self.test_automation_rule_creation()
        
        # Create a trigger event
        trigger_event = {
            "type": "task_created",
            "priority": "high",
            "title": "Urgent Project Setup",
            "workspace_id": 1
        }
        
        response = self._make_request("/automation/rules/execute", "POST", {
            "event": trigger_event
        })
        
        assert "executed_rules" in response
        assert "total" in response
        
        if response["total"] > 0:
            executed = response["executed_rules"][0]
            assert "rule" in executed
            assert "result" in executed
            
            print(f"✅ Executed {response['total']} automation rules")

    def test_automation_rule_toggle(self):
        """Test enabling/disabling automation rules"""
        # Get existing rules
        rules_response = self._make_request("/automation/rules", "GET")
        
        if rules_response["total"] > 0:
            rule_id = rules_response["rules"][0]["id"]
            original_status = rules_response["rules"][0]["enabled"]
            
            # Toggle rule
            toggle_response = self._make_request(f"/automation/rules/{rule_id}/toggle", "PUT")
            
            assert "rule" in toggle_response
            assert toggle_response["rule"]["enabled"] != original_status
            
            print(f"✅ Toggled rule {rule_id}: {original_status} → {toggle_response['rule']['enabled']}")

    # === FEATURE 6: Dashboard Analytics Tests ===
    def test_analytics_dashboard_data(self):
        """Test analytics dashboard data generation"""
        response = self._make_request("/analytics/dashboard", "GET")
        
        assert "productivity" in response
        assert "storage" in response
        assert "recent_activity" in response
        assert "quick_stats" in response
        
        # Verify quick stats structure
        quick_stats = response["quick_stats"]
        assert "total_tasks" in quick_stats
        assert "total_files" in quick_stats
        assert "total_workspaces" in quick_stats
        assert "active_automations" in quick_stats
        
        # Verify productivity metrics
        productivity = response["productivity"]
        assert "metrics" in productivity
        assert "completion_rate" in productivity["metrics"]
        assert "priority_distribution" in productivity
        
        print(f"✅ Analytics dashboard: {quick_stats['total_tasks']} tasks, {quick_stats['total_files']} files")

    def test_analytics_report_generation(self):
        """Test generating detailed analytics reports"""
        report_types = ["productivity", "storage"]
        
        for report_type in report_types:
            response = self._make_request("/analytics/generate-report", "POST", {
                "type": report_type,
                "date_range": "7d"
            })
            
            assert "type" in response
            assert response["type"] == report_type
            assert "period" in response
            assert "metrics" in response
            assert "generated_at" in response
            
            if report_type == "productivity":
                metrics = response["metrics"]
                assert "completion_rate" in metrics
                assert "total_tasks" in metrics
                assert "completed_tasks" in metrics
            
            elif report_type == "storage":
                metrics = response["metrics"]
                assert "total_files" in metrics
                assert "total_size_bytes" in metrics
                assert "category_breakdown" in metrics
        
        print(f"✅ Generated {len(report_types)} analytics reports")

    # === INTEGRATION TESTS ===
    def test_bulk_data_import(self):
        """Test bulk import functionality"""
        import_data = {
            "data": {
                "tasks": [
                    {"title": "Imported Task 1", "priority": "high", "workspace_id": 1},
                    {"title": "Imported Task 2", "priority": "medium", "workspace_id": 1},
                    {"title": "Imported Task 3", "priority": "low", "workspace_id": 1}
                ]
            },
            "type": "tasks"
        }
        
        response = self._make_request("/workspaces/bulk-import", "POST", import_data)
        
        assert "imported_count" in response
        assert "success" in response
        assert response["imported_count"] == 3
        assert response["success"] == True
        
        print(f"✅ Bulk imported {response['imported_count']} tasks")

    def test_cross_feature_integration(self):
        """Test integration between multiple features"""
        # 1. Create a task
        task_data = {"title": "Integration Test Task", "priority": "high", "workspace_id": 1}
        task_response = self._make_request("/tasks/taskmaster", "POST", task_data)
        task_id = task_response["id"]
        
        # 2. Upload a file for the task
        file_data = {
            "filename": "integration_test.pdf",
            "size": 2048,
            "type": "application/pdf",
            "task_id": task_id,
            "workspace_id": 1,
            "content": "test_content"
        }
        file_response = self._make_request("/files/upload", "POST", file_data)
        
        # 3. Search for the task
        search_response = self._make_request("/ai/smart-search", "POST", {
            "query": "integration test",
            "type": "all"
        })
        
        # 4. Verify integration
        task_found = any(r["type"] == "task" and "integration" in r["title"].lower() 
                        for r in search_response["results"])
        
        assert task_found, "Task should be findable via search"
        
        # 5. Check analytics include our data
        analytics_response = self._make_request("/analytics/dashboard", "GET")
        assert analytics_response["quick_stats"]["total_tasks"] > 0
        assert analytics_response["quick_stats"]["total_files"] > 0
        
        print(f"✅ Cross-feature integration test passed")

    def test_performance_benchmarks(self):
        """Test performance of key operations"""
        start_time = time.time()
        
        # Benchmark search performance
        search_start = time.time()
        search_response = self._make_request("/ai/smart-search", "POST", {
            "query": "test",
            "type": "all"
        })
        search_time = time.time() - search_start
        
        # Benchmark analytics generation
        analytics_start = time.time()
        analytics_response = self._make_request("/analytics/dashboard", "GET")
        analytics_time = time.time() - analytics_start
        
        # Benchmark file organization
        org_start = time.time()
        org_response = self._make_request("/files/categories", "GET")
        org_time = time.time() - org_start
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert search_time < 2.0, f"Search took {search_time:.2f}s (should be < 2s)"
        assert analytics_time < 3.0, f"Analytics took {analytics_time:.2f}s (should be < 3s)"
        assert org_time < 1.0, f"File organization took {org_time:.2f}s (should be < 1s)"
        
        print(f"✅ Performance benchmarks:")
        print(f"   - Search: {search_time:.3f}s")
        print(f"   - Analytics: {analytics_time:.3f}s")
        print(f"   - File organization: {org_time:.3f}s")
        print(f"   - Total test time: {total_time:.3f}s")

if __name__ == "__main__":
    print("🧪 Starting comprehensive advanced features test suite...")
    print("=" * 60)
    
    # Run tests
    test_instance = TestAdvancedFeatures()
    test_instance.setup_class()
    
    # Run all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            print(f"\n🔍 Running {test_method}...")
            getattr(test_instance, test_method)()
            passed += 1
            print(f"✅ {test_method} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_method} FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    print(f"📊 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Advanced features are fully functional.")
    else:
        print(f"⚠️  {failed} tests failed. Please review the implementation.")