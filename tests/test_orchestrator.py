import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from openai import OpenAIError, APIStatusError
import httpx
from orchestrator.orchestrator import app
from orchestrator.llm_integration import get_openai_client

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
                    "location": "San Francisco Bay Area"
                }
            }
        ]
    }
    return AsyncMock(
        choices=[
            AsyncMock(
                message=AsyncMock(
                    content=json.dumps(content)
                )
            )
        ]
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
            "code": "insufficient_quota"
        }
    }
    
    # Create a mock request and response
    mock_request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(
        status_code=429,
        request=mock_request,
        content=json.dumps(error_response).encode()
    )
    
    mock_client.chat.completions.create.side_effect = APIStatusError(
        message="You exceeded your current quota",
        response=mock_response,
        body=error_response
    )
    return mock_client

@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock OpenAI client"""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    with patch('orchestrator.llm_integration.get_openai_client', return_value=mock_client):
        yield mock_client

@pytest.fixture
def orchestrator_client():
    """Test client for the orchestrator API"""
    return TestClient(app)

def test_process_command(mock_openai_client, orchestrator_client):
    """Test processing a command"""
    command = {
        "command": "Find CTOs in San Francisco",
        "context": {
            "territory": "San Francisco Bay Area",
            "target_roles": ["CTO", "Chief Technology Officer"]
        }
    }
    response = orchestrator_client.post("/command", json=command)
    assert response.status_code == 200
    assert "objective" in response.json()
    assert "steps" in response.json()

def test_process_command_without_context(mock_openai_client, orchestrator_client):
    """Test processing a command without context"""
    command = {"command": "Find CTOs in San Francisco"}
    response = orchestrator_client.post("/command", json=command)
    assert response.status_code == 200
    assert "objective" in response.json()
    assert "steps" in response.json()

def test_process_invalid_command(orchestrator_client):
    """Test processing an invalid command"""
    # Empty command
    invalid_command = {}
    response = orchestrator_client.post("/command", json=invalid_command)
    assert response.status_code == 422  # Validation error
    
    # Missing command field
    invalid_command = {"context": {}}
    response = orchestrator_client.post("/command", json=invalid_command)
    assert response.status_code == 422
    
    # Empty command string
    invalid_command = {"command": ""}
    response = orchestrator_client.post("/command", json=invalid_command)
    assert response.status_code == 422

def test_process_command_with_invalid_context(orchestrator_client):
    """Test processing a command with invalid context"""
    # Invalid context type
    invalid_command = {
        "command": "Find CTOs",
        "context": "invalid_context"  # Should be a dict
    }
    response = orchestrator_client.post("/command", json=invalid_command)
    assert response.status_code == 422
    
    # Invalid context structure
    invalid_command = {
        "command": "Find CTOs",
        "context": {
            "territory": []  # Should be a string
        }
    }
    response = orchestrator_client.post("/command", json=invalid_command)
    assert response.status_code == 422

def test_process_complex_command(mock_openai_client, orchestrator_client):
    """Test processing a complex command with multiple steps"""
    complex_command = {
        "command": "Find CTOs in San Francisco, export to Google Sheets, and send email summary",
        "context": {
            "territory": "San Francisco Bay Area",
            "target_roles": ["CTO", "Chief Technology Officer"],
            "sheet_id": "test_sheet_123",
            "email": "test@example.com"
        }
    }
    response = orchestrator_client.post("/command", json=complex_command)
    assert response.status_code == 200
    assert "objective" in response.json()
    assert "steps" in response.json()

def test_rate_limiting(mock_openai_client, orchestrator_client):
    """Test rate limiting on the command endpoint"""
    # Make multiple requests in quick succession
    responses = []
    for _ in range(10):
        response = orchestrator_client.post("/command", json={"command": "Find CTOs"})
        responses.append(response)
    
    # Check if any requests were rate limited by the FastAPI rate limiter
    rate_limited = any(r.status_code == 429 for r in responses)
    successful = any(r.status_code == 200 for r in responses)
    
    assert rate_limited  # Some requests should be rate limited
    assert successful  # Some requests should succeed

def test_health_check(orchestrator_client):
    """Test health check endpoint"""
    response = orchestrator_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_openai_rate_limit_handling(mock_rate_limited_client, orchestrator_client):
    """Test that the API properly handles OpenAI rate limit errors"""
    with patch('orchestrator.llm_integration.get_openai_client', return_value=mock_rate_limited_client):
        command = {
            "command": "Find CTOs in San Francisco"
        }
        response = orchestrator_client.post("/command", json=command)
        
        # Verify response
        assert response.status_code == 429
        error_data = response.json()
        assert "detail" in error_data
        assert "exceeded your current quota" in error_data["detail"]

def test_api_rate_limit_handling(mock_openai_client, orchestrator_client):
    """Test that the API endpoint's own rate limiting works"""
    # Make requests until we hit the rate limit
    responses = []
    for _ in range(10):  # Our limit is 5/minute
        response = orchestrator_client.post(
            "/command",
            json={"command": "Find CTOs"},
            headers={"X-Forwarded-For": "127.0.0.1"}  # Ensure consistent IP for rate limiting
        )
        responses.append(response)
        if len(responses) >= 5 and response.status_code == 429:
            # We've hit the rate limit, no need to continue
            break
    
    # Verify we got both successful and rate-limited responses
    success_responses = [r for r in responses if r.status_code == 200]
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    
    assert len(success_responses) > 0, "Should have some successful responses"
    assert len(rate_limited_responses) > 0, "Should have some rate-limited responses"
    assert len(success_responses) <= 5, "Should not exceed rate limit of 5 per minute"