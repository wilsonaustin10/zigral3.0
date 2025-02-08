"""Tests for RabbitMQ integration in Lincoln agent."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.lincoln.main import LincolnAgent

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
async def mock_linkedin_client():
    """Create a mock LinkedIn client."""
    mock_client = AsyncMock()
    mock_client.initialize = AsyncMock()
    mock_client.cleanup = AsyncMock()
    mock_client.search_sales_navigator = AsyncMock(return_value=[])
    mock_client.get_profile_data = AsyncMock(return_value={})
    mock_client.capture_gui_state = AsyncMock(return_value={})
    return mock_client

@pytest.fixture
async def lincoln_agent(mock_rabbitmq, mock_linkedin_client):
    """Create a Lincoln agent with mocked dependencies."""
    with patch('src.agents.lincoln.main.RabbitMQClient', return_value=mock_rabbitmq), \
         patch('src.agents.lincoln.main.LinkedInClient', return_value=mock_linkedin_client):
        agent = LincolnAgent()
        await agent.initialize()
        yield agent
        await agent.cleanup()

@pytest.mark.asyncio
async def test_agent_initialization(lincoln_agent, mock_rabbitmq):
    """Test that the agent initializes correctly."""
    mock_rabbitmq.initialize.assert_called_once()
    mock_rabbitmq.subscribe.assert_called_once_with(
        "lincoln_commands",
        lincoln_agent.handle_command
    )

@pytest.mark.asyncio
async def test_handle_search_profiles(lincoln_agent, mock_rabbitmq, mock_linkedin_client):
    """Test handling search_profiles command."""
    # Mock search results
    mock_profiles = [
        {
            "name": "John Doe",
            "title": "CEO",
            "company": "Example Corp"
        }
    ]
    mock_linkedin_client.search_sales_navigator.return_value = mock_profiles
    
    # Create a mock message
    message = AsyncMock()
    message.body = json.dumps({
        "command": "search_profiles",
        "data": {
            "search_params": {
                "keywords": "CEO",
                "location": "San Francisco"
            }
        }
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await lincoln_agent.handle_command(message)
    
    # Verify LinkedIn client was called with correct parameters
    mock_linkedin_client.search_sales_navigator.assert_called_once_with({
        "keywords": "CEO",
        "location": "San Francisco"
    })
    
    # Verify response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "success"
    assert call_args.args[0]["profiles"] == mock_profiles
    assert call_args.kwargs["routing_key"] == "lincoln_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_get_profile_data(lincoln_agent, mock_rabbitmq, mock_linkedin_client):
    """Test handling get_profile_data command."""
    # Mock profile data
    mock_profile = {
        "name": "Jane Smith",
        "title": "CTO",
        "company": "Tech Corp"
    }
    mock_linkedin_client.get_profile_data.return_value = mock_profile
    
    # Create a mock message
    message = AsyncMock()
    message.body = json.dumps({
        "command": "get_profile_data",
        "data": {
            "profile_urls": ["https://linkedin.com/in/janesmith"]
        }
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await lincoln_agent.handle_command(message)
    
    # Verify LinkedIn client was called with correct URL
    mock_linkedin_client.get_profile_data.assert_called_once_with(
        "https://linkedin.com/in/janesmith"
    )
    
    # Verify response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "success"
    assert call_args.args[0]["profiles_data"] == [mock_profile]
    assert call_args.kwargs["routing_key"] == "lincoln_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_capture_state(lincoln_agent, mock_rabbitmq, mock_linkedin_client):
    """Test handling capture_state command."""
    # Mock GUI state data
    mock_state = {
        "html": "<html>...</html>",
        "screenshot": "base64_encoded_image"
    }
    mock_linkedin_client.capture_gui_state.return_value = mock_state
    
    # Create a mock message
    message = AsyncMock()
    message.body = json.dumps({
        "command": "capture_state",
        "data": {}
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await lincoln_agent.handle_command(message)
    
    # Verify LinkedIn client was called
    mock_linkedin_client.capture_gui_state.assert_called_once()
    
    # Verify response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "success"
    assert call_args.args[0]["state_data"] == mock_state
    assert call_args.kwargs["routing_key"] == "lincoln_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_unknown_command(lincoln_agent, mock_rabbitmq):
    """Test handling unknown command."""
    message = AsyncMock()
    message.body = json.dumps({
        "command": "unknown_command",
        "data": {}
    }).encode()
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await lincoln_agent.handle_command(message)
    
    # Verify error response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "error"
    assert "Unknown command" in call_args.args[0]["error"]
    assert call_args.kwargs["routing_key"] == "lincoln_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id"

@pytest.mark.asyncio
async def test_handle_invalid_message(lincoln_agent, mock_rabbitmq):
    """Test handling invalid message format."""
    message = AsyncMock()
    message.body = b"invalid json"
    message.correlation_id = "test-correlation-id"
    message.process = lambda: FakeAsyncContextManager()
    
    # Handle the message
    await lincoln_agent.handle_command(message)
    
    # Verify error response was published
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.args[0]["status"] == "error"
    assert call_args.kwargs["routing_key"] == "lincoln_responses"
    assert call_args.kwargs["correlation_id"] == "test-correlation-id" 