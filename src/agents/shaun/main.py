"""
Entry point for the Google Sheets Agent (Shaun).

This module initializes the FastAPI application for the Google Sheets agent and exposes
endpoints for managing prospect data in Google Sheets.
"""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
import os
import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from common.messaging import RabbitMQClient
from .sheets_client import GoogleSheetsClient
from .utils import setup_logger, format_prospect_data

# Initialize logger
logger = setup_logger("shaun.main")

# Initialize clients as None - they will be properly initialized in lifespan
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


class ShaunAgent:
    """Shaun agent for handling Google Sheets operations."""
    
    def __init__(self):
        """Initialize the Shaun agent."""
        self.sheets_client = GoogleSheetsClient()
        self.mq_client = RabbitMQClient("shaun")
        
    async def initialize(self):
        try:
            await self.sheets_client.initialize()
        except Exception as e:
            logger.error("Sheets client initialization failed: %s", e)
            self.sheets_client = None
        await self.mq_client.initialize()
        await self.mq_client.subscribe("shaun_commands", self.handle_command)
        
    async def handle_command(self, message):
        """
        Handle incoming commands from RabbitMQ.
        
        Commands:
        - update_prospects: Add or update prospect information in the sheet
        - get_prospects: Retrieve prospect information from the sheet
        """
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                command = body.get("command")
                data = body.get("data", {})
                
                if command == "update_prospects":
                    response = await self.handle_update_prospects(data)
                elif command == "get_prospects":
                    response = await self.handle_get_prospects(data)
                else:
                    response = {
                        "status": "error",
                        "error": f"Unknown command: {command}"
                    }
                
                await self.mq_client.publish_message(
                    response,
                    routing_key="shaun_responses",
                    correlation_id=message.correlation_id
                )
                
            except Exception as e:
                error_response = {
                    "status": "error",
                    "error": str(e)
                }
                await self.mq_client.publish_message(
                    error_response,
                    routing_key="shaun_responses",
                    correlation_id=message.correlation_id
                )
    
    async def handle_update_prospects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updating prospects in the Google Sheet."""
        try:
            prospects = data.get("prospects", [])
            formatted_data = [format_prospect_data(p) for p in prospects]
            
            # Update the sheet with the new prospect data
            await self.sheets_client.update_prospects(formatted_data)
            
            return {
                "status": "success",
                "message": f"Updated {len(prospects)} prospects"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to update prospects: {str(e)}"
            }
    
    async def handle_get_prospects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle retrieving prospects from the Google Sheet."""
        try:
            # Get filter criteria from data if any
            filters = data.get("filters", {})
            
            # Retrieve prospects from the sheet
            prospects = await self.sheets_client.get_prospects(filters)
            
            return {
                "status": "success",
                "prospects": prospects
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to retrieve prospects: {str(e)}"
            }
    
    async def cleanup(self):
        """Clean up resources for both Sheets and RabbitMQ clients."""
        await self.sheets_client.cleanup()
        await self.mq_client.cleanup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    """
    try:
        sheets_client = GoogleSheetsClient()
        await sheets_client.initialize()
        logger.info("Google Sheets client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Google Sheets client: %s", e)
        sheets_client = None

    try:
        rabbitmq_client = RabbitMQClient("shaun")
        await rabbitmq_client.initialize()
        logger.info("RabbitMQ client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize RabbitMQ client: %s", e)
        rabbitmq_client = None

    yield
    
    # Cleanup on shutdown
    if sheets_client:
        try:
            cleanup_fn = getattr(sheets_client, "cleanup", None)
            if cleanup_fn:
                if asyncio.iscoroutinefunction(cleanup_fn):
                    await cleanup_fn()
                else:
                    cleanup_fn()
            logger.info("Google Sheets client cleaned up successfully")
        except Exception as e:
            logger.error("Failed to cleanup Google Sheets client: %s", e)
            
    if rabbitmq_client:
        try:
            cleanup_fn = getattr(rabbitmq_client, "cleanup", None)
            if cleanup_fn:
                if asyncio.iscoroutinefunction(cleanup_fn):
                    await cleanup_fn()
                else:
                    cleanup_fn()
            logger.info("RabbitMQ client cleaned up successfully")
        except Exception as e:
            logger.error("Failed to cleanup RabbitMQ client: %s", e)


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
async def add_prospects_endpoint(prospects: List[ProspectData]):
    """Add prospects to Google Sheets."""
    try:
        if not sheets_client or not getattr(sheets_client, 'is_initialized', False):
            raise HTTPException(status_code=500, detail="Google Sheets client not initialized")

        # Format prospect data for Google Sheets
        formatted_prospects = [format_prospect_data(prospect.model_dump()) for prospect in prospects]

        # Add prospects to Google Sheets
        result = await sheets_client.add_prospects(formatted_prospects)
        if not result.get("success"):
            raise Exception(result.get("error", "Failed to add prospects"))

        return {
            "status": "success",
            "prospects_added": len(result.get("added", [])),
            "result": {"success": result.get("success"), "added": result.get("added", [])}
        }
    except Exception as e:
        logger.error("Failed to add prospects: %s", str(e))
        error_message = e.detail if hasattr(e, "detail") else str(e)
        return JSONResponse(
            status_code=500,
            content={"error": error_message}
        )


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


async def main():
    """Main entry point for the Shaun agent."""
    agent = ShaunAgent()
    try:
        await agent.initialize()
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 