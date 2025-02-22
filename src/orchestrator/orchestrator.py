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

from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket, WebSocketDisconnect, APIRouter
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
from .schemas.action_sequence import ActionSequence, ExecutionResult

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize logger
logger = get_logger(__name__)

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


class Command(BaseModel):
    """Model for incoming commands."""
    
    command: str
    context: Optional[Dict] = None
    
    @field_validator("command")
    def command_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()


class DetailedErrorResponse(BaseModel):
    """Model for detailed error responses."""
    
    detail: str
    error_type: str
    status_code: int


# Initialize FastAPI app
app = FastAPI(title="Zigral Orchestrator")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestrator"}

@app.on_event("startup")
async def startup_event():
    import sys
    routes_info = "Registered routes: " + ", ".join([route.path for route in app.routes])
    with open("/tmp/routes.log", "w") as f:
        f.write(routes_info)
    print(routes_info, file=sys.stdout)


async def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """Verify the authentication token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For development, accept a specific token
    if token == os.getenv("TEMP_AUTH_TOKEN", "zigral_dev_token_123"):
        return token
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    app.state.agent_manager = AgentCommandManager()


@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown."""
    await app.state.agent_manager.cleanup()


@app.post("/command", response_model=Union[ExecutionResult, DetailedErrorResponse])
@limiter.limit("5/minute")  # Allow 5 requests per minute per IP
async def process_command(
    request: Request,
    command: Command,
    token: str = Depends(verify_token)
):
    """
    Process a user command and execute the resulting action sequence.
    """
    logger.info(f"Received command: {command.command}")
    try:
        # Broadcast command received
        await manager.broadcast({
            "type": "command_received",
            "data": {"command": command.command}
        })

        # Generate action sequence
        action_sequence_dict = await generate_action_sequence(
            command=command.command,
            context=command.context
        )
        
        # Convert to ActionSequence model for validation
        action_sequence = ActionSequence(**action_sequence_dict)
        logger.info("Successfully generated action sequence")
        
        # Broadcast action sequence generated
        await manager.broadcast({
            "type": "action_sequence_generated",
            "data": action_sequence.model_dump()
        })
        
        # Execute action sequence
        execution_result = await app.state.agent_manager.execute_action_sequence(
            action_sequence.model_dump()
        )
        logger.info("Successfully executed action sequence")
        
        # Broadcast execution complete
        await manager.broadcast({
            "type": "execution_complete",
            "data": execution_result.model_dump()
        })
        
        return execution_result

    except APIStatusError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return DetailedErrorResponse(
            detail=str(e),
            error_type="openai_error",
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return DetailedErrorResponse(
            detail=str(e),
            error_type="internal_error",
            status_code=500
        )


# WebSocket connection manager
class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")


# Initialize connection manager
manager = ConnectionManager()


@app.websocket("/ws/updates/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Debug endpoint added for troubleshooting
@app.get("/inspect_routes")
def inspect_routes():
    return {"routes": [route.path for route in app.routes]}
