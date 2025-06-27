"""
Environment Configuration Manager for BlueBirdHub
Centralizes all environment-specific settings
"""
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from functools import lru_cache

class Settings:
    """Application settings with environment-aware configuration"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = self._get_bool("DEBUG", True if self.environment == "development" else False)
        
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_list(self, key: str, default: List[str] = None) -> List[str]:
        """Get list value from environment (comma-separated)"""
        if default is None:
            default = []
        value = os.getenv(key, "")
        return [item.strip() for item in value.split(",") if item.strip()] or default

    # Application Settings
    @property
    def app_name(self) -> str:
        return os.getenv("APP_NAME", "BlueBirdHub")
    
    @property
    def app_version(self) -> str:
        return os.getenv("APP_VERSION", "1.0.0")
    
    @property
    def app_url(self) -> str:
        default_url = "http://localhost:8001" if self.environment == "development" else "https://your-domain.com"
        return os.getenv("APP_URL", default_url)
    
    @property
    def frontend_url(self) -> str:
        default_url = "http://localhost:3000" if self.environment == "development" else "https://your-frontend-domain.com"
        return os.getenv("FRONTEND_URL", default_url)

    # Database Settings
    @property
    def database_url(self) -> str:
        if self.environment == "development":
            return os.getenv("DATABASE_URL", "sqlite:///./bluebbird.db")
        return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/bluebbirdhub")
    
    @property
    def db_echo(self) -> bool:
        return self._get_bool("SHOW_SQL_QUERIES", False)

    # Redis Settings
    @property
    def redis_url(self) -> str:
        return os.getenv("REDIS_URL", "redis://localhost:6379")
    
    @property
    def redis_password(self) -> Optional[str]:
        return os.getenv("REDIS_PASSWORD") or None
    
    @property
    def redis_ssl(self) -> bool:
        return self._get_bool("REDIS_SSL", False)
    
    @property
    def redis_max_connections(self) -> int:
        return self._get_int("REDIS_MAX_CONNECTIONS", 20 if self.environment == "development" else 100)

    # Authentication Settings
    @property
    def auth_secret_key(self) -> str:
        key = os.getenv("AUTH_SECRET_KEY")
        if not key or (self.environment == "production" and len(key) < 32):
            raise ValueError("AUTH_SECRET_KEY must be set and at least 32 characters in production")
        return key or "development-secret-key-change-this"
    
    @property
    def jwt_algorithm(self) -> str:
        return os.getenv("JWT_ALGORITHM", "HS256")
    
    @property
    def jwt_access_token_expire_minutes(self) -> int:
        default = 30 if self.environment == "development" else 15
        return self._get_int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default)
    
    @property
    def jwt_refresh_token_expire_days(self) -> int:
        return self._get_int("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7)

    # CORS Settings
    @property
    def cors_origins(self) -> List[str]:
        default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"] if self.environment == "development" else []
        return self._get_list("CORS_ORIGINS", default_origins)
    
    @property
    def cors_allow_credentials(self) -> bool:
        return self._get_bool("CORS_ALLOW_CREDENTIALS", True)
    
    @property
    def cors_allow_methods(self) -> List[str]:
        return self._get_list("CORS_ALLOW_METHODS", ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    @property
    def cors_allow_headers(self) -> List[str]:
        return self._get_list("CORS_ALLOW_HEADERS", ["*"])

    # Rate Limiting
    @property
    def rate_limit_enabled(self) -> bool:
        return self._get_bool("RATE_LIMIT_ENABLE", True)
    
    @property
    def rate_limit_requests_per_minute(self) -> int:
        default = 100 if self.environment == "development" else 60
        return self._get_int("RATE_LIMIT_REQUESTS_PER_MINUTE", default)
    
    @property
    def rate_limit_burst_size(self) -> int:
        default = 20 if self.environment == "development" else 10
        return self._get_int("RATE_LIMIT_BURST_SIZE", default)

    # Logging Settings
    @property
    def log_level(self) -> str:
        default = "DEBUG" if self.environment == "development" else "INFO"
        if self.environment == "production":
            default = "WARNING"
        return os.getenv("LOG_LEVEL", default)
    
    @property
    def log_file(self) -> str:
        return os.getenv("LOG_FILE", "logs/bluebbirdhub.log")
    
    @property
    def log_max_size_mb(self) -> int:
        return self._get_int("LOG_MAX_SIZE_MB", 10)
    
    @property
    def log_backup_count(self) -> int:
        return self._get_int("LOG_BACKUP_COUNT", 5)

    # File Upload Settings
    @property
    def upload_directory(self) -> str:
        return os.getenv("UPLOAD_DIRECTORY", "./uploads")
    
    @property
    def max_file_size_mb(self) -> int:
        default = 50 if self.environment == "development" else 100
        return self._get_int("MAX_FILE_SIZE_MB", default)
    
    @property
    def allowed_file_types(self) -> List[str]:
        return self._get_list("ALLOWED_FILE_TYPES", ["pdf", "doc", "docx", "txt", "png", "jpg", "jpeg", "gif"])

    # API Documentation
    @property
    def enable_api_docs(self) -> bool:
        return self._get_bool("ENABLE_API_DOCS", self.environment != "production")
    
    @property
    def api_docs_url(self) -> str:
        return os.getenv("API_DOCS_URL", "/docs")
    
    @property
    def openapi_url(self) -> str:
        return os.getenv("OPENAPI_URL", "/openapi.json")

    # Performance Settings
    @property
    def workers(self) -> int:
        return self._get_int("WORKERS", 1 if self.environment == "development" else 4)
    
    @property
    def max_worker_connections(self) -> int:
        return self._get_int("MAX_WORKER_CONNECTIONS", 100 if self.environment == "development" else 1000)

    # Monitoring Settings
    @property
    def enable_metrics(self) -> bool:
        return self._get_bool("ENABLE_METRICS", True)
    
    @property
    def metrics_port(self) -> int:
        return self._get_int("METRICS_PORT", 9090)
    
    @property
    def sentry_dsn(self) -> Optional[str]:
        return os.getenv("SENTRY_DSN") or None

    # AI Services
    @property
    def openai_api_key(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")
    
    @property
    def anthropic_api_key(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")
    
    @property
    def ai_model_default(self) -> str:
        default = "gpt-3.5-turbo" if self.environment == "development" else "gpt-4"
        return os.getenv("AI_MODEL_DEFAULT", default)

    def validate_production_settings(self) -> List[str]:
        """Validate production-specific settings"""
        errors = []
        
        if self.environment == "production":
            if not self.auth_secret_key or len(self.auth_secret_key) < 32:
                errors.append("AUTH_SECRET_KEY must be at least 32 characters in production")
            
            if self.debug:
                errors.append("DEBUG should be False in production")
            
            if "localhost" in self.app_url:
                errors.append("APP_URL should not contain localhost in production")
            
            if not self.sentry_dsn:
                errors.append("SENTRY_DSN should be configured for production monitoring")
            
            if "sqlite" in self.database_url.lower():
                errors.append("SQLite should not be used in production")
        
        return errors

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Global settings instance
settings = get_settings()