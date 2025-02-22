"""Tests for LLM integration with action sequence models."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest
from openai import AsyncOpenAI

from orchestrator.llm_integration import (
    get_openai_client,
    generate_action_sequence,
    _prepare_prompt,
    _get_system_prompt
)
from orchestrator.schemas.action_sequence import ActionSequence, ActionStep


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    content = {
        "job_id": "test_job_123",
        "objective": "Find CTOs in San Francisco",
        "steps": [
            {
                "agent": "lincoln",
                "action": "search",
                "target": None,
                "criteria": {
                    "title": ["CTO", "Chief Technology Officer"],
                    "location": "San Francisco Bay Area"
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
    return AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps(content)))]
    )


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Create a mock OpenAI client."""
    client = AsyncMock(spec=AsyncOpenAI)
    client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
    return client


def test_prepare_prompt():
    """Test prompt preparation with and without context."""
    # Test without context
    prompt = _prepare_prompt("Find CTOs in San Francisco")
    assert "Command: Find CTOs in San Francisco" in prompt
    assert "Context:" not in prompt

    # Test with context
    context = {
        "territory": "San Francisco Bay Area",
        "target_roles": ["CTO", "Chief Technology Officer"]
    }
    prompt = _prepare_prompt("Find CTOs in San Francisco", context)
    assert "Command: Find CTOs in San Francisco" in prompt
    assert "Context:" in prompt
    assert "territory: San Francisco Bay Area" in prompt
    assert "target_roles: ['CTO', 'Chief Technology Officer']" in prompt


def test_system_prompt():
    """Test the system prompt content."""
    prompt = _get_system_prompt()
    assert "You are an AI orchestrator" in prompt
    assert "Available Agents:" in prompt
    assert "lincoln: Can navigate LinkedIn" in prompt
    assert "shaun: Can read from and write to Google Sheets" in prompt
    assert "Example Response:" in prompt


@pytest.mark.asyncio
async def test_generate_action_sequence(mock_openai_client):
    """Test generating an action sequence."""
    command = "Find CTOs in San Francisco"
    context = {
        "territory": "San Francisco Bay Area",
        "target_roles": ["CTO", "Chief Technology Officer"]
    }

    result = await generate_action_sequence(command, context, client=mock_openai_client)

    # Verify result is an ActionSequence instance
    assert isinstance(result, ActionSequence)
    assert result.job_id == "test_job_123"
    assert result.objective == "Find CTOs in San Francisco"
    assert len(result.steps) == 2

    # Verify first step (LinkedIn search)
    step1 = result.steps[0]
    assert isinstance(step1, ActionStep)
    assert step1.agent == "lincoln"
    assert step1.action == "search"
    assert step1.criteria == {
        "title": ["CTO", "Chief Technology Officer"],
        "location": "San Francisco Bay Area"
    }
    assert step1.fields == ["name", "company", "location"]

    # Verify second step (Google Sheets update)
    step2 = result.steps[1]
    assert isinstance(step2, ActionStep)
    assert step2.agent == "shaun"
    assert step2.action == "update"
    assert step2.criteria == {
        "sheet_name": "Tech Prospects",
        "filters": {"industry": "Technology"}
    }


@pytest.mark.asyncio
async def test_generate_action_sequence_without_context(mock_openai_client):
    """Test generating an action sequence without context."""
    command = "Find CTOs in San Francisco"
    result = await generate_action_sequence(command, client=mock_openai_client)

    assert isinstance(result, ActionSequence)
    assert result.objective == "Find CTOs in San Francisco"
    assert len(result.steps) > 0


@pytest.mark.asyncio
async def test_generate_action_sequence_with_missing_job_id(mock_openai_client):
    """Test that job_id is generated if not provided by LLM."""
    # Modify the mock response to remove job_id
    content = json.loads(mock_openai_client.chat.completions.create.return_value.choices[0].message.content)
    del content["job_id"]
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps(content)

    result = await generate_action_sequence("Find CTOs", client=mock_openai_client)

    assert isinstance(result, ActionSequence)
    assert result.job_id is not None  # Should be auto-generated UUID
    assert isinstance(result.created_at, datetime)
    assert isinstance(result.updated_at, datetime) 