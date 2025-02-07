"""Tests for agent command handling in the orchestrator."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.orchestrator.agent_commands import AgentCommandManager

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
async def command_manager(mock_rabbitmq):
    """Create an agent command manager with mocked dependencies."""
    with patch('src.orchestrator.agent_commands.RabbitMQClient', return_value=mock_rabbitmq):
        manager = AgentCommandManager()
        await manager.initialize()
        yield manager
        await manager.cleanup()

@pytest.mark.asyncio
async def test_initialization(command_manager, mock_rabbitmq):
    """Test that the command manager initializes correctly."""
    mock_rabbitmq.initialize.assert_called_once()
    mock_rabbitmq.subscribe.assert_any_call(
        "lincoln_responses",
        command_manager.handle_lincoln_response
    )
    mock_rabbitmq.subscribe.assert_any_call(
        "shaun_responses",
        command_manager.handle_shaun_response
    )

@pytest.mark.asyncio
async def test_execute_lincoln_command(command_manager, mock_rabbitmq):
    """Test executing a command on the Lincoln agent."""
    # Create a response message
    response_data = {
        "status": "success",
        "profiles": [{"name": "John Doe"}]
    }
    
    # Simulate response handling
    async def simulate_response(correlation_id):
        message = AsyncMock()
        message.correlation_id = correlation_id
        message.body = json.dumps(response_data).encode()
        message.process = lambda: FakeAsyncContextManager()
        await command_manager.handle_lincoln_response(message)
    
    # Execute command and simulate response
    command_task = asyncio.create_task(
        command_manager.execute_lincoln_command(
            "search_profiles",
            {"search_params": {"keywords": "CEO"}}
        )
    )
    
    # Wait a bit to ensure the command is sent
    await asyncio.sleep(0.1)
    
    # Get the correlation ID from the publish call
    publish_calls = mock_rabbitmq.publish_message.call_args_list
    assert len(publish_calls) == 1
    correlation_id = publish_calls[0].kwargs["correlation_id"]
    
    # Simulate response
    await simulate_response(correlation_id)
    
    # Get command result
    result = await command_task
    assert result == response_data
    
    # Verify message was published correctly
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.kwargs["routing_key"] == "lincoln_commands"
    assert call_args.args[0] == {
        "command": "search_profiles",
        "data": {"search_params": {"keywords": "CEO"}}
    }

@pytest.mark.asyncio
async def test_execute_shaun_command(command_manager, mock_rabbitmq):
    """Test executing a command on the Shaun agent."""
    # Create a response message
    response_data = {
        "status": "success",
        "message": "Updated 1 prospect"
    }
    
    # Simulate response handling
    async def simulate_response(correlation_id):
        message = AsyncMock()
        message.correlation_id = correlation_id
        message.body = json.dumps(response_data).encode()
        message.process = lambda: FakeAsyncContextManager()
        await command_manager.handle_shaun_response(message)
    
    # Execute command and simulate response
    command_task = asyncio.create_task(
        command_manager.execute_shaun_command(
            "update_prospects",
            {"prospects": [{"name": "John Doe"}]}
        )
    )
    
    # Wait a bit to ensure the command is sent
    await asyncio.sleep(0.1)
    
    # Get the correlation ID from the publish call
    publish_calls = mock_rabbitmq.publish_message.call_args_list
    assert len(publish_calls) == 1
    correlation_id = publish_calls[0].kwargs["correlation_id"]
    
    # Simulate response
    await simulate_response(correlation_id)
    
    # Get command result
    result = await command_task
    assert result == response_data
    
    # Verify message was published correctly
    mock_rabbitmq.publish_message.assert_called_once()
    call_args = mock_rabbitmq.publish_message.call_args
    assert call_args.kwargs["routing_key"] == "shaun_commands"
    assert call_args.args[0] == {
        "command": "update_prospects",
        "data": {"prospects": [{"name": "John Doe"}]}
    }

@pytest.mark.asyncio
async def test_execute_action_sequence(command_manager, mock_rabbitmq):
    """Test executing a complete action sequence."""
    sequence = {
        "objective": "Find and update prospects",
        "steps": [
            {
                "agent": "lincoln",
                "action": "search_profiles",
                "criteria": {"keywords": "CEO"}
            },
            {
                "agent": "shaun",
                "action": "update_prospects",
                "data": {
                    "prospects": [{"name": "John Doe"}]
                }
            }
        ]
    }
    
    # Create response messages
    lincoln_response = {
        "status": "success",
        "profiles": [{"name": "John Doe"}]
    }
    shaun_response = {
        "status": "success",
        "message": "Updated 1 prospect"
    }
    
    # Create a list to store correlation IDs in order
    correlation_ids = []
    
    # Create a new mock for publish_message
    publish_mock = AsyncMock()
    async def side_effect(*args, **kwargs):
        correlation_ids.append(kwargs["correlation_id"])
    publish_mock.side_effect = side_effect
    mock_rabbitmq.publish_message = publish_mock
    
    # Execute sequence
    sequence_task = asyncio.create_task(
        command_manager.execute_action_sequence(sequence)
    )
    
    # Wait a bit to ensure the first command is sent
    await asyncio.sleep(0.1)
    
    # Simulate Lincoln response
    message = AsyncMock()
    message.correlation_id = correlation_ids[0]
    message.body = json.dumps(lincoln_response).encode()
    message.process = lambda: FakeAsyncContextManager()
    await command_manager.handle_lincoln_response(message)
    
    # Wait a bit to ensure the second command is sent
    await asyncio.sleep(0.1)
    
    # Simulate Shaun response
    message = AsyncMock()
    message.correlation_id = correlation_ids[1]
    message.body = json.dumps(shaun_response).encode()
    message.process = lambda: FakeAsyncContextManager()
    await command_manager.handle_shaun_response(message)
    
    # Get sequence results
    results = await sequence_task
    assert len(results) == 2
    assert results[0]["result"] == lincoln_response
    assert results[1]["result"] == shaun_response
    
    # Verify messages were published correctly
    assert publish_mock.call_count == 2
    lincoln_call = publish_mock.call_args_list[0]
    shaun_call = publish_mock.call_args_list[1]
    
    assert lincoln_call.kwargs["routing_key"] == "lincoln_commands"
    assert shaun_call.kwargs["routing_key"] == "shaun_commands"
    
    assert lincoln_call.args[0] == {
        "command": "search_profiles",
        "data": {
            "search_params": {"keywords": "CEO"},
            "profile_urls": [],
            "fields": []
        }
    }
    assert shaun_call.args[0] == {
        "command": "update_prospects",
        "data": {
            "prospects": [{"name": "John Doe"}],
            "filters": {}
        }
    }

@pytest.mark.asyncio
async def test_invalid_agent(command_manager):
    """Test handling invalid agent in action sequence."""
    sequence = {
        "objective": "Invalid test",
        "steps": [
            {
                "agent": "invalid_agent",
                "action": "test",
                "data": {}
            }
        ]
    }
    
    results = await command_manager.execute_action_sequence(sequence)
    assert len(results) == 1
    assert results[0]["result"]["status"] == "error"
    assert "Unknown agent" in results[0]["result"]["error"] 