"""Tests for Shaun agent RabbitMQ functionality."""
from src.common.messaging import RabbitMQClient

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from google.oauth2.service_account import Credentials
from src.agents.shaun.main import handle_rabbitmq_command, rabbitmq_client, sheets_client

from src.agents.shaun.main import app

@pytest.fixture(autouse=True)
def patch_rabbitmq_connect():
    """Automatically patch RabbitMQ connect function for all tests."""
    async def mock_connect(*args, **kwargs):
        connection = AsyncMock()
        channel = AsyncMock()
        queue = AsyncMock()
        channel.declare_queue = AsyncMock(return_value=queue)
        connection.channel = AsyncMock(return_value=channel)
        return connection

    with patch("src.common.messaging.connect_robust", new=mock_connect):
        yield

@pytest.fixture
def mock_sheets_client():
    """Mock Google Sheets client."""
    with patch("src.agents.shaun.main.sheets_client") as mock:
        instance = AsyncMock()
        instance.initialize = AsyncMock()
        mock.return_value = instance
        yield instance

@pytest.fixture
def mock_credentials():
    """Mock Google credentials."""
    with patch("src.agents.shaun.sheets_client.Credentials") as mock:
        creds = MagicMock(spec=Credentials)
        mock.from_service_account_file.return_value = creds
        yield mock

@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "GOOGLE_SHEETS_CREDS_PATH": "test_creds.json",
        "RABBITMQ_URL": "amqp://guest:guest@localhost:5672/"
    }):
        yield

def test_health_check_with_rabbitmq(mock_env_vars, mock_sheets_client, mock_credentials):
    """Test health check endpoint with RabbitMQ status."""
    with TestClient(app) as client:
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "shaun"
        assert data["client_initialized"] is True
        assert data["rabbitmq_connected"] is True

@pytest.mark.asyncio
async def test_handle_rabbitmq_command_success(mock_sheets_client):
    """Test successful handling of RabbitMQ command."""
    # Create mock message
    message = MagicMock()
    message.action = "test_action"
    message.parameters = {"param": "value"}
    message.correlation_id = "test-correlation-id"

    # Set global clients in the module
    from src.agents.shaun import main as shaun_main
    shaun_main.rabbitmq_client = AsyncMock()
    shaun_main.sheets_client = mock_sheets_client

    # Set expected return for execute_command
    mock_sheets_client.execute_command.return_value = {"status": "success"}

    # Call the command handler
    await handle_rabbitmq_command(message)

    # Verify sheets client called
    mock_sheets_client.execute_command.assert_called_once_with(
        message.action,
        message.parameters
    )

    # Verify response published
    shaun_main.rabbitmq_client.publish_message.assert_called_once_with(
        {
            "status": "success",
            "result": {"status": "success"},
            "service": "shaun"
        },
        routing_key="shaun_responses",
        correlation_id="test-correlation-id"
    )

@pytest.mark.asyncio
async def test_handle_rabbitmq_command_error(mock_sheets_client):
    """Test error handling in RabbitMQ command handler."""
    # Setup mock to raise exception
    mock_sheets_client.execute_command.side_effect = Exception("Test error")

    # Create mock message
    message = MagicMock()
    message.action = "test_action"
    message.parameters = {"param": "value"}
    message.correlation_id = "test-correlation-id"

    # Set global clients
    from src.agents.shaun import main as shaun_main
    shaun_main.rabbitmq_client = AsyncMock()
    shaun_main.sheets_client = mock_sheets_client

    # Call the command handler
    await handle_rabbitmq_command(message)

    # Verify error response published
    shaun_main.rabbitmq_client.publish_message.assert_called_once_with(
        {
            "status": "error",
            "error": "Test error",
            "service": "shaun"
        },
        routing_key="shaun_responses",
        correlation_id="test-correlation-id"
    )

@pytest.mark.asyncio
async def test_rabbitmq_client_initialization():
    """Test RabbitMQ client initialization."""
    client = RabbitMQClient("test-service")
    
    # Create mock connection function
    async def mock_connect_robust(url):
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_queue = AsyncMock()
        
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
        
        return mock_connection

    # Set mock connection function
    client.set_connect_func(mock_connect_robust)

    # Initialize client
    await client.initialize()

    # Verify connection established
    assert client.connection is not None
    assert client.channel is not None

    # Verify queues declared
    client.channel.declare_queue.assert_called()

@pytest.mark.asyncio
async def test_rabbitmq_client_cleanup():
    """Test RabbitMQ client cleanup."""
    client = RabbitMQClient("test-service")
    
    # Set mock connection and channel
    client.connection = AsyncMock()
    client.channel = AsyncMock()

    # Cleanup
    await client.cleanup()

    # Verify cleanup calls
    client.channel.close.assert_called_once()
    client.connection.close.assert_called_once()

@pytest.fixture
def mock_lifespan():
    """Fixture to mock the lifespan context manager."""
    with patch("src.agents.shaun.main.lifespan") as mock:
        yield mock

def test_health_check_with_rabbitmq(mock_env_vars, mock_sheets_client, mock_lifespan, mock_credentials):
    """Test health check endpoint with RabbitMQ status."""
    # Set the environment variable for Google Sheets credentials path
    os.environ["GOOGLE_SHEETS_CREDS_PATH"] = "test_creds.json"

    with TestClient(app) as client:
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "shaun"
        assert response.json()["client_initialized"] is True
        assert response.json()["rabbitmq_connected"] is True 