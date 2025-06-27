"""
Security Middleware for BlueBirdHub
Implements various security measures including rate limiting and security headers
"""
import time
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
import ipaddress
from loguru import logger

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, deque] = defaultdict(deque)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support"""
        # Check for forwarded IP first (behind reverse proxy)
        forwarded_ip = request.headers.get("X-Forwarded-For")
        if forwarded_ip:
            # Take the first IP if multiple are present
            ip = forwarded_ip.split(",")[0].strip()
            try:
                # Validate IP address
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                pass
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            try:
                ipaddress.ip_address(real_ip)
                return real_ip
            except ValueError:
                pass
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove old requests outside the time window
        while client_requests and client_requests[0] <= now - self.period:
            client_requests.popleft()
        
        # Check if limit exceeded
        if len(client_requests) >= self.calls:
            return True
        
        # Record this request
        client_requests.append(now)
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_ip = self.get_client_ip(request)
        
        # Apply stricter limits to auth endpoints
        if request.url.path.startswith("/auth/"):
            # More restrictive for auth endpoints: 10 requests per minute
            if self.is_auth_rate_limited(client_ip):
                logger.warning(f"Auth rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please try again later.",
                    headers={"Retry-After": "60"}
                )
        
        # General rate limiting
        elif self.is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(self.period)}
            )
        
        response = await call_next(request)
        return response
    
    def is_auth_rate_limited(self, client_ip: str, calls: int = 10, period: int = 60) -> bool:
        """Stricter rate limiting for authentication endpoints"""
        now = time.time()
        auth_key = f"auth_{client_ip}"
        client_requests = self.clients[auth_key]
        
        # Remove old requests
        while client_requests and client_requests[0] <= now - period:
            client_requests.popleft()
        
        # Check limit
        if len(client_requests) >= calls:
            return True
        
        # Record request
        client_requests.append(now)
        return False

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
        self.security_headers = self._get_security_headers()
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get appropriate security headers based on environment"""
        headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        if self.environment == "production":
            headers.update({
                # Force HTTPS in production
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                
                # Content Security Policy
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self'; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none';"
                ),
            })
        else:
            # More relaxed CSP for development
            headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: blob: https:; "
                "connect-src 'self' ws: wss: http: https:;"
            )
        
        return headers
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware for admin endpoints"""
    
    def __init__(self, app, admin_ips: list = None, admin_paths: list = None):
        super().__init__(app)
        self.admin_ips = set(admin_ips or [])
        self.admin_paths = admin_paths or ["/docs", "/redoc", "/openapi.json"]
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_ip = request.headers.get("X-Forwarded-For")
        if forwarded_ip:
            return forwarded_ip.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Check IP whitelist for admin endpoints"""
        # Check if this is an admin endpoint
        if any(request.url.path.startswith(path) for path in self.admin_paths):
            client_ip = self.get_client_ip(request)
            
            # If whitelist is configured and IP not in whitelist
            if self.admin_ips and client_ip not in self.admin_ips:
                logger.warning(f"Unauthorized admin access attempt from IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        response = await call_next(request)
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log security-relevant requests"""
    
    def __init__(self, app, log_auth_attempts: bool = True):
        super().__init__(app)
        self.log_auth_attempts = log_auth_attempts
    
    async def dispatch(self, request: Request, call_next):
        """Log relevant security events"""
        start_time = time.time()
        
        # Get client info
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log authentication attempts
        if self.log_auth_attempts and request.url.path.startswith("/auth/"):
            log_data = {
                "ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "response_time": round(process_time, 3),
                "user_agent": user_agent[:100],  # Truncate long user agents
            }
            
            if response.status_code >= 400:
                logger.warning(f"Auth failure: {log_data}")
            else:
                logger.info(f"Auth success: {log_data}")
        
        # Log failed requests
        elif response.status_code >= 400:
            logger.warning(
                f"Failed request: {client_ip} {request.method} {request.url.path} "
                f"-> {response.status_code} ({process_time:.3f}s)"
            )
        
        # Add response time header
        response.headers["X-Response-Time"] = str(round(process_time, 3))
        
        return response