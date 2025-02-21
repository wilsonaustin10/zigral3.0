"""Browser command execution and session management for VNC agent.

This module provides classes for managing browser sessions and executing browser
commands through VNC using Playwright for browser automation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from pydantic import BaseModel

from .utils.config import Settings

# Configure logging
logger = logging.getLogger(__name__)

class BrowserCommandStatus(Enum):
    """Status of a browser command execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BrowserCommand(BaseModel):
    """Represents a browser command with its parameters and status."""
    command_type: str
    parameters: Dict[str, Any]
    status: BrowserCommandStatus = BrowserCommandStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

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
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._screenshots_dir = Path("captures/screenshots")
        self._html_dir = Path("captures/html")
        
        logger.info(f"Browser session {session_id} initialized")
    
    async def initialize(self) -> None:
        """Initialize the browser session."""
        try:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized', '--no-sandbox']
            )
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            self._page = await self._context.new_page()
            
            # Setup error handling
            self._page.on("console", lambda msg: 
                logger.error(f"Browser console error: {msg.text}") 
                if msg.type == "error" else None
            )
            
            # Create capture directories
            self._screenshots_dir.mkdir(parents=True, exist_ok=True)
            self._html_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Browser session initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser session: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            logger.info("Browser resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def execute_command(self, command: BrowserCommand) -> Dict[str, Any]:
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
    
    async def _execute_command_by_type(self, command: BrowserCommand) -> Dict[str, Any]:
        """Execute a specific type of browser command."""
        command_handlers = {
            "navigate": self._navigate,
            "click": self._click,
            "type": self._type,
            "wait_for_selector": self._wait_for_selector,
            "get_text": self._get_text,
            "screenshot": self._take_screenshot,
            "scroll": self._scroll,
            "evaluate": self._evaluate,
            "wait_for_navigation": self._wait_for_navigation,
        }
        
        handler = command_handlers.get(command.command_type)
        if not handler:
            raise ValueError(f"Unknown command type: {command.command_type}")
        
        return await handler(**command.parameters)
    
    async def _navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """Navigate to a URL and wait for page load."""
        await self._page.goto(url, wait_until=wait_until)
        self.current_url = url
        return {"url": url, "title": await self._page.title()}
    
    async def _click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click an element matching the selector."""
        element = await self._page.wait_for_selector(selector, timeout=timeout)
        await element.click()
        return {"selector": selector}
    
    async def _type(self, selector: str, text: str, timeout: int = 5000) -> Dict[str, Any]:
        """Type text into an element matching the selector."""
        element = await self._page.wait_for_selector(selector, timeout=timeout)
        await element.fill(text)
        return {"selector": selector, "text": text}
    
    async def _wait_for_selector(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Wait for an element matching the selector to appear."""
        await self._page.wait_for_selector(selector, timeout=timeout)
        return {"selector": selector}
    
    async def _get_text(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Get text content of an element matching the selector."""
        element = await self._page.wait_for_selector(selector, timeout=timeout)
        text = await element.text_content()
        return {"selector": selector, "text": text}
    
    async def _take_screenshot(self, name: Optional[str] = None) -> Dict[str, str]:
        """Take a screenshot of the current page."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}" if name else timestamp
        
        screenshot_path = self._screenshots_dir / f"{filename}.png"
        html_path = self._html_dir / f"{filename}.html"
        
        await self._page.screenshot(path=str(screenshot_path), full_page=True)
        html_content = await self._page.content()
        html_path.write_text(html_content, encoding='utf-8')
        
        return {
            "screenshot": str(screenshot_path),
            "html": str(html_path)
        }
    
    async def _scroll(self, selector: Optional[str] = None, distance: int = 0) -> Dict[str, Any]:
        """Scroll the page or a specific element."""
        if selector:
            element = await self._page.wait_for_selector(selector)
            await element.evaluate(f"el => el.scrollBy(0, {distance})")
        else:
            await self._page.evaluate(f"window.scrollBy(0, {distance})")
        return {"distance": distance}
    
    async def _evaluate(self, script: str, arg: Optional[Any] = None) -> Dict[str, Any]:
        """Evaluate JavaScript code in the page context."""
        result = await self._page.evaluate(script, arg)
        return {"result": result}
    
    async def _wait_for_navigation(self, timeout: int = 30000, wait_until: str = "networkidle") -> Dict[str, Any]:
        """Wait for page navigation to complete."""
        await self._page.wait_for_load_state(wait_until, timeout=timeout)
        return {"url": self._page.url}

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
        await session.initialize()
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
        await session.cleanup()
        session.is_active = False
        del self.sessions[session_id]
        logger.info(f"Session {session_id} closed")
    
    async def cleanup_inactive_sessions(self) -> None:
        """Clean up inactive sessions."""
        now = datetime.now()
        for session_id, session in list(self.sessions.items()):
            if (now - session.last_active).seconds > self.settings.SESSION_TIMEOUT:
                await self.close_session(session_id) 