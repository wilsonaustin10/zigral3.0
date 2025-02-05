"""
Entry point for the LinkedIn Agent (Lincoln).

This module initializes the FastAPI application for the LinkedIn agent and exposes
endpoints for controlling LinkedIn automation tasks.
"""

import asyncio
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .linkedin_client import LinkedInClient
from .utils import setup_logger

# Initialize FastAPI app
app = FastAPI(title="Lincoln - LinkedIn Agent")
logger = setup_logger("lincoln.main")

# Initialize LinkedIn client (None until configured)
linkedin_client: Optional[LinkedInClient] = None


class CommandRequest(BaseModel):
    """Model for incoming command requests."""
    action: str
    parameters: Dict


@app.post("/command")
async def execute_command(request: CommandRequest):
    """
    Execute a LinkedIn automation command.
    
    Args:
        request: The command request containing action and parameters.
        
    Returns:
        Dict containing the result of the command execution.
        
    Raises:
        HTTPException: If the client is not initialized or command execution fails.
    """
    if not linkedin_client:
        raise HTTPException(status_code=500, detail="LinkedIn client not initialized")
    
    try:
        result = await linkedin_client.execute_command(request.action, request.parameters)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize the LinkedIn client on application startup."""
    global linkedin_client
    try:
        linkedin_client = LinkedInClient()
        await linkedin_client.initialize()
        logger.info("LinkedIn client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LinkedIn client: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    if linkedin_client:
        await linkedin_client.cleanup()
        logger.info("LinkedIn client cleaned up successfully") 