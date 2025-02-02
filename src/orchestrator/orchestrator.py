from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from .llm_integration import generate_action_sequence
from .logger import get_logger

# Initialize FastAPI app
app = FastAPI(title="Zigral Orchestrator", version="3.0.0")
logger = get_logger(__name__)

class Command(BaseModel):
    """Model for incoming command requests"""
    command: str
    context: Optional[Dict] = None

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
async def process_command(command: Command):
    """
    Process a user command and generate an action sequence
    """
    try:
        logger.info(f"Received command: {command.command}")
        
        # Generate action sequence using LLM
        action_sequence = await generate_action_sequence(
            command=command.command,
            context=command.context
        )
        
        logger.info(f"Generated action sequence with {len(action_sequence['steps'])} steps")
        return action_sequence
    
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing command: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "orchestrator"} 