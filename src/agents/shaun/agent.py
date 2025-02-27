"""Shaun agent for Google Sheets automation.

This module provides Google Sheets-specific automation capabilities, including
authentication, data entry, and spreadsheet manipulation.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel

from ..base.browser import BaseBrowser, BrowserCommand
from ..vnc.browser_controller import VncBrowserController, connect_to_vnc_browser
from playwright.async_api import Browser

# Configure logging
logger = logging.getLogger(__name__)

class GoogleCredentials(BaseModel):
    """Google authentication credentials."""
    email: str
    password: str

class SheetRange(BaseModel):
    """Represents a range in a spreadsheet."""
    sheet_name: str
    start_cell: str
    end_cell: Optional[str] = None

class SheetData(BaseModel):
    """Data structure for spreadsheet operations."""
    values: List[List[Any]]
    range: SheetRange
    timestamp: datetime = datetime.now()

class ShaunAgent(BaseBrowser):
    """Google Sheets automation agent using Playwright or VNC."""
    
    def __init__(self, headless: bool = False, use_vnc: bool = False, frontend_url: Optional[str] = None):
        """Initialize the Shaun agent.
        
        Args:
            headless: Whether to run the browser in headless mode
            use_vnc: Whether to use the VNC browser controller instead of direct Playwright
            frontend_url: URL of the Zigral frontend with VNC (required if use_vnc is True)
        """
        super().__init__(headless=headless)
        self.base_url = "https://docs.google.com/spreadsheets"
        self._logged_in = False
        self.current_sheet_id: Optional[str] = None
        
        # VNC-specific attributes
        self.use_vnc = use_vnc
        self.frontend_url = frontend_url or os.environ.get("FRONTEND_URL", "http://localhost:8090")
        self.vnc_controller: Optional[VncBrowserController] = None
        self._playwright_browser: Optional[Browser] = None
    
    async def initialize(self) -> None:
        """Initialize the browser, either directly or through VNC."""
        if not self.use_vnc:
            # Use standard Playwright initialization from BaseBrowser
            await super().initialize()
            return
        
        try:
            # Initialize Playwright browser for VNC connection
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            self._playwright_browser = await playwright.chromium.launch(headless=False)
            
            # Connect to VNC browser
            logger.info(f"Connecting to VNC browser via {self.frontend_url}")
            self.vnc_controller = await connect_to_vnc_browser(
                self._playwright_browser, 
                self.frontend_url
            )
            
            if not self.vnc_controller:
                raise RuntimeError("Failed to connect to VNC browser")
            
            logger.info("VNC Browser connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VNC browser controller: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        if self.use_vnc:
            if self._playwright_browser:
                await self._playwright_browser.close()
            return
            
        await super().cleanup()
    
    async def login(self, credentials: Optional[GoogleCredentials] = None) -> Dict[str, Any]:
        """Log in to Google account."""
        if not credentials:
            credentials = GoogleCredentials(
                email=os.environ.get("GOOGLE_EMAIL", ""),
                password=os.environ.get("GOOGLE_PASSWORD", "")
            )
        
        if not credentials.email or not credentials.password:
            raise ValueError("Google credentials not found")
        
        if self.use_vnc:
            return await self._login_vnc(credentials)
        else:
            return await self._login_playwright(credentials)
    
    async def _login_playwright(self, credentials: GoogleCredentials) -> Dict[str, Any]:
        """Log in using standard Playwright method."""
        try:
            # Navigate to Google login
            await self._navigate(url="https://accounts.google.com")
            
            # Enter email
            await self._type(selector='input[type="email"]', text=credentials.email)
            await self._click(selector='#identifierNext')
            
            # Wait for and enter password
            await self._page.wait_for_selector('input[type="password"]', timeout=5000)
            await self._type(selector='input[type="password"]', text=credentials.password)
            await self._click(selector='#passwordNext')
            
            # Check for 2FA
            try:
                two_step_challenge = await self._page.wait_for_selector(
                    '#challengePickerList',
                    timeout=5000
                )
                if two_step_challenge:
                    return {'logged_in': False, 'requires_2fa': True}
            except:
                pass
            
            # Wait for successful login
            await self._page.wait_for_selector('a[aria-label="Google apps"]', timeout=10000)
            self._logged_in = True
            return {'logged_in': True, 'requires_2fa': False}
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {'logged_in': False, 'error': str(e)}
    
    async def _login_vnc(self, credentials: GoogleCredentials) -> Dict[str, Any]:
        """Log in using VNC browser controller."""
        if not self.vnc_controller:
            raise RuntimeError("VNC controller not initialized")
        
        try:
            # Navigate to Google login
            await self.vnc_controller.navigate("https://accounts.google.com")
            await asyncio.sleep(3)
            
            # Get screen resolution for positioning
            resolution = await self.vnc_controller.get_resolution()
            
            # Click in the email field (approximated position)
            await self.vnc_controller.click(int(resolution[0] * 0.5), int(resolution[1] * 0.4))
            await asyncio.sleep(1)
            
            # Type email
            await self.vnc_controller.type_text(credentials.email)
            await asyncio.sleep(1)
            
            # Press tab and enter to submit
            await self.vnc_controller._send_keys("Tab")
            await asyncio.sleep(0.5)
            await self.vnc_controller._send_keys("Enter")
            await asyncio.sleep(3)
            
            # Type password (assuming we're now at password field)
            await self.vnc_controller.type_text(credentials.password)
            await asyncio.sleep(1)
            
            # Press enter to submit
            await self.vnc_controller._send_keys("Enter")
            await asyncio.sleep(5)
            
            # Simple detection of success by taking screenshot (would need image recognition in production)
            screenshot = await self.vnc_controller.take_screenshot()
            if screenshot:
                # In a real implementation, we would analyze the screenshot to confirm successful login
                self._logged_in = True
                return {'logged_in': True, 'requires_2fa': False}
            else:
                return {'logged_in': False, 'error': "Failed to capture login state"}
            
        except Exception as e:
            logger.error(f"VNC login failed: {str(e)}")
            return {'logged_in': False, 'error': str(e)}
    
    async def verify_2fa(self, code: str) -> Dict[str, Any]:
        """Verify 2FA code."""
        if self.use_vnc:
            return await self._verify_2fa_vnc(code)
        else:
            return await self._verify_2fa_playwright(code)
    
    async def _verify_2fa_playwright(self, code: str) -> Dict[str, Any]:
        """Verify 2FA code using standard Playwright method."""
        try:
            await self._type(selector='input[name="totpPin"]', text=code)
            await self._click(selector='#totpNext')
            
            # Wait for successful login
            await self._page.wait_for_selector('a[aria-label="Google apps"]', timeout=10000)
            self._logged_in = True
            return {"success": True}
        except Exception as e:
            logger.error(f"2FA verification failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _verify_2fa_vnc(self, code: str) -> Dict[str, Any]:
        """Verify 2FA code using VNC browser controller."""
        if not self.vnc_controller:
            raise RuntimeError("VNC controller not initialized")
        
        try:
            # Type the 2FA code
            await self.vnc_controller.type_text(code)
            await asyncio.sleep(1)
            
            # Press enter to submit
            await self.vnc_controller._send_keys("Enter")
            await asyncio.sleep(5)
            
            # In a real implementation, analyze a screenshot to confirm success
            self._logged_in = True
            return {"success": True}
        except Exception as e:
            logger.error(f"VNC 2FA verification failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Import the missing asyncio module 
    import asyncio

    # Implement required methods from BaseBrowser for VNC mode
    
    async def take_screenshot(self) -> bytes:
        """Take a screenshot of the current browser window."""
        if self.use_vnc and self.vnc_controller:
            screenshot = await self.vnc_controller.take_screenshot()
            if screenshot:
                return screenshot
            raise RuntimeError("Failed to take VNC screenshot")
        
        # For direct Playwright mode, take screenshot of the page
        if self._page:
            return await self._page.screenshot()
        
        raise RuntimeError("Browser not initialized")

    async def click_element(self, element: Any) -> bool:
        """Click an element at the specified location."""
        if self.use_vnc and self.vnc_controller:
            return await self.vnc_controller.click(element.x, element.y)
        
        # For direct Playwright mode
        if element and hasattr(element, 'click') and callable(element.click):
            await element.click()
            return True
        
        return False

    async def type_text(self, element: Any, text: str) -> bool:
        """Type text into an element."""
        if self.use_vnc and self.vnc_controller:
            # For VNC mode, click the element first then type
            await self.vnc_controller.click(element.x, element.y)
            await asyncio.sleep(0.5)
            return await self.vnc_controller.type_text(text)
        
        # For direct Playwright mode
        if element and hasattr(element, 'fill') and callable(element.fill):
            await element.fill(text)
            return True
        
        return False

    async def scroll_to_element(self, element: Any) -> bool:
        """Scroll to make an element visible."""
        if self.use_vnc and self.vnc_controller:
            # Rough approximation for VNC
            resolution = await self.vnc_controller.get_resolution()
            return await self.vnc_controller.scroll(
                resolution[0] // 2, 
                resolution[1] // 2,
                100  # Scroll down a bit
            )
        
        # For direct Playwright mode
        if self._page and element:
            await element.scroll_into_view_if_needed()
            return True
        
        return False

    async def open_spreadsheet(self, sheet_id: str) -> Dict[str, Any]:
        """Open a Google Spreadsheet by ID."""
        if not self._logged_in:
            raise RuntimeError("Must be logged in to open spreadsheet")
        
        if self.use_vnc:
            return await self._open_spreadsheet_vnc(sheet_id)
        else:
            return await self._open_spreadsheet_playwright(sheet_id)
    
    async def _open_spreadsheet_playwright(self, sheet_id: str) -> Dict[str, Any]:
        """Open a Google Spreadsheet using standard Playwright method."""
        try:
            url = f"{self.base_url}/d/{sheet_id}/edit"
            await self._navigate(url=url)
            
            # Wait for spreadsheet to load
            await self._page.wait_for_selector('.grid-container', timeout=10000)
            self.current_sheet_id = sheet_id
            
            # Get spreadsheet title
            title = await self._get_text('.docs-title-input')
            
            return {
                "sheet_id": sheet_id,
                "title": title,
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Failed to open spreadsheet: {str(e)}")
            raise
    
    async def _open_spreadsheet_vnc(self, sheet_id: str) -> Dict[str, Any]:
        """Open a Google Spreadsheet using VNC browser controller."""
        if not self.vnc_controller:
            raise RuntimeError("VNC controller not initialized")
        
        try:
            url = f"{self.base_url}/d/{sheet_id}/edit"
            
            # Navigate to the spreadsheet
            success = await self.vnc_controller.navigate(url)
            if not success:
                raise RuntimeError("Failed to navigate to spreadsheet")
            
            # Wait for spreadsheet to load (simple delay-based approach)
            await asyncio.sleep(5)
            
            # Take a screenshot for verification/debugging
            screenshot = await self.vnc_controller.take_screenshot()
            
            self.current_sheet_id = sheet_id
            
            # In a real implementation, we would extract title from visual analysis
            return {
                "sheet_id": sheet_id,
                "title": f"Spreadsheet {sheet_id}",  # Placeholder
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Failed to open spreadsheet via VNC: {str(e)}")
            raise
    
    async def read_range(self, range: SheetRange) -> SheetData:
        """Read data from a specified range in the current spreadsheet."""
        if not self.current_sheet_id:
            raise RuntimeError("No spreadsheet is currently open")
        
        try:
            # Select the sheet
            await self._click(selector=f'[aria-label="{range.sheet_name}"]')
            
            # Navigate to start cell
            await self._type(selector='.formula-bar', text=range.start_cell)
            await self._page.keyboard.press('Enter')
            
            # Select range if end_cell is specified
            if range.end_cell:
                await self._page.keyboard.down('Shift')
                await self._type(selector='.formula-bar', text=range.end_cell)
                await self._page.keyboard.up('Shift')
            
            # Copy range
            await self._page.keyboard.press('Control+C')
            
            # Get clipboard content
            clipboard_content = await self._page.evaluate('''() => {
                return navigator.clipboard.readText();
            }''')
            
            # Parse TSV data
            values = [
                row.split('\t')
                for row in clipboard_content.split('\n')
                if row.strip()
            ]
            
            return SheetData(values=values, range=range)
            
        except Exception as e:
            logger.error(f"Failed to read range: {str(e)}")
            raise
    
    async def write_range(self, data: SheetData) -> Dict[str, Any]:
        """Write data to a specified range in the current spreadsheet."""
        if not self.current_sheet_id:
            raise RuntimeError("No spreadsheet is currently open")
        
        try:
            # Select the sheet
            await self._click(selector=f'[aria-label="{data.range.sheet_name}"]')
            
            # Navigate to start cell
            await self._type(selector='.formula-bar', text=data.range.start_cell)
            await self._page.keyboard.press('Enter')
            
            # Prepare data as TSV
            tsv_content = '\n'.join(
                '\t'.join(str(cell) for cell in row)
                for row in data.values
            )
            
            # Set clipboard content and paste
            await self._page.evaluate(f'''async () => {{
                await navigator.clipboard.writeText(`{tsv_content}`);
            }}''')
            await self._page.keyboard.press('Control+V')
            
            return {
                "rows": len(data.values),
                "columns": len(data.values[0]) if data.values else 0,
                "range": data.range.dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to write range: {str(e)}")
            raise
    
    async def create_sheet(self, title: str) -> Dict[str, Any]:
        """Create a new sheet in the current spreadsheet."""
        if not self.current_sheet_id:
            raise RuntimeError("No spreadsheet is currently open")
        
        try:
            # Click the add sheet button
            await self._click(selector='[aria-label="Add sheet"]')
            
            # Wait for the new sheet to be created
            await self._page.wait_for_selector(f'[aria-label="{title}"]', timeout=5000)
            
            return {"title": title}
            
        except Exception as e:
            logger.error(f"Failed to create sheet: {str(e)}")
            raise
    
    async def format_range(
        self,
        range: SheetRange,
        formatting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply formatting to a range of cells."""
        if not self.current_sheet_id:
            raise RuntimeError("No spreadsheet is currently open")
        
        try:
            # Select the range
            await self._click(selector=f'[aria-label="{range.sheet_name}"]')
            await self._type(selector='.formula-bar', text=range.start_cell)
            
            if range.end_cell:
                await self._page.keyboard.down('Shift')
                await self._type(selector='.formula-bar', text=range.end_cell)
                await self._page.keyboard.up('Shift')
            
            # Apply formatting
            for format_type, value in formatting.items():
                if format_type == "bold":
                    await self._page.keyboard.press('Control+B')
                elif format_type == "italic":
                    await self._page.keyboard.press('Control+I')
                elif format_type == "background_color":
                    await self._click(selector='[aria-label="Fill color"]')
                    await self._click(selector=f'[aria-label="{value}"]')
                # Add more formatting options as needed
            
            return {
                "range": range.dict(),
                "formatting": formatting
            }
            
        except Exception as e:
            logger.error(f"Failed to apply formatting: {str(e)}")
            raise 