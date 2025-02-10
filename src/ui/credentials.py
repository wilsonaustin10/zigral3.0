"""
UI components for handling credentials and 2FA.

This module provides FastAPI endpoints and Pydantic models for managing
credentials and handling two-factor authentication interactions.
"""

from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import asyncio
import json
from datetime import datetime

# Pydantic models for request/response handling
class TwoFactorRequest(BaseModel):
    """Model for 2FA request data."""
    service: str  # e.g., 'linkedin', 'google'
    user_id: str
    session_id: str
    type: str  # e.g., 'sms', 'authenticator', 'email'
    metadata: Optional[Dict[str, Any]] = None

class TwoFactorResponse(BaseModel):
    """Model for 2FA response data."""
    code: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

# Create FastAPI router for credential endpoints
router = FastAPI()

# Store active 2FA requests (in-memory for development, use Redis in production)
active_2fa_requests: Dict[str, asyncio.Event] = {}
twofa_responses: Dict[str, TwoFactorResponse] = {}

@router.post("/2fa/request")
async def request_2fa(request: TwoFactorRequest) -> Dict[str, Any]:
    """
    Request 2FA code from user.
    
    Args:
        request: The 2FA request details
        
    Returns:
        Dict containing request status and session ID
    """
    # Create an event for this request
    event = asyncio.Event()
    active_2fa_requests[request.session_id] = event
    
    try:
        # Wait for user to provide 2FA code (with timeout)
        await asyncio.wait_for(event.wait(), timeout=300)  # 5 minute timeout
        
        # Get and clear the response
        response = twofa_responses.pop(request.session_id)
        return {
            "status": "success",
            "code": response.code,
            "timestamp": response.timestamp,
            "metadata": response.metadata
        }
    except asyncio.TimeoutError:
        # Clean up on timeout
        active_2fa_requests.pop(request.session_id, None)
        raise HTTPException(
            status_code=408,
            detail="2FA request timed out. Please try again."
        )
    finally:
        # Clean up the event
        active_2fa_requests.pop(request.session_id, None)

@router.post("/2fa/submit/{session_id}")
async def submit_2fa(session_id: str, response: TwoFactorResponse) -> Dict[str, str]:
    """
    Submit 2FA code from user.
    
    Args:
        session_id: The session ID for this 2FA request
        response: The 2FA response including the code
        
    Returns:
        Dict containing submission status
    """
    event = active_2fa_requests.get(session_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail="No active 2FA request found for this session"
        )
    
    # Store the response and trigger the event
    twofa_responses[session_id] = response
    event.set()
    
    return {"status": "success"}

@router.websocket("/2fa/ws/{session_id}")
async def websocket_2fa(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time 2FA interactions.
    
    This allows for push notifications and real-time updates during the 2FA process.
    
    Args:
        websocket: The WebSocket connection
        session_id: The session ID for this 2FA request
    """
    await websocket.accept()
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "2fa_code":
                # Create a response object
                response = TwoFactorResponse(
                    code=message["code"],
                    timestamp=datetime.now(),
                    metadata=message.get("metadata")
                )
                
                # Submit the code
                await submit_2fa(session_id, response)
                
                # Send confirmation
                await websocket.send_json({
                    "type": "confirmation",
                    "status": "success"
                })
                
            elif message.get("type") == "cancel":
                # Handle cancellation
                if session_id in active_2fa_requests:
                    event = active_2fa_requests[session_id]
                    event.set()  # This will trigger an error in the main request
                
                await websocket.send_json({
                    "type": "confirmation",
                    "status": "cancelled"
                })
                break
                
    except WebSocketDisconnect:
        # Clean up if needed
        pass
    except Exception as e:
        # Log the error and clean up
        print(f"WebSocket error: {str(e)}")
        if session_id in active_2fa_requests:
            event = active_2fa_requests[session_id]
            event.set()  # Signal the main request to fail 