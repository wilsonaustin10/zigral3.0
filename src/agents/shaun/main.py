"""
Entry point for the Google Sheets Agent (Shaun).

This module initializes the FastAPI application for the Google Sheets agent and exposes
endpoints for managing prospect data in Google Sheets.
"""

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .sheets_client import GoogleSheetsClient
from .utils import setup_logger

# Initialize FastAPI app
app = FastAPI(title="Shaun - Google Sheets Agent")
logger = setup_logger("shaun.main")

# Initialize Google Sheets client (None until configured)
sheets_client: Optional[GoogleSheetsClient] = None


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


@app.on_event("startup")
async def startup_event():
    """Initialize the Google Sheets client on application startup."""
    global sheets_client
    try:
        sheets_client = GoogleSheetsClient()
        await sheets_client.initialize()
        logger.info("Google Sheets client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets client: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    if sheets_client:
        await sheets_client.cleanup()
        logger.info("Google Sheets client cleaned up successfully") 