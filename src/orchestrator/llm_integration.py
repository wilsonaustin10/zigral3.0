import os
import json
from typing import Dict, Optional, List
from openai import AsyncOpenAI
from .logger import get_logger

logger = get_logger(__name__)

# Global client instance
_client = None

def get_openai_client() -> AsyncOpenAI:
    """Get or create the OpenAI client instance"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

async def generate_action_sequence(command: str, context: Optional[Dict] = None, client: Optional[AsyncOpenAI] = None) -> Dict:
    """
    Generate an action sequence using OpenAI's GPT model
    
    Args:
        command (str): The user's command
        context (Optional[Dict]): Additional context for the command
        client (Optional[AsyncOpenAI]): OpenAI client instance for testing
        
    Returns:
        Dict: Action sequence in the format:
        {
            "objective": str,
            "steps": [
                {
                    "agent": str,
                    "action": str,
                    "target": Optional[str],
                    "criteria": Optional[Dict],
                    "fields": Optional[List[str]]
                },
                ...
            ]
        }
    """
    try:
        # Use provided client or get default
        openai_client = client or get_openai_client()
        
        # Prepare the prompt with command and context
        prompt = _prepare_prompt(command, context)
        
        # Call OpenAI API
        response = await openai_client.chat.completions.create(
            model="gpt-4-1106-preview",  # Using the latest GPT-4 model
            messages=[
                {"role": "system", "content": _get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Extract and validate the response
        action_sequence = json.loads(response.choices[0].message.content)
        logger.info("Successfully generated action sequence")
        
        return action_sequence
        
    except Exception as e:
        logger.error(f"Error generating action sequence: {str(e)}")
        raise

def _prepare_prompt(command: str, context: Optional[Dict] = None) -> str:
    """Prepare the prompt for the LLM"""
    prompt = f"Command: {command}\n\n"
    
    if context:
        prompt += "Context:\n"
        for key, value in context.items():
            prompt += f"- {key}: {value}\n"
    
    prompt += "\nGenerate a detailed action sequence for this command."
    return prompt

def _get_system_prompt() -> str:
    """Get the system prompt for the LLM"""
    return """You are an AI orchestrator that generates action sequences for sales prospecting and outreach tasks.
Your role is to break down high-level commands into specific, actionable steps that can be executed by specialized agents.

Available Agents:
- LinkedIn: Can navigate LinkedIn, search for prospects, and collect information
- GoogleSheets: Can read from and write to Google Sheets
- Email: Can compose and send emails
- Calendar: Can schedule meetings and manage calendar events

For each command, generate a JSON object with:
1. An "objective" field summarizing the goal
2. A "steps" array containing the sequence of actions, where each step has:
   - "agent": The agent to perform the action
   - "action": The specific action to take
   - "target": (optional) The target of the action
   - "criteria": (optional) Search or filtering criteria
   - "fields": (optional) Fields to collect or update

Ensure the steps are logical, sequential, and achievable by the specified agents.""" 