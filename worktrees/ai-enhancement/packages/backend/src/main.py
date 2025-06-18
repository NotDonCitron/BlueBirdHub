from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

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
    description="AI-Powered System Organizer Backend",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for web access
origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # For development
    "http://127.0.0.1:8080",
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

@app.get("/")
async def read_root():
    return {
        "status": "running",
        "message": "OrdnungsHub API is operational",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    # Check database connection
    db_status = "operational"
    try:
        from database.database import SessionLocal
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

@app.post("/seed")
async def seed_database_endpoint():
    """Manually trigger database seeding"""
    try:
        from database.seed import seed_database
        seed_database()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return {"error": f"Seeding failed: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )