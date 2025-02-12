"""Tests for WebSocket functionality in the orchestrator.

Recent Changes (2025-02-12):
1. Added mock_env_vars fixture to properly mock TEMP_AUTH_TOKEN
2. Updated test_command_updates to handle FastAPI's error response format
3. Added proper authentication headers to test requests
4. Fixed WebSocket update assertions to match the orchestrator's response format
"""

import json
import os
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from unittest.mock import AsyncMock, patch

from orchestrator.orchestrator import app, manager


@pytest.fixture
def mock_agent_manager():
    """Create a mock agent manager."""
    manager = AsyncMock()
    manager.execute_action_sequence = AsyncMock(return_value=[
        {"step": {"action": "test"}, "result": {"status": "success", "message": "Test completed"}}
    ])
    return manager


@pytest.fixture
def mock_action_sequence():
    """Create a mock action sequence."""
    return {
        "objective": "Test objective",
        "steps": [
            {
                "agent": "test",
                "action": "test",
                "target": "test"
            }
        ]
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {"TEMP_AUTH_TOKEN": "zigral_dev_token_123"}):
        yield


@pytest.fixture
def websocket_client(mock_agent_manager, mock_env_vars):
    """Create a test client for WebSocket connections."""
    app.state.agent_manager = mock_agent_manager
    return TestClient(app)


def test_websocket_connection(websocket_client):
    """Test WebSocket connection and basic message exchange."""
    with websocket_client.websocket_connect("/ws/updates/test-client-1") as websocket:
        # Test sending a message
        websocket.send_text("ping")
        
        # Verify response
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert response["data"] == "ping"


@pytest.mark.asyncio
async def test_broadcast_message():
    """Test broadcasting messages to connected clients."""
    # Create mock WebSocket connections
    mock_ws1 = AsyncMock(spec=WebSocket)
    mock_ws2 = AsyncMock(spec=WebSocket)
    
    # Connect mock clients
    await manager.connect(mock_ws1, "client-1")
    await manager.connect(mock_ws2, "client-2")
    
    # Test broadcasting a message
    test_message = {
        "type": "test_event",
        "data": {"message": "test"}
    }
    await manager.broadcast(test_message)
    
    # Verify both clients received the message
    mock_ws1.send_json.assert_called_once_with(test_message)
    mock_ws2.send_json.assert_called_once_with(test_message)


@pytest.mark.asyncio
async def test_client_disconnect_handling():
    """Test proper handling of client disconnections."""
    # Create mock WebSocket connection
    mock_ws = AsyncMock(spec=WebSocket)
    
    # Connect mock client
    await manager.connect(mock_ws, "client-1")
    assert "client-1" in manager.active_connections
    
    # Simulate disconnection
    mock_ws.send_json.side_effect = Exception("Connection lost")
    await manager.broadcast({"type": "test"})
    
    # Verify client was removed
    assert "client-1" not in manager.active_connections


@pytest.mark.asyncio
async def test_command_updates(websocket_client, mock_action_sequence):
    """Test that command processing sends appropriate WebSocket updates."""
    with (
        patch('orchestrator.orchestrator.generate_action_sequence', 
              return_value=mock_action_sequence) as mock_generate,
        websocket_client.websocket_connect("/ws/updates/test-client") as websocket
    ):
        # Send a command via HTTP
        response = websocket_client.post(
            "/command",
            json={"command": "test command"},
            headers={"Authorization": "Bearer zigral_dev_token_123"}
        )
        assert response.status_code == 200
        
        # Verify WebSocket updates
        updates = []
        for _ in range(3):  # Expect 3 updates: received, generated, complete
            updates.append(websocket.receive_json())
        
        # Verify update sequence
        assert updates[0]["type"] == "command_received"
        assert updates[0]["data"]["command"] == "test command"
        
        assert updates[1]["type"] == "action_sequence_generated"
        assert updates[1]["data"] == mock_action_sequence
        
        assert updates[2]["type"] == "execution_complete"
        assert updates[2]["data"]["objective"] == mock_action_sequence["objective"]
        assert len(updates[2]["data"]["steps"]) == 1
        assert updates[2]["data"]["steps"][0]["result"]["status"] == "success" 