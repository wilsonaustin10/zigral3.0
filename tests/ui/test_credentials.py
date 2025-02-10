"""Tests for the credentials and 2FA handling functionality."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
import json
import asyncio
from src.ui.credentials import (
    router,
    TwoFactorRequest,
    TwoFactorResponse,
    active_2fa_requests,
    twofa_responses,
    timeout
)

# Create FastAPI app for testing
app = FastAPI()
app.include_router(router)

# Create test client
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_storage():
    """Clear the storage before and after each test."""
    active_2fa_requests.clear()
    twofa_responses.clear()
    # Store original timeout
    original_timeout = globals()['timeout']
    yield
    # Restore original timeout
    globals()['timeout'] = original_timeout
    active_2fa_requests.clear()
    twofa_responses.clear()

def test_request_2fa_timeout():
    """Test that 2FA request times out after specified period."""
    # Set a short timeout for testing
    globals()['timeout'] = 0.1
    
    request_data = {
        "service": "linkedin",
        "user_id": "test_user",
        "session_id": "test_session",
        "type": "sms"
    }
    
    print("DEBUG: Before POST request in test_request_2fa_timeout")
    response = client.post("/2fa/request", json=request_data)
    print("DEBUG: After POST request, response status:", response.status_code)
    
    assert response.status_code == 408
    assert "timed out" in response.json()["detail"]
    
    # Verify cleanup
    assert "test_session" not in active_2fa_requests
    assert "test_session" not in twofa_responses

def test_submit_2fa_invalid_session():
    """Test submitting 2FA code for invalid session."""
    response_data = {
        "code": "123456",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"source": "test"}
    }
    
    response = client.post("/2fa/submit/invalid_session", json=response_data)
    assert response.status_code == 404
    assert "No active 2FA request found" in response.json()["detail"]

def test_2fa_flow():
    """Test complete 2FA flow."""
    # Start 2FA request
    request_data = {
        "service": "linkedin",
        "user_id": "test_user",
        "session_id": "test_session",
        "type": "sms"
    }
    
    # Create background task to handle 2FA request
    def submit_2fa():
        # Wait a bit before submitting
        import time
        time.sleep(0.1)
        
        # Submit 2FA code
        response_data = {
            "code": "123456",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"source": "test"}
        }
        return client.post("/2fa/submit/test_session", json=response_data)
    
    import threading
    submit_thread = threading.Thread(target=submit_2fa)
    submit_thread.start()
    
    # Make the 2FA request
    response = client.post("/2fa/request", json=request_data)
    submit_thread.join()
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["code"] == "123456"
    
    # Verify cleanup
    assert "test_session" not in active_2fa_requests
    assert "test_session" not in twofa_responses

def test_websocket_2fa():
    """Test WebSocket-based 2FA interaction."""
    with client.websocket_connect("/2fa/ws/test_session") as websocket:
        # Create 2FA request
        request_data = {
            "service": "linkedin",
            "user_id": "test_user",
            "session_id": "test_session",
            "type": "sms"
        }
        
        # Create background task to handle 2FA request
        def handle_2fa_request():
            return client.post("/2fa/request", json=request_data)
        
        import threading
        request_thread = threading.Thread(target=handle_2fa_request)
        request_thread.start()
        
        # Wait a bit for request to be processed
        import time
        time.sleep(0.1)
        
        # Send 2FA code via WebSocket
        websocket.send_json({
            "type": "2fa_code",
            "code": "123456",
            "metadata": {"source": "test"}
        })
        
        # Get confirmation
        response = websocket.receive_json()
        assert response["type"] == "confirmation"
        assert response["status"] == "success"
        
        # Wait for request to complete
        request_thread.join()
        
        # Verify cleanup
        assert "test_session" not in active_2fa_requests
        assert "test_session" not in twofa_responses

def test_websocket_cancel():
    """Test cancelling 2FA request via WebSocket."""
    with client.websocket_connect("/2fa/ws/test_session") as websocket:
        # Create 2FA request
        request_data = {
            "service": "linkedin",
            "user_id": "test_user",
            "session_id": "test_session",
            "type": "sms"
        }
        
        # Create background task to handle 2FA request
        def handle_2fa_request():
            return client.post("/2fa/request", json=request_data)
        
        import threading
        request_thread = threading.Thread(target=handle_2fa_request)
        request_thread.start()
        
        # Wait a bit for request to be processed
        import time
        time.sleep(0.1)
        
        # Send cancel message
        websocket.send_json({
            "type": "cancel"
        })
        
        # Get confirmation
        response = websocket.receive_json()
        assert response["type"] == "confirmation"
        assert response["status"] == "cancelled"
        
        # Wait for request to complete
        request_thread.join()
        
        # Verify cleanup
        assert "test_session" not in active_2fa_requests
        assert "test_session" not in twofa_responses 