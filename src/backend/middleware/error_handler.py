from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from loguru import logger
import traceback
import time
from typing import Union

class ErrorDetail:
    def __init__(self, message: str, code: str, field: str = None):
        self.message = message
        self.code = code
        self.field = field

async def error_handler_middleware(request: Request, call_next):
    """Global error handler middleware"""
    start_time = time.time()
    request_id = f"{int(time.time())}-{request.client.host}"
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log successful requests
        logger.info(
            f"Request {request_id} - {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as exc:
        process_time = time.time() - start_time
        error_response = await handle_error(exc, request, request_id, process_time)
        return error_response

async def handle_error(
    exc: Exception, 
    request: Request, 
    request_id: str,
    process_time: float
) -> JSONResponse:
    """Convert exceptions to proper JSON responses"""
    
    # Log error details
    logger.error(
        f"Request {request_id} failed - {request.method} {request.url.path} "
        f"- Error: {type(exc).__name__}: {str(exc)} - Time: {process_time:.3f}s"
    )
    logger.debug(f"Traceback: {traceback.format_exc()}")
    
    # Handle different error types
    if isinstance(exc, RequestValidationError):
        return await handle_validation_error(exc, request_id)
    
    elif isinstance(exc, StarletteHTTPException):
        return await handle_http_error(exc, request_id)
    
    elif isinstance(exc, IntegrityError):
        return await handle_database_integrity_error(exc, request_id)
    
    elif isinstance(exc, SQLAlchemyError):
        return await handle_database_error(exc, request_id)
    
    else:
        return await handle_unexpected_error(exc, request_id)

async def handle_validation_error(exc: RequestValidationError, request_id: str) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    
    for error in exc.errors():
        field_path = '.'.join(str(x) for x in error['loc'])
        errors.append({
            'field': field_path,
            'message': error['msg'],
            'type': error['type']
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': errors,
            'request_id': request_id
        }
    )

async def handle_http_error(exc: StarletteHTTPException, request_id: str) -> JSONResponse:
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': exc.detail or 'HTTP Error',
            'message': get_user_friendly_message(exc.status_code),
            'status_code': exc.status_code,
            'request_id': request_id
        }
    )

async def handle_database_integrity_error(exc: IntegrityError, request_id: str) -> JSONResponse:
    """Handle database integrity constraint violations"""
    message = 'Data conflict'
    
    if 'UNIQUE constraint failed' in str(exc):
        message = 'This record already exists'
    elif 'FOREIGN KEY constraint failed' in str(exc):
        message = 'Related record not found'
    elif 'NOT NULL constraint failed' in str(exc):
        message = 'Required field is missing'
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            'error': 'Database Integrity Error',
            'message': message,
            'request_id': request_id
        }
    )

async def handle_database_error(exc: SQLAlchemyError, request_id: str) -> JSONResponse:
    """Handle general database errors"""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            'error': 'Database Error',
            'message': 'Database operation failed. Please try again later.',
            'request_id': request_id
        }
    )

async def handle_unexpected_error(exc: Exception, request_id: str) -> JSONResponse:
    """Handle unexpected errors"""
    # In production, don't expose internal error details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Please try again later.',
            'request_id': request_id
        }
    )

def get_user_friendly_message(status_code: int) -> str:
    """Get user-friendly error messages for status codes"""
    messages = {
        400: 'Invalid request. Please check your input.',
        401: 'Authentication required. Please log in.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        405: 'This action is not allowed.',
        409: 'Data conflict. The resource may already exist.',
        422: 'Invalid data provided. Please check your input.',
        429: 'Too many requests. Please slow down.',
        500: 'Server error. We are working to fix this.',
        502: 'Service temporarily unavailable.',
        503: 'Service under maintenance. Please try again later.'
    }
    return messages.get(status_code, 'An error occurred. Please try again.')