from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from src.backend.database.database import init_db
from src.backend.api.ai import router as ai_router
from src.backend.api.workspaces import router as workspaces_router
from src.backend.api.workspaces_bulk import router as workspaces_bulk_router
from src.backend.api.tasks import router as tasks_router
from src.backend.api.dashboard import router as dashboard_router
from src.backend.api.files import router as files_router
from src.backend.api.file_management import router as file_management_router

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

# Configure CORS for Electron app and demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router)
app.include_router(workspaces_router)
app.include_router(workspaces_bulk_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)
app.include_router(files_router)
app.include_router(file_management_router)

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

@app.post("/seed")
async def seed_database_endpoint():
    """Manually trigger database seeding"""
    try:
        from src.backend.database.seed import seed_database
        seed_database()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return {"error": f"Seeding failed: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )