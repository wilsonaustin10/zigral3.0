"""Tests for RabbitMQ integration in Shaun agent."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.shaun.main import ShaunAgent

class FakeAsyncContextManager:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.fixture
async def mock_rabbitmq():
    """Create a mock RabbitMQ client."""
    mock_client = AsyncMock()
    mock_client.initialize = AsyncMock()
    mock_client.cleanup = AsyncMock()
    mock_client.publish_message = AsyncMock()
    mock_client.subscribe = AsyncMock()
    return mock_client

@pytest.fixture
async def mock_sheets_client():
    """Create a mock Google Sheets client."""
    mock_client = AsyncMock()
    mock_client.update_prospects = AsyncMock()
    mock_client.get_prospects = AsyncMock(return_value=[])
    return mock_client

@pytest.fixture
async def shaun_agent(mock_rabbitmq, mock_sheets_client):
    """Create a Shaun agent with mocked dependencies."""
    with patch('src.agents.shaun.main.RabbitMQClient', return_value=mock_rabbitmq), \
         patch('src.agents.shaun.main.GoogleSheetsClient', return_value=mock_sheets_client):
        agent = ShaunAgent()
        await agent.initialize()
        yield agent
        await agent.cleanup()

@pytest.mark.asyncio
async def test_agent_initialization(shaun_agent, mock_rabbitmq):
    """Test that the agent initializes correctly."""
    mock_rabbitmq.initialize.assert_called_once()
    mock_rabbitmq.subscribe.assert_called_once_with(
        "shaun_commands",
        shaun_agent.handle_command
    )

@pytest.mark.asyncio
async def test_handle_update_prospects(shaun_agent, mock_rabbitmq, mock_sheets_client):
    """Test handling update_prospects command."""
    # Create a mock message
    message = AsyncMock()
    message.body = json.dumps({
        "command": "update_prospects",
        "data": {
            "prospects": [
                {
                    "full_name": "John Doe",
                    "title": "CEO",
                    "company": "Example Corp"
                }
            ]
        }
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await shaun_agent.handle_command(message)
    
    # Verify sheets client was called
    mock_sheets_client.update_prospects.assert_called_once()
    
    # Verify response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "success"
    assert call_args.kwargs["routing_key"] == "shaun_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_get_prospects(shaun_agent, mock_rabbitmq, mock_sheets_client):
    """Test handling get_prospects command."""
    # Mock return data
    mock_prospects = [
        {
            "full_name": "Jane Smith",
            "title": "CTO",
            "company": "Tech Corp"
        }
    ]
    mock_sheets_client.get_prospects.return_value = mock_prospects
    
    # Create a mock message
    message = AsyncMock()
    message.body = json.dumps({
        "command": "get_prospects",
        "data": {
            "filters": {"company": "Tech Corp"}
        }
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await shaun_agent.handle_command(message)
    
    # Verify sheets client was called with filters
    mock_sheets_client.get_prospects.assert_called_once_with({"company": "Tech Corp"})
    
    # Verify response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "success"
    assert call_args.args[0]["prospects"] == mock_prospects
    assert call_args.kwargs["routing_key"] == "shaun_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_unknown_command(shaun_agent, mock_rabbitmq):
    """Test handling unknown command."""
    message = AsyncMock()
    message.body = json.dumps({
        "command": "unknown_command",
        "data": {}
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await shaun_agent.handle_command(message)
    
    # Verify error response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "error"
    assert "Unknown command" in call_args.args[0]["error"]
    assert call_args.kwargs["routing_key"] == "shaun_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_invalid_message(shaun_agent, mock_rabbitmq):
    """Test handling invalid message format."""
    message = AsyncMock()
    message.body = b"invalid json"
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await shaun_agent.handle_command(message)
    
    # Verify error response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "error"
    assert call_args.kwargs["routing_key"] == "shaun_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id" 