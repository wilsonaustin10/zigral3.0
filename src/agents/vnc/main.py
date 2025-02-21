"""
VNC Agent Runner Service
Main FastAPI application entry point.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Zigral VNC Agent",
    description="VNC Agent Runner Service for browser automation",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check model
class HealthCheck(BaseModel):
    status: str
    version: str
    services: Dict[str, str]

@app.get("/api/v1/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint to verify service status
    """
    try:
        # Check critical services
        services_status = {
            "chrome": "running",  # TODO: Implement actual Chrome status check
            "vnc": "running",     # TODO: Implement actual VNC status check
            "websocket": "running" # TODO: Implement actual WebSocket status check
        }
        
        return HealthCheck(
            status="healthy",
            version="1.0.0",
            services=services_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

def main():
    """
    Main entry point for the VNC Agent Runner service
    """
    try:
        # Get configuration from environment
        host = os.getenv("VNC_AGENT_HOST", "0.0.0.0")
        port = int(os.getenv("VNC_AGENT_PORT", "8080"))
        
        # Log startup
        logger.info(f"Starting VNC Agent Runner on {host}:{port}")
        
        # Start the FastAPI application
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    
    except Exception as e:
        logger.error(f"Failed to start VNC Agent Runner: {str(e)}")
        raise

if __name__ == "__main__":
    main() 