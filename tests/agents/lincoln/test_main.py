"""Tests for Lincoln agent FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.agents.lincoln.main import app, CommandRequest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_linkedin_client():
    """Create a mock LinkedIn client."""
    with patch("src.agents.lincoln.main.LinkedInClient") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


def test_command_endpoint_client_not_initialized(client):
    """Test command endpoint when client is not initialized."""
    response = client.post("/command", json={"action": "search", "parameters": {}})
    assert response.status_code == 500
    assert "LinkedIn client not initialized" in response.json()["detail"]


def test_command_endpoint_success(client, mock_linkedin_client):
    """Test successful command execution."""
    # Mock successful command execution
    mock_linkedin_client.execute_command.return_value = {"result": "success"}
    
    # Initialize the client by triggering startup event
    with TestClient(app) as client:
        response = client.post(
            "/command",
            json={"action": "search", "parameters": {"title": "CTO"}}
        )
    
    assert response.status_code == 200
    assert response.json() == {"status": "success", "result": {"result": "success"}}


def test_command_endpoint_failure(client, mock_linkedin_client):
    """Test command execution failure."""
    # Mock command execution failure
    mock_linkedin_client.execute_command.side_effect = Exception("Command failed")
    
    # Initialize the client by triggering startup event
    with TestClient(app) as client:
        response = client.post(
            "/command",
            json={"action": "search", "parameters": {"title": "CTO"}}
        )
    
    assert response.status_code == 500
    assert "Command failed" in response.json()["detail"]


def test_command_request_validation():
    """Test command request validation."""
    # Valid request
    request = CommandRequest(action="search", parameters={"title": "CTO"})
    assert request.action == "search"
    assert request.parameters == {"title": "CTO"}
    
    # Invalid request (missing parameters)
    with pytest.raises(ValueError):
        CommandRequest(action="search") 