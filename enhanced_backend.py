#!/usr/bin/env python3
"""
Enhanced Backend mit API-Integrationen
Erweitert den ultra_simple_backend um API-Features
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import urlparse, parse_qs

# Füge src zum Python-Path hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.backend.api_integrations import api_manager

# Existierender Code...
from ultra_simple_backend import workspaces_storage, tasks_storage, update_parent_task_status

class EnhancedRequestHandler(BaseHTTPRequestHandler):
    """Erweitert den Handler um API-Endpoints"""
    
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers(200)
    
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Bestehende Endpoints
        if path == '/api/health':
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "message": "✅ Enhanced OrdnungsHub Backend with APIs",
                "apis_loaded": list(api_manager.keys.keys())
            }).encode())
            
        elif path == '/api/workspaces':
            self._set_headers()
            self.wfile.write(json.dumps(workspaces_storage).encode())
            
        elif path == '/api/tasks':
            self._set_headers()
            self.wfile.write(json.dumps(tasks_storage).encode())
            
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # 🧠 AI Zusammenfassung
        if path == '/api/ai/summarize':
            text = data.get('text', '')
            length = data.get('length', 'medium')
            
            result = api_manager.summarize_with_cohere(text, length)
            
            if result['success']:
                self._set_headers()
                self.wfile.write(json.dumps({
                    "summary": result['summary'],
                    "provider": "cohere"
                }).encode())
            else:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": result['error']}).encode())
        
        # 📄 Dokument-Klassifizierung
        elif path == '/api/ai/classify':
            text = data.get('text', '')
            
            result = api_manager.classify_document(text)
            
            if 'labels' in result:
                self._set_headers()
                self.wfile.write(json.dumps({
                    "classification": result['labels'][0],
                    "confidence": result['scores'][0],
                    "all_results": [
                        {"label": l, "score": s} 
                        for l, s in zip(result['labels'], result['scores'])
                    ]
                }).encode())
            else:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": "Classification failed"}).encode())
        
        # 🔍 Web-Suche  
        elif path == '/api/search':
            query = data.get('query', '')
            
            result = api_manager.search_web(query)
            
            if 'web' in result:
                self._set_headers()
                self.wfile.write(json.dumps({
                    "results": result['web'].get('results', [])[:5],
                    "query": query
                }).encode())
            else:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": "Search failed"}).encode())
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, EnhancedRequestHandler)
    print(f'🚀 Enhanced OrdnungsHub Backend running on http://localhost:{port}')
    print('📋 Available API Endpoints:')
    print('  - GET  /api/health')
    print('  - GET  /api/workspaces')
    print('  - GET  /api/tasks')
    print('  - POST /api/ai/summarize')
    print('  - POST /api/ai/classify')
    print('  - POST /api/search')
    print('\n✨ Press Ctrl+C to stop\n')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
