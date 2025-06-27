#!/usr/bin/env python3
"""
Test script to verify login functionality
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_login():
    """Test the login functionality"""
    print("Testing BlueBirdHub Login...")
    
    # Test data
    test_users = [
        {"username": "testuser", "password": "password123"},
        {"username": "admin", "password": "admin123"},
        {"username": "demo@bluebirdhub.com", "password": "demo123"}
    ]
    
    for user in test_users:
        print(f"\nTesting login for user: {user['username']}")
        
        # Try JSON login endpoint
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login-json",
                json=user,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Login successful!")
                token_data = response.json()
                print(f"   Token type: {token_data.get('token_type')}")
                
                # Test /me endpoint
                headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
                me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    print(f"   User ID: {user_data.get('id')}")
                    print(f"   Username: {user_data.get('username')}")
                    print(f"   Email: {user_data.get('email')}")
                else:
                    print(f"❌ Failed to get user info: {me_response.status_code}")
                    
                # Test logout
                logout_response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
                if logout_response.status_code == 200:
                    print(f"✅ Logout successful!")
                else:
                    print(f"❌ Logout failed: {logout_response.status_code}")
                    
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed - is the server running?")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            
    return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)