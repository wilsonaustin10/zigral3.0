"""
Zigral Orchestrator API

This module provides a FastAPI application for orchestrating command processing with
robust validation and rate limiting. It handles command processing and context validation.

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

from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from openai import APIStatusError
from pydantic import BaseModel, ConfigDict, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .llm_integration import generate_action_sequence
from .logger import get_logger

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(title="Zigral Orchestrator", version="3.0.0", description=__doc__)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger = get_logger(__name__)


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


@app.post("/command", response_model=Union[ActionSequence, ErrorResponse])
@limiter.limit("5/minute")  # Allow 5 requests per minute per IP
async def process_command(request: Request, command: Command):
    """
    Process a user command and generate an action sequence
    """
    logger.info(f"Received command: {command.command}")
    try:
        # Validate command
        if not command.command:
            raise HTTPException(status_code=422, detail="Command cannot be empty")

        # Generate action sequence
        action_sequence = await generate_action_sequence(
            command=command.command, context=command.context
        )
        logger.info("Successfully processed command")
        return action_sequence
    except APIStatusError as e:
        if e.status_code == 429:
            logger.error(f"Error processing command: {str(e)}")
            return ErrorResponse(error=str(e))
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "orchestrator", "version": "3.0.0"}
