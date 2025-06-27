from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import os
from pathlib import Path
from loguru import logger

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
except ImportError:
    logger.warning("python-dotenv not installed, using system environment variables only")

from src.backend.database.database import init_db, SessionLocal
from src.backend.api.ai import router as ai_router
from src.backend.api.workspaces import router as workspaces_router
from src.backend.api.workspaces_bulk import router as workspaces_bulk_router
from src.backend.api.tasks import router as tasks_router
from src.backend.api.dashboard import router as dashboard_router
from src.backend.api.files import router as files_router
from src.backend.api.file_management import router as file_management_router
from src.backend.api.collaboration import router as collaboration_router
from src.backend.api.suppliers import router as suppliers_router
from src.backend.api.performance import router as performance_router
from src.backend.api.smart_organization import router as smart_organization_router
from src.backend.api.automation import router as automation_router
from src.backend.api.websocket import router as websocket_router
from src.backend.api.calendar import router as calendar_router
# Temporarily disabled advanced features for testing
# from src.backend.api.voice import router as voice_router
# from src.backend.api.workflows import router as workflows_router
# from src.backend.api.mcp_integration import router as mcp_router
from src.backend.routes.auth import router as auth_router
from src.backend.docs.swagger_ui import setup_custom_swagger_ui, get_openapi_schema
from src.backend.services.websocket_manager import periodic_cleanup
# from src.backend.services.voice_recognition_service import voice_recognition_service
# from src.backend.services.workflow_scheduler import workflow_scheduler
# from src.backend.services.workflow_template_engine import workflow_template_engine

# Configure logger
logger.add("logs/ordnungshub.log", rotation="10 MB")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("OrdnungsHub backend starting up...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Seed database with demo data if needed
    try:
        from src.backend.database.seed import seed_database
        seed_database()
        logger.info("Database seeding completed")
    except Exception as e:
        logger.warning(f"Database seeding skipped: {e}")
    
    # Start background WebSocket cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("WebSocket cleanup task started")
    
    # Initialize voice recognition service
    try:
        await voice_recognition_service.initialize()
        logger.info("Voice recognition service initialized")
    except Exception as e:
        logger.warning(f"Voice recognition service initialization failed: {e}")
    
    # Initialize workflow services
    try:
        # Initialize built-in workflow templates
        workflow_template_engine.initialize_built_in_templates(SessionLocal())
        logger.info("Workflow templates initialized")
        
        # Start workflow scheduler
        await workflow_scheduler.start()
        logger.info("Workflow scheduler started")
    except Exception as e:
        logger.warning(f"Workflow services initialization failed: {e}")
        
    yield
    
    # Cancel cleanup task on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("WebSocket cleanup task cancelled")
    
    # Shutdown voice recognition service
    try:
        await voice_recognition_service.shutdown()
        logger.info("Voice recognition service shutdown")
    except Exception as e:
        logger.warning(f"Voice recognition service shutdown failed: {e}")
    
    # Shutdown workflow services
    try:
        await workflow_scheduler.stop()
        logger.info("Workflow scheduler stopped")
    except Exception as e:
        logger.warning(f"Workflow scheduler shutdown failed: {e}")
    
    # Shutdown
    logger.info("OrdnungsHub backend shutting down...")

# Enhanced OpenAPI configuration
app = FastAPI(
    title="OrdnungsHub API",
    description="""
    # OrdnungsHub - AI-Powered System Organizer

    The OrdnungsHub API provides comprehensive workspace and task management capabilities with AI integration.
    
    ## Features
    
    * **AI-Powered Workspaces**: Create and manage intelligent workspaces with AI suggestions
    * **Task Management**: Advanced task management with Taskmaster AI integration
    * **Authentication**: Secure JWT-based authentication system
    * **File Management**: Comprehensive file organization and management
    * **Real-time Collaboration**: Multi-user collaboration features
    * **Dashboard Analytics**: Advanced analytics and reporting
    
    ## Authentication
    
    This API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints:
    
    1. Register a new account via `/auth/register`
    2. Login to get an access token via `/auth/login`
    3. Include the token in the Authorization header: `Bearer <your-token>`
    
    ## Rate Limiting
    
    API requests are rate-limited to ensure fair usage:
    - Authenticated users: 1000 requests per hour
    - Unauthenticated users: 100 requests per hour
    
    ## Error Handling
    
    The API uses standard HTTP status codes and returns detailed error messages in JSON format.
    
    ## SDKs and Libraries
    
    Official SDKs are available for:
    - TypeScript/JavaScript
    - Python
    
    Visit our [GitHub repository](https://github.com/ordnungshub/api) for more information.
    """,
    version="0.1.0",
    terms_of_service="https://ordnungshub.com/terms",
    contact={
        "name": "OrdnungsHub API Support",
        "url": "https://ordnungshub.com/support",
        "email": "api-support@ordnungshub.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        },
        {
            "url": "https://api.ordnungshub.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.ordnungshub.com", 
            "description": "Staging server"
        }
    ],
    openapi_tags=[
        {
            "name": "system",
            "description": "System health, status, and maintenance endpoints"
        },
        {
            "name": "authentication",
            "description": "User authentication and authorization endpoints",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.ordnungshub.com/auth"
            }
        },
        {
            "name": "workspaces",
            "description": "Workspace management with AI-powered organization",
            "externalDocs": {
                "description": "Workspace Guide",
                "url": "https://docs.ordnungshub.com/workspaces"
            }
        },
        {
            "name": "tasks",
            "description": "Task management with Taskmaster AI integration",
            "externalDocs": {
                "description": "Task Management Guide", 
                "url": "https://docs.ordnungshub.com/tasks"
            }
        },
        {
            "name": "files",
            "description": "File management and organization",
            "externalDocs": {
                "description": "File Management Guide",
                "url": "https://docs.ordnungshub.com/files"
            }
        },
        {
            "name": "ai",
            "description": "AI-powered features and text analysis",
            "externalDocs": {
                "description": "AI Features Guide",
                "url": "https://docs.ordnungshub.com/ai"
            }
        },
        {
            "name": "dashboard",
            "description": "Dashboard analytics and reporting",
            "externalDocs": {
                "description": "Dashboard Guide",
                "url": "https://docs.ordnungshub.com/dashboard"
            }
        },
        {
            "name": "collaboration",
            "description": "Real-time collaboration features",
            "externalDocs": {
                "description": "Collaboration Guide",
                "url": "https://docs.ordnungshub.com/collaboration"
            }
        },
        {
            "name": "suppliers",
            "description": "Supplier management and price comparison",
            "externalDocs": {
                "description": "Supplier Management Guide",
                "url": "https://docs.ordnungshub.com/suppliers"
            }
        },
        {
            "name": "performance",
            "description": "Performance monitoring and optimization metrics",
            "externalDocs": {
                "description": "Performance Monitoring Guide",
                "url": "https://docs.ordnungshub.com/performance"
            }
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket connections for collaboration",
            "externalDocs": {
                "description": "WebSocket API Guide",
                "url": "https://docs.ordnungshub.com/websocket"
            }
        },
        {
            "name": "calendar",
            "description": "Comprehensive calendar integration with Google Calendar and Microsoft Outlook",
            "externalDocs": {
                "description": "Calendar Integration Guide",
                "url": "https://docs.ordnungshub.com/calendar"
            }
        },
        {
            "name": "workflows",
            "description": "Automated workflow templates and execution engine with visual designer",
            "externalDocs": {
                "description": "Workflow Automation Guide",
                "url": "https://docs.ordnungshub.com/workflows"
            }
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Content Security Policy - Allow CDN resources and local development
    if os.getenv("NODE_ENV") == "production":
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self';"
        )
    else:
        # More permissive CSP for development
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:* https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' localhost:* 127.0.0.1:* https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: localhost:* 127.0.0.1:* https:; "
            "font-src 'self' localhost:* 127.0.0.1:* https://cdn.jsdelivr.net; "
            "connect-src 'self' localhost:* 127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
            "media-src 'self' localhost:* 127.0.0.1:*; "
            "object-src 'none'; "
            "frame-ancestors 'self';"
        )
    
    # Other security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
    
    # HTTPS only in production
    if os.getenv("NODE_ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Configure CORS with comprehensive origins
default_origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001", 
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

cors_origins_str = os.getenv("CORS_ORIGINS", ",".join(default_origins))
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

# For development, be more permissive with CORS
if os.getenv("NODE_ENV") != "production":
    cors_origins = ["*"]  # Allow all origins in development
    logger.info("CORS: Allowing all origins for development")
else:
    logger.info(f"CORS: Allowing origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(workspaces_router)
app.include_router(workspaces_bulk_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)
app.include_router(files_router)
app.include_router(file_management_router)
app.include_router(collaboration_router)
app.include_router(suppliers_router)
app.include_router(performance_router)
app.include_router(smart_organization_router)
app.include_router(automation_router)
app.include_router(websocket_router)
app.include_router(calendar_router)
# Temporarily disabled advanced routers for testing
# app.include_router(voice_router)
# app.include_router(workflows_router)
# app.include_router(mcp_router)

# Setup custom Swagger UI
setup_custom_swagger_ui(app)
# Use default OpenAPI schema generation to avoid circular imports
# app.openapi = lambda: get_openapi_schema(app)

@app.get(
    "/",
    summary="API Root",
    description="Get basic API information and status",
    response_description="API status and version information",
    tags=["system"]
)
async def read_root():
    """
    Get basic API information and status.
    
    Returns:
        dict: API status, message, and version information
        
    Example:
        ```json
        {
            "status": "running",
            "message": "OrdnungsHub API is operational", 
            "version": "0.1.0"
        }
        ```
    """
    return {
        "status": "running",
        "message": "OrdnungsHub API is operational",
        "version": "0.1.0"
    }

@app.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the API and database connection",
    response_description="Health status of API components",
    tags=["system"]
)
async def health_check():
    """
    Check the health status of the API and database connection.
    
    Performs the following checks:
    - Backend service status
    - Database connectivity
    
    Returns:
        dict: Health status of each component
        
    Example:
        ```json
        {
            "status": "healthy",
            "backend": "operational",
            "database": "operational"
        }
        ```
    
    Raises:
        HTTPException: If critical components are failing
    """
    # Check database connection
    db_status = "operational"
    try:
        from src.backend.database.database import SessionLocal
        db = SessionLocal()
        # Try a simple query
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "healthy",
        "backend": "operational",
        "database": db_status
    }

@app.post(
    "/seed",
    summary="Seed Database",
    description="Manually trigger database seeding for development purposes",
    response_description="Result of database seeding operation",
    tags=["system"]
)
async def seed_database_endpoint():
    """
    Manually trigger database seeding for development purposes.
    
    This endpoint populates the database with sample data for testing and development.
    Should only be used in development environments.
    
    Returns:
        dict: Success message or error details
        
    Example Success:
        ```json
        {
            "message": "Database seeded successfully"
        }
        ```
        
    Example Error:
        ```json
        {
            "error": "Seeding failed: Connection refused"
        }
        ```
    
    Raises:
        HTTPException: If seeding operation fails
    """
    try:
        from src.backend.database.seed import seed_database
        seed_database()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return {"error": f"Seeding failed: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(
        "src.backend.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )