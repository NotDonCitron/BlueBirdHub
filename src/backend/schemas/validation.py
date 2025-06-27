from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import semver

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
    priority: str = Field('medium', pattern='^(low|medium|high|urgent)$')
    
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
    sort_order: str = Field('asc', pattern='^(asc|desc)$')

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

# Plugin validation schemas
class PluginManifestValidation(BaseModel):
    id: str = Field(..., pattern=r'^[a-zA-Z0-9._-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(...)
    description: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=100)
    author_email: Optional[EmailStr] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    plugin_type: str = Field(..., pattern=r'^(integration|ui_component|theme|workflow|data_processor|ai_enhancement|field_type|api_extension|background_service|schema_extension|auth_provider)$')
    entry_point: str = Field(..., min_length=1)
    module_path: str = Field(..., min_length=1)
    bluebirdHub_version: str = Field(...)
    python_version: str = Field(...)
    
    @validator('version')
    def validate_semver(cls, v):
        try:
            semver.VersionInfo.parse(v)
            return v
        except ValueError:
            raise ValueError('Version must be in semver format (e.g., "1.0.0")')
    
    @validator('homepage', 'repository')
    def validate_url(cls, v):
        if v is not None:
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, v):
                raise ValueError('Invalid URL format')
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

def validate_plugin_data(data: Dict[str, Any]) -> List[str]:
    """Validate plugin manifest data and return list of errors"""
    errors = []
    
    if not isinstance(data, dict):
        return ["Plugin data must be a dictionary"]
    
    # Check required top-level sections
    if "metadata" not in data:
        errors.append("Missing 'metadata' section")
        return errors
    
    metadata = data["metadata"]
    
    # Validate metadata using Pydantic schema
    validation_result = validate_request_data(metadata, PluginManifestValidation)
    if not validation_result.valid:
        for error in validation_result.errors:
            errors.append(f"metadata.{error.field}: {error.message}")
    
    # Validate config definitions if present
    if "config_definitions" in data:
        errors.extend(_validate_config_definitions(data["config_definitions"]))
    
    # Validate permissions if present
    if "permissions" in data:
        errors.extend(_validate_permissions(data["permissions"]))
    
    return errors

def _validate_config_definitions(config_defs: List[Dict[str, Any]]) -> List[str]:
    """Validate configuration definitions"""
    errors = []
    
    if not isinstance(config_defs, list):
        return ["config_definitions must be a list"]
    
    for i, config_def in enumerate(config_defs):
        if not isinstance(config_def, dict):
            errors.append(f"config_definitions[{i}] must be a dictionary")
            continue
        
        # Required fields
        required_fields = ["key", "config_type", "description"]
        for field in required_fields:
            if field not in config_def:
                errors.append(f"Missing required field: config_definitions[{i}].{field}")
        
        # Validate config_type
        if "config_type" in config_def:
            valid_types = ["string", "integer", "float", "boolean", "array", "object", "secret"]
            if config_def["config_type"] not in valid_types:
                errors.append(f"Invalid config_type in config_definitions[{i}]. Must be one of: {', '.join(valid_types)}")
        
        # Validate key format
        if "key" in config_def:
            key_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
            if not re.match(key_pattern, config_def["key"]):
                errors.append(f"Invalid config key format in config_definitions[{i}]: {config_def['key']}")
        
        # Validate choices if present
        if "choices" in config_def:
            if not isinstance(config_def["choices"], list):
                errors.append(f"choices in config_definitions[{i}] must be a list")
        
        # Validate min/max values
        if "min_value" in config_def and "max_value" in config_def:
            if config_def["min_value"] > config_def["max_value"]:
                errors.append(f"min_value cannot be greater than max_value in config_definitions[{i}]")
    
    return errors

def _validate_permissions(permissions: List[Dict[str, Any]]) -> List[str]:
    """Validate permission definitions"""
    errors = []
    
    if not isinstance(permissions, list):
        return ["permissions must be a list"]
    
    for i, perm in enumerate(permissions):
        if not isinstance(perm, dict):
            errors.append(f"permissions[{i}] must be a dictionary")
            continue
        
        # Required fields
        required_fields = ["permission", "scope", "description"]
        for field in required_fields:
            if field not in perm:
                errors.append(f"Missing required field: permissions[{i}].{field}")
        
        # Validate permission format
        if "permission" in perm:
            perm_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$'
            if not re.match(perm_pattern, perm["permission"]):
                errors.append(f"Invalid permission format in permissions[{i}]: {perm['permission']}")
        
        # Validate scope
        if "scope" in perm:
            valid_scopes = ["global", "workspace", "user", "plugin", "resource"]
            if perm["scope"] not in valid_scopes:
                errors.append(f"Invalid scope in permissions[{i}]. Must be one of: {', '.join(valid_scopes)}")
    
    return errors