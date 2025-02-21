"""Browser command execution and session management for VNC agent.

This module provides classes for managing browser sessions and executing browser
commands through VNC using pyautogui for GUI automation.
"""

import asyncio
import logging
import pyautogui
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .utils.config import Settings

# Configure logging
logger = logging.getLogger(__name__)

class BrowserCommandStatus(Enum):
    """Status of a browser command execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BrowserCommand:
    """Represents a browser command with its parameters and status."""
    command_type: str
    parameters: Dict
    status: BrowserCommandStatus = BrowserCommandStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict] = None

class BrowserSession:
    """Manages a browser session and its state."""
    
    def __init__(self, session_id: str, settings: Settings):
        self.session_id = session_id
        self.settings = settings
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.command_history: List[BrowserCommand] = []
        self.is_active = True
        self.current_url: Optional[str] = None
        self.current_command: Optional[BrowserCommand] = None
        
        # Initialize pyautogui settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # Add small delay between actions
        
        logger.info(f"Browser session {session_id} initialized")
    
    async def execute_command(self, command: BrowserCommand) -> Dict:
        """Execute a browser command and return the result."""
        try:
            self.current_command = command
            command.status = BrowserCommandStatus.RUNNING
            command.started_at = datetime.now()
            
            # Execute command based on type
            result = await self._execute_command_by_type(command)
            
            command.status = BrowserCommandStatus.COMPLETED
            command.completed_at = datetime.now()
            command.result = result
            
            self.command_history.append(command)
            self.last_active = datetime.now()
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            command.status = BrowserCommandStatus.FAILED
            command.error = str(e)
            command.completed_at = datetime.now()
            return {"status": "error", "error": str(e)}
    
    async def _execute_command_by_type(self, command: BrowserCommand) -> Dict:
        """Execute a specific type of browser command."""
        command_handlers = {
            "navigate": self._navigate,
            "click": self._click,
            "type": self._type_text,
            "scroll": self._scroll,
            "wait": self._wait,
            "find_element": self._find_element,
        }
        
        handler = command_handlers.get(command.command_type)
        if not handler:
            raise ValueError(f"Unknown command type: {command.command_type}")
        
        return await handler(command.parameters)
    
    async def _navigate(self, params: Dict) -> Dict:
        """Navigate to a URL."""
        url = params.get("url")
        if not url:
            raise ValueError("URL parameter is required")
        
        # Simulate clicking address bar and typing URL
        await self._click_address_bar()
        await self._type_text({"text": url})
        pyautogui.press("enter")
        
        # Wait for page load
        await asyncio.sleep(2)  # Basic wait, can be improved
        self.current_url = url
        return {"url": url}
    
    async def _click(self, params: Dict) -> Dict:
        """Click at specified coordinates or on an element."""
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            raise ValueError("x and y coordinates are required")
        
        pyautogui.click(x, y)
        return {"x": x, "y": y}
    
    async def _type_text(self, params: Dict) -> Dict:
        """Type text at current position."""
        text = params.get("text")
        if not text:
            raise ValueError("text parameter is required")
        
        pyautogui.typewrite(text)
        return {"text": text}
    
    async def _scroll(self, params: Dict) -> Dict:
        """Scroll the page."""
        amount = params.get("amount", 0)
        pyautogui.scroll(amount)
        return {"amount": amount}
    
    async def _wait(self, params: Dict) -> Dict:
        """Wait for specified duration."""
        duration = params.get("duration", 1)
        await asyncio.sleep(duration)
        return {"duration": duration}
    
    async def _find_element(self, params: Dict) -> Dict:
        """Find an element on the page using image recognition."""
        image_path = params.get("image_path")
        if not image_path:
            raise ValueError("image_path parameter is required")
        
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.9)
            if location:
                return {
                    "found": True,
                    "x": location.left + location.width / 2,
                    "y": location.top + location.height / 2
                }
            return {"found": False}
        except Exception as e:
            logger.error(f"Error finding element: {str(e)}")
            return {"found": False, "error": str(e)}
    
    async def _click_address_bar(self) -> None:
        """Click the browser address bar."""
        pyautogui.hotkey("command", "l")  # Cmd+L for Mac, Ctrl+L for Windows/Linux
        await asyncio.sleep(0.1)

class BrowserManager:
    """Manages multiple browser sessions."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sessions: Dict[str, BrowserSession] = {}
        logger.info("Browser manager initialized")
    
    async def create_session(self, session_id: str) -> BrowserSession:
        """Create a new browser session."""
        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        if len(self.sessions) >= self.settings.MAX_SESSIONS:
            raise ValueError("Maximum number of sessions reached")
        
        session = BrowserSession(session_id, self.settings)
        self.sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> BrowserSession:
        """Get an existing browser session."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return session
    
    async def close_session(self, session_id: str) -> None:
        """Close a browser session."""
        session = await self.get_session(session_id)
        session.is_active = False
        del self.sessions[session_id]
        logger.info(f"Session {session_id} closed")
    
    async def cleanup_inactive_sessions(self) -> None:
        """Clean up inactive sessions."""
        now = datetime.now()
        for session_id, session in list(self.sessions.items()):
            if (now - session.last_active).seconds > self.settings.SESSION_TIMEOUT:
                await self.close_session(session_id) 