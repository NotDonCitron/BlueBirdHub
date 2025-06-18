#!/usr/bin/env python3
"""Simple mock backend for testing"""

import json
import http.server
import socketserver

class SimpleHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/health':
            response = {"status": "healthy", "message": "Simple mock running"}
        else:
            response = {"status": "ok", "path": self.path}
            
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

if __name__ == "__main__":
    PORT = 8001
    try:
        with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
            print(f"Simple mock server running on port {PORT}")
            httpd.serve_forever()
    except OSError as e:
        print(f"Error: {e}")