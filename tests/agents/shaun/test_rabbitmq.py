"""Tests for RabbitMQ integration in the Shaun agent."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import os

from src.agents.shaun.main import app, handle_rabbitmq_command
from common.messaging import RabbitMQClient
from src.agents.shaun.sheets_client import GoogleSheetsClient


@pytest.fixture
def mock_rabbitmq():
    """Fixture for mocked RabbitMQ client."""
    with patch("src.agents.shaun.main.rabbitmq_client") as mock:
        mock.publish_message = AsyncMock()
        mock.connection = MagicMock()
        mock.initialize = AsyncMock()
        yield mock


@pytest.fixture
def mock_sheets_client():
    """Fixture for mocked Google Sheets client."""
    with patch("src.agents.shaun.main.sheets_client") as mock:
        mock.execute_command = AsyncMock(return_value={"status": "success"})
        mock.initialize = AsyncMock()
        mock.cleanup = AsyncMock()
        yield mock


@pytest.fixture
def mock_credentials():
    """Fixture for mocked Google Sheets credentials."""
    with patch("google.oauth2.service_account.Credentials") as mock:
        mock.from_service_account_file = MagicMock()
        yield mock


@pytest.mark.asyncio
async def test_handle_rabbitmq_command_success(mock_rabbitmq, mock_sheets_client):
    """Test successful handling of RabbitMQ command."""
    # Create mock message
    message = MagicMock()
    message.action = "test_action"
    message.parameters = {"param": "value"}
    message.correlation_id = "test-correlation-id"

    # Execute command handler
    await handle_rabbitmq_command(message)

    # Verify sheets client called
    mock_sheets_client.execute_command.assert_called_once_with(
        message.action,
        message.parameters
    )

    # Verify response published
    mock_rabbitmq.publish_message.assert_called_once_with(
        {
            "status": "success",
            "result": {"status": "success"},
            "service": "shaun"
        },
        routing_key="shaun_responses",
        correlation_id="test-correlation-id"
    )


@pytest.mark.asyncio
async def test_handle_rabbitmq_command_error(mock_rabbitmq, mock_sheets_client):
    """Test error handling in RabbitMQ command handler."""
    # Setup mock to raise exception
    mock_sheets_client.execute_command.side_effect = Exception("Test error")

    # Create mock message
    message = MagicMock()
    message.action = "test_action"
    message.parameters = {"param": "value"}
    message.correlation_id = "test-correlation-id"

    # Execute command handler
    await handle_rabbitmq_command(message)

    # Verify error response published
    mock_rabbitmq.publish_message.assert_called_once_with(
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
    async def mock_lifespan_context(*args, **kwargs):
        yield None

    with patch("src.agents.shaun.main.lifespan") as mock:
        mock.return_value = mock_lifespan_context()
        yield mock


def test_health_check_with_rabbitmq(mock_rabbitmq, mock_sheets_client, mock_lifespan, mock_credentials):
    """Test health check endpoint with RabbitMQ status."""
    import os
    from fastapi.testclient import TestClient
    from unittest.mock import MagicMock, AsyncMock, patch

    # Set the environment variable for Google Sheets credentials path
    os.environ["GOOGLE_SHEETS_CREDS_PATH"] = "test_creds.json"

    # Patch the Credentials.from_service_account_file to return a dummy credentials object
    with patch("src.agents.shaun.sheets_client.Credentials.from_service_account_file", return_value=MagicMock()):
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "shaun"
            assert data["version"] == "1.0.0"
            assert data["client_initialized"] is True
            assert data["rabbitmq_connected"] is True 