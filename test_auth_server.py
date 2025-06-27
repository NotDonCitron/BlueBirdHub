#!/usr/bin/env python3
"""
Minimal test server for authentication functionality.
This server only includes basic auth endpoints for testing login/registration.
"""

import sys
sys.path.append('.')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.database.database import init_db
from src.backend.routes.auth import router as auth_router
from src.backend.api.workspaces import router as workspaces_router
from src.backend.api.tasks import router as tasks_router

# Create FastAPI app
app = FastAPI(
    title="BlueBirdHub Auth Test Server",
    description="Minimal server for testing authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(tasks_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Auth test server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)