from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from openai import APIStatusError
from .llm_integration import generate_action_sequence
from .logger import get_logger

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(title="Zigral Orchestrator", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger = get_logger(__name__)

class Command(BaseModel):
    """Model for incoming command requests"""
    command: str
    context: Optional[Dict] = None

    @validator('command')
    def validate_command(cls, v):
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()

    @validator('context')
    def validate_context(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Context must be a dictionary")
            for key, value in v.items():
                if not isinstance(key, str):
                    raise ValueError("Context keys must be strings")
                if isinstance(value, list) and not all(isinstance(x, str) for x in value):
                    raise ValueError("Context list values must contain only strings")
        return v

class ActionStep(BaseModel):
    """Model for individual action steps"""
    agent: str
    action: str
    target: Optional[str] = None
    criteria: Optional[Dict] = None
    fields: Optional[List[str]] = None

class ActionSequence(BaseModel):
    """Model for the complete action sequence"""
    objective: str
    steps: List[ActionStep]

@app.post("/command", response_model=ActionSequence)
@limiter.limit("5/minute")  # Allow 5 requests per minute per IP
async def process_command(request: Request, command: Command):
    """
    Process a user command and generate an action sequence
    """
    logger.info(f"Received command: {command.command}")
    try:
        # Validate command
        if not command.command:
            raise HTTPException(
                status_code=422,
                detail="Command cannot be empty"
            )

        # Generate action sequence
        action_sequence = await generate_action_sequence(
            command=command.command,
            context=command.context
        )
        logger.info("Successfully processed command")
        return action_sequence
    except APIStatusError as e:
        if e.status_code == 429:
            logger.error(f"Error processing command: {str(e)}")
            raise HTTPException(
                status_code=429,
                detail=str(e)
            )
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "orchestrator", "version": "3.0.0"} 