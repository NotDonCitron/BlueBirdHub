#!/usr/bin/env python3
"""
Security summary generator for BlueBirdHub CI/CD pipeline.
Consolidates all security scan results into a comprehensive report.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def load_json_report(file_path):
    """Load a JSON report file safely."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None

def parse_bandit_report(reports_dir):
    """Parse Bandit security scan results."""
    bandit_file = os.path.join(reports_dir, 'sast-reports', 'bandit-report.json')
    if not os.path.exists(bandit_file):
        return {"status": "not_found", "issues": 0}
    
    data = load_json_report(bandit_file)
    if not data:
        return {"status": "error", "issues": 0}
    
    metrics = data.get('metrics', {})
    total_issues = sum(len(data.get('results', [])) for result in data.get('results', []))
    
    return {
        "status": "completed",
        "total_files": metrics.get('_totals', {}).get('loc', 0),
        "issues": total_issues,
        "high": len([r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']),
        "medium": len([r for r in data.get('results', []) if r.get('issue_severity') == 'MEDIUM']),
        "low": len([r for r in data.get('results', []) if r.get('issue_severity') == 'LOW'])
    }

def parse_trivy_report(reports_dir):
    """Parse Trivy container scan results."""
    trivy_file = os.path.join(reports_dir, 'container-scan-reports', 'trivy-results.json')
    if not os.path.exists(trivy_file):
        return {"status": "not_found", "vulnerabilities": 0}
    
    data = load_json_report(trivy_file)
    if not data:
        return {"status": "error", "vulnerabilities": 0}
    
    total_vulns = 0
    critical = 0
    high = 0
    medium = 0
    low = 0
    
    results = data.get('Results', [])
    for result in results:
        vulns = result.get('Vulnerabilities', [])
        total_vulns += len(vulns)
        
        for vuln in vulns:
            severity = vuln.get('Severity', '').upper()
            if severity == 'CRITICAL':
                critical += 1
            elif severity == 'HIGH':
                high += 1
            elif severity == 'MEDIUM':
                medium += 1
            elif severity == 'LOW':
                low += 1
    
    return {
        "status": "completed",
        "vulnerabilities": total_vulns,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low
    }

def parse_snyk_reports(reports_dir):
    """Parse Snyk dependency scan results."""
    snyk_python_file = os.path.join(reports_dir, 'dependency-scan-reports', 'snyk-python-report.json')
    snyk_node_file = os.path.join(reports_dir, 'dependency-scan-reports', 'snyk-node-report.json')
    
    python_results = {"vulnerabilities": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
    node_results = {"vulnerabilities": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
    
    if os.path.exists(snyk_python_file):
        data = load_json_report(snyk_python_file)
        if data and 'vulnerabilities' in data:
            vulns = data['vulnerabilities']
            python_results['vulnerabilities'] = len(vulns)
            for vuln in vulns:
                severity = vuln.get('severity', '').lower()
                if severity in python_results:
                    python_results[severity] += 1
    
    if os.path.exists(snyk_node_file):
        data = load_json_report(snyk_node_file)
        if data and 'vulnerabilities' in data:
            vulns = data['vulnerabilities']
            node_results['vulnerabilities'] = len(vulns)
            for vuln in vulns:
                severity = vuln.get('severity', '').lower()
                if severity in node_results:
                    node_results[severity] += 1
    
    return {
        "status": "completed",
        "python": python_results,
        "node": node_results,
        "total_vulnerabilities": python_results['vulnerabilities'] + node_results['vulnerabilities']
    }

def parse_license_report(reports_dir):
    """Parse license compliance results."""
    license_file = os.path.join(reports_dir, 'license-reports', 'license-compliance-report.md')
    if not os.path.exists(license_file):
        return {"status": "not_found", "violations": 0}
    
    try:
        with open(license_file, 'r') as f:
            content = f.read()
        
        # Simple parsing of markdown report
        violations = content.count('❌ License Violations')
        needs_review = content.count('⚠️ Licenses Requiring Review')
        
        return {
            "status": "completed",
            "violations": 1 if violations > 0 else 0,
            "needs_review": 1 if needs_review > 0 else 0,
            "compliant": violations == 0 and needs_review == 0
        }
    except Exception as e:
        return {"status": "error", "violations": 0}

def generate_security_summary(reports_dir):
    """Generate comprehensive security summary."""
    
    # Parse individual reports
    bandit = parse_bandit_report(reports_dir)
    trivy = parse_trivy_report(reports_dir)
    snyk = parse_snyk_reports(reports_dir)
    licenses = parse_license_report(reports_dir)
    
    # Calculate overall security score
    score = 100
    critical_issues = 0
    high_issues = 0
    
    # Deduct points for security issues
    if bandit['status'] == 'completed':
        critical_issues += bandit.get('high', 0)
        high_issues += bandit.get('medium', 0)
        score -= bandit.get('high', 0) * 10  # -10 points per high severity
        score -= bandit.get('medium', 0) * 5  # -5 points per medium severity
    
    if trivy['status'] == 'completed':
        critical_issues += trivy.get('critical', 0) + trivy.get('high', 0)
        score -= trivy.get('critical', 0) * 15  # -15 points per critical vulnerability
        score -= trivy.get('high', 0) * 10  # -10 points per high vulnerability
        score -= trivy.get('medium', 0) * 3  # -3 points per medium vulnerability
    
    if snyk['status'] == 'completed':
        critical_issues += snyk['python'].get('critical', 0) + snyk['node'].get('critical', 0)
        critical_issues += snyk['python'].get('high', 0) + snyk['node'].get('high', 0)
        score -= snyk['total_vulnerabilities'] * 2  # -2 points per dependency vulnerability
    
    if licenses['status'] == 'completed' and not licenses.get('compliant', True):
        critical_issues += licenses.get('violations', 0)
        score -= licenses.get('violations', 0) * 20  # -20 points per license violation
    
    score = max(0, score)  # Ensure score doesn't go below 0
    
    # Determine overall status
    if critical_issues > 0:
        overall_status = "CRITICAL"
        status_emoji = "🚨"
    elif high_issues > 5:
        overall_status = "HIGH"
        status_emoji = "⚠️"
    elif score < 80:
        overall_status = "MEDIUM"
        status_emoji = "⚠️"
    else:
        overall_status = "GOOD"
        status_emoji = "✅"
    
    # Generate summary report
    summary = f"""# {status_emoji} Security Scan Summary

**Overall Security Score**: {score}/100
**Status**: {overall_status}
**Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

## 🔍 Scan Results Overview

| Category | Status | Critical | High | Medium | Low | Total |
|----------|--------|----------|------|--------|-----|-------|
| Static Analysis (Bandit) | {bandit['status']} | {bandit.get('high', 0)} | {bandit.get('medium', 0)} | {bandit.get('low', 0)} | - | {bandit.get('issues', 0)} |
| Container Security (Trivy) | {trivy['status']} | {trivy.get('critical', 0)} | {trivy.get('high', 0)} | {trivy.get('medium', 0)} | {trivy.get('low', 0)} | {trivy.get('vulnerabilities', 0)} |
| Dependencies (Snyk) | {snyk['status']} | {snyk['python'].get('critical', 0) + snyk['node'].get('critical', 0)} | {snyk['python'].get('high', 0) + snyk['node'].get('high', 0)} | {snyk['python'].get('medium', 0) + snyk['node'].get('medium', 0)} | {snyk['python'].get('low', 0) + snyk['node'].get('low', 0)} | {snyk.get('total_vulnerabilities', 0)} |
| License Compliance | {licenses['status']} | {licenses.get('violations', 0)} | - | {licenses.get('needs_review', 0)} | - | {licenses.get('violations', 0) + licenses.get('needs_review', 0)} |

## 📊 Detailed Findings

### Static Application Security Testing (SAST)
"""

    if bandit['status'] == 'completed':
        if bandit['issues'] == 0:
            summary += "✅ No security issues found in Python code\n"
        else:
            summary += f"⚠️ {bandit['issues']} potential security issues identified\n"
            summary += f"- High severity: {bandit.get('high', 0)}\n"
            summary += f"- Medium severity: {bandit.get('medium', 0)}\n"
            summary += f"- Low severity: {bandit.get('low', 0)}\n"
    else:
        summary += "❌ Static analysis scan not available\n"

    summary += "\n### Container Security\n"
    if trivy['status'] == 'completed':
        if trivy['vulnerabilities'] == 0:
            summary += "✅ No vulnerabilities found in container images\n"
        else:
            summary += f"⚠️ {trivy['vulnerabilities']} vulnerabilities found in container images\n"
            summary += f"- Critical: {trivy.get('critical', 0)}\n"
            summary += f"- High: {trivy.get('high', 0)}\n"
            summary += f"- Medium: {trivy.get('medium', 0)}\n"
            summary += f"- Low: {trivy.get('low', 0)}\n"
    else:
        summary += "❌ Container security scan not available\n"

    summary += "\n### Dependency Vulnerabilities\n"
    if snyk['status'] == 'completed':
        if snyk['total_vulnerabilities'] == 0:
            summary += "✅ No known vulnerabilities in dependencies\n"
        else:
            summary += f"⚠️ {snyk['total_vulnerabilities']} vulnerabilities found in dependencies\n"
            summary += f"- Python packages: {snyk['python']['vulnerabilities']}\n"
            summary += f"- Node.js packages: {snyk['node']['vulnerabilities']}\n"
    else:
        summary += "❌ Dependency scan not available\n"

    summary += "\n### License Compliance\n"
    if licenses['status'] == 'completed':
        if licenses.get('compliant', True):
            summary += "✅ All licenses are compliant\n"
        else:
            summary += f"⚠️ License compliance issues found\n"
            summary += f"- Violations: {licenses.get('violations', 0)}\n"
            summary += f"- Needs review: {licenses.get('needs_review', 0)}\n"
    else:
        summary += "❌ License compliance scan not available\n"

    # Recommendations
    summary += "\n## 🔧 Recommended Actions\n\n"
    
    if critical_issues > 0:
        summary += "### 🚨 IMMEDIATE ACTION REQUIRED\n"
        summary += "1. Address all critical and high severity vulnerabilities\n"
        summary += "2. Review and fix license violations\n"
        summary += "3. Update vulnerable dependencies\n\n"
    
    if high_issues > 0:
        summary += "### ⚠️ HIGH PRIORITY\n"
        summary += "1. Review and address medium severity issues\n"
        summary += "2. Update security scanning tools\n"
        summary += "3. Implement additional security controls\n\n"
    
    summary += "### 📈 CONTINUOUS IMPROVEMENT\n"
    summary += "1. Set up automated security monitoring\n"
    summary += "2. Regular dependency updates\n"
    summary += "3. Security awareness training\n"
    summary += "4. Implement security policies\n\n"
    
    summary += f"---\n*Report generated by BlueBirdHub CI/CD Security Pipeline*\n"
    summary += f"*Next scan: Automated daily at 2:00 AM UTC*"
    
    return summary

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate-security-summary.py <reports_directory>")
        sys.exit(1)
    
    reports_dir = sys.argv[1]
    
    if not os.path.exists(reports_dir):
        print(f"Reports directory not found: {reports_dir}")
        sys.exit(1)
    
    try:
        summary = generate_security_summary(reports_dir)
        print(summary)
    except Exception as e:
        print(f"Error generating security summary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()