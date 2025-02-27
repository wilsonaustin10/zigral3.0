"""Browser controller for interacting with the VNC-based browser.

This module provides a bridge between Playwright and the noVNC interface,
allowing agents to control the browser running in the VNC session.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple

from playwright.async_api import Page, Browser, BrowserContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class VncBrowserController:
    """Controller for interacting with a browser via VNC."""
    
    def __init__(self, page: Page):
        """Initialize the VNC browser controller.
        
        Args:
            page: Playwright page object connected to the frontend with noVNC
        """
        self.page = page
        self._initialized = False
        self._last_error = None
    
    async def initialize(self) -> bool:
        """Initialize the connection to the noVNC interface.
        
        Returns:
            bool: Whether initialization was successful
        """
        try:
            # Wait for the zigralVNC object to be available
            await self.page.wait_for_function("""
                () => window.zigralVNC !== undefined && 
                      window.zigralVNC !== null
            """, timeout=30000)
            
            # Focus the VNC display
            await self.page.evaluate("window.focusVNC()")
            
            self._initialized = True
            logger.info("VNC Browser Controller initialized successfully")
            return True
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Failed to initialize VNC Browser Controller: {e}")
            return False
    
    async def navigate(self, url: str) -> bool:
        """Navigate to a URL in the VNC browser.
        
        Args:
            url: URL to navigate to
            
        Returns:
            bool: Whether navigation was successful
        """
        if not self._initialized:
            logger.error("VNC Browser Controller not initialized")
            return False
        
        try:
            # Type Ctrl+L to focus address bar
            await self._send_key_combination(["Control", "l"])
            await asyncio.sleep(0.5)
            
            # Clear the address bar and type the URL
            await self._send_keys("Control+a")  # Select all
            await asyncio.sleep(0.1)
            await self._send_keys("Delete")  # Delete current content
            await asyncio.sleep(0.1)
            
            # Type the URL
            for char in url:
                await self._send_character(char)
                await asyncio.sleep(0.01)  # Small delay between characters
            
            # Press Enter to navigate
            await self._send_keys("Enter")
            
            # Wait for navigation to complete
            await asyncio.sleep(2)  # Basic wait for page load
            return True
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
    
    async def click(self, x: int, y: int) -> bool:
        """Click at the specified coordinates in the VNC display.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            bool: Whether the click was successful
        """
        if not self._initialized:
            logger.error("VNC Browser Controller not initialized")
            return False
        
        try:
            # Convert frontend coordinates to VNC coordinates if needed
            await self.page.evaluate(f"""
                () => {{
                    const coords = window.zigralVNC.getCanvasCoordinates({x}, {y});
                    window.zigralVNC.sendPointer(coords.x, coords.y, 1);  // Mouse down
                    setTimeout(() => {{
                        window.zigralVNC.sendPointer(coords.x, coords.y, 0);  // Mouse up
                    }}, 50);
                }}
            """)
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Click error: {e}")
            return False
    
    async def type_text(self, text: str) -> bool:
        """Type text into the currently focused element.
        
        Args:
            text: Text to type
            
        Returns:
            bool: Whether typing was successful
        """
        if not self._initialized:
            logger.error("VNC Browser Controller not initialized")
            return False
        
        try:
            for char in text:
                await self._send_character(char)
                await asyncio.sleep(0.01)  # Small delay between characters
            return True
        except Exception as e:
            logger.error(f"Type text error: {e}")
            return False
    
    async def take_screenshot(self) -> Optional[bytes]:
        """Take a screenshot of the current VNC display.
        
        Returns:
            Optional[bytes]: Screenshot as bytes or None if failed
        """
        if not self._initialized:
            logger.error("VNC Browser Controller not initialized")
            return None
        
        try:
            # Use Playwright to take a screenshot of the VNC display element
            screenshot = await self.page.locator("#vnc-display").screenshot()
            return screenshot
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    async def get_resolution(self) -> Tuple[int, int]:
        """Get the resolution of the VNC display.
        
        Returns:
            Tuple[int, int]: Width and height of the VNC display
        """
        if not self._initialized:
            logger.error("VNC Browser Controller not initialized")
            return (0, 0)
        
        try:
            resolution = await self.page.evaluate("""
                () => {
                    const res = window.zigralVNC.getScreenResolution();
                    return [res.width, res.height];
                }
            """)
            return tuple(resolution)
        except Exception as e:
            logger.error(f"Resolution error: {e}")
            return (0, 0)
    
    async def _send_character(self, char: str) -> None:
        """Send a single character to the VNC display.
        
        Args:
            char: Character to send
        """
        await self.page.evaluate(f"""
            () => {{
                const element = document.querySelector('#vnc-display canvas');
                const event = new KeyboardEvent('keypress', {{
                    key: '{char}',
                    code: 'Key{char.upper() if char.isalpha() else char}',
                    charCode: {ord(char)},
                    keyCode: {ord(char)},
                    which: {ord(char)},
                    bubbles: true
                }});
                element.dispatchEvent(event);
            }}
        """)
    
    async def _send_keys(self, key_combo: str) -> None:
        """Send a key or key combination to the VNC display.
        
        Args:
            key_combo: Key or key combination (e.g., "Enter", "Control+a")
        """
        if "+" in key_combo:
            keys = key_combo.split("+")
            await self._send_key_combination(keys)
        else:
            await self.page.keyboard.press(key_combo)
    
    async def _send_key_combination(self, keys: List[str]) -> None:
        """Send a key combination to the VNC display.
        
        Args:
            keys: List of keys to press simultaneously
        """
        # Press all keys in sequence
        for key in keys:
            await self.page.keyboard.down(key)
        
        # Small delay to ensure key combination is registered
        await asyncio.sleep(0.1)
        
        # Release all keys in reverse order
        for key in reversed(keys):
            await self.page.keyboard.up(key)

    async def scroll(self, x: int, y: int, delta_y: int) -> bool:
        """Scroll at the specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            delta_y: Amount to scroll vertically (positive for down, negative for up)
            
        Returns:
            bool: Whether the scroll was successful
        """
        if not self._initialized:
            logger.error("VNC Browser Controller not initialized")
            return False
        
        try:
            await self.page.evaluate(f"""
                () => {{
                    const coords = window.zigralVNC.getCanvasCoordinates({x}, {y});
                    const element = document.querySelector('#vnc-display canvas');
                    const wheelEvent = new WheelEvent('wheel', {{
                        clientX: coords.x,
                        clientY: coords.y,
                        deltaY: {delta_y},
                        bubbles: true
                    }});
                    element.dispatchEvent(wheelEvent);
                }}
            """)
            return True
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return False

async def connect_to_vnc_browser(browser: Browser, frontend_url: str) -> Optional[VncBrowserController]:
    """Connect to the VNC browser via the frontend.
    
    Args:
        browser: Playwright browser instance
        frontend_url: URL of the Zigral frontend with VNC
        
    Returns:
        Optional[VncBrowserController]: VNC browser controller or None if failed
    """
    try:
        # Open a new page to the frontend
        page = await browser.new_page()
        await page.goto(frontend_url, wait_until="networkidle")
        
        # Create and initialize the VNC browser controller
        controller = VncBrowserController(page)
        success = await controller.initialize()
        
        if success:
            return controller
        else:
            await page.close()
            return None
    except Exception as e:
        logger.error(f"Failed to connect to VNC browser: {e}")
        return None 