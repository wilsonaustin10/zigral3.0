"""Tests for WebSocket functionality in the orchestrator."""

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from unittest.mock import AsyncMock, patch

from orchestrator.orchestrator import app, manager


@pytest.fixture
def websocket_client():
    """Create a test client for WebSocket connections."""
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
async def test_command_updates(websocket_client):
    """Test that command processing sends appropriate WebSocket updates."""
    with websocket_client.websocket_connect("/ws/updates/test-client") as websocket:
        # Send a command via HTTP
        response = websocket_client.post(
            "/command",
            json={"command": "test command"},
            headers={"Authorization": f"Bearer {pytest.TEST_AUTH_TOKEN}"}
        )
        assert response.status_code == 200
        
        # Verify WebSocket updates
        updates = []
        for _ in range(3):  # Expect 3 updates: received, generated, complete
            updates.append(websocket.receive_json())
        
        # Verify update sequence
        assert updates[0]["type"] == "command_received"
        assert updates[1]["type"] == "action_sequence_generated"
        assert updates[2]["type"] == "execution_complete" 