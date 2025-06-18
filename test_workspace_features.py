#!/usr/bin/env python3
"""
Test script for workspace features
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        else:
            response = requests.request(method, url, json=data)
        
        print(f"✅ {method} {endpoint}: {response.status_code}")
        if response.status_code == expected_status:
            return response.json()
        else:
            print(f"❌ Expected {expected_status}, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error testing {method} {endpoint}: {e}")
        return None

def main():
    print("🧪 Testing Workspace Features")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Health Check")
    health = test_endpoint("GET", "/health")
    if not health:
        print("❌ Backend not available, exiting")
        return
    
    # Test 2: Get workspaces
    print("\n2. Get Workspaces")
    workspaces = test_endpoint("GET", "/workspaces/")
    if workspaces:
        print(f"   Found {len(workspaces)} workspaces")
        workspace_id = workspaces[0]["id"] if workspaces else 1
    else:
        workspace_id = 1
    
    # Test 3: Test workspace detail endpoint  
    print("\n3. Workspace Detail")
    detail = test_endpoint("GET", f"/workspaces/{workspace_id}/detail")
    if detail:
        print(f"   Workspace: {detail.get('workspace', {}).get('name', 'Unknown')}")
        print(f"   Tasks: {detail.get('statistics', {}).get('tasks', {}).get('total', 0)}")
    
    # Test 4: Test AI workspace suggestions
    print("\n4. AI Workspace Suggestions")
    ai_data = {
        "task_title": "Build React component for user management",
        "task_description": "Create a dashboard component with user authentication",
        "existing_workspaces": []
    }
    suggestions = test_endpoint("POST", "/ai/suggest-workspaces", ai_data)
    if suggestions:
        print(f"   Generated {len(suggestions.get('suggestions', []))} suggestions")
        for i, suggestion in enumerate(suggestions.get('suggestions', [])):
            print(f"   {i+1}. {suggestion.get('name', 'Unknown')}: {suggestion.get('description', '')}")
    
    # Test 5: Create workspace
    print("\n5. Create Workspace")
    new_workspace = {
        "name": "Test Workspace",
        "description": "Created by test script",
        "theme": "modern_light",
        "color": "#3b82f6",
        "user_id": 1
    }
    created = test_endpoint("POST", "/workspaces/", new_workspace, 200)
    if created:
        print(f"   Created workspace: {created.get('name')} (ID: {created.get('id')})")
        
        # Test the detail of newly created workspace
        print("\n6. New Workspace Detail")
        new_detail = test_endpoint("GET", f"/workspaces/{created['id']}/detail")
        if new_detail:
            print(f"   New workspace has {new_detail.get('statistics', {}).get('tasks', {}).get('total', 0)} tasks")
    
    # Test 6: Workspace analytics
    print("\n7. Workspace Analytics")
    analytics = test_endpoint("GET", f"/workspaces/{workspace_id}/analytics")
    if analytics:
        print(f"   Productivity score: {analytics.get('ai_insights', {}).get('productivity_score', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    main()