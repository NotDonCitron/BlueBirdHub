#!/usr/bin/env python3
"""Debug script to test registration endpoint directly"""

import requests
import json
import time

def test_registration():
    """Test registration endpoint directly"""
    base_url = "http://localhost:8888"
    
    # Test health first
    health_response = requests.get(f"{base_url}/health")
    print(f"Health check: {health_response.status_code} - {health_response.json()}")
    
    # Test registration
    unique_suffix = str(int(time.time()))
    user_data = {
        "username": f"testuser_{unique_suffix}",
        "email": f"test_{unique_suffix}@example.com",
        "password": "testpass123"
    }
    
    print(f"Registering user: {user_data}")
    
    try:
        response = requests.post(
            f"{base_url}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"Registration successful!")
            print(f"Access token: {data.get('access_token', 'Not found')[:50]}...")
            
        elif response.status_code == 500:
            print("Server error - checking if it's a known issue")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_registration()