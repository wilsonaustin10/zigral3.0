import pytest
from fastapi.testclient import TestClient
from orchestrator.orchestrator import app

def test_process_command(orchestrator_client: TestClient, test_command):
    """Test processing a command through the orchestrator"""
    response = orchestrator_client.post("/command", json=test_command)
    assert response.status_code == 200
    
    data = response.json()
    assert "objective" in data
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0
    
    # Verify step structure
    step = data["steps"][0]
    assert "agent" in step
    assert "action" in step
    assert step["agent"] in ["LinkedIn", "GoogleSheets", "Email", "Calendar"]

def test_process_command_without_context(orchestrator_client: TestClient):
    """Test processing a command without context"""
    command = {"command": "Find CTOs in San Francisco"}
    response = orchestrator_client.post("/command", json=command)
    assert response.status_code == 200
    
    data = response.json()
    assert "objective" in data
    assert "steps" in data

def test_process_invalid_command(orchestrator_client: TestClient):
    """Test processing an invalid command"""
    invalid_command = {}  # Missing required field
    response = orchestrator_client.post("/command", json=invalid_command)
    assert response.status_code == 422  # Validation error

def test_health_check(orchestrator_client: TestClient):
    """Test health check endpoint"""
    response = orchestrator_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "orchestrator" 