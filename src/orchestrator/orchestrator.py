"""
Zigral Orchestrator API

This module provides a FastAPI application for orchestrating command processing with
robust validation and rate limiting. It handles command processing and context validation.

Recent Changes (2025-02-12):
1. Updated error handling for OpenAI API rate limits:
   - Removed dependency on headers attribute from APIStatusError
   - Added default 60-second retry value for rate limit errors
   - Updated to use model_dump() instead of deprecated dict() method
2. Improved error response structure with DetailedErrorResponse model
3. Added proper HTTP status code propagation for API errors

Context Validation Rules:
1. Structure Validation:
   - Context must be a dictionary
   - Keys must be strings
   - Values must be either strings or lists of strings
2. Content Validation:
   - String values cannot be empty or whitespace
   - List values cannot be empty
   - List elements must be strings
3. Rate Limiting:
   - 5 requests per minute per IP address
   - Returns 429 status code when limit exceeded

Example Valid Context:
{
    "territory": "North America",
    "industries": ["tech", "finance"],
    "keywords": ["AI", "machine learning"]
}

Error Handling:
- 422: Validation Error (invalid command or context)
- 429: Rate Limit Exceeded
- 500: Internal Server Error
"""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Union
import os

from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from openai import APIStatusError
from pydantic import BaseModel, ConfigDict, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .agent_commands import AgentCommandManager
from .llm_integration import generate_action_sequence
from .logger import get_logger

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize logger
logger = get_logger(__name__)

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Command(BaseModel):
    """Model for incoming command requests"""

    command: str
    context: Optional[Dict] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("command")
    @classmethod
    def validate_command(cls, v):
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Context must be a dictionary")
            for key, value in v.items():
                if not isinstance(key, str):
                    raise ValueError("Context keys must be strings")
                if not isinstance(value, (str, list)):
                    raise ValueError("Context values must be strings or lists")
                if isinstance(value, list):
                    if not all(isinstance(x, str) for x in value):
                        raise ValueError(
                            "Context list values must contain only strings"
                        )
                    if not value:  # Check if list is empty
                        raise ValueError("Context list values cannot be empty")
                elif not value.strip():  # Check if string is empty or whitespace
                    raise ValueError("Context string values cannot be empty")
        return v


class ActionStep(BaseModel):
    """Model for individual action steps"""

    agent: str
    action: str
    target: Optional[str] = None
    criteria: Optional[Dict] = None
    fields: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class ActionSequence(BaseModel):
    """Model for the complete action sequence"""

    objective: str
    steps: List[ActionStep]

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Model for error responses"""

    error: str

    model_config = ConfigDict(from_attributes=True)


class ExecutionResult(BaseModel):
    """Model for execution results"""

    objective: str
    steps: List[Dict]

    model_config = ConfigDict(from_attributes=True)


# Enhanced error response
class DetailedErrorResponse(BaseModel):
    """Model for detailed error responses"""
    error: str
    error_type: str
    details: Optional[Dict] = None
    status_code: int

    model_config = ConfigDict(from_attributes=True)


async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify JWT token."""
    # TODO: Implement proper JWT verification
    if not token or token != os.getenv("TEMP_AUTH_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Initialize agent command manager
    app.state.agent_manager = AgentCommandManager()
    await app.state.agent_manager.initialize()
    logger.info("Agent command manager initialized")
    
    yield
    
    # Cleanup on shutdown
    await app.state.agent_manager.cleanup()
    logger.info("Agent command manager cleaned up")


# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="Zigral Orchestrator",
    version="3.0.0",
    description=__doc__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Production frontend
        os.getenv("FRONTEND_URL", ""),  # Configurable frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class ConnectionManager:
    """Manage active WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Disconnect a client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(client_id)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

# Initialize connection manager
manager = ConnectionManager()


@app.post("/command", response_model=Union[ExecutionResult, DetailedErrorResponse])
@limiter.limit("5/minute")  # Allow 5 requests per minute per IP
async def process_command(
    request: Request,
    command: Command,
    token: str = Depends(verify_token)
):
    """
    Process a user command and execute the resulting action sequence
    """
    logger.info(f"Received command: {command.command}")
    try:
        # Broadcast command received
        await manager.broadcast({
            "type": "command_received",
            "data": {"command": command.command}
        })

        # Validate command
        if not command.command:
            raise HTTPException(status_code=422, detail="Command cannot be empty")

        # Generate action sequence
        action_sequence = await generate_action_sequence(
            command=command.command, context=command.context
        )
        logger.info("Successfully generated action sequence")
        
        # Broadcast action sequence generated
        await manager.broadcast({
            "type": "action_sequence_generated",
            "data": action_sequence
        })
        
        # Execute action sequence
        results = await app.state.agent_manager.execute_action_sequence(action_sequence)
        logger.info("Successfully executed action sequence")
        
        # Broadcast execution complete
        await manager.broadcast({
            "type": "execution_complete",
            "data": {
                "objective": action_sequence["objective"],
                "steps": results
            }
        })
        
        return ExecutionResult(
            objective=action_sequence["objective"],
            steps=results
        )
        
    except APIStatusError as e:
        error_response = None
        if e.status_code == 429:
            error_response = DetailedErrorResponse(
                error="Rate limit exceeded",
                error_type="rate_limit",
                details={"retry_after": 60},  # Default to 60 seconds for rate limit retry
                status_code=429
            )
            # Broadcast error
            await manager.broadcast({
                "type": "error",
                "data": error_response.model_dump()  # Updated to use model_dump instead of dict
            })
            raise HTTPException(
                status_code=429,
                detail=error_response.model_dump()
            )
        else:
            error_response = DetailedErrorResponse(
                error=str(e),
                error_type="api_error",
                status_code=e.status_code
            )
            # Broadcast error
            await manager.broadcast({
                "type": "error",
                "data": error_response.model_dump()  # Updated to use model_dump instead of dict
            })
            raise HTTPException(
                status_code=e.status_code,
                detail=error_response.model_dump()
            )
        
    except HTTPException as e:
        error_response = DetailedErrorResponse(
            error=str(e.detail),
            error_type="validation_error",
            status_code=e.status_code
        )
        await manager.broadcast({
            "type": "error",
            "data": error_response.dict()
        })
        return error_response
        
    except Exception as e:
        error_response = DetailedErrorResponse(
            error="Internal server error",
            error_type="server_error",
            details={"message": str(e)},
            status_code=500
        )
        await manager.broadcast({
            "type": "error",
            "data": error_response.dict()
        })
        return error_response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "3.0.0",
        "agent_manager": hasattr(app.state, "agent_manager")
    }


@app.websocket("/ws/updates/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    try:
        await manager.connect(websocket, client_id)
        while True:
            try:
                # Wait for messages from the client (can be used for ping/pong)
                data = await websocket.receive_text()
                # Echo back to confirm receipt
                await websocket.send_json({"type": "pong", "data": data})
            except WebSocketDisconnect:
                manager.disconnect(client_id)
                break
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        manager.disconnect(client_id)
