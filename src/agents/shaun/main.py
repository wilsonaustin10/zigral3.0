"""
Entry point for the Google Sheets Agent (Shaun).

This module initializes the FastAPI application for the Google Sheets agent and exposes
endpoints for managing prospect data in Google Sheets.
"""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from common.messaging import RabbitMQClient
from .sheets_client import GoogleSheetsClient
from .utils import setup_logger

# Initialize logger
logger = setup_logger("shaun.main")

# Initialize clients (None until configured)
sheets_client = None
rabbitmq_client = None


class ProspectData(BaseModel):
    """Model for prospect data to be added to sheets."""
    full_name: str
    current_title: str
    current_company: str
    location: str
    linkedin_url: str
    experience: Optional[List[Dict]] = None
    education: Optional[List[Dict]] = None


class CommandRequest(BaseModel):
    """Model for incoming command requests."""
    action: str
    parameters: Dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    """
    # Initialize clients on startup
    global sheets_client, rabbitmq_client
    if os.environ.get("TESTING"):
        logger.info("Skipping client initialization during testing")
    else:
        try:
            await sheets_client.initialize()
            logger.info("Google Sheets client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Google Sheets client: %s", e)
            sheets_client = None

        try:
            await rabbitmq_client.initialize()
            logger.info("RabbitMQ client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize RabbitMQ client: %s", e)
            rabbitmq_client = None
    
    yield
    
    # Cleanup on shutdown
    import asyncio
    if sheets_client:
        cleanup_fn = getattr(sheets_client, "cleanup", None)
        if cleanup_fn:
            if asyncio.iscoroutinefunction(cleanup_fn):
                await cleanup_fn()
            else:
                cleanup_fn()
        logger.info("Google Sheets client cleaned up successfully")
    if rabbitmq_client:
        cleanup_fn = getattr(rabbitmq_client, "cleanup", None)
        if cleanup_fn:
            if asyncio.iscoroutinefunction(cleanup_fn):
                await cleanup_fn()
            else:
                cleanup_fn()
        logger.info("RabbitMQ client cleaned up successfully")


# Initialize FastAPI app with lifespan manager
app = FastAPI(title="Shaun - Google Sheets Agent", lifespan=lifespan)


async def handle_rabbitmq_command(message):
    """
    Handle commands received via RabbitMQ.
    
    Args:
        message: RabbitMQ message containing the command
    """
    if not sheets_client or not rabbitmq_client:
        raise RuntimeError("Clients not initialized")

    try:
        # Execute command
        result = await sheets_client.execute_command(message.action, message.parameters)
        
        # Send response
        await rabbitmq_client.publish_message(
            {
                "status": "success",
                "result": result,
                "service": "shaun"
            },
            routing_key="shaun_responses",
            correlation_id=message.correlation_id
        )
    except Exception as e:
        logger.error(f"Error handling RabbitMQ command: {str(e)}")
        # Send error response
        await rabbitmq_client.publish_message(
            {
                "status": "error",
                "error": str(e),
                "service": "shaun"
            },
            routing_key="shaun_responses",
            correlation_id=message.correlation_id
        )


@app.post("/command")
async def command_endpoint(request: CommandRequest):
    """
    Execute a Google Sheets command.
    
    Args:
        request: The command request containing action and parameters.
        
    Returns:
        Dict containing the result of the command execution.
        
    Raises:
        HTTPException: If the client is not initialized or command execution fails.
    """
    if not sheets_client:
        return JSONResponse(status_code=500, content={"detail": "Sheets client not initialized"})
    
    command_payload = {"action": request.action, "parameters": request.parameters}
    try:
        result = await sheets_client.execute_command(command_payload)
        return JSONResponse(status_code=200, content={"status": "success", "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/prospects")
async def add_prospects(prospects: List[ProspectData]):
    """
    Add new prospects to the Google Sheet.
    
    Args:
        prospects: List of prospect data to add.
        
    Returns:
        Dict containing status and number of prospects added.
        
    Raises:
        HTTPException: If the client is not initialized or update fails.
    """
    if not sheets_client:
        return JSONResponse(status_code=500, content={"detail": "Sheets client not initialized"})
    
    try:
        result = await sheets_client.add_prospects([p.model_dump() for p in prospects])
        added = result.get("added", [])
        return JSONResponse(status_code=200, content={"status": "success", "prospects_added": len(added), "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(status_code=200, content={
        "status": "healthy",
        "service": "shaun",
        "version": "1.0.0",
        "client_initialized": sheets_client is not None,
        "rabbitmq_connected": rabbitmq_client is not None
    }) 