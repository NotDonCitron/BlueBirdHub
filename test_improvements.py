#!/usr/bin/env python3
"""
Test script to verify OrdnungsHub improvements without running the full application.
This script validates the code structure and configuration changes.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_security_fixes():
    """Test that API keys have been removed from .env.example"""
    print("🔐 Testing Security Fixes...")
    
    env_example_path = Path(".env.example")
    if env_example_path.exists():
        content = env_example_path.read_text()
        
        # Check for exposed keys
        exposed_keys = [
            "sk-proj-efsl01eEVMWPTK7r",  # OpenAI key
            "AIzaSyB_mr3o3sZqo8TsLOdC9bgwphQB9_tSoYw"  # Google key
        ]
        
        security_issues = []
        for key in exposed_keys:
            if key in content:
                security_issues.append(key[:20] + "...")
        
        if security_issues:
            print(f"❌ SECURITY ISSUE: Found exposed keys: {security_issues}")
            return False
        else:
            print("✅ No exposed API keys found in .env.example")
            return True
    else:
        print("❌ .env.example file not found")
        return False

def test_dependency_cleanup():
    """Test that unused dependencies have been removed"""
    print("\n📦 Testing Dependency Cleanup...")
    
    package_json_path = Path("package.json")
    if package_json_path.exists():
        with open(package_json_path) as f:
            package_data = json.load(f)
        
        # Check removed dependencies
        removed_deps = ["puppeteer", "@types/react-router-dom"]
        
        issues = []
        all_deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
        
        for dep in removed_deps:
            if dep in all_deps:
                issues.append(dep)
        
        if issues:
            print(f"❌ Unused dependencies still present: {issues}")
            return False
        else:
            print("✅ Unused dependencies successfully removed")
            
        # Check new dependencies
        new_deps = ["redis", "prometheus-client"]
        backend_requirements = Path("requirements.txt")
        if backend_requirements.exists():
            req_content = backend_requirements.read_text()
            for dep in new_deps:
                if dep in req_content:
                    print(f"✅ New dependency added: {dep}")
                else:
                    print(f"❌ Missing new dependency: {dep}")
                    return False
            
        return True
    else:
        print("❌ package.json file not found")
        return False

def test_api_documentation():
    """Test FastAPI documentation enhancements"""
    print("\n📚 Testing API Documentation...")
    
    main_py_path = Path("packages/backend/src/main.py")
    if main_py_path.exists():
        content = main_py_path.read_text()
        
        doc_features = [
            "docs_url=\"/docs\"",
            "redoc_url=\"/redoc\"",
            "openapi_url=\"/openapi.json\"",
            "contact={",
            "license_info={",
            "servers=[",
            "tags=[\"Health\"]"
        ]
        
        missing_features = []
        for feature in doc_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing documentation features: {missing_features}")
            return False
        else:
            print("✅ API documentation enhancements implemented")
            return True
    else:
        print("❌ main.py file not found")
        return False

def test_caching_implementation():
    """Test Redis caching implementation"""
    print("\n⚡ Testing Caching Implementation...")
    
    cache_service_path = Path("packages/backend/src/services/cache_service.py")
    if cache_service_path.exists():
        content = cache_service_path.read_text()
        
        cache_features = [
            "class CacheService:",
            "def get(self, key: str)",
            "def set(self, key: str, value: Any",
            "def delete(self, key: str)",
            "def health_check(self)",
            "def cached_response"
        ]
        
        missing_features = []
        for feature in cache_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing cache features: {missing_features}")
            return False
        else:
            print("✅ Redis caching service implemented")
            return True
    else:
        print("❌ cache_service.py file not found")
        return False

def test_metrics_implementation():
    """Test Prometheus metrics implementation"""
    print("\n📊 Testing Metrics Implementation...")
    
    metrics_service_path = Path("packages/backend/src/services/metrics_service.py")
    if metrics_service_path.exists():
        content = metrics_service_path.read_text()
        
        metrics_features = [
            "class MetricsService:",
            "prometheus_client",
            "http_requests_total",
            "db_query_duration",
            "cache_operations_total",
            "ai_requests_total"
        ]
        
        missing_features = []
        for feature in metrics_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing metrics features: {missing_features}")
            return False
        else:
            print("✅ Prometheus metrics service implemented")
            
        # Check metrics endpoint in main.py
        main_py_path = Path("packages/backend/src/main.py")
        if main_py_path.exists():
            main_content = main_py_path.read_text()
            if "@app.get(\"/metrics\"" in main_content:
                print("✅ Metrics endpoint configured")
                return True
            else:
                print("❌ Metrics endpoint not found")
                return False
    else:
        print("❌ metrics_service.py file not found")
        return False

def test_worktree_documentation():
    """Test worktree cleanup documentation"""
    print("\n🏗️ Testing Worktree Documentation...")
    
    cleanup_guide_path = Path("WORKTREE_CLEANUP.md")
    if cleanup_guide_path.exists():
        content = cleanup_guide_path.read_text()
        
        guide_features = [
            "Current Worktree Analysis",
            "Consolidation Strategy",
            "Branch Naming Convention",
            "Migration Commands"
        ]
        
        missing_features = []
        for feature in guide_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing guide features: {missing_features}")
            return False
        else:
            print("✅ Worktree cleanup guide created")
            return True
    else:
        print("❌ WORKTREE_CLEANUP.md file not found")
        return False

def test_file_structure():
    """Test overall file structure and created files"""
    print("\n📁 Testing File Structure...")
    
    expected_files = [
        "IMPROVEMENTS_IMPLEMENTED.md",
        "WORKTREE_CLEANUP.md",
        ".cspellrc.json",
        "packages/backend/src/services/cache_service.py",
        "packages/backend/src/services/metrics_service.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All expected files created")
        return True

def run_tests():
    """Run all improvement tests"""
    print("🧪 Testing OrdnungsHub Improvements\n" + "="*50)
    
    tests = [
        test_security_fixes,
        test_dependency_cleanup,
        test_api_documentation,
        test_caching_implementation,
        test_metrics_implementation,
        test_worktree_documentation,
        test_file_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*50)
    print("📋 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All improvements successfully implemented!")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)