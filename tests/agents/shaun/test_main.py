"""Tests for Shaun agent FastAPI endpoints."""

import os
os.environ["TESTING"] = "true"
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from google.oauth2.service_account import Credentials

from src.agents.shaun.main import app, ProspectData

@pytest.fixture
def mock_rabbitmq_connection():
    """Mock RabbitMQ connection."""
    connection = AsyncMock()
    channel = AsyncMock()
    queue = AsyncMock()
    
    channel.declare_queue = AsyncMock(return_value=queue)
    connection.channel = AsyncMock(return_value=channel)
    
    async def mock_connect(*args, **kwargs):
        return connection
    
    with patch("src.common.messaging.connect_robust", mock_connect):
        yield connection

@pytest.fixture
def mock_credentials():
    """Mock Google credentials."""
    with patch("src.agents.shaun.sheets_client.Credentials") as mock:
        creds = MagicMock(spec=Credentials)
        mock.from_service_account_file.return_value = creds
        yield mock

@pytest.fixture
def mock_sheets_client(mock_credentials):
    """Mock Google Sheets client."""
    with patch("src.agents.shaun.main.sheets_client") as mock:
        instance = AsyncMock()
        instance.initialize = AsyncMock()
        mock.return_value = instance
        yield instance

@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict("os.environ", {
        "GOOGLE_SHEETS_CREDS_PATH": "test_creds.json",
        "RABBITMQ_URL": "amqp://guest:guest@localhost:5672/"
    }):
        yield

def test_command_endpoint_client_not_initialized():
    """Test command endpoint when client is not initialized."""
    from src.agents.shaun import main as shaun_main
    shaun_main.sheets_client = None
    from fastapi.testclient import TestClient
    with TestClient(shaun_main.app) as client:
        response = client.post("/command", json={"action": "connect", "parameters": {"sheet_id": "test"}})
    assert response.status_code == 500
    assert "not initialized" in response.json()["detail"]

def test_command_endpoint_success(mock_env_vars, mock_sheets_client, mock_rabbitmq_connection):
    """Test successful command execution."""
    from src.agents.shaun import main as shaun_main
    # Set global clients
    shaun_main.sheets_client = mock_sheets_client
    from unittest.mock import AsyncMock
    shaun_main.rabbitmq_client = AsyncMock()
    mock_sheets_client.execute_command = AsyncMock(return_value={"success": True})
    from fastapi.testclient import TestClient
    with TestClient(shaun_main.app) as client:
        response = client.post("/command", json={"action": "connect", "parameters": {"sheet_id": "test"}})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_add_prospects_endpoint_success(mock_env_vars, mock_sheets_client, mock_rabbitmq_connection):
    """Test successful prospect addition."""
    from src.agents.shaun import main as shaun_main
    prospect = {
        "full_name": "John Doe",
        "current_title": "CTO",
        "current_company": "Tech Corp",
        "location": "San Francisco",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "experience": [{"company": "Previous Corp"}],
        "education": [{"school": "University"}]
    }
    # Set global clients
    shaun_main.sheets_client = mock_sheets_client
    from unittest.mock import AsyncMock
    shaun_main.rabbitmq_client = AsyncMock()
    mock_sheets_client.add_prospects = AsyncMock(return_value={"success": True, "added": [prospect]})
    from fastapi.testclient import TestClient
    with TestClient(shaun_main.app) as client:
        response = client.post("/prospects", json=[prospect])
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["prospects_added"] == 1

def test_add_prospects_validation():
    """Test prospect data validation."""
    from src.agents.shaun import main as shaun_main
    # Set dummy clients
    from unittest.mock import AsyncMock
    shaun_main.sheets_client = AsyncMock()
    shaun_main.rabbitmq_client = AsyncMock()
    from fastapi.testclient import TestClient
    with TestClient(shaun_main.app) as client:
        invalid_prospect = {
            "full_name": "John Doe"
            # Missing current_title, current_company, location, linkedin_url
        }
        response = client.post("/prospects", json=[invalid_prospect])
    assert response.status_code == 422

def test_health_check():
    """Test health check endpoint."""
    from src.agents.shaun import main as shaun_main
    from unittest.mock import AsyncMock
    shaun_main.sheets_client = AsyncMock()
    dummy_rmq = AsyncMock()
    dummy_rmq.connection = object()
    shaun_main.rabbitmq_client = dummy_rmq
    from fastapi.testclient import TestClient
    with TestClient(shaun_main.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy" 