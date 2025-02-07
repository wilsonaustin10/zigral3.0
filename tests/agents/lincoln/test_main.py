"""Tests for the Lincoln agent's main module."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.agents.lincoln.main import app, CommandRequest

@pytest.fixture
def mock_linkedin_client():
    """Create a mock LinkedIn client."""
    return AsyncMock()

@pytest.fixture
def client():
    """Create a test client."""
    app.state.testing = True
    return TestClient(app)

def test_command_endpoint_client_not_initialized(client):
    """Test command endpoint when client is not initialized."""
    response = client.post("/command", json={"action": "search", "parameters": {"title": "CTO"}})
    assert response.status_code == 500
    assert "Lincoln agent not initialized" in response.json()["detail"]

@pytest.mark.asyncio
async def test_command_endpoint_success(client, mock_linkedin_client):
    """Test successful command execution."""
    # Mock successful command execution
    mock_linkedin_client.execute_command.return_value = {"result": "success"}
    
    # Set up the test state
    app.state.testing = True
    app.state.agent = AsyncMock()
    app.state.agent.handle_search_profiles.return_value = {"status": "success", "profiles": []}
    
    response = client.post(
        "/command",
        json={
            "action": "search",
            "parameters": {"title": "CEO", "location": "San Francisco"}
        }
    )
    
    assert response.status_code == 200
    assert response.json() == {"result": "success"}

@pytest.mark.asyncio
async def test_command_endpoint_failure(client, mock_linkedin_client):
    """Test command execution failure."""
    # Mock command execution failure
    mock_linkedin_client.execute_command.side_effect = Exception("Command failed")
    
    # Set up the test state
    app.state.testing = True
    app.state.agent = AsyncMock()
    app.state.agent.handle_search_profiles.side_effect = Exception("Command failed")
    
    response = client.post(
        "/command",
        json={
            "action": "search",
            "parameters": {"title": "CEO", "location": "San Francisco"}
        }
    )
    
    assert response.status_code == 500
    assert "Command failed" in response.json()["detail"]

def test_command_request_validation():
    """Test command request validation."""
    # Valid request
    request = CommandRequest(action="search", parameters={"title": "CTO"})
    assert request.action == "search"
    assert request.parameters == {"title": "CTO"}

    # Invalid request - missing required field
    with pytest.raises(ValueError):
        CommandRequest(parameters={"title": "CTO"})

    # Invalid request - empty parameters
    with pytest.raises(ValueError):
        CommandRequest(action="search", parameters={})

    # Invalid request - invalid action
    with pytest.raises(ValueError):
        CommandRequest(action="invalid_action", parameters={"title": "CTO"}) 