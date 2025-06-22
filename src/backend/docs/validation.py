#!/usr/bin/env python3
"""
API Documentation Validation Tools

This module provides comprehensive validation for API documentation
including endpoint documentation, schema validation, and example testing.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

import requests
from loguru import logger


class DocumentationValidator:
    """Validate API documentation quality and completeness"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.openapi_spec = None
    
    def load_openapi_spec(self) -> bool:
        """Load OpenAPI specification from API"""
        try:
            response = requests.get(f"{self.api_base_url}/openapi.json")
            response.raise_for_status()
            self.openapi_spec = response.json()
            return True
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec: {e}")
            return False
    
    def validate_endpoint_documentation(self) -> Dict[str, Any]:
        """Validate documentation for all endpoints"""
        if not self.openapi_spec:
            if not self.load_openapi_spec():
                return {"error": "Failed to load OpenAPI specification"}
        
        validation_results = {
            "total_endpoints": 0,
            "well_documented": 0,
            "issues": [],
            "endpoint_scores": {}
        }
        
        for path, methods in self.openapi_spec["paths"].items():
            for method, details in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue
                
                endpoint_id = f"{method.upper()} {path}"
                validation_results["total_endpoints"] += 1
                
                # Score endpoint documentation
                score, issues = self._score_endpoint_documentation(endpoint_id, details)
                validation_results["endpoint_scores"][endpoint_id] = score
                
                if score >= 80:  # Well documented threshold
                    validation_results["well_documented"] += 1
                
                if issues:
                    validation_results["issues"].extend([
                        {"endpoint": endpoint_id, "issue": issue} for issue in issues
                    ])
        
        # Calculate overall score
        if validation_results["total_endpoints"] > 0:
            avg_score = sum(validation_results["endpoint_scores"].values()) / validation_results["total_endpoints"]
            validation_results["overall_score"] = round(avg_score, 1)
        else:
            validation_results["overall_score"] = 0
        
        return validation_results
    
    def _score_endpoint_documentation(self, endpoint_id: str, details: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Score individual endpoint documentation quality"""
        score = 0
        max_score = 100
        issues = []
        
        # Summary (20 points)
        if details.get("summary"):
            if len(details["summary"]) >= 10:
                score += 20
            else:
                score += 10
                issues.append("Summary is too short (< 10 characters)")
        else:
            issues.append("Missing summary")
        
        # Description (20 points)
        if details.get("description"):
            if len(details["description"]) >= 50:
                score += 20
            else:
                score += 10
                issues.append("Description is too short (< 50 characters)")
        else:
            issues.append("Missing description")
        
        # Parameters documentation (15 points)
        if "parameters" in details:
            param_score = 0
            for param in details["parameters"]:
                if param.get("description"):
                    param_score += 1
            if param_score == len(details["parameters"]):
                score += 15
            elif param_score > 0:
                score += 10
                issues.append("Some parameters missing descriptions")
            else:
                issues.append("All parameters missing descriptions")
        else:
            # No points deducted if no parameters
            score += 15
        
        # Request body documentation (10 points)
        if "requestBody" in details:
            if details["requestBody"].get("description"):
                score += 10
            else:
                score += 5
                issues.append("Request body missing description")
        else:
            # No points deducted if no request body
            score += 10
        
        # Response documentation (20 points)
        if "responses" in details:
            response_score = 0
            total_responses = len(details["responses"])
            
            for code, response in details["responses"].items():
                if response.get("description"):
                    response_score += 1
            
            if response_score == total_responses:
                score += 20
            elif response_score > 0:
                score += 10
                issues.append("Some responses missing descriptions")
            else:
                score += 0
                issues.append("All responses missing descriptions")
        else:
            issues.append("No response definitions")
        
        # Examples (10 points)
        has_examples = self._has_examples(details)
        if has_examples:
            score += 10
        else:
            issues.append("Missing request/response examples")
        
        # Tags (5 points)
        if details.get("tags"):
            score += 5
        else:
            issues.append("Missing tags")
        
        return min(score, max_score), issues
    
    def _has_examples(self, details: Dict[str, Any]) -> bool:
        """Check if endpoint has examples"""
        # Check request examples
        if "requestBody" in details and "content" in details["requestBody"]:
            for content in details["requestBody"]["content"].values():
                if "example" in content or "examples" in content:
                    return True
        
        # Check response examples
        if "responses" in details:
            for response in details["responses"].values():
                if "content" in response:
                    for content in response["content"].values():
                        if "example" in content or "examples" in content:
                            return True
        
        return False
    
    def validate_schema_consistency(self) -> Dict[str, Any]:
        """Validate schema consistency across endpoints"""
        if not self.openapi_spec:
            if not self.load_openapi_spec():
                return {"error": "Failed to load OpenAPI specification"}
        
        consistency_issues = []
        schema_usage = {}  # Track how schemas are used
        
        # Collect all schema references
        self._collect_schema_references(self.openapi_spec, schema_usage)
        
        # Check for unused schemas
        defined_schemas = set(self.openapi_spec.get("components", {}).get("schemas", {}).keys())
        used_schemas = set(schema_usage.keys())
        unused_schemas = defined_schemas - used_schemas
        
        if unused_schemas:
            consistency_issues.append({
                "type": "unused_schemas",
                "schemas": list(unused_schemas),
                "description": "These schemas are defined but never used"
            })
        
        # Check for missing schema definitions
        missing_schemas = used_schemas - defined_schemas
        if missing_schemas:
            consistency_issues.append({
                "type": "missing_schemas", 
                "schemas": list(missing_schemas),
                "description": "These schemas are referenced but not defined"
            })
        
        # Check for inconsistent parameter naming
        parameter_patterns = self._check_parameter_consistency()
        if parameter_patterns["inconsistencies"]:
            consistency_issues.append({
                "type": "parameter_naming",
                "issues": parameter_patterns["inconsistencies"],
                "description": "Inconsistent parameter naming patterns"
            })
        
        return {
            "consistency_score": self._calculate_consistency_score(consistency_issues),
            "issues": consistency_issues,
            "schema_usage": schema_usage,
            "total_schemas": len(defined_schemas)
        }
    
    def _collect_schema_references(self, obj: Any, schema_usage: Dict[str, int], path: str = ""):
        """Recursively collect schema references"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    # Extract schema name from reference
                    if "/schemas/" in value:
                        schema_name = value.split("/schemas/")[-1]
                        schema_usage[schema_name] = schema_usage.get(schema_name, 0) + 1
                else:
                    self._collect_schema_references(value, schema_usage, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._collect_schema_references(item, schema_usage, f"{path}[{i}]")
    
    def _check_parameter_consistency(self) -> Dict[str, Any]:
        """Check for consistent parameter naming patterns"""
        if not self.openapi_spec:
            return {"inconsistencies": []}
        
        # Common parameter patterns to check
        id_parameters = []
        limit_parameters = []
        offset_parameters = []
        
        for path, methods in self.openapi_spec["paths"].items():
            for method, details in methods.items():
                if "parameters" not in details:
                    continue
                
                for param in details["parameters"]:
                    name = param.get("name", "")
                    
                    if name.endswith("_id") or name == "id":
                        id_parameters.append({
                            "endpoint": f"{method.upper()} {path}",
                            "name": name,
                            "type": param.get("schema", {}).get("type", "unknown")
                        })
                    elif name in ["limit", "max_results", "page_size"]:
                        limit_parameters.append({
                            "endpoint": f"{method.upper()} {path}",
                            "name": name,
                            "type": param.get("schema", {}).get("type", "unknown")
                        })
                    elif name in ["offset", "skip", "page"]:
                        offset_parameters.append({
                            "endpoint": f"{method.upper()} {path}",
                            "name": name,
                            "type": param.get("schema", {}).get("type", "unknown")
                        })
        
        inconsistencies = []
        
        # Check ID parameter consistency
        id_types = set(p["type"] for p in id_parameters)
        if len(id_types) > 1:
            inconsistencies.append({
                "category": "id_parameters",
                "issue": "Inconsistent ID parameter types",
                "details": id_parameters
            })
        
        # Check pagination parameter naming
        limit_names = set(p["name"] for p in limit_parameters)
        if len(limit_names) > 1:
            inconsistencies.append({
                "category": "pagination",
                "issue": "Inconsistent limit parameter names",
                "details": list(limit_names)
            })
        
        offset_names = set(p["name"] for p in offset_parameters)
        if len(offset_names) > 1:
            inconsistencies.append({
                "category": "pagination",
                "issue": "Inconsistent offset parameter names",
                "details": list(offset_names)
            })
        
        return {"inconsistencies": inconsistencies}
    
    def _calculate_consistency_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate consistency score based on issues"""
        if not issues:
            return 100.0
        
        # Deduct points for each type of issue
        score = 100.0
        for issue in issues:
            if issue["type"] == "unused_schemas":
                score -= len(issue["schemas"]) * 2  # 2 points per unused schema
            elif issue["type"] == "missing_schemas":
                score -= len(issue["schemas"]) * 10  # 10 points per missing schema
            elif issue["type"] == "parameter_naming":
                score -= len(issue["issues"]) * 5  # 5 points per naming inconsistency
        
        return max(0.0, score)
    
    def validate_examples(self) -> Dict[str, Any]:
        """Validate that examples in documentation are correct"""
        if not self.openapi_spec:
            if not self.load_openapi_spec():
                return {"error": "Failed to load OpenAPI specification"}
        
        example_validation = {
            "total_examples": 0,
            "valid_examples": 0,
            "invalid_examples": [],
            "missing_examples": []
        }
        
        for path, methods in self.openapi_spec["paths"].items():
            for method, details in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue
                
                endpoint_id = f"{method.upper()} {path}"
                
                # Check request body examples
                if "requestBody" in details:
                    self._validate_request_examples(
                        endpoint_id, details["requestBody"], example_validation
                    )
                
                # Check response examples
                if "responses" in details:
                    self._validate_response_examples(
                        endpoint_id, details["responses"], example_validation
                    )
                
                # Check if endpoint should have examples but doesn't
                if not self._has_examples(details):
                    example_validation["missing_examples"].append(endpoint_id)
        
        return example_validation
    
    def _validate_request_examples(self, endpoint_id: str, request_body: Dict[str, Any], 
                                   validation: Dict[str, Any]):
        """Validate request body examples"""
        if "content" not in request_body:
            return
        
        for content_type, content in request_body["content"].items():
            if "example" in content:
                validation["total_examples"] += 1
                if self._is_valid_json_example(content["example"]):
                    validation["valid_examples"] += 1
                else:
                    validation["invalid_examples"].append({
                        "endpoint": endpoint_id,
                        "type": "request_body",
                        "content_type": content_type,
                        "issue": "Invalid JSON format"
                    })
            
            if "examples" in content:
                for example_name, example_data in content["examples"].items():
                    validation["total_examples"] += 1
                    if "value" in example_data and self._is_valid_json_example(example_data["value"]):
                        validation["valid_examples"] += 1
                    else:
                        validation["invalid_examples"].append({
                            "endpoint": endpoint_id,
                            "type": "request_body",
                            "content_type": content_type,
                            "example_name": example_name,
                            "issue": "Invalid JSON format"
                        })
    
    def _validate_response_examples(self, endpoint_id: str, responses: Dict[str, Any],
                                    validation: Dict[str, Any]):
        """Validate response examples"""
        for status_code, response in responses.items():
            if "content" not in response:
                continue
            
            for content_type, content in response["content"].items():
                if "example" in content:
                    validation["total_examples"] += 1
                    if self._is_valid_json_example(content["example"]):
                        validation["valid_examples"] += 1
                    else:
                        validation["invalid_examples"].append({
                            "endpoint": endpoint_id,
                            "type": "response",
                            "status_code": status_code,
                            "content_type": content_type,
                            "issue": "Invalid JSON format"
                        })
                
                if "examples" in content:
                    for example_name, example_data in content["examples"].items():
                        validation["total_examples"] += 1
                        if "value" in example_data and self._is_valid_json_example(example_data["value"]):
                            validation["valid_examples"] += 1
                        else:
                            validation["invalid_examples"].append({
                                "endpoint": endpoint_id,
                                "type": "response",
                                "status_code": status_code,
                                "content_type": content_type,
                                "example_name": example_name,
                                "issue": "Invalid JSON format"
                            })
    
    def _is_valid_json_example(self, example: Any) -> bool:
        """Check if example is valid JSON"""
        try:
            if isinstance(example, str):
                json.loads(example)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating comprehensive validation report...")
        
        report = {
            "timestamp": "now",
            "endpoint_documentation": self.validate_endpoint_documentation(),
            "schema_consistency": self.validate_schema_consistency(),
            "example_validation": self.validate_examples()
        }
        
        # Calculate overall grade
        report["overall_grade"] = self._calculate_overall_grade(report)
        
        return report
    
    def _calculate_overall_grade(self, report: Dict[str, Any]) -> str:
        """Calculate overall documentation grade"""
        scores = []
        
        # Endpoint documentation score
        if "overall_score" in report["endpoint_documentation"]:
            scores.append(report["endpoint_documentation"]["overall_score"])
        
        # Schema consistency score
        if "consistency_score" in report["schema_consistency"]:
            scores.append(report["schema_consistency"]["consistency_score"])
        
        # Example validation score
        example_val = report["example_validation"]
        if example_val["total_examples"] > 0:
            example_score = (example_val["valid_examples"] / example_val["total_examples"]) * 100
            scores.append(example_score)
        
        if not scores:
            return "F"
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 90:
            return "A"
        elif avg_score >= 80:
            return "B"
        elif avg_score >= 70:
            return "C"
        elif avg_score >= 60:
            return "D"
        else:
            return "F"


def main():
    """CLI interface for validation tools"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validation.py <command>")
        print("Commands: endpoints, schemas, examples, report")
        sys.exit(1)
    
    command = sys.argv[1]
    validator = DocumentationValidator()
    
    if command == "endpoints":
        result = validator.validate_endpoint_documentation()
        print(json.dumps(result, indent=2))
    elif command == "schemas":
        result = validator.validate_schema_consistency()
        print(json.dumps(result, indent=2))
    elif command == "examples":
        result = validator.validate_examples()
        print(json.dumps(result, indent=2))
    elif command == "report":
        result = validator.generate_validation_report()
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()