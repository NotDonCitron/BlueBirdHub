"""
Security Configuration for BlueBirdHub
Centralized security settings and utilities
"""
import secrets
import os
from typing import List, Dict, Any
from config.settings import get_settings

settings = get_settings()

class SecurityConfig:
    """Security configuration manager"""
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a cryptographically secure secret key"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """Get CORS configuration based on environment"""
        if settings.environment == "production":
            return {
                "allow_origins": settings.cors_origins,
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type", "X-Requested-With"],
                "expose_headers": ["X-Response-Time"],
            }
        else:
            # More permissive for development
            return {
                "allow_origins": settings.cors_origins or ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            }
    
    @staticmethod
    def get_rate_limit_config() -> Dict[str, int]:
        """Get rate limiting configuration"""
        if settings.environment == "production":
            return {
                "general_calls": 60,      # 60 requests per minute
                "general_period": 60,
                "auth_calls": 5,          # 5 auth attempts per minute
                "auth_period": 60,
            }
        else:
            # More permissive for development
            return {
                "general_calls": 200,     # 200 requests per minute
                "general_period": 60,
                "auth_calls": 20,         # 20 auth attempts per minute
                "auth_period": 60,
            }
    
    @staticmethod
    def get_admin_ip_whitelist() -> List[str]:
        """Get IP whitelist for admin endpoints"""
        whitelist = os.getenv("ADMIN_IP_WHITELIST", "").split(",")
        return [ip.strip() for ip in whitelist if ip.strip()]
    
    @staticmethod
    def should_enable_docs() -> bool:
        """Check if API documentation should be enabled"""
        return settings.enable_api_docs and settings.environment != "production"
    
    @staticmethod
    def get_security_headers_config() -> Dict[str, str]:
        """Get security headers configuration"""
        base_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        if settings.environment == "production":
            base_headers.update({
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self';"
                ),
            })
        
        return base_headers
    
    @staticmethod
    def validate_production_security() -> List[str]:
        """Validate security configuration for production"""
        issues = []
        
        if settings.environment == "production":
            # Check secret key
            secret_key = settings.auth_secret_key
            if not secret_key or len(secret_key) < 32:
                issues.append("AUTH_SECRET_KEY must be at least 32 characters in production")
            
            if "change-this" in secret_key.lower() or "default" in secret_key.lower():
                issues.append("AUTH_SECRET_KEY appears to be a default value")
            
            # Check CORS
            if not settings.cors_origins or "*" in settings.cors_origins:
                issues.append("CORS origins should be restricted in production")
            
            # Check debug mode
            if settings.debug:
                issues.append("DEBUG should be False in production")
            
            # Check database
            if "sqlite" in settings.database_url.lower():
                issues.append("SQLite should not be used in production")
            
            # Check HTTPS
            if not settings.app_url.startswith("https://"):
                issues.append("APP_URL should use HTTPS in production")
        
        return issues

# Global security config instance
security_config = SecurityConfig()