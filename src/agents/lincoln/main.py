"""
Entry point for the LinkedIn Agent (Lincoln).

This module initializes the FastAPI application for the LinkedIn agent and exposes
endpoints for controlling LinkedIn automation tasks.
"""

import asyncio
import json
import os
from typing import Dict, Optional, Any, Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from common.messaging import RabbitMQClient
from .linkedin_client import LinkedInClient
from .utils import setup_logger

# Initialize logger
logger = setup_logger("lincoln.main")

class CommandRequest(BaseModel):
    """Model for incoming command requests."""
    action: Literal["search", "get_profile", "capture_state", "login"]
    parameters: Dict = Field(..., min_items=1)

    @validator("parameters")
    def validate_parameters(cls, v):
        if not v:
            raise ValueError("parameters cannot be empty")
        return v


class LincolnAgent:
    """Lincoln agent for handling LinkedIn operations."""
    
    def __init__(self):
        """Initialize the Lincoln agent."""
        self.linkedin_client = LinkedInClient()
        self.mq_client = RabbitMQClient("lincoln")
        
    async def initialize(self):
        """Initialize RabbitMQ connection and set up message handlers."""
        await self.linkedin_client.initialize()
        await self.linkedin_client.login()
        await self.mq_client.initialize()
        await self.mq_client.subscribe(
            "lincoln_commands",
            self.handle_command
        )
        
    async def handle_command(self, message):
        """
        Handle incoming commands from RabbitMQ.
        
        Commands:
        - search_profiles: Search for profiles on LinkedIn
        - get_profile_data: Get detailed data for specific profiles
        - capture_state: Capture the current GUI state
        """
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                command = body.get("command")
                data = body.get("data", {})
                
                if command == "search_profiles":
                    response = await self.handle_search_profiles(data)
                elif command == "get_profile_data":
                    response = await self.handle_get_profile_data(data)
                elif command == "capture_state":
                    response = await self.handle_capture_state(data)
                elif command == "login":
                    response = await self.handle_login(data)
                else:
                    response = {
                        "status": "error",
                        "error": f"Unknown command: {command}"
                    }
                
                await self.mq_client.publish_message(
                    response,
                    routing_key="lincoln_responses",
                    correlation_id=message.correlation_id
                )
                
            except Exception as e:
                error_response = {
                    "status": "error",
                    "error": str(e)
                }
                await self.mq_client.publish_message(
                    error_response,
                    routing_key="lincoln_responses",
                    correlation_id=message.correlation_id
                )
    
    async def handle_search_profiles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle searching for profiles on LinkedIn."""
        try:
            search_params = data.get("search_params", {})
            results = await self.linkedin_client.search_sales_navigator(search_params)
            
            return {
                "status": "success",
                "profiles": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to search profiles: {str(e)}"
            }
    
    async def handle_get_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle retrieving detailed profile data."""
        try:
            profile_urls = data.get("profile_urls", [])
            profiles_data = []
            
            for url in profile_urls:
                profile_data = await self.linkedin_client.get_profile_data(url)
                profiles_data.append(profile_data)
            
            return {
                "status": "success",
                "profiles_data": profiles_data
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get profile data: {str(e)}"
            }
    
    async def handle_capture_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle capturing the current GUI state."""
        try:
            state_data = await self.linkedin_client.capture_gui_state()
            return {
                "status": "success",
                "state_data": state_data
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to capture GUI state: {str(e)}"
            }
    
    async def handle_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LinkedIn login."""
        try:
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                return {
                    "status": "error",
                    "error": "Username and password are required"
                }
            
            # Set environment variables for the login
            os.environ["LINKEDIN_USERNAME"] = username
            os.environ["LINKEDIN_PASSWORD"] = password
            
            # Attempt login
            success = await self.linkedin_client.login()
            
            return {
                "status": "success" if success else "error",
                "message": "Successfully logged in" if success else "Login failed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Login failed: {str(e)}"
            }
    
    async def cleanup(self):
        """Clean up RabbitMQ and LinkedIn client resources."""
        await self.linkedin_client.cleanup()
        await self.mq_client.cleanup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    # Initialize clients on startup
    global linkedin_client
    if not app.state.testing:
        try:
            agent = LincolnAgent()
            await agent.initialize()
            app.state.agent = agent
            logger.info("Lincoln agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Lincoln agent: {str(e)}")
            raise
    
    yield
    
    # Cleanup on shutdown
    if not app.state.testing and hasattr(app.state, 'agent'):
        await app.state.agent.cleanup()
        logger.info("Lincoln agent cleaned up successfully")


# Initialize FastAPI app with lifespan manager
app = FastAPI(title="Lincoln - LinkedIn Agent", lifespan=lifespan)
app.state.testing = False


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
    if not hasattr(app.state, 'agent'):
        return JSONResponse(
            status_code=500,
            content={"detail": "Lincoln agent not initialized"}
        )
    
    try:
        if request.action == "login":
            response = await app.state.agent.handle_login(request.parameters)
        elif request.action == "search":
            if not app.state.agent.linkedin_client._logged_in:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Please log in first using the login action"}
                )
            response = await app.state.agent.handle_search_profiles(request.parameters)
        elif request.action == "get_profile":
            if not app.state.agent.linkedin_client._logged_in:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Please log in first using the login action"}
                )
            response = await app.state.agent.handle_get_profile_data(request.parameters)
        elif request.action == "capture_state":
            if not app.state.agent.linkedin_client._logged_in:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Please log in first using the login action"}
                )
            response = await app.state.agent.handle_capture_state(request.parameters)
        else:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Unknown command: {request.action}"}
            )

        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(status_code=200, content={
        "status": "healthy",
        "service": "lincoln",
        "version": "1.0.0",
        "agent_initialized": hasattr(app.state, 'agent')
    })


async def main():
    """Main entry point for the Lincoln agent."""
    agent = LincolnAgent()
    try:
        await agent.initialize()
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 