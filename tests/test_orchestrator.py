"""Tests for the orchestrator API."""

import json
import os
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIStatusError

from orchestrator.orchestrator import app
from orchestrator.agent_commands import AgentCommandManager


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
    with patch(
        "orchestrator.llm_integration.get_openai_client", return_value=mock_client
    ):
        yield mock_client


@pytest.fixture
def mock_agent_manager():
    """Create a mock agent manager."""
    manager = AsyncMock(spec=AgentCommandManager)
    manager.execute_action_sequence = AsyncMock(return_value=[
        {"step": {"agent": "test", "action": "test"}, "result": {"status": "success"}}
    ])
    return manager


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {"TEMP_AUTH_TOKEN": "zigral_dev_token_123"}):
        yield


@pytest.fixture
def orchestrator_client(mock_agent_manager, mock_env_vars):
    """Create a test client for the orchestrator with mocked dependencies."""
    app.state.agent_manager = mock_agent_manager
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests"""
    from orchestrator.orchestrator import limiter
    limiter.reset()
    yield


def test_process_command(mock_openai_client, orchestrator_client):
    """Test processing a command"""
    command = {
        "command": "Find CTOs in San Francisco",
        "context": {
            "territory": "San Francisco Bay Area",
            "target_roles": ["CTO", "Chief Technology Officer"],
        },
    }
    response = orchestrator_client.post(
        "/command",
        json=command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 200
    assert "objective" in response.json()
    assert "steps" in response.json()


def test_process_command_without_context(mock_openai_client, orchestrator_client):
    """Test processing a command without context"""
    command = {"command": "Find CTOs in San Francisco"}
    response = orchestrator_client.post(
        "/command",
        json=command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 200
    assert "objective" in response.json()
    assert "steps" in response.json()


def test_process_invalid_command(orchestrator_client):
    """Test processing an invalid command"""
    # Empty command
    invalid_command = {}
    response = orchestrator_client.post(
        "/command",
        json=invalid_command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 422  # Validation error

    # Missing command field
    invalid_command = {"context": {}}
    response = orchestrator_client.post(
        "/command",
        json=invalid_command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 422

    # Empty command string
    invalid_command = {"command": ""}
    response = orchestrator_client.post(
        "/command",
        json=invalid_command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 422


def test_process_command_with_invalid_context(orchestrator_client):
    """Test processing a command with invalid context"""
    # Invalid context type
    invalid_command = {
        "command": "Find CTOs",
        "context": "invalid_context",  # Should be a dict
    }
    response = orchestrator_client.post(
        "/command",
        json=invalid_command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 422

    # Invalid context structure
    invalid_command = {
        "command": "Find CTOs",
        "context": {"territory": []},  # Should be a string
    }
    response = orchestrator_client.post(
        "/command",
        json=invalid_command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 422


def test_process_complex_command(mock_openai_client, orchestrator_client):
    """Test processing a complex command with multiple steps"""
    complex_command = {
        "command": "Find CTOs in San Francisco, export to Google Sheets, and send email summary",
        "context": {
            "territory": "San Francisco Bay Area",
            "target_roles": ["CTO", "Chief Technology Officer"],
            "sheet_id": "test_sheet_123",
            "email": "test@example.com",
        },
    }
    response = orchestrator_client.post(
        "/command",
        json=complex_command,
        headers={"Authorization": "Bearer zigral_dev_token_123"}
    )
    assert response.status_code == 200
    assert "objective" in response.json()
    assert "steps" in response.json()


def test_rate_limiting(mock_openai_client, orchestrator_client):
    """Test rate limiting on the command endpoint"""
    # Configure mock to return a successful response
    mock_response = {
        "objective": "Test objective",
        "steps": [{"agent": "Test", "action": "test"}],
    }
    mock_openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps(mock_response)))]
    )

    with patch(
        "orchestrator.llm_integration.get_openai_client",
        return_value=mock_openai_client,
    ):
        # Make multiple requests in quick succession
        responses = []
        for _ in range(10):  # Our limit is 5/minute
            response = orchestrator_client.post(
                "/command",
                json={"command": "Find CTOs"},
                headers={
                    "Authorization": "Bearer zigral_dev_token_123",
                    "X-Forwarded-For": "127.0.0.1"  # Ensure consistent IP for rate limiting
                }
            )
            responses.append(response)

        # Verify response distribution
        success_responses = [r for r in responses if r.status_code == 200]
        rate_limited_responses = [r for r in responses if r.status_code == 429]

        assert len(success_responses) == 5, "Should have exactly 5 successful responses (rate limit)"
        assert len(rate_limited_responses) == 5, "Should have 5 rate-limited responses"

        # Verify successful response format
        for response in success_responses:
            data = response.json()
            assert "objective" in data
            assert "steps" in data

        # Verify rate limit response format
        for response in rate_limited_responses:
            data = response.json()
            assert "error" in data
            assert "Rate limit exceeded" in data["error"]


def test_health_check(orchestrator_client):
    """Test health check endpoint"""
    response = orchestrator_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_openai_rate_limit_handling(mock_rate_limited_client, orchestrator_client):
    """Test that the API properly handles OpenAI rate limit errors"""
    with patch(
        "orchestrator.llm_integration.get_openai_client",
        return_value=mock_rate_limited_client,
    ):
        command = {"command": "Find CTOs in San Francisco"}
        response = orchestrator_client.post(
            "/command",
            json=command,
            headers={"Authorization": "Bearer zigral_dev_token_123"}
        )
        
        assert response.status_code == 429
        data = response.json()
        detail = data["detail"]
        assert detail["error"] == "Rate limit exceeded"
        assert detail["error_type"] == "rate_limit"
        assert detail["details"]["retry_after"] == 60
        assert detail["status_code"] == 429


def test_api_rate_limit_reset(mock_openai_client, orchestrator_client):
    """Test that rate limits reset after the time window"""
    # Configure mock to return a successful response
    mock_response = {
        "objective": "Test objective",
        "steps": [{"agent": "Test", "action": "test"}],
    }
    mock_openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps(mock_response)))]
    )

    with patch(
        "orchestrator.llm_integration.get_openai_client",
        return_value=mock_openai_client,
    ):
        # First batch of requests (should get 5 successes)
        first_responses = []
        for _ in range(5):
            response = orchestrator_client.post(
                "/command",
                json={"command": "Find CTOs"},
                headers={
                    "Authorization": "Bearer zigral_dev_token_123",
                    "X-Forwarded-For": "127.0.0.1"
                }
            )
            first_responses.append(response)

        assert all(r.status_code == 200 for r in first_responses), "First 5 requests should succeed"

        # Next request should be rate limited
        rate_limited = orchestrator_client.post(
            "/command",
            json={"command": "Find CTOs"},
            headers={
                "Authorization": "Bearer zigral_dev_token_123",
                "X-Forwarded-For": "127.0.0.1"
            }
        )
        assert rate_limited.status_code == 429, "6th request should be rate limited"

        # Wait for rate limit window to reset (in test environment, we mock this)
        with patch("slowapi.extension.time.time", return_value=time.time() + 61):
            # Should succeed after window reset
            response = orchestrator_client.post(
                "/command",
                json={"command": "Find CTOs"},
                headers={
                    "Authorization": "Bearer zigral_dev_token_123",
                    "X-Forwarded-For": "127.0.0.1"
                }
            )
            assert response.status_code == 200, "Request should succeed after rate limit window reset"
