"""
Comprehensive Error Handling Middleware for BlueBirdHub
Provides structured error responses and logging
"""
import traceback
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import uuid
from config.settings import get_settings

settings = get_settings()

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Centralized error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Handle all application errors"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return await self.handle_error(request, e)
    
    async def handle_error(self, request: Request, error: Exception) -> JSONResponse:
        """Convert exceptions to structured error responses"""
        error_id = str(uuid.uuid4())
        
        # Log error with context
        self._log_error(error, request, error_id)
        
        # Handle specific error types
        if isinstance(error, HTTPException):
            return self._handle_http_exception(error, error_id)
        elif isinstance(error, RequestValidationError):
            return self._handle_validation_error(error, error_id)
        elif isinstance(error, ValidationError):
            return self._handle_pydantic_error(error, error_id)
        elif isinstance(error, SQLAlchemyError):
            return self._handle_database_error(error, error_id)
        else:
            return self._handle_generic_error(error, error_id)
    
    def _log_error(self, error: Exception, request: Request, error_id: str):
        """Log error with context information"""
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        user_agent = request.headers.get("User-Agent", "unknown")
        
        log_context = {
            "error_id": error_id,
            "error_type": type(error).__name__,
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": user_agent[:100],
        }
        
        if isinstance(error, HTTPException):
            logger.warning(f"HTTP Exception: {log_context}")
        elif isinstance(error, (RequestValidationError, ValidationError)):
            logger.warning(f"Validation Error: {log_context}")
        elif isinstance(error, SQLAlchemyError):
            logger.error(f"Database Error: {log_context}")
        else:
            logger.error(f"Unexpected Error: {log_context}")
            
        # Log full traceback for 500 errors in development
        if settings.debug and not isinstance(error, HTTPException):
            logger.error(f"Full traceback for {error_id}:\n{traceback.format_exc()}")
    
    def _handle_http_exception(self, error: HTTPException, error_id: str) -> JSONResponse:
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": error.status_code,
                    "message": error.detail,
                    "error_id": error_id,
                }
            },
            headers=error.headers or {}
        )
    
    def _handle_validation_error(self, error: RequestValidationError, error_id: str) -> JSONResponse:
        """Handle FastAPI validation errors"""
        errors = []
        for err in error.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
                "input": err.get("input")
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "validation_error",
                    "code": 422,
                    "message": "Validation failed",
                    "details": errors,
                    "error_id": error_id,
                }
            }
        )
    
    def _handle_pydantic_error(self, error: ValidationError, error_id: str) -> JSONResponse:
        """Handle Pydantic validation errors"""
        errors = []
        for err in error.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "validation_error",
                    "code": 422,
                    "message": "Data validation failed",
                    "details": errors,
                    "error_id": error_id,
                }
            }
        )
    
    def _handle_database_error(self, error: SQLAlchemyError, error_id: str) -> JSONResponse:
        """Handle database errors"""
        if isinstance(error, IntegrityError):
            # Handle common integrity constraint violations
            error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)
            
            if "UNIQUE constraint failed" in error_msg:
                message = "A record with this information already exists"
            elif "FOREIGN KEY constraint failed" in error_msg:
                message = "Referenced record not found"
            elif "NOT NULL constraint failed" in error_msg:
                message = "Required field is missing"
            else:
                message = "Data integrity error"
            
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": {
                        "type": "integrity_error",
                        "code": 409,
                        "message": message,
                        "error_id": error_id,
                    }
                }
            )
        
        # Generic database error
        message = "Database operation failed" if not settings.debug else str(error)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "database_error",
                    "code": 500,
                    "message": message,
                    "error_id": error_id,
                }
            }
        )
    
    def _handle_generic_error(self, error: Exception, error_id: str) -> JSONResponse:
        """Handle unexpected errors"""
        message = "An unexpected error occurred"
        
        # In development, show more details
        if settings.debug:
            message = f"{type(error).__name__}: {str(error)}"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "internal_error",
                    "code": 500,
                    "message": message,
                    "error_id": error_id,
                }
            }
        )

# Custom exception classes
class BusinessLogicError(HTTPException):
    """Custom exception for business logic errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
        self.details = details

class AuthenticationError(HTTPException):
    """Custom exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"}
        )