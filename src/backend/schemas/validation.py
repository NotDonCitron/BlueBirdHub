from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class ValidationError(BaseModel):
    field: str
    message: str
    code: str

class ValidationResponse(BaseModel):
    valid: bool
    errors: List[ValidationError] = []

# Base validators
class EmailStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('invalid email format')
        return cls(v.lower())

class SecurePasswordStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        if len(v) < 8:
            raise ValueError('password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('password must contain special character')
        return cls(v)

class SanitizedStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        # Remove potential XSS attempts
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe.*?>.*?</iframe>',
        ]
        for pattern in dangerous_patterns:
            v = re.sub(pattern, '', v, flags=re.IGNORECASE)
        return cls(v.strip())

# Common validation schemas
class UserCreateValidation(BaseModel):
    email: EmailStr
    password: SecurePasswordStr
    name: SanitizedStr = Field(..., min_length=2, max_length=100)
    
    @validator('email')
    def email_not_disposable(cls, v):
        # Add disposable email domains to block
        disposable_domains = ['tempmail.com', 'throwaway.email', '10minutemail.com']
        domain = v.split('@')[1]
        if domain in disposable_domains:
            raise ValueError('disposable email addresses not allowed')
        return v

class WorkspaceCreateValidation(BaseModel):
    name: SanitizedStr = Field(..., min_length=3, max_length=100)
    description: Optional[SanitizedStr] = Field(None, max_length=500)
    template_id: Optional[str] = None
    
    @validator('name')
    def name_not_reserved(cls, v):
        reserved_names = ['admin', 'api', 'root', 'system', 'public']
        if v.lower() in reserved_names:
            raise ValueError('this name is reserved')
        return v

class FileUploadValidation(BaseModel):
    filename: SanitizedStr
    content_type: str
    size: int = Field(..., gt=0, le=104857600)  # Max 100MB
    
    @validator('content_type')
    def allowed_content_type(cls, v):
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/json',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        if v not in allowed_types:
            raise ValueError(f'file type {v} not allowed')
        return v
    
    @validator('filename')
    def safe_filename(cls, v):
        # Remove path traversal attempts
        v = v.replace('..', '').replace('/', '').replace('\\', '')
        # Ensure has extension
        if '.' not in v:
            raise ValueError('filename must have extension')
        # Check extension
        ext = v.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'txt', 'json', 'docx', 'xlsx']
        if ext not in allowed_extensions:
            raise ValueError(f'file extension .{ext} not allowed')
        return v

class TaskCreateValidation(BaseModel):
    title: SanitizedStr = Field(..., min_length=1, max_length=200)
    description: Optional[SanitizedStr] = Field(None, max_length=2000)
    due_date: Optional[datetime] = None
    priority: str = Field('medium', regex='^(low|medium|high|urgent)$')
    
    @validator('due_date')
    def due_date_future(cls, v):
        if v and v < datetime.now():
            raise ValueError('due date must be in the future')
        return v

# API Request validation
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field('asc', regex='^(asc|desc)$')

class SearchParams(BaseModel):
    query: SanitizedStr = Field(..., min_length=1, max_length=200)
    filters: Optional[Dict[str, Any]] = None
    
    @validator('query')
    def query_not_sql_injection(cls, v):
        sql_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'EXEC', 'UNION']
        for keyword in sql_keywords:
            if keyword in v.upper():
                raise ValueError('invalid search query')
        return v

# Validation utilities
def validate_request_data(data: Dict[str, Any], schema: BaseModel) -> ValidationResponse:
    """Validate request data against a Pydantic schema"""
    try:
        schema(**data)
        return ValidationResponse(valid=True)
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for error in e.errors():
                errors.append(ValidationError(
                    field='.'.join(str(x) for x in error['loc']),
                    message=error['msg'],
                    code=error['type']
                ))
        else:
            errors.append(ValidationError(
                field='_general',
                message=str(e),
                code='validation_error'
            ))
        return ValidationResponse(valid=False, errors=errors)