"""
HTTP/2 Server Implementation for OrdnungsHub
Provides multiplexing, server push, and header compression for improved performance
"""

import asyncio
import ssl
import uvicorn
from hypercorn.config import Config as HypercornConfig
from hypercorn.asyncio import serve
from pathlib import Path
from loguru import logger
import os

class HTTP2Server:
    """
    HTTP/2 server implementation with advanced features
    """
    
    def __init__(self, app, host="127.0.0.1", port=8000):
        self.app = app
        self.host = host
        self.port = port
        self.config = HypercornConfig()
        self._setup_http2_config()
    
    def _setup_http2_config(self):
        """Configure HTTP/2 settings"""
        # Basic server settings
        self.config.bind = [f"{self.host}:{self.port}"]
        self.config.application_path = "src.backend.main:app"
        
        # HTTP/2 specific settings
        self.config.h2_max_concurrent_streams = 100
        self.config.h2_max_header_list_size = 65536
        self.config.h2_max_inbound_frame_size = 16384
        
        # Performance optimizations
        self.config.keep_alive_timeout = 30
        self.config.max_requests = 10000
        self.config.max_requests_jitter = 100
        
        # Enable HTTP/2 features
        self.config.http2_server_push = True
        self.config.http2_settings = {
            'HEADER_TABLE_SIZE': 4096,
            'ENABLE_PUSH': 1,
            'MAX_CONCURRENT_STREAMS': 100,
            'INITIAL_WINDOW_SIZE': 65535,
            'MAX_FRAME_SIZE': 16384,
            'MAX_HEADER_LIST_SIZE': 8192
        }
        
        # Security headers
        self.config.server_names = ["ordnungshub.local", "localhost"]
        
        # Development vs Production settings
        if os.getenv("NODE_ENV") == "production":
            self._setup_ssl_config()
        else:
            # Development mode - HTTP/2 cleartext (h2c)
            self.config.alpn_protocols = ["h2c", "http/1.1"]
            logger.info("HTTP/2 server configured for development (h2c)")
    
    def _setup_ssl_config(self):
        """Setup SSL configuration for production HTTP/2"""
        ssl_dir = Path(__file__).parent.parent.parent / "ssl"
        
        if ssl_dir.exists():
            cert_file = ssl_dir / "cert.pem"
            key_file = ssl_dir / "key.pem"
            
            if cert_file.exists() and key_file.exists():
                self.config.certfile = str(cert_file)
                self.config.keyfile = str(key_file)
                self.config.ssl_enabled = True
                self.config.alpn_protocols = ["h2", "http/1.1"]
                logger.info("HTTP/2 server configured with SSL")
            else:
                logger.warning("SSL certificates not found, falling back to HTTP/1.1")
        else:
            logger.warning("SSL directory not found, using HTTP/1.1")
    
    async def start(self):
        """Start the HTTP/2 server"""
        try:
            logger.info(f"Starting HTTP/2 server on {self.host}:{self.port}")
            logger.info(f"HTTP/2 features: multiplexing, server push, header compression")
            
            await serve(self.app, self.config)
            
        except Exception as e:
            logger.error(f"Failed to start HTTP/2 server: {e}")
            # Fallback to HTTP/1.1
            logger.info("Falling back to HTTP/1.1 server")
            await self._start_fallback_server()
    
    async def _start_fallback_server(self):
        """Fallback to standard HTTP/1.1 server"""
        uvicorn_config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            reload=False,
            log_level="info",
            access_log=True,
            server_header=False
        )
        
        server = uvicorn.Server(uvicorn_config)
        await server.serve()

class HTTP2Middleware:
    """
    Middleware to optimize HTTP/2 features
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add HTTP/2 optimizations
            await self._optimize_response(scope, receive, send)
        else:
            await self.app(scope, receive, send)
    
    async def _optimize_response(self, scope, receive, send):
        """Optimize HTTP/2 response"""
        
        # Server push hints for critical resources
        critical_resources = [
            "/static/js/main.js",
            "/static/css/main.css",
            "/static/js/vendor.js"
        ]
        
        # Add push hints to response headers
        async def send_with_push_hints(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # Add Link headers for server push
                for resource in critical_resources:
                    link_header = f"<{resource}>; rel=preload; as=script" if resource.endswith('.js') else f"<{resource}>; rel=preload; as=style"
                    headers.append([b"link", link_header.encode()])
                
                # Add HTTP/2 optimization headers
                headers.extend([
                    [b"x-http2-multiplexing", b"enabled"],
                    [b"x-http2-server-push", b"enabled"],
                    [b"x-http2-header-compression", b"enabled"]
                ])
                
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_push_hints)

def create_http2_app():
    """Create FastAPI app with HTTP/2 optimizations"""
    from src.backend.main import app
    
    # Add HTTP/2 middleware
    app.add_middleware(HTTP2Middleware)
    
    return app

# HTTP/2 performance utilities
class HTTP2PerformanceMonitor:
    """Monitor HTTP/2 specific performance metrics"""
    
    def __init__(self):
        self.stream_count = 0
        self.pushed_resources = 0
        self.compression_ratio = 0.0
    
    def log_stream_created(self):
        """Log new HTTP/2 stream creation"""
        self.stream_count += 1
        if self.stream_count % 10 == 0:
            logger.debug(f"HTTP/2 streams created: {self.stream_count}")
    
    def log_server_push(self, resource):
        """Log server push event"""
        self.pushed_resources += 1
        logger.debug(f"Server pushed resource: {resource}")
    
    def calculate_compression_ratio(self, original_size, compressed_size):
        """Calculate header compression ratio"""
        if original_size > 0:
            self.compression_ratio = (original_size - compressed_size) / original_size
            logger.debug(f"Header compression ratio: {self.compression_ratio:.2%}")

# Global HTTP/2 monitor instance
http2_monitor = HTTP2PerformanceMonitor()

if __name__ == "__main__":
    # Development server start
    app = create_http2_app()
    server = HTTP2Server(app)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("HTTP/2 server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")