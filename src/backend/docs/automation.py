#!/usr/bin/env python3
"""
Documentation Automation for OrdnungsHub API

This script provides automation for API documentation including:
- OpenAPI spec validation
- SDK generation
- Documentation testing
- CI/CD integration
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

import requests
from loguru import logger


class DocumentationAutomation:
    """Automate API documentation tasks"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.docs_dir = Path(__file__).parent
    
    def validate_openapi_spec(self) -> bool:
        """Validate the OpenAPI specification"""
        try:
            logger.info("Validating OpenAPI specification...")
            
            # Fetch the spec
            response = requests.get(f"{self.api_base_url}/openapi.json")
            response.raise_for_status()
            spec = response.json()
            
            # Save spec to temporary file for validation
            spec_file = self.docs_dir / "temp_openapi.json"
            with open(spec_file, 'w') as f:
                json.dump(spec, f, indent=2)
            
            # Validate using openapi-spec-validator
            try:
                from openapi_spec_validator import validate_spec
                validate_spec(spec)
                logger.info("✅ OpenAPI specification is valid")
                validation_success = True
            except ImportError:
                # Fallback: basic structure validation
                validation_success = self._basic_spec_validation(spec)
            except Exception as e:
                logger.error(f"❌ OpenAPI validation failed: {e}")
                validation_success = False
            
            # Clean up
            if spec_file.exists():
                spec_file.unlink()
            
            return validation_success
            
        except Exception as e:
            logger.error(f"Failed to validate OpenAPI spec: {e}")
            return False
    
    def _basic_spec_validation(self, spec: Dict[str, Any]) -> bool:
        """Basic OpenAPI spec structure validation"""
        required_fields = ["openapi", "info", "paths"]
        missing_fields = [field for field in required_fields if field not in spec]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return False
        
        # Check for endpoints
        if not spec["paths"]:
            logger.error("No API endpoints defined")
            return False
        
        # Check info section
        info = spec["info"]
        if not info.get("title") or not info.get("version"):
            logger.error("Missing title or version in info section")
            return False
        
        logger.info("✅ Basic OpenAPI structure validation passed")
        return True
    
    def check_documentation_coverage(self) -> Dict[str, Any]:
        """Check documentation coverage across all endpoints"""
        try:
            response = requests.get(f"{self.api_base_url}/openapi.json")
            response.raise_for_status()
            spec = response.json()
            
            total_endpoints = 0
            documented_endpoints = 0
            missing_docs = []
            
            for path, methods in spec["paths"].items():
                for method, details in methods.items():
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        total_endpoints += 1
                        
                        # Check for documentation elements
                        has_summary = bool(details.get("summary"))
                        has_description = bool(details.get("description"))
                        has_examples = self._has_examples(details)
                        has_response_descriptions = self._has_response_descriptions(details)
                        
                        if has_summary and has_description:
                            documented_endpoints += 1
                        else:
                            missing_docs.append({
                                "endpoint": f"{method.upper()} {path}",
                                "missing": {
                                    "summary": not has_summary,
                                    "description": not has_description,
                                    "examples": not has_examples,
                                    "response_descriptions": not has_response_descriptions
                                }
                            })
            
            coverage_percentage = (documented_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
            
            result = {
                "total_endpoints": total_endpoints,
                "documented_endpoints": documented_endpoints,
                "coverage_percentage": round(coverage_percentage, 1),
                "missing_documentation": missing_docs
            }
            
            logger.info(f"Documentation coverage: {coverage_percentage:.1f}% ({documented_endpoints}/{total_endpoints})")
            
            if coverage_percentage < 80:
                logger.warning(f"⚠️  Documentation coverage below 80%")
            else:
                logger.info(f"✅ Good documentation coverage")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check documentation coverage: {e}")
            return {"error": str(e)}
    
    def _has_examples(self, endpoint_details: Dict[str, Any]) -> bool:
        """Check if endpoint has request/response examples"""
        # Check request body examples
        if "requestBody" in endpoint_details:
            request_body = endpoint_details["requestBody"]
            if "content" in request_body:
                for content_type, content in request_body["content"].items():
                    if "example" in content or "examples" in content:
                        return True
        
        # Check response examples
        if "responses" in endpoint_details:
            for response in endpoint_details["responses"].values():
                if "content" in response:
                    for content_type, content in response["content"].items():
                        if "example" in content or "examples" in content:
                            return True
        
        return False
    
    def _has_response_descriptions(self, endpoint_details: Dict[str, Any]) -> bool:
        """Check if endpoint has response descriptions"""
        if "responses" not in endpoint_details:
            return False
        
        for response in endpoint_details["responses"].values():
            if not response.get("description"):
                return False
        
        return True
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints for basic functionality"""
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": [],
            "test_details": []
        }
        
        # Basic endpoint tests
        basic_tests = [
            {"method": "GET", "path": "/", "expected_status": 200},
            {"method": "GET", "path": "/health", "expected_status": 200},
            {"method": "GET", "path": "/docs", "expected_status": 200},
            {"method": "GET", "path": "/openapi.json", "expected_status": 200},
        ]
        
        for test in basic_tests:
            test_results["total_tests"] += 1
            
            try:
                response = requests.request(
                    test["method"],
                    f"{self.api_base_url}{test['path']}",
                    timeout=10
                )
                
                if response.status_code == test["expected_status"]:
                    test_results["passed_tests"] += 1
                    test_results["test_details"].append({
                        "test": f"{test['method']} {test['path']}",
                        "status": "PASSED",
                        "response_code": response.status_code
                    })
                else:
                    test_results["failed_tests"].append({
                        "test": f"{test['method']} {test['path']}",
                        "expected": test["expected_status"],
                        "actual": response.status_code
                    })
                    test_results["test_details"].append({
                        "test": f"{test['method']} {test['path']}",
                        "status": "FAILED",
                        "response_code": response.status_code,
                        "expected": test["expected_status"]
                    })
                    
            except Exception as e:
                test_results["failed_tests"].append({
                    "test": f"{test['method']} {test['path']}",
                    "error": str(e)
                })
                test_results["test_details"].append({
                    "test": f"{test['method']} {test['path']}",
                    "status": "ERROR",
                    "error": str(e)
                })
        
        success_rate = (test_results["passed_tests"] / test_results["total_tests"] * 100) if test_results["total_tests"] > 0 else 0
        logger.info(f"API tests: {success_rate:.1f}% success rate ({test_results['passed_tests']}/{test_results['total_tests']})")
        
        return test_results
    
    def generate_documentation_report(self) -> Dict[str, Any]:
        """Generate comprehensive documentation report"""
        logger.info("Generating documentation report...")
        
        report = {
            "timestamp": "now",
            "api_base_url": self.api_base_url,
            "openapi_validation": self.validate_openapi_spec(),
            "coverage_analysis": self.check_documentation_coverage(),
            "endpoint_tests": self.test_api_endpoints()
        }
        
        # Save report
        report_file = self.docs_dir / "documentation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Documentation report saved to: {report_file}")
        
        # Generate summary
        self._generate_report_summary(report)
        
        return report
    
    def _generate_report_summary(self, report: Dict[str, Any]):
        """Generate human-readable summary of documentation report"""
        logger.info("=== DOCUMENTATION REPORT SUMMARY ===")
        
        # OpenAPI validation
        if report["openapi_validation"]:
            logger.info("✅ OpenAPI specification is valid")
        else:
            logger.error("❌ OpenAPI specification validation failed")
        
        # Coverage analysis
        coverage = report["coverage_analysis"]
        if "coverage_percentage" in coverage:
            percentage = coverage["coverage_percentage"]
            if percentage >= 90:
                logger.info(f"✅ Excellent documentation coverage: {percentage}%")
            elif percentage >= 80:
                logger.info(f"✅ Good documentation coverage: {percentage}%")
            elif percentage >= 60:
                logger.warning(f"⚠️  Moderate documentation coverage: {percentage}%")
            else:
                logger.error(f"❌ Poor documentation coverage: {percentage}%")
        
        # Endpoint tests
        tests = report["endpoint_tests"]
        passed = tests["passed_tests"]
        total = tests["total_tests"]
        if passed == total:
            logger.info(f"✅ All API endpoint tests passed ({passed}/{total})")
        elif passed >= total * 0.8:
            logger.warning(f"⚠️  Most API tests passed ({passed}/{total})")
        else:
            logger.error(f"❌ Many API tests failed ({passed}/{total})")
        
        logger.info("=== END REPORT SUMMARY ===")
    
    def create_github_workflow(self) -> bool:
        """Create GitHub Actions workflow for documentation automation"""
        try:
            workflows_dir = self.project_root / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_content = """name: API Documentation

on:
  push:
    branches: [ main, develop ]
    paths: 
      - 'src/backend/**'
      - 'requirements.txt'
  pull_request:
    branches: [ main ]
    paths:
      - 'src/backend/**'
      - 'requirements.txt'

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Start API server
      run: |
        cd src/backend
        python main.py &
        sleep 10  # Wait for server to start
    
    - name: Validate OpenAPI spec
      run: |
        python src/backend/docs/automation.py validate
    
    - name: Check documentation coverage
      run: |
        python src/backend/docs/automation.py coverage
    
    - name: Test API endpoints
      run: |
        python src/backend/docs/automation.py test
    
    - name: Generate SDKs
      run: |
        npm install -g @openapitools/openapi-generator-cli
        python src/backend/docs/generate_sdk.py
    
    - name: Upload SDK artifacts
      uses: actions/upload-artifact@v3
      with:
        name: api-sdks
        path: sdks/
    
    - name: Generate documentation report
      run: |
        python src/backend/docs/automation.py report
    
    - name: Upload documentation report
      uses: actions/upload-artifact@v3
      with:
        name: documentation-report
        path: src/backend/docs/documentation_report.json

  deploy-docs:
    needs: validate-docs
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Generate OpenAPI spec
      run: |
        cd src/backend
        python -c "
from main import app
import json
spec = app.openapi()
with open('../../docs/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2)
"
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs
        destination_dir: api-docs
"""
            
            workflow_file = workflows_dir / "api-documentation.yml"
            workflow_file.write_text(workflow_content)
            
            logger.info(f"✅ GitHub workflow created: {workflow_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create GitHub workflow: {e}")
            return False
    
    def run_command(self, command: str) -> bool:
        """Run specific automation command"""
        if command == "validate":
            return self.validate_openapi_spec()
        elif command == "coverage":
            result = self.check_documentation_coverage()
            return "error" not in result
        elif command == "test":
            result = self.test_api_endpoints()
            return len(result["failed_tests"]) == 0
        elif command == "report":
            result = self.generate_documentation_report()
            return result is not None
        elif command == "workflow":
            return self.create_github_workflow()
        else:
            logger.error(f"Unknown command: {command}")
            return False


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python automation.py <command>")
        print("Commands: validate, coverage, test, report, workflow")
        sys.exit(1)
    
    command = sys.argv[1]
    automation = DocumentationAutomation()
    
    success = automation.run_command(command)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()