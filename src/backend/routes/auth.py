from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.backend.database.database import get_db
from src.backend.services.auth import (
    Token,
    UserCreate,
    UserLogin,
    authenticate_user,
    create_access_token,
    create_user,
    get_user,
    get_user_by_email,
    verify_token,
    TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.backend.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post(
    "/register", 
    response_model=Token,
    summary="Register New User",
    description="Create a new user account and return an access token",
    response_description="JWT access token for immediate authentication",
    status_code=201,
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {
            "description": "Username or email already exists",
            "content": {
                "application/json": {
                    "examples": {
                        "username_exists": {
                            "summary": "Username already taken",
                            "value": {"detail": "Username already registered"}
                        },
                        "email_exists": {
                            "summary": "Email already registered", 
                            "value": {"detail": "Email already registered"}
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error in user data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user account with the provided credentials and returns
    a JWT access token for immediate authentication.
    
    Args:
        user (UserCreate): User registration data including username, email, and password
        db (Session): Database session dependency
    
    Returns:
        Token: JWT access token and token type
        
    Raises:
        HTTPException: 400 if username or email already exists
        HTTPException: 422 if validation fails
        
    Example:
        ```python
        import requests
        
        user_data = {
            "username": "johndoe",
            "email": "john@example.com", 
            "password": "securepassword123"
        }
        
        response = requests.post("/auth/register", json=user_data)
        token = response.json()["access_token"]
        ```
    """
    # Check if username already exists
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = create_user(db, user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
    description="Authenticate user and return access token",
    response_description="JWT access token for API authentication",
    responses={
        200: {
            "description": "Successfully authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect username or password"
                    }
                }
            }
        },
        422: {
            "description": "Missing username or password",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "username"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT access token that can be used
    to authenticate subsequent API requests.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Login form containing username and password
        db (Session): Database session dependency
    
    Returns:
        Token: JWT access token and token type
        
    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 422 if required fields are missing
        
    Example:
        ```python
        import requests
        
        login_data = {
            "username": "johndoe",
            "password": "securepassword123"
        }
        
        response = requests.post(
            "/auth/login", 
            data=login_data,  # Note: form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = response.json()["access_token"]
        
        # Use token in subsequent requests
        headers = {"Authorization": f"Bearer {token}"}
        profile = requests.get("/auth/me", headers=headers)
        ```
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get(
    "/me",
    summary="Get Current User",
    description="Get information about the currently authenticated user",
    response_description="Current user profile information",
    responses={
        200: {
            "description": "Current user information",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "johndoe",
                        "email": "john@example.com",
                        "is_active": True
                    }
                }
            }
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not validate credentials"
                    }
                }
            }
        },
        400: {
            "description": "User account is inactive",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Inactive user"
                    }
                }
            }
        }
    }
)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the currently authenticated user.
    
    Returns profile information for the user associated with the provided
    JWT access token.
    
    Args:
        current_user (User): Current authenticated user from JWT token
    
    Returns:
        dict: User profile information including id, username, email, and status
        
    Raises:
        HTTPException: 401 if token is invalid or expired
        HTTPException: 400 if user account is inactive
        
    Example:
        ```python
        import requests
        
        # First, get an access token
        token = "your_jwt_token_here"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get("/auth/me", headers=headers)
        user_info = response.json()
        
        print(f"Logged in as: {user_info['username']}")
        print(f"Email: {user_info['email']}")
        ```
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }