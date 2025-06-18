from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
import traceback
from datetime import datetime, timezone

from database.database import init_db
from api.ai import router as ai_router
from api.workspaces import router as workspaces_router
from api.workspaces_bulk import router as workspaces_bulk_router
from api.tasks import router as tasks_router
from api.dashboard import router as dashboard_router
from api.files import router as files_router
from api.file_management import router as file_management_router
from api.search import router as search_router
from api.automation import router as automation_router
from api.error_logs import router as error_logs_router
from api.settings import router as settings_router
from api.workspace_files import router as workspace_files_router

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
    
    # Initialize cache service
    try:
        from services.cache_service import cache
        cache_health = cache.health_check()
        if cache_health["status"] == "healthy":
            logger.info("Redis cache service initialized successfully")
        else:
            logger.warning(f"Cache service status: {cache_health['status']} - {cache_health.get('message', '')}")
    except Exception as e:
        logger.warning(f"Cache service initialization failed: {e}")
    
    # Initialize metrics service
    try:
        from services.metrics_service import metrics
        if metrics.enabled:
            logger.info("Prometheus metrics service initialized successfully")
        else:
            logger.info("Metrics collection disabled")
    except Exception as e:
        logger.warning(f"Metrics service initialization failed: {e}")
    
    # Seed database with demo data if needed (disabled for development)
    # try:
    #     from database.seed import seed_database
    #     seed_database()
    #     logger.info("Database seeding completed")
    # except Exception as e:
    #     logger.warning(f"Database seeding skipped: {e}")
        
    yield
    # Shutdown
    logger.info("OrdnungsHub backend shutting down...")

# Create FastAPI instance
app = FastAPI(
    title="OrdnungsHub API",
    description="AI-Powered System Organizer Backend - Comprehensive workspace and task management with AI integration",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "OrdnungsHub Support",
        "email": "support@ordnungshub.dev",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.ordnungshub.dev",
            "description": "Production server"
        }
    ]
)

# Configure CORS for web access
import os

# Get CORS origins from environment variable or use defaults
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    origins = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # For development
        "http://127.0.0.1:8080",
        "file://",  # For Electron app
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600  # Cache preflight requests for 1 hour
)

# Add metrics middleware
try:
    from services.metrics_service import MetricsMiddleware
    app.add_middleware(MetricsMiddleware)
except ImportError:
    logger.warning("Metrics middleware not available")

# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": str(request.url)
        }
    )

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# Include routers
app.include_router(ai_router)
app.include_router(workspace_files_router)
app.include_router(workspaces_router)
app.include_router(workspaces_bulk_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)
app.include_router(files_router)
app.include_router(file_management_router)
app.include_router(search_router)
app.include_router(automation_router)
app.include_router(error_logs_router)
app.include_router(settings_router)

@app.get("/", 
         summary="API Status",
         description="Get the current status of the OrdnungsHub API",
         response_description="API status information",
         tags=["Health"])
async def read_root():
    """
    Get API status and basic information.
    
    Returns:
        dict: API status, message, and version information
    """
    return {
        "status": "running",
        "message": "OrdnungsHub API is operational",
        "version": "0.1.0"
    }

@app.get("/health",
         summary="Health Check",
         description="Comprehensive health check including database and Redis connectivity", 
         response_description="Detailed health status of all system components",
         tags=["Health"])
async def health_check():
    # Check database connection
    db_status = "operational"
    db_latency = None
    try:
        from database.database import SessionLocal
        from sqlalchemy import text
        import time
        
        start_time = time.time()
        db = SessionLocal()
        # Try a simple query
        db.execute(text("SELECT 1"))
        db.close()
        db_latency = round((time.time() - start_time) * 1000, 2)  # ms
    except Exception as e:
        db_status = "error"
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check Redis/Cache connection
    try:
        from services.cache_service import cache
        cache_health = cache.health_check()
        redis_status = cache_health["status"]
        redis_latency = None  # Could add latency test here if needed
    except Exception as e:
        redis_status = "error"
        logger.error(f"Cache health check failed: {str(e)}")
        
    return {
        "status": "healthy" if db_status == "operational" else "degraded",
        "backend": "operational",
        "database": {
            "status": db_status,
            "latency_ms": db_latency
        },
        "cache": {
            "status": redis_status,
            "latency_ms": redis_latency
        },
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/seed",
          summary="Seed Database",
          description="Manually trigger database seeding with demo data",
          response_description="Seeding operation result",
          tags=["Admin"])
async def seed_database_endpoint():
    """Manually trigger database seeding"""
    try:
        from database.seed import seed_database
        seed_database()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return {"error": f"Seeding failed: {str(e)}"}

@app.get("/metrics",
         summary="Prometheus Metrics",
         description="Get application metrics in Prometheus format",
         response_description="Metrics data in Prometheus exposition format",
         tags=["Monitoring"])
async def get_metrics():
    """
    Get application metrics for Prometheus scraping.
    
    Returns:
        Response: Metrics data in Prometheus format
    """
    try:
        from services.metrics_service import metrics
        from prometheus_client import CONTENT_TYPE_LATEST
        metrics_data = metrics.get_metrics()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return Response(content="# Metrics unavailable\n", media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )