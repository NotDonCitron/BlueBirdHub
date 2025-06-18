#!/usr/bin/env python3
"""
Simple HTTP server to serve the collaborative workspace demo
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def start_demo_server():
    """Start a simple HTTP server for the demo"""
    port = 8080
    
    # Change to the directory containing our demo files
    os.chdir(Path(__file__).parent)
    
    # Create handler
    handler = http.server.SimpleHTTPRequestHandler
    
    # Create server
    with socketserver.TCPServer(("", port), handler) as httpd:
        print("🚀 OrdnungsHub Collaborative Workspace Demo Server")
        print("=" * 60)
        print(f"🌐 Server running on: http://localhost:{port}")
        print(f"📄 Demo page: http://localhost:{port}/collaborative_workspace_demo.html")
        print("⏹️  Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Try to open the demo in browser
        try:
            demo_url = f"http://localhost:{port}/collaborative_workspace_demo.html"
            webbrowser.open(demo_url)
            print(f"🌐 Opening demo in browser: {demo_url}")
        except Exception as e:
            print(f"⚠️  Could not auto-open browser: {e}")
            print(f"🔗 Please open manually: http://localhost:{port}/collaborative_workspace_demo.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped by user")
            print("✅ Demo session completed")

if __name__ == "__main__":
    start_demo_server()