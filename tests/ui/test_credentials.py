"""Tests for the credentials and 2FA handling functionality."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json
import asyncio
from src.ui.credentials import (
    router,
    TwoFactorRequest,
    TwoFactorResponse,
    active_2fa_requests,
    twofa_responses
)

# Create test client
client = TestClient(router)

@pytest.fixture
def clear_storage():
    """Clear the storage before and after each test."""
    active_2fa_requests.clear()
    twofa_responses.clear()
    yield
    active_2fa_requests.clear()
    twofa_responses.clear()

def test_request_2fa_timeout(clear_storage):
    """Test that 2FA request times out after specified period."""
    request_data = {
        "service": "linkedin",
        "user_id": "test_user",
        "session_id": "test_session",
        "type": "sms"
    }
    
    # Override timeout for testing
    router.timeout = 0.1
    
    response = client.post("/2fa/request", json=request_data)
    assert response.status_code == 408
    assert "timed out" in response.json()["detail"]

def test_submit_2fa_invalid_session(clear_storage):
    """Test submitting 2FA code for invalid session."""
    response_data = {
        "code": "123456",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"source": "test"}
    }
    
    response = client.post("/2fa/submit/invalid_session", json=response_data)
    assert response.status_code == 404
    assert "No active 2FA request found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_2fa_flow(clear_storage):
    """Test complete 2FA flow with WebSocket."""
    request_data = TwoFactorRequest(
        service="linkedin",
        user_id="test_user",
        session_id="test_session",
        type="sms"
    )
    
    # Start 2FA request in background
    request_task = asyncio.create_task(
        router.request_2fa(request_data)
    )
    
    # Wait a bit for request to be processed
    await asyncio.sleep(0.1)
    
    # Submit 2FA code
    response_data = TwoFactorResponse(
        code="123456",
        timestamp=datetime.now(),
        metadata={"source": "test"}
    )
    
    submit_response = await router.submit_2fa(
        "test_session",
        response_data
    )
    assert submit_response["status"] == "success"
    
    # Wait for request to complete
    result = await request_task
    assert result["status"] == "success"
    assert result["code"] == "123456"

@pytest.mark.asyncio
async def test_websocket_2fa(clear_storage):
    """Test WebSocket-based 2FA interaction."""
    async with client.websocket_connect("/2fa/ws/test_session") as websocket:
        # Create 2FA request
        request_data = TwoFactorRequest(
            service="linkedin",
            user_id="test_user",
            session_id="test_session",
            type="sms"
        )
        
        # Start request in background
        request_task = asyncio.create_task(
            router.request_2fa(request_data)
        )
        
        # Wait a bit for request to be processed
        await asyncio.sleep(0.1)
        
        # Send 2FA code via WebSocket
        await websocket.send_json({
            "type": "2fa_code",
            "code": "123456",
            "metadata": {"source": "test"}
        })
        
        # Get confirmation
        response = await websocket.receive_json()
        assert response["type"] == "confirmation"
        assert response["status"] == "success"
        
        # Wait for request to complete
        result = await request_task
        assert result["status"] == "success"
        assert result["code"] == "123456"

@pytest.mark.asyncio
async def test_websocket_cancel(clear_storage):
    """Test cancelling 2FA request via WebSocket."""
    async with client.websocket_connect("/2fa/ws/test_session") as websocket:
        # Create 2FA request
        request_data = TwoFactorRequest(
            service="linkedin",
            user_id="test_user",
            session_id="test_session",
            type="sms"
        )
        
        # Start request in background
        request_task = asyncio.create_task(
            router.request_2fa(request_data)
        )
        
        # Wait a bit for request to be processed
        await asyncio.sleep(0.1)
        
        # Send cancel message
        await websocket.send_json({
            "type": "cancel"
        })
        
        # Get confirmation
        response = await websocket.receive_json()
        assert response["type"] == "confirmation"
        assert response["status"] == "cancelled"
        
        # Verify request was cancelled
        with pytest.raises(Exception):
            await request_task 