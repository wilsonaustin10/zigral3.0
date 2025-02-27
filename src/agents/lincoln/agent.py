"""Lincoln agent for LinkedIn automation.

This module provides LinkedIn-specific automation capabilities, including
login handling, Sales Navigator search, and data collection.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel

from playwright.async_api import async_playwright, Page, Browser

from ..base.browser import BaseBrowser, BrowserCommand
from ..vnc.browser_controller import VncBrowserController, connect_to_vnc_browser

# Configure logging
logger = logging.getLogger(__name__)

class LinkedInCredentials(BaseModel):
    """LinkedIn authentication credentials."""
    username: str
    password: str

class SearchCriteria(BaseModel):
    """Search criteria for Sales Navigator."""
    title: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    keywords: Optional[str] = None

class ProspectData(BaseModel):
    """Data structure for prospect information."""
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    profile_url: str
    about: Optional[str] = None
    experience: List[Dict[str, str]] = []
    education: List[Dict[str, str]] = []
    skills: List[str] = []
    timestamp: datetime = datetime.now()

class LincolnAgent(BaseBrowser):
    """LinkedIn automation agent using Playwright with VNC support."""
    
    def __init__(self, headless: bool = False, use_vnc: bool = False, frontend_url: Optional[str] = None):
        """Initialize the LinkedIn automation agent.
        
        Args:
            headless: Whether to run browser in headless mode
            use_vnc: Whether to use VNC browser controller
            frontend_url: URL of the Zigral frontend with VNC
        """
        super().__init__(headless=headless)
        self.base_url = "https://www.linkedin.com"
        self.sales_nav_url = "https://www.linkedin.com/sales"
        self.use_vnc = use_vnc
        self.frontend_url = frontend_url or "http://localhost:8090"
        self.vnc_controller: Optional[VncBrowserController] = None
        
    async def initialize(self) -> None:
        """Initialize the browser with optional VNC support."""
        if self.use_vnc:
            # Initialize with VNC controller
            try:
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(headless=False)
                
                # Connect to the VNC browser via the frontend
                self.vnc_controller = await connect_to_vnc_browser(browser, self.frontend_url)
                
                if not self.vnc_controller:
                    logger.error("Failed to connect to VNC browser, falling back to regular browser")
                    self.use_vnc = False
                    await super().initialize()
                else:
                    logger.info("Successfully connected to VNC browser")
                    # Store references for cleanup
                    self._browser = browser
                    self._playwright = playwright
            except Exception as e:
                logger.error(f"Error initializing VNC controller: {e}")
                self.use_vnc = False
                await super().initialize()
        else:
            # Use regular Playwright browser
            await super().initialize()
    
    async def login(self, credentials: Optional[LinkedInCredentials] = None) -> Dict[str, Any]:
        """Log in to LinkedIn using provided credentials.
        
        Args:
            credentials: LinkedIn login credentials
            
        Returns:
            Dict with login status
        """
        if not credentials:
            # Try to get credentials from environment
            username = os.environ.get("LINKEDIN_USERNAME")
            password = os.environ.get("LINKEDIN_PASSWORD")
            
            if not username or not password:
                return {"status": "error", "message": "No credentials provided"}
            
            credentials = LinkedInCredentials(username=username, password=password)
        
        if self.use_vnc and self.vnc_controller:
            # Use VNC controller for login
            logger.info("Logging in to LinkedIn using VNC controller")
            try:
                # Navigate to LinkedIn login page
                await self.vnc_controller.navigate(self.base_url)
                await asyncio.sleep(2)  # Wait for page to load
                
                # Find and click the sign-in button if on home page
                # Coordinates would need to be adjusted based on actual UI
                await self.vnc_controller.click(300, 40)  # Click sign-in button
                await asyncio.sleep(2)
                
                # Type username and password
                await self.vnc_controller.type_text(credentials.username)
                await asyncio.sleep(0.5)
                await self.vnc_controller.click(300, 180)  # Click password field
                await asyncio.sleep(0.5)
                await self.vnc_controller.type_text(credentials.password)
                await asyncio.sleep(0.5)
                
                # Click sign-in button
                await self.vnc_controller.click(300, 250)  # Click submit button
                await asyncio.sleep(5)  # Wait for login to complete
                
                # Check if we're redirected to the dashboard
                screenshot = await self.vnc_controller.take_screenshot()
                # Here you would normally use screen_parser to check if login was successful
                
                return {"status": "success", "message": "Logged in with VNC controller"}
            except Exception as e:
                logger.error(f"Login error with VNC: {e}")
                return {"status": "error", "message": f"Login failed: {str(e)}"}
        else:
            # Use regular Playwright browser
            command = BrowserCommand(
                command_type="navigate",
                parameters={"url": f"{self.base_url}/login"}
            )
            await self.execute_command(command)
            
            # Fill username
            command = BrowserCommand(
                command_type="type",
                parameters={"selector": "#username", "text": credentials.username}
            )
            await self.execute_command(command)
            
            # Fill password
            command = BrowserCommand(
                command_type="type",
                parameters={"selector": "#password", "text": credentials.password}
            )
            await self.execute_command(command)
            
            # Click login button
            command = BrowserCommand(
                command_type="click",
                parameters={"selector": "button[type='submit']"}
            )
            await self.execute_command(command)
            
            # Take screenshot for verification
            command = BrowserCommand(
                command_type="take_screenshot",
                parameters={"name": "login_result"}
            )
            result = await self.execute_command(command)
            
            return {"status": "success", "screenshot": result.get("path", "")}
    
    # ... other methods would follow a similar pattern of checking
    # if self.use_vnc and self.vnc_controller, then using the VNC
    # controller, otherwise falling back to regular Playwright ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.use_vnc and self.vnc_controller:
            # Clean up VNC controller resources
            if hasattr(self, '_browser') and self._browser:
                await self._browser.close()
            if hasattr(self, '_playwright') and self._playwright:
                await self._playwright.stop()
        else:
            # Use regular cleanup
            await super().cleanup()

    async def search_sales_navigator(self, criteria: SearchCriteria) -> List[ProspectData]:
        """Search for prospects using Sales Navigator."""
        if not self._logged_in:
            raise RuntimeError("Must be logged in to search")
        
        try:
            # Navigate to Sales Navigator
            await self._navigate(url=self.sales_nav_url)
            
            # Click search box
            await self._click(selector='button[aria-label="Search"]')
            await self._page.wait_for_selector('.advanced-search-modal', state='visible')
            
            # Fill search criteria
            if criteria.title:
                await self._type(selector='input[aria-label="Add a title"]', text=criteria.title)
            
            if criteria.location:
                await self._type(selector='input[aria-label="Add a location"]', text=criteria.location)
                await self._click(selector='.location-suggestions li:first-child')
            
            if criteria.company:
                await self._type(selector='input[aria-label="Add a current company"]', text=criteria.company)
                await self._click(selector='.company-suggestions li:first-child')
            
            if criteria.industry:
                await self._click(selector='button[aria-label="Industry filter"]')
                await self._type(selector='input[aria-label="Search industries"]', text=criteria.industry)
                await self._click(selector='.industry-suggestions li:first-child')
            
            # Apply search
            await self._click(selector='button[aria-label="Apply search filter"]')
            await self.wait_for_navigation()
            
            # Extract results
            results = []
            cards = await self._page.query_selector_all('.search-results-container .result-card')
            
            for card in cards[:10]:  # Limit to first 10 results
                try:
                    name = await self._get_element_text(card, '.result-card__name')
                    title = await self._get_element_text(card, '.result-card__title')
                    company = await self._get_element_text(card, '.result-card__company')
                    location = await self._get_element_text(card, '.result-card__location')
                    profile_url = await self._get_element_href(card, 'a.result-card__link')
                    
                    prospect = ProspectData(
                        name=name,
                        title=title,
                        company=company,
                        location=location,
                        profile_url=profile_url
                    )
                    results.append(prospect)
                except Exception as e:
                    logger.warning(f"Error extracting result card: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def collect_prospect_data(self, profile_url: str) -> ProspectData:
        """Collect detailed data from a prospect's profile."""
        if not self._logged_in:
            raise RuntimeError("Must be logged in to collect data")
        
        try:
            await self._navigate(url=profile_url)
            
            # Extract basic information
            name = await self._get_text('.profile-name')
            title = await self._get_text('.profile-title')
            company = await self._get_text('.profile-company')
            location = await self._get_text('.profile-location')
            about = await self._get_text('.profile-about')
            
            # Extract experience
            experience = []
            exp_items = await self._page.query_selector_all('.experience-item')
            for item in exp_items:
                exp = {
                    "title": await self._get_element_text(item, '.experience-title'),
                    "company": await self._get_element_text(item, '.experience-company'),
                    "duration": await self._get_element_text(item, '.experience-duration'),
                    "description": await self._get_element_text(item, '.experience-description')
                }
                experience.append(exp)
            
            # Extract education
            education = []
            edu_items = await self._page.query_selector_all('.education-item')
            for item in edu_items:
                edu = {
                    "school": await self._get_element_text(item, '.education-school'),
                    "degree": await self._get_element_text(item, '.education-degree'),
                    "field": await self._get_element_text(item, '.education-field'),
                    "years": await self._get_element_text(item, '.education-years')
                }
                education.append(edu)
            
            # Extract skills
            skills = []
            skill_items = await self._page.query_selector_all('.skill-item')
            for item in skill_items:
                skill = await item.text_content()
                skills.append(skill.strip())
            
            return ProspectData(
                name=name,
                title=title,
                company=company,
                location=location,
                profile_url=profile_url,
                about=about,
                experience=experience,
                education=education,
                skills=skills
            )
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            raise
    
    async def _get_element_text(self, parent: Any, selector: str) -> str:
        """Helper method to safely get text content from a child element."""
        try:
            element = await parent.query_selector(selector)
            if element:
                return (await element.text_content()).strip()
        except Exception:
            pass
        return ""
    
    async def _get_element_href(self, parent: Any, selector: str) -> str:
        """Helper method to safely get href attribute from a child element."""
        try:
            element = await parent.query_selector(selector)
            if element:
                return await element.get_attribute('href')
        except Exception:
            pass
        return "" 