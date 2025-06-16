from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psutil
import time
import sys
from datetime import datetime

# Create FastAPI instance
app = FastAPI(
    title="OrdnungsHub API",
    description="AI-Powered System Organizer Backend",
    version="0.1.0"
)

# Configure CORS for web access
origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

@app.get("/")
async def read_root():
    return {
        "status": "running",
        "message": "OrdnungsHub API is operational",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "backend": "operational",
            "database": "mock_healthy",  # Placeholder for real DB check
            "system": {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "memory_available": f"{memory.available // (1024**3)} GB",
                "disk_usage": f"{disk.percent}%",
                "disk_free": f"{disk.free // (1024**3)} GB"
            },
            "service": {
                "python_version": sys.version.split()[0],
                "uptime": time.time()  # Simple uptime tracking
            }
        }
        
        # Mark as unhealthy if resources are critical
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
            health_data["status"] = "degraded"
            
        return health_data
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        metrics = f"""
# HELP cpu_usage_percent Current CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent {cpu_percent}

# HELP memory_usage_percent Current memory usage percentage  
# TYPE memory_usage_percent gauge
memory_usage_percent {memory.percent}

# HELP memory_available_bytes Available memory in bytes
# TYPE memory_available_bytes gauge
memory_available_bytes {memory.available}

# HELP ordnungshub_up Application up status
# TYPE ordnungshub_up gauge
ordnungshub_up 1
"""
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

@app.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    # Add checks for dependencies (database, external services, etc.)
    checks = {
        "backend": True,
        "database": True,  # Placeholder - add real DB check
        "external_services": True  # Placeholder
    }
    
    ready = all(checks.values())
    status_code = 200 if ready else 503
    
    return {
        "ready": ready,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )