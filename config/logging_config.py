"""
Logging Configuration for BlueBirdHub
Provides structured logging with different levels and outputs
"""
import os
import sys
from pathlib import Path
from loguru import logger
from config.settings import get_settings

settings = get_settings()

class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Configure loguru logging"""
        # Remove default logger
        logger.remove()
        
        # Console logging
        self._setup_console_logging()
        
        # File logging
        self._setup_file_logging()
        
        # Security logging
        self._setup_security_logging()
        
        # Error logging
        self._setup_error_logging()
        
        # Performance logging
        if settings.enable_metrics:
            self._setup_performance_logging()
        
        logger.info(f"Logging configured for {settings.environment} environment")
    
    def _setup_console_logging(self):
        """Configure console logging"""
        log_level = settings.log_level
        
        if settings.environment == "production":
            # Minimal console output in production
            logger.add(
                sys.stdout,
                level="WARNING",
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                       "<level>{message}</level>",
                colorize=True,
                backtrace=False,
                diagnose=False
            )
        else:
            # Verbose console output for development
            logger.add(
                sys.stdout,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                       "<level>{message}</level>",
                colorize=True,
                backtrace=True,
                diagnose=True
            )
    
    def _setup_file_logging(self):
        """Configure general file logging"""
        logger.add(
            self.log_dir / "app.log",
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=f"{settings.log_max_size_mb} MB",
            retention=f"{settings.log_backup_count} files",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True  # Async logging
        )
    
    def _setup_security_logging(self):
        """Configure security event logging"""
        logger.add(
            self.log_dir / "security.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event_type]} | {message}",
            filter=lambda record: "security" in record["extra"],
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            enqueue=True
        )
    
    def _setup_error_logging(self):
        """Configure error logging"""
        logger.add(
            self.log_dir / "errors.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="50 MB",
            retention="60 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
    
    def _setup_performance_logging(self):
        """Configure performance logging"""
        logger.add(
            self.log_dir / "performance.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[metric_type]} | {message}",
            filter=lambda record: "performance" in record["extra"],
            rotation="100 MB",
            retention="7 days",
            compression="zip",
            enqueue=True
        )

# Security event logger
class SecurityLogger:
    """Specialized logger for security events"""
    
    @staticmethod
    def log_auth_attempt(username: str, ip_address: str, success: bool, **kwargs):
        """Log authentication attempt"""
        event_type = "AUTH_SUCCESS" if success else "AUTH_FAILURE"
        logger.bind(security=True, event_type=event_type).info(
            f"Authentication {event_type.lower()}: user={username}, ip={ip_address}, extra={kwargs}"
        )
    
    @staticmethod
    def log_access_denied(resource: str, user: str, ip_address: str, reason: str):
        """Log access denied events"""
        logger.bind(security=True, event_type="ACCESS_DENIED").warning(
            f"Access denied: resource={resource}, user={user}, ip={ip_address}, reason={reason}"
        )
    
    @staticmethod
    def log_rate_limit_exceeded(ip_address: str, endpoint: str, limit: int):
        """Log rate limit violations"""
        logger.bind(security=True, event_type="RATE_LIMIT_EXCEEDED").warning(
            f"Rate limit exceeded: ip={ip_address}, endpoint={endpoint}, limit={limit}"
        )
    
    @staticmethod
    def log_suspicious_activity(activity_type: str, details: dict, ip_address: str):
        """Log suspicious activities"""
        logger.bind(security=True, event_type="SUSPICIOUS_ACTIVITY").error(
            f"Suspicious activity detected: type={activity_type}, ip={ip_address}, details={details}"
        )
    
    @staticmethod
    def log_data_access(user: str, resource: str, action: str, success: bool):
        """Log data access events"""
        event_type = "DATA_ACCESS_SUCCESS" if success else "DATA_ACCESS_FAILURE"
        logger.bind(security=True, event_type=event_type).info(
            f"Data access: user={user}, resource={resource}, action={action}, success={success}"
        )

# Performance logger
class PerformanceLogger:
    """Specialized logger for performance metrics"""
    
    @staticmethod
    def log_request_timing(endpoint: str, method: str, duration_ms: float, status_code: int):
        """Log request timing"""
        logger.bind(performance=True, metric_type="REQUEST_TIMING").info(
            f"Request completed: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
        )
    
    @staticmethod
    def log_database_query(query_type: str, duration_ms: float, rows_affected: int = None):
        """Log database query performance"""
        logger.bind(performance=True, metric_type="DB_QUERY").info(
            f"Database query: type={query_type}, duration={duration_ms:.2f}ms, rows={rows_affected}"
        )
    
    @staticmethod
    def log_cache_operation(operation: str, key: str, hit: bool, duration_ms: float = None):
        """Log cache operations"""
        logger.bind(performance=True, metric_type="CACHE_OPERATION").info(
            f"Cache {operation}: key={key}, hit={hit}, duration={duration_ms:.2f}ms"
        )
    
    @staticmethod
    def log_resource_usage(cpu_percent: float, memory_mb: float, connections: int):
        """Log resource usage"""
        logger.bind(performance=True, metric_type="RESOURCE_USAGE").info(
            f"Resource usage: CPU={cpu_percent:.1f}%, Memory={memory_mb:.1f}MB, Connections={connections}"
        )

# Application event logger
class ApplicationLogger:
    """General application event logger"""
    
    @staticmethod
    def log_startup(component: str, duration_ms: float = None):
        """Log application startup events"""
        message = f"Component started: {component}"
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"
        logger.info(message)
    
    @staticmethod
    def log_shutdown(component: str, reason: str = None):
        """Log application shutdown events"""
        message = f"Component shutdown: {component}"
        if reason:
            message += f" (reason: {reason})"
        logger.info(message)
    
    @staticmethod
    def log_configuration_change(setting: str, old_value: str, new_value: str, user: str):
        """Log configuration changes"""
        logger.warning(
            f"Configuration changed: {setting} changed from '{old_value}' to '{new_value}' by {user}"
        )
    
    @staticmethod
    def log_feature_usage(feature: str, user: str, parameters: dict = None):
        """Log feature usage for analytics"""
        message = f"Feature used: {feature} by {user}"
        if parameters:
            message += f" with parameters: {parameters}"
        logger.info(message)

# Error tracking integration
class ErrorTracker:
    """Integration with error tracking services"""
    
    def __init__(self):
        self.sentry_enabled = bool(settings.sentry_dsn)
        if self.sentry_enabled:
            self._setup_sentry()
    
    def _setup_sentry(self):
        """Setup Sentry error tracking"""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.loguru import LoguruIntegration
            
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.environment,
                traces_sample_rate=1.0 if settings.environment == "development" else 0.1,
                integrations=[
                    FastApiIntegration(auto_enable=True),
                    SqlalchemyIntegration(),
                    LoguruIntegration(),
                ],
                send_default_pii=False,  # Don't send personally identifiable information
                attach_stacktrace=True,
                debug=settings.debug,
            )
            logger.info("Sentry error tracking initialized")
        except ImportError:
            logger.warning("Sentry SDK not installed, error tracking disabled")
    
    @staticmethod
    def capture_exception(error: Exception, context: dict = None):
        """Capture exception with context"""
        if context:
            try:
                import sentry_sdk
                with sentry_sdk.configure_scope() as scope:
                    for key, value in context.items():
                        scope.set_tag(key, value)
                sentry_sdk.capture_exception(error)
            except ImportError:
                pass
        
        # Always log locally
        logger.exception(f"Exception captured: {error}")

# Initialize logging
def setup_application_logging():
    """Setup all application logging"""
    logging_config = LoggingConfig()
    logging_config.setup_logging()
    
    # Initialize error tracking
    error_tracker = ErrorTracker()
    
    return {
        "security_logger": SecurityLogger(),
        "performance_logger": PerformanceLogger(),
        "app_logger": ApplicationLogger(),
        "error_tracker": error_tracker,
    }

# Global loggers
loggers = setup_application_logging()
security_logger = loggers["security_logger"]
performance_logger = loggers["performance_logger"]
app_logger = loggers["app_logger"]
error_tracker = loggers["error_tracker"]