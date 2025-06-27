#!/usr/bin/env python3
"""
License compliance checker for BlueBirdHub CI/CD pipeline.
Checks for prohibited licenses and generates compliance reports.
"""

import json
import sys
import re
from typing import Dict, List, Set, Tuple

# Prohibited licenses (copyleft and others)
PROHIBITED_LICENSES = {
    'GPL-2.0', 'GPL-3.0', 'LGPL-2.1', 'LGPL-3.0', 'AGPL-3.0',
    'GPL-2.0-only', 'GPL-3.0-only', 'LGPL-2.1-only', 'LGPL-3.0-only',
    'AGPL-3.0-only', 'AGPL-3.0-or-later', 'GPL-2.0-or-later', 'GPL-3.0-or-later'
}

# Allowed licenses
ALLOWED_LICENSES = {
    'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'Unlicense',
    'Apache License 2.0', 'MIT License', 'BSD License', 'ISC License',
    'Python Software Foundation License', 'PSF-2.0', 'BSD-3-Clause-Clear'
}

# Licenses requiring review
REVIEW_REQUIRED = {
    'MPL-2.0', 'EPL-2.0', 'CDDL-1.0', 'CC-BY-4.0', 'CC-BY-SA-4.0'
}

def normalize_license(license_str: str) -> str:
    """Normalize license string for comparison."""
    if not license_str:
        return 'UNKNOWN'
    
    # Clean up common variations
    license_str = license_str.strip()
    license_str = re.sub(r'\s+', ' ', license_str)
    license_str = license_str.replace('License', '').strip()
    
    # Handle common variations
    variations = {
        'Apache Software License': 'Apache-2.0',
        'Apache 2.0': 'Apache-2.0',
        'Apache License Version 2.0': 'Apache-2.0',
        'MIT License': 'MIT',
        'BSD License (BSD-3-Clause)': 'BSD-3-Clause',
        'GNU General Public License v3 (GPLv3)': 'GPL-3.0',
        'GNU Lesser General Public License v3 (LGPLv3)': 'LGPL-3.0',
    }
    
    return variations.get(license_str, license_str)

def check_python_licenses(python_licenses_file: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Check Python package licenses."""
    violations = []
    needs_review = []
    approved = []
    
    try:
        with open(python_licenses_file, 'r') as f:
            licenses = json.load(f)
        
        for package in licenses:
            name = package.get('Name', 'Unknown')
            version = package.get('Version', 'Unknown')
            license_name = normalize_license(package.get('License', ''))
            
            package_info = {
                'name': name,
                'version': version,
                'license': license_name,
                'type': 'python'
            }
            
            if license_name in PROHIBITED_LICENSES or any(prohibited in license_name for prohibited in PROHIBITED_LICENSES):
                violations.append(package_info)
            elif license_name in REVIEW_REQUIRED:
                needs_review.append(package_info)
            elif license_name in ALLOWED_LICENSES or any(allowed in license_name for allowed in ALLOWED_LICENSES):
                approved.append(package_info)
            else:
                # Unknown license needs review
                needs_review.append(package_info)
                
    except Exception as e:
        print(f"Error reading Python licenses: {e}")
        sys.exit(1)
    
    return violations, needs_review, approved

def check_node_licenses(node_licenses_file: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Check Node.js package licenses."""
    violations = []
    needs_review = []
    approved = []
    
    try:
        with open(node_licenses_file, 'r') as f:
            licenses = json.load(f)
        
        for package_path, package_info in licenses.items():
            name = package_path.split('@')[0] if '@' in package_path else package_path
            version = package_info.get('version', 'Unknown')
            license_name = normalize_license(package_info.get('licenses', ''))
            
            pkg_info = {
                'name': name,
                'version': version,
                'license': license_name,
                'type': 'node'
            }
            
            if license_name in PROHIBITED_LICENSES or any(prohibited in license_name for prohibited in PROHIBITED_LICENSES):
                violations.append(pkg_info)
            elif license_name in REVIEW_REQUIRED:
                needs_review.append(pkg_info)
            elif license_name in ALLOWED_LICENSES or any(allowed in license_name for allowed in ALLOWED_LICENSES):
                approved.append(pkg_info)
            else:
                # Unknown license needs review
                needs_review.append(pkg_info)
                
    except Exception as e:
        print(f"Error reading Node.js licenses: {e}")
        sys.exit(1)
    
    return violations, needs_review, approved

def generate_report(violations: List[Dict], needs_review: List[Dict], approved: List[Dict]) -> str:
    """Generate a comprehensive license compliance report."""
    report = """# License Compliance Report

## Summary
"""
    
    total_packages = len(violations) + len(needs_review) + len(approved)
    report += f"- **Total Packages**: {total_packages}\n"
    report += f"- **Approved Licenses**: {len(approved)}\n"
    report += f"- **Needs Review**: {len(needs_review)}\n"
    report += f"- **Violations**: {len(violations)}\n\n"
    
    if violations:
        report += "## ❌ License Violations (PROHIBITED)\n\n"
        report += "| Package | Version | License | Type |\n"
        report += "|---------|---------|---------|------|\n"
        for pkg in violations:
            report += f"| {pkg['name']} | {pkg['version']} | {pkg['license']} | {pkg['type']} |\n"
        report += "\n"
    
    if needs_review:
        report += "## ⚠️ Licenses Requiring Review\n\n"
        report += "| Package | Version | License | Type |\n"
        report += "|---------|---------|---------|------|\n"
        for pkg in needs_review:
            report += f"| {pkg['name']} | {pkg['version']} | {pkg['license']} | {pkg['type']} |\n"
        report += "\n"
    
    report += "## ✅ Approved Licenses\n\n"
    if approved:
        # Group by license type for better overview
        license_groups = {}
        for pkg in approved:
            license_type = pkg['license']
            if license_type not in license_groups:
                license_groups[license_type] = []
            license_groups[license_type].append(pkg)
        
        for license_type, packages in license_groups.items():
            report += f"### {license_type} ({len(packages)} packages)\n"
            for pkg in packages[:5]:  # Show first 5
                report += f"- {pkg['name']} v{pkg['version']} ({pkg['type']})\n"
            if len(packages) > 5:
                report += f"- ... and {len(packages) - 5} more\n"
            report += "\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    if violations:
        report += "1. **Immediate Action Required**: Remove or replace packages with prohibited licenses\n"
    if needs_review:
        report += "2. **Legal Review**: Have legal team review packages with unknown or restricted licenses\n"
    
    report += "3. **Continuous Monitoring**: Set up automated license scanning in CI/CD pipeline\n"
    report += "4. **License Policy**: Maintain an updated list of approved licenses\n"
    
    return report

def main():
    if len(sys.argv) != 3:
        print("Usage: python check-licenses.py <python_licenses.json> <node_licenses.json>")
        sys.exit(1)
    
    python_file = sys.argv[1]
    node_file = sys.argv[2]
    
    print("🔍 Checking license compliance...")
    
    # Check Python licenses
    py_violations, py_review, py_approved = check_python_licenses(python_file)
    
    # Check Node.js licenses
    node_violations, node_review, node_approved = check_node_licenses(node_file)
    
    # Combine results
    all_violations = py_violations + node_violations
    all_review = py_review + node_review
    all_approved = py_approved + node_approved
    
    # Generate report
    report = generate_report(all_violations, all_review, all_approved)
    
    # Write report to file
    with open('license-compliance-report.md', 'w') as f:
        f.write(report)
    
    # Print summary
    print(f"📊 License Compliance Summary:")
    print(f"   Approved: {len(all_approved)}")
    print(f"   Needs Review: {len(all_review)}")
    print(f"   Violations: {len(all_violations)}")
    
    if all_violations:
        print("\n❌ CRITICAL: Prohibited licenses found!")
        for violation in all_violations:
            print(f"   - {violation['name']} ({violation['license']})")
        print("\nReport saved to: license-compliance-report.md")
        sys.exit(1)
    elif all_review:
        print("\n⚠️ WARNING: Some licenses need review")
        print("Report saved to: license-compliance-report.md")
        sys.exit(0)
    else:
        print("\n✅ All licenses are compliant!")
        sys.exit(0)

if __name__ == "__main__":
    main()