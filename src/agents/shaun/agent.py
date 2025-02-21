"""Shaun agent for Google Sheets automation.

This module provides Google Sheets-specific automation capabilities, including
authentication, data entry, and spreadsheet manipulation.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel

from ..base.browser import BaseBrowser, BrowserCommand

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
    """Google Sheets automation agent using Playwright."""
    
    def __init__(self, headless: bool = False):
        super().__init__(headless=headless)
        self.base_url = "https://docs.google.com/spreadsheets"
        self._logged_in = False
        self.current_sheet_id: Optional[str] = None
    
    async def login(self, credentials: Optional[GoogleCredentials] = None) -> Dict[str, Any]:
        """Log in to Google account."""
        if not credentials:
            credentials = GoogleCredentials(
                email=os.environ.get("GOOGLE_EMAIL", ""),
                password=os.environ.get("GOOGLE_PASSWORD", "")
            )
        
        if not credentials.email or not credentials.password:
            raise ValueError("Google credentials not found")
        
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
    
    async def verify_2fa(self, code: str) -> Dict[str, Any]:
        """Verify 2FA code."""
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
    
    async def open_spreadsheet(self, sheet_id: str) -> Dict[str, Any]:
        """Open a Google Spreadsheet by ID."""
        if not self._logged_in:
            raise RuntimeError("Must be logged in to open spreadsheet")
        
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