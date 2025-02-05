"""
Entry point for the Google Sheets Agent (Shaun).

This module initializes the FastAPI application for the Google Sheets agent and exposes
endpoints for managing prospect data in Google Sheets.
"""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common.messaging import RabbitMQClient
from .sheets_client import GoogleSheetsClient
from .utils import setup_logger

# Initialize logger
logger = setup_logger("shaun.main")

# Initialize clients (None until configured)
sheets_client: Optional[GoogleSheetsClient] = None
rabbitmq_client: Optional[RabbitMQClient] = None


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
    try:
        # Initialize Google Sheets client
        sheets_client = GoogleSheetsClient()
        await sheets_client.initialize()
        logger.info("Google Sheets client initialized successfully")

        # Initialize RabbitMQ client
        rabbitmq_client = RabbitMQClient("shaun")
        await rabbitmq_client.initialize()
        await rabbitmq_client.subscribe(
            "shaun_commands",
            handle_rabbitmq_command
        )
        logger.info("RabbitMQ client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize clients: {str(e)}")
        raise
    
    yield
    
    # Cleanup on shutdown
    if sheets_client:
        await sheets_client.cleanup()
        logger.info("Google Sheets client cleaned up successfully")
    if rabbitmq_client:
        await rabbitmq_client.cleanup()
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
async def execute_command(request: CommandRequest):
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
        raise HTTPException(status_code=500, detail="Google Sheets client not initialized")
    
    try:
        result = await sheets_client.execute_command(request.action, request.parameters)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail="Google Sheets client not initialized")
    
    try:
        result = await sheets_client.add_prospects([p.model_dump() for p in prospects])
        return {
            "status": "success",
            "prospects_added": len(prospects),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error adding prospects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "shaun",
        "version": "1.0.0",
        "client_initialized": sheets_client is not None,
        "rabbitmq_connected": rabbitmq_client is not None and rabbitmq_client.connection is not None
    } 