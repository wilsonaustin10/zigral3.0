import json
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import APIStatusError

from orchestrator.llm_integration import (
    _get_system_prompt,
    _prepare_prompt,
    generate_action_sequence,
)


@pytest.fixture
def mock_openai_response():
    """Mock response from OpenAI API"""
    content = {
        "objective": "Find CTOs in San Francisco",
        "steps": [
            {
                "agent": "LinkedIn",
                "action": "search",
                "target": "people",
                "criteria": {
                    "title": ["CTO", "Chief Technology Officer"],
                    "location": "San Francisco Bay Area",
                },
            }
        ],
    }
    return AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps(content)))]
    )


@pytest.fixture
def mock_rate_limited_client():
    """Mock OpenAI client that simulates a rate limit error"""
    mock_client = AsyncMock()
    error_response = {
        "error": {
            "message": "You exceeded your current quota",
            "type": "insufficient_quota",
            "param": None,
            "code": "insufficient_quota",
        }
    }

    # Create a mock request and response
    mock_request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(
        status_code=429,
        request=mock_request,
        content=json.dumps(error_response).encode(),
    )

    mock_client.chat.completions.create.side_effect = APIStatusError(
        message="You exceeded your current quota",
        response=mock_response,
        body=error_response,
    )
    return mock_client


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock OpenAI client"""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    return mock_client


@pytest.mark.asyncio
async def test_generate_action_sequence(mock_openai_client):
    """Test generating an action sequence"""
    command = "Find CTOs in San Francisco"
    context = {
        "territory": "San Francisco Bay Area",
        "target_roles": ["CTO", "Chief Technology Officer"],
    }

    result = await generate_action_sequence(command, context, client=mock_openai_client)

    assert isinstance(result, dict)
    assert "objective" in result
    assert "steps" in result
    assert isinstance(result["steps"], list)
    assert len(result["steps"]) > 0

    # Verify step structure
    step = result["steps"][0]
    assert "agent" in step
    assert "action" in step
    assert step["agent"] == "LinkedIn"
    assert step["action"] == "search"


@pytest.mark.asyncio
async def test_generate_action_sequence_without_context(mock_openai_client):
    """Test generating an action sequence without context"""
    command = "Find CTOs in San Francisco"

    result = await generate_action_sequence(command, client=mock_openai_client)

    assert isinstance(result, dict)
    assert "objective" in result
    assert "steps" in result


def test_prepare_prompt():
    """Test prompt preparation"""
    command = "Find CTOs"
    context = {"territory": "San Francisco"}

    prompt = _prepare_prompt(command, context)

    assert command in prompt
    assert "territory" in prompt
    assert "San Francisco" in prompt


def test_prepare_prompt_without_context():
    """Test prompt preparation without context"""
    command = "Find CTOs"

    prompt = _prepare_prompt(command)

    assert command in prompt
    assert "Context" not in prompt


def test_get_system_prompt():
    """Test system prompt retrieval"""
    system_prompt = _get_system_prompt()

    assert isinstance(system_prompt, str)
    assert "LinkedIn" in system_prompt
    assert "GoogleSheets" in system_prompt
    assert "Email" in system_prompt
    assert "Calendar" in system_prompt
    assert "JSON" in system_prompt


@pytest.mark.asyncio
async def test_rate_limit_handling(mock_rate_limited_client):
    """Test handling of OpenAI rate limit errors"""
    command = "Find CTOs in San Francisco"

    with pytest.raises(APIStatusError) as exc_info:
        await generate_action_sequence(command, client=mock_rate_limited_client)

    assert exc_info.value.status_code == 429
    assert "exceeded your current quota" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_real_api_calls():
    """Test that no real API calls are made during testing."""
    command = "Find CTOs in San Francisco"
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception(
        "Real API call attempted"
    )
    
    with pytest.raises(Exception, match="Real API call attempted"):
        await generate_action_sequence(command, client=mock_client)
