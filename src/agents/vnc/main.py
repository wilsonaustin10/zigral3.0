"""
VNC Agent Runner Service
Main FastAPI application entry point.
"""

import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn

from .browser import BrowserManager, BrowserCommand, BrowserCommandStatus
from .utils.config import Settings, get_settings
from .utils.auth import verify_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Zigral VNC Agent",
    description="VNC Agent Runner Service for browser automation",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize browser manager
browser_manager = BrowserManager(get_settings())

class CommandRequest(BaseModel):
    """Request model for browser commands."""
    session_id: str
    command_type: str
    parameters: Dict

class CommandResponse(BaseModel):
    """Response model for browser commands."""
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None

@app.post("/api/v1/session/create")
async def create_session(session_id: str, settings: Settings = Depends(get_settings)):
    """Create a new browser session."""
    try:
        session = await browser_manager.create_session(session_id)
        return {"status": "success", "session_id": session.session_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/session/close")
async def close_session(session_id: str):
    """Close a browser session."""
    try:
        await browser_manager.close_session(session_id)
        return {"status": "success", "message": f"Session {session_id} closed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/execute", response_model=CommandResponse)
async def execute_command(
    command: CommandRequest,
    settings: Settings = Depends(get_settings)
):
    """Execute a browser command in a session."""
    try:
        session = await browser_manager.get_session(command.session_id)
        browser_command = BrowserCommand(
            command_type=command.command_type,
            parameters=command.parameters
        )
        result = await session.execute_command(browser_command)
        return CommandResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/api/v1/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates."""
    try:
        # Accept the connection
        await websocket.accept()
        logger.info(f"WebSocket connection established for session {session_id}")
        
        # Get or create session
        try:
            session = await browser_manager.get_session(session_id)
        except ValueError:
            session = await browser_manager.create_session(session_id)
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "session_id": session_id,
            "is_active": session.is_active,
            "current_url": session.current_url
        })
        
        # Start heartbeat
        heartbeat_task = asyncio.create_task(
            send_heartbeat(websocket, get_settings().WS_HEARTBEAT_INTERVAL)
        )
        
        try:
            while True:
                # Wait for messages
                data = await websocket.receive_json()
                
                # Handle command
                if data.get("type") == "command":
                    command = BrowserCommand(
                        command_type=data["command_type"],
                        parameters=data["parameters"]
                    )
                    
                    # Execute command
                    result = await session.execute_command(command)
                    
                    # Send result
                    await websocket.send_json({
                        "type": "command_result",
                        "command_id": data.get("command_id"),
                        **result
                    })
                
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        
        finally:
            # Cancel heartbeat
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    
    finally:
        try:
            await websocket.close()
        except:
            pass

async def send_heartbeat(websocket: WebSocket, interval: int):
    """Send periodic heartbeat messages."""
    try:
        while True:
            await asyncio.sleep(interval)
            await websocket.send_json({"type": "heartbeat"})
    except Exception as e:
        logger.error(f"Heartbeat error: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": get_settings().VERSION,
        "active_sessions": len(browser_manager.sessions)
    }

# Cleanup task for inactive sessions
@app.on_event("startup")
async def start_cleanup_task():
    """Start the cleanup task for inactive sessions."""
    async def cleanup_loop():
        while True:
            try:
                await browser_manager.cleanup_inactive_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
            await asyncio.sleep(60)  # Run every minute
    
    asyncio.create_task(cleanup_loop())

def main():
    """
    Main entry point for the VNC Agent Runner service
    """
    try:
        # Get configuration from environment
        host = os.getenv("VNC_AGENT_HOST", "0.0.0.0")
        port = int(os.getenv("VNC_AGENT_PORT", "8080"))
        
        # Log startup
        logger.info(f"Starting VNC Agent Runner on {host}:{port}")
        
        # Start the FastAPI application
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    
    except Exception as e:
        logger.error(f"Failed to start VNC Agent Runner: {str(e)}")
        raise

if __name__ == "__main__":
    main() 