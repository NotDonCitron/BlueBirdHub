import pytest
from fastapi.testclient import TestClient
from main_simple import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns correct status"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "OrdnungsHub API" in data["message"]
    assert data["version"] == "0.1.0"

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["backend"] == "operational"
    assert "database" in data

def test_cors_headers():
    """Test CORS headers are properly set"""
    response = client.get("/", headers={"Origin": "http://localhost:3001"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"

def test_invalid_endpoint():
    """Test that invalid endpoints return 404"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404

class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_api_response_format(self):
        """Test that API responses follow expected format"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)
        assert all(key in data for key in ["status", "message", "version"])
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(r.status_code == 200 for r in results)
        assert all(r.json()["status"] == "healthy" for r in results)