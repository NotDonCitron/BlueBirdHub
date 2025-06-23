#!/usr/bin/env python3
"""
Test script to verify OrdnungsHub deployment
"""

import requests
import json
import sys

def test_backend():
    """Test backend API connectivity"""
    print("🔧 Testing Backend API...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health Check: {health_data}")
        else:
            print(f"   ❌ Health Check Failed: {response.status_code}")
            return False
            
        # Test root endpoint
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            root_data = response.json()
            print(f"   ✅ Root Endpoint: {root_data}")
        else:
            print(f"   ❌ Root Endpoint Failed: {response.status_code}")
            return False
            
        # Test CORS headers
        response = requests.options("http://localhost:8000/", timeout=5)
        cors_headers = {
            k: v for k, v in response.headers.items() 
            if k.lower().startswith('access-control')
        }
        if cors_headers:
            print(f"   ✅ CORS Headers: {cors_headers}")
        else:
            print("   ⚠️  CORS Headers: Not found (might be set dynamically)")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend Connection Failed: {e}")
        return False

def test_frontend():
    """Test frontend connectivity"""
    print("🌐 Testing Frontend...")
    
    try:
        # Test frontend on port 3002
        response = requests.get("http://localhost:3002", timeout=5)
        if response.status_code == 200:
            print("   ✅ Frontend responding on port 3002")
            return True
        else:
            print(f"   ❌ Frontend failed on port 3002: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Frontend Connection Failed on 3002: {e}")
    
    try:
        # Test frontend on port 3001
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("   ✅ Frontend responding on port 3001")
            return True
        else:
            print(f"   ❌ Frontend failed on port 3001: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Frontend Connection Failed on 3001: {e}")
    
    return False

def test_cors():
    """Test CORS by simulating a frontend request"""
    print("🔗 Testing CORS...")
    
    try:
        headers = {
            'Origin': 'http://localhost:3002',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options("http://localhost:8000/health", headers=headers, timeout=5)
        
        if response.status_code in [200, 204]:
            cors_allow_origin = response.headers.get('Access-Control-Allow-Origin', 'Not set')
            print(f"   ✅ CORS Preflight: {response.status_code}")
            print(f"   ✅ Allow-Origin: {cors_allow_origin}")
            return True
        else:
            print(f"   ❌ CORS Preflight Failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ CORS Test Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 OrdnungsHub Deployment Test")
    print("=" * 40)
    
    backend_ok = test_backend()
    print()
    
    frontend_ok = test_frontend()
    print()
    
    cors_ok = test_cors()
    print()
    
    print("📊 Test Results:")
    print(f"   Backend:  {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"   Frontend: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"   CORS:     {'✅ PASS' if cors_ok else '❌ FAIL'}")
    print()
    
    if backend_ok and cors_ok:
        print("🎉 Deployment looks good!")
        if not frontend_ok:
            print("⚠️  Frontend might still be starting up...")
        
        print("\n🌐 Access your app at:")
        print("   • Frontend: http://localhost:3002")
        print("   • Backend:  http://localhost:8000")
        print("   • API Docs: http://localhost:8000/docs")
        
        return 0
    else:
        print("❌ Some issues found. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 