"""Base browser automation functionality for Zigral agents.

This module provides the core browser automation capabilities using Playwright,
which all agents (Lincoln for LinkedIn, Shaun for Google Sheets) will inherit from.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

class BrowserCommand(BaseModel):
    """Represents a browser automation command."""
    command_type: str
    parameters: Dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class BaseBrowser:
    """Base browser automation class using Playwright."""
    
    def __init__(self, headless: bool = False):
        """Initialize the browser automation.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._headless = headless
        self._screenshots_dir = Path("captures/screenshots")
        self._html_dir = Path("captures/html")
        self.command_history: List[BrowserCommand] = []
        
    async def initialize(self) -> None:
        """Initialize the browser and create a new page."""
        try:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=self._headless,
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
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
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
            command.started_at = datetime.now()
            
            # Execute command based on type
            result = await self._execute_command_by_type(command)
            
            command.completed_at = datetime.now()
            command.result = result
            self.command_history.append(command)
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            command.error = str(e)
            command.completed_at = datetime.now()
            self.command_history.append(command)
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
        }
        
        handler = command_handlers.get(command.command_type)
        if not handler:
            raise ValueError(f"Unknown command type: {command.command_type}")
        
        return await handler(**command.parameters)
    
    async def _navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """Navigate to a URL and wait for page load."""
        await self._page.goto(url, wait_until=wait_until)
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
    
    async def wait_for_navigation(self, timeout: int = 30000) -> None:
        """Wait for page navigation to complete."""
        await self._page.wait_for_load_state("networkidle", timeout=timeout)
    
    def is_initialized(self) -> bool:
        """Check if the browser is initialized."""
        return bool(self._browser and self._context and self._page) 