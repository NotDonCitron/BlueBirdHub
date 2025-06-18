#!/usr/bin/env python3
"""
OrdnungsHub Connection Diagnostic Tool
Identifies and helps fix front/backend connection issues
"""

import asyncio
import aiohttp
import json
import sys
import subprocess
import platform
from typing import Dict, List, Tuple, Optional
from datetime import datetime

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
        self.log(f"✅ {message}", Colors.GREEN)

    def warning(self, message: str):
        self.log(f"⚠️  {message}", Colors.YELLOW)
        self.issues.append(message)

    def error(self, message: str):
        self.log(f"❌ {message}", Colors.RED)
        self.issues.append(message)

    def info(self, message: str):
        self.log(f"ℹ️  {message}", Colors.BLUE)

    def check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netstat", "-ano"], 
                    capture_output=True, 
                    text=True
                )
                return f":{port}" in result.stdout
            else:
                result = subprocess.run(
                    ["lsof", f"-i:{port}"], 
                    capture_output=True, 
                    text=True
                )
                return result.returncode == 0
        except:
            return False

    async def test_endpoint(self, url: str, timeout: int = 5) -> Tuple[bool, Optional[Dict]]:
        """Test if an endpoint is responding"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, data
                    else:
                        return False, {"error": f"HTTP {response.status}"}
        except Exception as e:
            return False, {"error": str(e)}

    async def diagnose_ports(self):
        """Check all required ports"""
        self.info("Checking port availability...")
        
        for name, port in self.ports.items():
            if self.check_port(port):
                if name == 'frontend':
                    self.success(f"{name.title()} service running on port {port}")
                else:
                    self.success(f"{name.title()} service running on port {port}")
            else:
                self.warning(f"{name.title()} service not running on port {port}")

    async def diagnose_backend_connectivity(self):
        """Test backend endpoints"""
        self.info("Testing backend connectivity...")
        
        endpoints = [
            ("FastAPI Backend", "http://localhost:8000/health"),
            ("Mock Backend", "http://localhost:8001/health"),
        ]
        
        working_backends = []
        
        for name, url in endpoints:
            success, data = await self.test_endpoint(url)
            if success:
                self.success(f"{name} responding: {data.get('status', 'unknown')}")
                working_backends.append(name)
            else:
                self.error(f"{name} not responding: {data.get('error', 'unknown error')}")
        
        if not working_backends:
            self.error("No backend services are responding!")
            self.recommendations.append("Start backend services with: python src/backend/main.py")
            self.recommendations.append("Or start mock backend with: python mock_backend.py")
        elif len(working_backends) == 1:
            self.warning(f"Only {working_backends[0]} is running")
            self.recommendations.append("Consider running both backends for redundancy")

    async def diagnose_frontend_connectivity(self):
        """Test frontend connectivity"""
        self.info("Testing frontend connectivity...")
        
        frontend_url = "http://localhost:3001"
        success, data = await self.test_endpoint(frontend_url, timeout=3)
        
        if success:
            self.success("Frontend responding correctly")
        else:
            self.error(f"Frontend not responding: {data.get('error', 'unknown error')}")
            self.recommendations.append("Start frontend with: npm run dev:react")

    async def diagnose_cors_issues(self):
        """Check for potential CORS issues"""
        self.info("Checking CORS configuration...")
        
        # Try to make a cross-origin request
        try:
            headers = {
                'Origin': 'http://localhost:3001',
                'Access-Control-Request-Method': 'GET',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.options("http://localhost:8000/health", headers=headers) as response:
                    cors_headers = response.headers
                    
                    if 'Access-Control-Allow-Origin' in cors_headers:
                        allowed_origin = cors_headers['Access-Control-Allow-Origin']
                        if allowed_origin == '*' or 'localhost:3001' in allowed_origin:
                            self.success("CORS properly configured")
                        else:
                            self.warning(f"CORS may be restrictive: {allowed_origin}")
                            self.recommendations.append("Check CORS_ORIGINS in .env file")
                    else:
                        self.warning("CORS headers not found")
                        self.recommendations.append("Verify CORS middleware in backend")
        except Exception as e:
            self.warning(f"Could not test CORS: {e}")

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
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            self.success("Python backend dependencies installed")
        except ImportError:
            self.error("Python backend dependencies missing")
            self.recommendations.append("Install Python dependencies: pip install -r requirements.txt")
        
        # Check if node_modules exists
        import os
        if os.path.exists('node_modules'):
            self.success("Node.js dependencies installed")
        else:
            self.warning("Node.js dependencies not found")
            self.recommendations.append("Install Node.js dependencies: npm install")

    def generate_startup_script(self):
        """Generate a custom startup script based on detected issues"""
        if self.issues:
            self.info("Generating custom startup script...")
            
            script_content = """#!/bin/bash
# Auto-generated startup script based on diagnostics

echo "🔧 Starting OrdnungsHub with automatic fixes..."

"""
            
            if "Python backend dependencies missing" in '\n'.join(self.issues):
                script_content += """
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
"""
            
            if "Node.js dependencies not found" in '\n'.join(self.issues):
                script_content += """
echo "📦 Installing Node.js dependencies..."
npm install
"""
            
            script_content += """
echo "🧹 Cleaning up ports..."
kill -9 $(lsof -ti:3001) 2>/dev/null || true
kill -9 $(lsof -ti:8000) 2>/dev/null || true
kill -9 $(lsof -ti:8001) 2>/dev/null || true

echo "🚀 Starting services..."
python src/backend/main.py &
python mock_backend.py &
sleep 3
npm run dev:react &

echo "✅ All services started!"
"""
            
            with open('auto-start.sh', 'w') as f:
                f.write(script_content)
            
            import stat
            os.chmod('auto-start.sh', stat.S_IRWXU)
            
            self.success("Created auto-start.sh script")

    async def run_full_diagnosis(self):
        """Run complete diagnostic suite"""
        print(f"{Colors.BOLD}🔍 OrdnungsHub Connection Diagnostics{Colors.RESET}")
        print("=" * 50)
        
        # Run all diagnostic tests
        self.check_dependencies()
        self.check_environment_files()
        await self.diagnose_ports()
        await self.diagnose_backend_connectivity()
        await self.diagnose_frontend_connectivity()
        await self.diagnose_cors_issues()
        
        # Summary
        print(f"\n{Colors.BOLD}📊 Diagnostic Summary{Colors.RESET}")
        print("=" * 30)
        
        if not self.issues:
            self.success("No issues detected! 🎉")
        else:
            print(f"{Colors.YELLOW}Issues found: {len(self.issues)}{Colors.RESET}")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.recommendations:
            print(f"\n{Colors.BLUE}💡 Recommendations:{Colors.RESET}")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
            
            self.generate_startup_script()
        
        print(f"\n{Colors.GREEN}✅ Diagnosis complete!{Colors.RESET}")

async def main():
    diagnostics = ConnectionDiagnostics()
    await diagnostics.run_full_diagnosis()

if __name__ == "__main__":
    asyncio.run(main())
