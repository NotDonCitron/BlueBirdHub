#!/usr/bin/env python3
"""
Smart Search API Test Suite
Tests all search functionality including AI-generated tags and filtering
"""

import requests
import json
import time
from typing import Dict, List, Any

# Test configuration
BASE_URL = "http://127.0.0.1:8001"

class SmartSearchTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = 0
        self.passed_tests = 0

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def test_backend_connection(self):
        """Test if backend is running"""
        try:
            response = requests.get(f"{BASE_URL}/")
            data = response.json()
            self.log_test("Backend Connection", 
                         response.status_code == 200 and data.get('status') == 'running',
                         f"Status: {data.get('status', 'unknown')}")
            return True
        except Exception as e:
            self.log_test("Backend Connection", False, f"Error: {str(e)}")
            return False

    def test_get_tags(self):
        """Test getting all available tags"""
        try:
            response = requests.get(f"{BASE_URL}/search/tags")
            data = response.json()
            
            success = (
                response.status_code == 200 and 
                data.get('success') and
                'tags' in data and
                len(data['tags']) > 0
            )
            
            details = f"Found {len(data.get('tags', []))} tags: {data.get('tags', [])[:5]}..."
            self.log_test("Get All Tags", success, details)
            return data.get('tags', [])
        except Exception as e:
            self.log_test("Get All Tags", False, f"Error: {str(e)}")
            return []

    def test_get_categories(self):
        """Test getting all available categories"""
        try:
            response = requests.get(f"{BASE_URL}/search/categories")
            data = response.json()
            
            success = (
                response.status_code == 200 and 
                data.get('success') and
                'categories' in data and
                len(data['categories']) > 0
            )
            
            details = f"Found categories: {data.get('categories', [])}"
            self.log_test("Get All Categories", success, details)
            return data.get('categories', [])
        except Exception as e:
            self.log_test("Get All Categories", False, f"Error: {str(e)}")
            return []

    def test_search_by_text(self, query: str, expected_count: int = None):
        """Test text-based search"""
        try:
            response = requests.get(f"{BASE_URL}/search/files", params={'q': query})
            data = response.json()
            
            success = response.status_code == 200 and data.get('success')
            results = data.get('results', [])
            
            if expected_count is not None:
                success = success and len(results) == expected_count
            
            details = f"Query: '{query}' → {len(results)} results"
            if results:
                details += f" (e.g., {results[0].get('name', 'unknown')})"
            
            self.log_test(f"Text Search: '{query}'", success, details)
            return results
        except Exception as e:
            self.log_test(f"Text Search: '{query}'", False, f"Error: {str(e)}")
            return []

    def test_search_by_category(self, category: str):
        """Test category-based search"""
        try:
            response = requests.get(f"{BASE_URL}/search/files", params={'category': category})
            data = response.json()
            
            success = response.status_code == 200 and data.get('success')
            results = data.get('results', [])
            
            # Check if all results have the correct category
            if results:
                correct_category = all(r.get('category', '').lower() == category.lower() for r in results)
                success = success and correct_category
            
            details = f"Category: '{category}' → {len(results)} results"
            self.log_test(f"Category Search: '{category}'", success, details)
            return results
        except Exception as e:
            self.log_test(f"Category Search: '{category}'", False, f"Error: {str(e)}")
            return []

    def test_search_by_workspace(self, workspace: str):
        """Test workspace-based search"""
        try:
            response = requests.get(f"{BASE_URL}/search/files", params={'workspace': workspace})
            data = response.json()
            
            success = response.status_code == 200 and data.get('success')
            results = data.get('results', [])
            
            details = f"Workspace: '{workspace}' → {len(results)} results"
            self.log_test(f"Workspace Search: '{workspace}'", success, details)
            return results
        except Exception as e:
            self.log_test(f"Workspace Search: '{workspace}'", False, f"Error: {str(e)}")
            return []

    def test_search_by_tags(self, tags: List[str]):
        """Test tag-based search"""
        try:
            tags_str = ','.join(tags)
            response = requests.get(f"{BASE_URL}/search/files", params={'tags': tags_str})
            data = response.json()
            
            success = response.status_code == 200 and data.get('success')
            results = data.get('results', [])
            
            details = f"Tags: {tags} → {len(results)} results"
            self.log_test(f"Tag Search: {tags}", success, details)
            return results
        except Exception as e:
            self.log_test(f"Tag Search: {tags}", False, f"Error: {str(e)}")
            return []

    def test_combined_search(self):
        """Test complex search with multiple parameters"""
        try:
            params = {
                'q': 'web',
                'category': 'development',
                'workspace': 'Website'
            }
            response = requests.get(f"{BASE_URL}/search/files", params=params)
            data = response.json()
            
            success = response.status_code == 200 and data.get('success')
            results = data.get('results', [])
            
            details = f"Combined search → {len(results)} results"
            self.log_test("Combined Search", success, details)
            return results
        except Exception as e:
            self.log_test("Combined Search", False, f"Error: {str(e)}")
            return []

    def test_ai_file_upload(self):
        """Test AI-powered file upload with automatic tagging"""
        try:
            test_file = {
                'filename': 'test_important_project.pdf',
                'workspace_id': 1,
                'content_preview': 'This is an important project document with detailed information.',
                'size': '250KB'
            }
            
            response = requests.post(f"{BASE_URL}/files/upload", json=test_file)
            data = response.json()
            
            success = (
                response.status_code == 200 and 
                data.get('success') and
                'ai_analysis' in data and
                len(data.get('file', {}).get('tags', [])) > 0
            )
            
            if success:
                ai_analysis = data['ai_analysis']
                file_info = data['file']
                details = f"Generated tags: {file_info.get('tags', [])}, Category: {ai_analysis.get('category')}"
            else:
                details = "Failed to generate AI tags"
            
            self.log_test("AI File Upload & Tagging", success, details)
            return data.get('file', {})
        except Exception as e:
            self.log_test("AI File Upload & Tagging", False, f"Error: {str(e)}")
            return {}

    def test_search_performance(self):
        """Test search response time"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/search/files", params={'q': 'web'})
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            success = response.status_code == 200 and response_time < 1000  # Under 1 second
            
            details = f"Response time: {response_time:.2f}ms"
            self.log_test("Search Performance", success, details)
            return response_time
        except Exception as e:
            self.log_test("Search Performance", False, f"Error: {str(e)}")
            return 0

    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Smart Search Test Suite")
        print("=" * 50)
        
        # 1. Basic connectivity
        if not self.test_backend_connection():
            print("❌ Backend not available, stopping tests")
            return
        
        # 2. Test tag and category endpoints
        available_tags = self.test_get_tags()
        available_categories = self.test_get_categories()
        
        # 3. Test various search scenarios
        print("\n📝 Testing Search Scenarios:")
        self.test_search_by_text("web")
        self.test_search_by_text("marketing")
        self.test_search_by_text("2024")
        self.test_search_by_text("nonexistent", 0)  # Should return 0 results
        
        # 4. Test category searches
        print("\n🏷️ Testing Category Searches:")
        if available_categories:
            for category in available_categories[:3]:  # Test first 3 categories
                self.test_search_by_category(category)
        
        # 5. Test workspace searches
        print("\n🏠 Testing Workspace Searches:")
        workspaces = ["Website", "Marketing", "Einkauf", "Finanzen"]
        for workspace in workspaces[:2]:  # Test first 2 workspaces
            self.test_search_by_workspace(workspace)
        
        # 6. Test tag searches
        print("\n🏷️ Testing Tag Searches:")
        if available_tags:
            self.test_search_by_tags(["web"])
            self.test_search_by_tags(["marketing", "2024"])
        
        # 7. Test combined search
        print("\n🔍 Testing Advanced Searches:")
        self.test_combined_search()
        
        # 8. Test AI features
        print("\n🤖 Testing AI Features:")
        self.test_ai_file_upload()
        
        # 9. Test performance
        print("\n⚡ Testing Performance:")
        self.test_search_performance()
        
        # Final results
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎉 Test suite completed!")
        
        if self.failed_tests == 0:
            print("🌟 All tests passed! Smart Search is working perfectly!")
        else:
            print(f"⚠️  {self.failed_tests} test(s) failed. Check the details above.")

def main():
    """Run the test suite"""
    tester = SmartSearchTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()