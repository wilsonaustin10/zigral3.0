"""Tests for Shaun agent FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.agents.shaun.main import app, ProspectData

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_sheets_client():
    """Mock Google Sheets client."""
    with patch("src.agents.shaun.main.GoogleSheetsClient") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance

def test_command_endpoint_client_not_initialized(client):
    """Test command endpoint when client is not initialized."""
    response = client.post(
        "/command",
        json={"action": "connect", "parameters": {"sheet_id": "test"}}
    )
    assert response.status_code == 500
    assert "not initialized" in response.json()["detail"]

def test_command_endpoint_success(client, mock_sheets_client):
    """Test successful command execution."""
    # Mock successful command execution
    mock_sheets_client.execute_command.return_value = {"success": True}
    
    # Initialize the client by triggering startup event
    with TestClient(app) as client:
        response = client.post(
            "/command",
            json={"action": "connect", "parameters": {"sheet_id": "test"}}
        )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_add_prospects_endpoint_success(client, mock_sheets_client):
    """Test successful prospect addition."""
    prospects = [
        {
            "full_name": "John Doe",
            "current_title": "CTO",
            "current_company": "Tech Corp",
            "location": "San Francisco",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "experience": [{"company": "Previous Corp"}],
            "education": [{"school": "University"}]
        }
    ]
    
    mock_sheets_client.add_prospects.return_value = {
        "success": True,
        "added": prospects
    }
    
    # Initialize the client by triggering startup event
    with TestClient(app) as client:
        response = client.post("/prospects", json=prospects)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["prospects_added"] == 1

def test_add_prospects_validation(client):
    """Test prospect data validation."""
    invalid_prospect = {
        # Missing required fields
        "full_name": "John Doe"
    }
    
    response = client.post("/prospects", json=[invalid_prospect])
    assert response.status_code == 422  # Validation error

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy" 