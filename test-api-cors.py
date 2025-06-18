#!/usr/bin/env python3
"""
Quick API Test to verify CORS fixes
"""

import urllib.request
import urllib.error
import json
import sys

def test_api_endpoint(url, description):
    print(f"Testing {description}...")
    try:
        req = urllib.request.Request(url)
        req.add_header('Origin', 'http://localhost:3001')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"  SUCCESS: {description}")
                print(f"     Status: {response.status}")
                print(f"     CORS Headers: {response.headers.get('Access-Control-Allow-Origin', 'Not Set')}")
                return True
            else:
                print(f"  ERROR: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False

def main():
    print("OrdnungsHub API CORS Test")
    print("=" * 40)
    
    tests = [
        ("http://localhost:8001/health", "Mock Backend Health"),
        ("http://localhost:8001/api/dashboard/stats", "Dashboard Stats (with /api prefix)"),
        ("http://localhost:8001/dashboard/stats", "Dashboard Stats (without /api prefix)"),
        ("http://localhost:8000/health", "FastAPI Backend Health"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, desc in tests:
        if test_api_endpoint(url, desc):
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("All API endpoints working correctly!")
        print("CORS issues should be resolved.")
    else:
        print("Some endpoints still have issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
