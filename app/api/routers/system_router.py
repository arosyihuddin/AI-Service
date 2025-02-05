# app/api/routers/system_router.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Health check route (a simple "ping" endpoint to check if the API is running)
@router.get("/health")
async def health_check():
    """Check if the system is healthy"""
    return JSONResponse(content={"status": "OK", "message": "System is healthy"})

# Status route (can be used to provide system-related information)
@router.get("/status")
async def system_status():
    """Get system status"""
    # This could check various system statuses (like database connection, memory usage, etc.)
    status = {
        "database": "connected",
        "storage": "available",
        "uptime": "72 hours"  # Example: Could be retrieved from the system's uptime
    }
    return JSONResponse(content={"status": "OK", "system_status": status})

# Example route to get system information (e.g., server info)
@router.get("/info")
async def system_info():
    """Get information about the system (e.g., version, environment, etc.)"""
    info = {
        "api_version": "1.0.0",
        "environment": "production",  # Could also be "staging" or "development"
        "author": "Your Name"
    }
    return JSONResponse(content={"status": "OK", "system_info": info})
