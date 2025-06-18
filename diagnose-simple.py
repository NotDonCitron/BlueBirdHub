#!/usr/bin/env python3
"""
OrdnungsHub Connection Diagnostic Tool (Simplified)
Identifies and helps fix front/backend connection issues
"""

import json
import sys
import subprocess
import platform
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import socket
import os

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class ConnectionDiagnostics:
    def __init__(self):
        self.ports = {
            'frontend': 3001,
            'backend': 8000,
            'mock': 8001
        }
        self.issues = []
        self.recommendations = []

    def log(self, message: str, color: str = Colors.RESET):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {message}{Colors.RESET}")

    def success(self, message: str):
        self.log(f"[OK] {message}", Colors.GREEN)

    def warning(self, message: str):
        self.log(f"[WARN] {message}", Colors.YELLOW)
        self.issues.append(message)

    def error(self, message: str):
        self.log(f"[ERROR] {message}", Colors.RED)
        self.issues.append(message)

    def info(self, message: str):
        self.log(f"[INFO] {message}", Colors.BLUE)

    def check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except:
            return False

    def test_endpoint(self, url: str, timeout: int = 5) -> Tuple[bool, Optional[Dict]]:
        """Test if an endpoint is responding"""
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return True, data
                else:
                    return False, {"error": f"HTTP {response.status}"}
        except Exception as e:
            return False, {"error": str(e)}

    def diagnose_ports(self):
        """Check all required ports"""
        self.info("Checking port availability...")
        
        for name, port in self.ports.items():
            if self.check_port(port):
                self.success(f"{name.title()} service running on port {port}")
            else:
                self.warning(f"{name.title()} service not running on port {port}")

    def diagnose_backend_connectivity(self):
        """Test backend endpoints"""
        self.info("Testing backend connectivity...")
        
        endpoints = [
            ("FastAPI Backend", "http://localhost:8000/health"),
            ("Mock Backend", "http://localhost:8001/health"),
        ]
        
        working_backends = []
        
        for name, url in endpoints:
            success, data = self.test_endpoint(url)
            if success:
                self.success(f"{name} responding: {data.get('status', 'unknown')}")
                working_backends.append(name)
            else:
                self.error(f"{name} not responding: {data.get('error', 'unknown error')}")
        
        if not working_backends:
            self.error("No backend services are responding!")
            self.recommendations.append("Start backend services with: py src/backend/main.py")
            self.recommendations.append("Or start mock backend with: py mock_backend.py")
        elif len(working_backends) == 1:
            self.warning(f"Only {working_backends[0]} is running")
            self.recommendations.append("Consider running both backends for redundancy")

    def diagnose_frontend_connectivity(self):
        """Test frontend connectivity"""
        self.info("Testing frontend connectivity...")
        
        frontend_url = "http://localhost:3001"
        success, data = self.test_endpoint(frontend_url, timeout=3)
        
        if success:
            self.success("Frontend responding correctly")
        else:
            self.error(f"Frontend not responding: {data.get('error', 'unknown error')}")
            self.recommendations.append("Start frontend with: npm run dev:react")

    def check_environment_files(self):
        """Check environment configuration"""
        self.info("Checking environment configuration...")
        
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            if 'CORS_ORIGINS' in env_content:
                self.success("CORS_ORIGINS found in .env")
                if 'localhost:3001' in env_content:
                    self.success("Frontend port included in CORS_ORIGINS")
                else:
                    self.warning("Frontend port not in CORS_ORIGINS")
                    self.recommendations.append("Add http://localhost:3001 to CORS_ORIGINS in .env")
            else:
                self.warning("CORS_ORIGINS not found in .env")
                self.recommendations.append("Add CORS_ORIGINS=http://localhost:3001 to .env")
                
        except FileNotFoundError:
            self.warning(".env file not found")
            self.recommendations.append("Create .env file from .env.example")

    def check_dependencies(self):
        """Check if required dependencies are installed"""
        self.info("Checking dependencies...")
        
        # Check if node_modules exists
        if os.path.exists('node_modules'):
            self.success("Node.js dependencies installed")
        else:
            self.warning("Node.js dependencies not found")
            self.recommendations.append("Install Node.js dependencies: npm install")
        
        # Check if requirements.txt exists
        if os.path.exists('requirements.txt'):
            self.success("Python requirements.txt found")
        else:
            self.warning("Python requirements.txt not found")

    def generate_startup_script(self):
        """Generate a custom startup script based on detected issues"""
        if self.issues:
            self.info("Generating custom startup script...")
            
            script_content = """@echo off
echo Starting OrdnungsHub with automatic fixes...

"""
            
            if "Node.js dependencies not found" in '\n'.join(self.issues):
                script_content += """
echo Installing Node.js dependencies...
npm install
"""
            
            script_content += """
echo Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

echo Starting services...
start "FastAPI Backend" /min py src/backend/main.py
start "Mock Backend" /min py mock_backend.py
timeout /t 3 >nul
start "Frontend" npm run dev:react

echo All services started!
pause
"""
            
            with open('auto-start.bat', 'w') as f:
                f.write(script_content)
            
            self.success("Created auto-start.bat script")

    def run_full_diagnosis(self):
        """Run complete diagnostic suite"""
        print(f"{Colors.BOLD}OrdnungsHub Connection Diagnostics{Colors.RESET}")
        print("=" * 50)
        
        # Run all diagnostic tests
        self.check_dependencies()
        self.check_environment_files()
        self.diagnose_ports()
        self.diagnose_backend_connectivity()
        self.diagnose_frontend_connectivity()
        
        # Summary
        print(f"\n{Colors.BOLD}Diagnostic Summary{Colors.RESET}")
        print("=" * 30)
        
        if not self.issues:
            self.success("No issues detected!")
        else:
            print(f"{Colors.YELLOW}Issues found: {len(self.issues)}{Colors.RESET}")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.recommendations:
            print(f"\n{Colors.BLUE}Recommendations:{Colors.RESET}")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
            
            self.generate_startup_script()
        
        print(f"\n{Colors.GREEN}Diagnosis complete!{Colors.RESET}")

def main():
    diagnostics = ConnectionDiagnostics()
    diagnostics.run_full_diagnosis()

if __name__ == "__main__":
    main()
