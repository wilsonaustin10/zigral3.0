"""LLM integration for generating action sequences.

This module handles the integration with OpenAI's GPT models for generating
structured action sequences from user commands.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime
import uuid

from openai import AsyncOpenAI
from .logger import get_logger
from .schemas.action_sequence import ActionSequence, ActionStep

logger = get_logger(__name__)


def get_openai_client() -> AsyncOpenAI:
    """Get an instance of the OpenAI client."""
    return AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        organization=os.getenv("OPENAI_ORG_ID")
    )


async def generate_action_sequence(
    command: str, context: Optional[Dict] = None, client: Optional[AsyncOpenAI] = None
) -> ActionSequence:
    """
    Generate an action sequence using OpenAI's GPT model.

    Args:
        command (str): The user's command
        context (Optional[Dict]): Additional context for the command
        client (Optional[AsyncOpenAI]): OpenAI client instance for testing

    Returns:
        ActionSequence: A validated action sequence model
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
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Extract and parse the response
        action_sequence_dict = json.loads(response.choices[0].message.content)
        
        # Add job_id and timestamps if not present
        if "job_id" not in action_sequence_dict:
            action_sequence_dict["job_id"] = str(uuid.uuid4())
        if "created_at" not in action_sequence_dict:
            action_sequence_dict["created_at"] = datetime.utcnow()
        if "updated_at" not in action_sequence_dict:
            action_sequence_dict["updated_at"] = datetime.utcnow()

        # Convert to ActionSequence model for validation
        action_sequence = ActionSequence(**action_sequence_dict)
        logger.info("Successfully generated action sequence")

        return action_sequence

    except Exception as e:
        logger.error(f"Error generating action sequence: {str(e)}")
        raise


def _prepare_prompt(command: str, context: Optional[Dict] = None) -> str:
    """Prepare the prompt for the LLM."""
    prompt = f"Command: {command}\n\n"

    if context:
        prompt += "Context:\n"
        for key, value in context.items():
            prompt += f"- {key}: {value}\n"

    prompt += "\nGenerate a detailed action sequence for this command."
    return prompt


def _get_system_prompt() -> str:
    """Get the system prompt for the LLM."""
    return """You are an AI orchestrator that generates action sequences for sales prospecting and outreach tasks.
Your role is to break down high-level commands into specific, actionable steps that can be executed by specialized agents.

Available Agents:
- lincoln: Can navigate LinkedIn, search for prospects, and collect information
- shaun: Can read from and write to Google Sheets

For each command, generate a JSON object with:
1. A "job_id" field with a unique identifier (if not provided)
2. An "objective" field summarizing the goal
3. A "steps" array containing the sequence of actions, where each step has:
   - "agent": The agent to perform the action (must be one of: "lincoln", "shaun")
   - "action": The specific action to take
   - "target": (optional) The target of the action (e.g., URL, element selector)
   - "criteria": (optional) Search or filtering criteria
   - "fields": (optional) Fields to collect or update
   - "timeout": (optional) Timeout in milliseconds (default: 5000)

Example Response:
{
    "job_id": "prospect_search_123",
    "objective": "Find tech CTOs and update prospect list",
    "steps": [
        {
            "agent": "lincoln",
            "action": "search",
            "criteria": {
                "title": ["CTO", "Chief Technology Officer"],
                "industry": "Technology"
            },
            "fields": ["name", "company", "location"]
        },
        {
            "agent": "shaun",
            "action": "update",
            "criteria": {
                "sheet_name": "Tech Prospects",
                "filters": {"industry": "Technology"}
            }
        }
    ]
}

Ensure the steps are logical, sequential, and achievable by the specified agents."""
