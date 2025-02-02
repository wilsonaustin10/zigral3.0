import pytest
from fastapi.testclient import TestClient
from orchestrator.orchestrator import app

# Happy Path Tests
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
    assert "parameters" in step or "target" in step

def test_process_command_without_context(orchestrator_client: TestClient):
    """Test processing a command without context"""
    command = {"command": "Find CTOs in San Francisco"}
    response = orchestrator_client.post("/command", json=command)
    assert response.status_code == 200
    
    data = response.json()
    assert "objective" in data
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0

# Error Cases
def test_process_invalid_command(orchestrator_client: TestClient):
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

def test_process_command_with_invalid_context(orchestrator_client: TestClient):
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

def test_process_complex_command(orchestrator_client: TestClient):
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
    
    data = response.json()
    assert len(data["steps"]) > 2  # Should have multiple steps
    
    # Verify sequence of steps
    actions = [step["action"] for step in data["steps"]]
    assert "search" in actions  # Should include search
    assert "export" in actions or "update" in actions  # Should include data export
    assert "send" in actions  # Should include email sending

def test_health_check(orchestrator_client: TestClient):
    """Test health check endpoint"""
    response = orchestrator_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

# Rate Limiting Tests (if implemented)
def test_rate_limiting(orchestrator_client: TestClient):
    """Test rate limiting on the command endpoint"""
    # Make multiple requests in quick succession
    responses = []
    for _ in range(10):
        response = orchestrator_client.post("/command", json={"command": "Find CTOs"})
        responses.append(response)
    
    # Check if any requests were rate limited
    rate_limited = any(r.status_code == 429 for r in responses)
    successful = any(r.status_code == 200 for r in responses)
    assert successful  # At least some requests should succeed
    # Note: This test may need adjustment based on your rate limiting configuration 