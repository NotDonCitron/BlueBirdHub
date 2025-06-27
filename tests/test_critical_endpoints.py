"""
Critical API Endpoints Test Suite
Tests the most important API endpoints for functionality and security
"""
import pytest
import requests
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TestConfig:
    """Test configuration"""
    base_url: str = "http://localhost:8888"  # Test server
    timeout: int = 10
    max_retries: int = 3

@dataclass
class TestUser:
    """Test user credentials"""
    username: str = "testuser"
    email: str = "test@example.com"
    password: str = "testpass123"

class TestCriticalEndpoints:
    """Test suite for critical API endpoints"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        cls.config = TestConfig()
        cls.test_user = TestUser()
        cls.access_token: Optional[str] = None
        cls.workspace_id: Optional[int] = None
        cls.task_id: Optional[int] = None
        
        # Wait for server to be ready
        cls._wait_for_server()
    
    @classmethod
    def _wait_for_server(cls, max_wait: int = 30) -> bool:
        """Wait for test server to be ready"""
        for _ in range(max_wait):
            try:
                response = requests.get(f"{cls.config.base_url}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        pytest.fail("Test server not available")
        return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    pytest.fail(f"Request failed after {self.config.max_retries} attempts: {e}")
                time.sleep(1)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.access_token:
            pytest.fail("No access token available. Login first.")
        
        return {"Authorization": f"Bearer {self.access_token}"}

    # =====================
    # HEALTH CHECK TESTS
    # =====================
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self._make_request("GET", "/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    # =====================
    # AUTHENTICATION TESTS
    # =====================
    
    def test_user_registration(self):
        """Test user registration"""
        # Use unique username to avoid conflicts
        import time
        unique_suffix = str(int(time.time()))
        user_data = {
            "username": f"{self.test_user.username}_{unique_suffix}",
            "email": f"test_{unique_suffix}@example.com",
            "password": self.test_user.password
        }
        
        response = self._make_request(
            "POST", 
            "/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Debug output for failed registration
        if response.status_code not in [201, 400]:
            print(f"Registration failed with status {response.status_code}")
            print(f"Response: {response.text}")
        
        # Allow 201 (created) or 400 (user already exists)
        assert response.status_code in [201, 400]
        
        if response.status_code == 201:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
    
    def test_user_login(self):
        """Test user login and JWT token generation"""
        login_data = {
            "username": self.test_user.username,
            "password": self.test_user.password
        }
        
        response = self._make_request(
            "POST",
            "/auth/login-json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Store token for subsequent tests
        self.__class__.access_token = data["access_token"]
        
        # Verify token is valid JWT format
        import base64
        try:
            # JWT has 3 parts separated by dots
            parts = data["access_token"].split(".")
            assert len(parts) == 3
            
            # Decode header (first part)
            header = json.loads(base64.b64decode(parts[0] + "=="))
            assert "alg" in header
            assert "typ" in header
            assert header["typ"] == "JWT"
        except Exception as e:
            pytest.fail(f"Invalid JWT token format: {e}")
    
    def test_get_current_user(self):
        """Test getting current user info with JWT"""
        if not self.access_token:
            self.test_user_login()
        
        response = self._make_request(
            "GET",
            "/auth/me",
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert data["username"] == self.test_user.username
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = self._make_request(
            "POST",
            "/auth/login-json",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [401, 422]  # Unauthorized or validation error
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = self._make_request("GET", "/auth/me")
        
        assert response.status_code == 401  # Unauthorized
    
    def test_invalid_token_access(self):
        """Test accessing protected endpoint with invalid token"""
        response = self._make_request(
            "GET",
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401  # Unauthorized

    # =====================
    # WORKSPACE TESTS
    # =====================
    
    def test_get_workspaces(self):
        """Test getting user workspaces"""
        if not self.access_token:
            self.test_user_login()
        
        response = self._make_request(
            "GET",
            "/workspaces/",
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list (might be empty for new user)
        assert isinstance(data, list)
    
    def test_create_workspace(self):
        """Test creating a new workspace"""
        if not self.access_token:
            self.test_user_login()
        
        workspace_data = {
            "name": f"Test Workspace {int(time.time())}",
            "description": "Test workspace for API testing",
            "theme": "default",
            "color": "#007bff"
        }
        
        response = self._make_request(
            "POST",
            "/workspaces/",
            json=workspace_data,
            headers={**self._get_auth_headers(), "Content-Type": "application/json"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["name"] == workspace_data["name"]
        assert data["description"] == workspace_data["description"]
        
        # Store workspace ID for subsequent tests
        self.__class__.workspace_id = data["id"]
    
    def test_get_workspace_by_id(self):
        """Test getting specific workspace"""
        if not self.workspace_id:
            self.test_create_workspace()
        
        response = self._make_request(
            "GET",
            f"/workspaces/{self.workspace_id}",
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.workspace_id

    # =====================
    # TASK MANAGEMENT TESTS
    # =====================
    
    def test_get_tasks(self):
        """Test getting user tasks"""
        if not self.access_token:
            self.test_user_login()
        
        response = self._make_request(
            "GET",
            "/tasks/taskmaster/all",
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)
        assert isinstance(data["total"], int)
    
    def test_create_task(self):
        """Test creating a new task"""
        if not self.access_token:
            self.test_user_login()
        
        if not self.workspace_id:
            self.test_create_workspace()
        
        task_data = {
            "title": f"Test Task {int(time.time())}",
            "description": "Test task for API testing",
            "priority": "medium",
            "workspace_id": self.workspace_id
        }
        
        response = self._make_request(
            "POST",
            "/tasks/taskmaster/add",
            json=task_data,
            headers={**self._get_auth_headers(), "Content-Type": "application/json"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        
        # Store task ID for subsequent tests
        self.__class__.task_id = data["id"]

    # =====================
    # INPUT VALIDATION TESTS
    # =====================
    
    def test_create_workspace_invalid_data(self):
        """Test creating workspace with invalid data"""
        if not self.access_token:
            self.test_user_login()
        
        # Test with missing required fields
        invalid_data = {
            "description": "Missing name field"
        }
        
        response = self._make_request(
            "POST",
            "/workspaces/",
            json=invalid_data,
            headers={**self._get_auth_headers(), "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_task_invalid_data(self):
        """Test creating task with invalid data"""
        if not self.access_token:
            self.test_user_login()
        
        # Test with missing required fields
        invalid_data = {
            "description": "Missing title field"
        }
        
        response = self._make_request(
            "POST",
            "/tasks/taskmaster/add",
            json=invalid_data,
            headers={**self._get_auth_headers(), "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error

    # =====================
    # PERFORMANCE TESTS
    # =====================
    
    def test_response_times(self):
        """Test API response times are reasonable"""
        if not self.access_token:
            self.test_user_login()
        
        endpoints = [
            "/health",
            "/auth/me",
            "/workspaces/",
            "/tasks/taskmaster/all"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            
            headers = {} if endpoint == "/health" else self._get_auth_headers()
            response = self._make_request("GET", endpoint, headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0, f"Endpoint {endpoint} took {response_time:.2f}s (should be < 5s)"

    # =====================
    # SECURITY TESTS
    # =====================
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        if not self.access_token:
            self.test_user_login()
        
        # Attempt SQL injection in workspace name
        malicious_data = {
            "name": "'; DROP TABLE workspaces; --",
            "description": "SQL injection attempt"
        }
        
        response = self._make_request(
            "POST",
            "/workspaces/",
            json=malicious_data,
            headers={**self._get_auth_headers(), "Content-Type": "application/json"}
        )
        
        # Should either create workspace with escaped name or return validation error
        assert response.status_code in [201, 422]
        
        # Verify workspaces endpoint still works (table wasn't dropped)
        response = self._make_request(
            "GET",
            "/workspaces/",
            headers=self._get_auth_headers()
        )
        assert response.status_code == 200
    
    def test_xss_protection(self):
        """Test XSS protection"""
        if not self.access_token:
            self.test_user_login()
        
        # Attempt XSS in workspace description
        malicious_data = {
            "name": "XSS Test",
            "description": "<script>alert('XSS')</script>"
        }
        
        response = self._make_request(
            "POST",
            "/workspaces/",
            json=malicious_data,
            headers={**self._get_auth_headers(), "Content-Type": "application/json"}
        )
        
        # Should create workspace but escape/sanitize the content
        assert response.status_code == 201
        data = response.json()
        
        # Description should not contain raw script tags
        assert "<script>" not in data["description"]

# =====================
# PYTEST CONFIGURATION
# =====================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "critical: mark test as critical API endpoint test"
    )

# Mark all tests in this file as critical
pytestmark = pytest.mark.critical

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])