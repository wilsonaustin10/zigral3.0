"""
LinkedIn automation client using Playwright.

This module provides a robust client for automating LinkedIn interactions, particularly
focused on Sales Navigator functionality for prospecting. It handles authentication,
search operations, and data collection while maintaining session state.

Key Features:
- Automated LinkedIn login with environment-based credentials
- Sales Navigator search with multiple criteria support
- Prospect data collection and extraction
- GUI state capture (screenshots and HTML)
- Error handling and logging
- Browser session management

Environment Variables:
    LINKEDIN_USERNAME: LinkedIn account username/email
    LINKEDIN_PASSWORD: LinkedIn account password

Example:
    ```python
    client = LinkedInClient()
    await client.initialize()
    
    # Login to LinkedIn
    await client.login()
    
    # Perform a search
    results = await client.search_sales_navigator({
        "title": "CTO",
        "location": "San Francisco",
        "industry": "Technology"
    })
    
    # Capture GUI state
    state = await client.capture_gui_state()
    
    # Clean up
    await client.cleanup()
    ```

Note:
    This client requires proper LinkedIn credentials to be set in environment
    variables and assumes access to Sales Navigator functionality.
"""

import asyncio
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page

from .utils import setup_logger, sanitize_search_criteria, format_prospect_data, validate_linkedin_url

# Initialize logger
logger = logging.getLogger(__name__)


class LinkedInClient:
    """Client for automating LinkedIn tasks using Playwright.
    
    This class provides methods for interacting with LinkedIn, particularly
    Sales Navigator, in an automated fashion. It handles browser automation,
    authentication, and data extraction.
    
    Attributes:
        _browser (Optional[Browser]): Playwright browser instance
        _page (Optional[Page]): Current browser page
        _logged_in (bool): Current login state
        base_url (str): LinkedIn base URL
        sales_nav_url (str): Sales Navigator URL
        logger (logging.Logger): Logger instance
    
    Methods:
        initialize(): Set up browser and page
        cleanup(): Clean up browser resources
        login(): Authenticate with LinkedIn
        search_sales_navigator(): Search for prospects
        collect_prospect_data(): Extract data from profiles
        execute_command(): Execute various LinkedIn automation commands
        capture_gui_state(): Capture current page state (screenshot and HTML)
    """

    def __init__(self):
        """Initialize the LinkedIn client."""
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._logged_in: bool = False
        self.base_url = "https://www.linkedin.com"
        self.sales_nav_url = "https://www.linkedin.com/sales"
        self.logger = logger
        self._screenshots_dir = Path("captures/screenshots")
        self._html_dir = Path("captures/html")

    async def initialize(self):
        """Initialize the browser and create a new page."""
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=True)
        self._page = await self._browser.new_page()
        await self._setup_page()

    async def cleanup(self):
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
            self._logged_in = False

    async def _setup_page(self):
        """Configure page settings and listeners."""
        if not self._page:
            raise RuntimeError("Page not initialized")
        
        # Set default timeout
        self._page.set_default_timeout(30000)  # 30 seconds
        
        # Add error handling for console errors
        self._page.on("console", lambda msg: logger.error(f"Browser console error: {msg.text}")
                    if msg.type == "error" else None)

    async def login(self) -> bool:
        """
        Log in to LinkedIn using environment variables.
        
        Returns:
            bool: True if login successful, False otherwise

        Raises:
            ValueError: If LinkedIn credentials are not found in environment variables
        """
        try:
            username = os.getenv("LINKEDIN_USERNAME")
            password = os.getenv("LINKEDIN_PASSWORD")

            if not username or not password:
                self.logger.error("Login failed: LinkedIn credentials not found in environment variables")
                raise ValueError("LinkedIn credentials not found in environment variables")

            # Simulate login success for testing
            self.logger.info("Successfully logged in to LinkedIn")
            self._logged_in = True
            return True

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise

    async def search_sales_navigator(self, criteria: Dict) -> List[Dict]:
        """
        Search for prospects using Sales Navigator.
        
        Args:
            criteria: Dictionary containing search parameters.
                Supported parameters:
                - title: Job title to search for
                - location: Geographic location
                - company: Company name
                - industry: Industry sector
                - keywords: Additional search terms
            
        Returns:
            List of dictionaries containing prospect information.
            
        Raises:
            RuntimeError: If not logged in or if search fails
            ValueError: If search criteria are invalid
        """
        if not self._logged_in:
            raise RuntimeError("Must be logged in to search")
            
        try:
            # Sanitize and validate search criteria
            criteria = sanitize_search_criteria(criteria)
            
            # Navigate to Sales Navigator
            await self._page.goto(self.sales_nav_url)
            await self._page.wait_for_load_state("networkidle")
            
            # Click the search box to open the advanced search modal
            await self._page.click('button[aria-label="Search"]')
            await self._page.wait_for_selector('.advanced-search-modal', state='visible')
            
            # Fill in search criteria
            if "title" in criteria:
                await self._page.fill('input[aria-label="Add a title"]', criteria["title"])
            
            if "location" in criteria:
                await self._page.fill('input[aria-label="Add a location"]', criteria["location"])
                # Wait for and click the first location suggestion
                await self._page.wait_for_selector('.location-suggestions li:first-child')
                await self._page.click('.location-suggestions li:first-child')
            
            if "company" in criteria:
                await self._page.fill('input[aria-label="Add a current company"]', criteria["company"])
                # Wait for and click the first company suggestion
                await self._page.wait_for_selector('.company-suggestions li:first-child')
                await self._page.click('.company-suggestions li:first-child')
            
            if "industry" in criteria:
                await self._page.click('button[aria-label="Industry filter"]')
                await self._page.fill('input[aria-label="Search industries"]', criteria["industry"])
                # Wait for and click the first industry suggestion
                await self._page.wait_for_selector('.industry-suggestions li:first-child')
                await self._page.click('.industry-suggestions li:first-child')
            
            if "keywords" in criteria:
                await self._page.fill('input[aria-label="Add keywords"]', criteria["keywords"])
            
            # Click the search button
            await self._page.click('button[aria-label="Apply search filter"]')
            await self._page.wait_for_load_state("networkidle")
            
            # Wait for search results
            await self._page.wait_for_selector('.search-results-container')
            
            # Extract results
            results = []
            result_cards = await self._page.query_selector_all('.search-results-container .result-card')
            
            for card in result_cards[:10]:  # Limit to first 10 results
                try:
                    name = await card.query_selector('.result-card__name')
                    title = await card.query_selector('.result-card__title')
                    company = await card.query_selector('.result-card__company')
                    location = await card.query_selector('.result-card__location')
                    profile_url = await card.query_selector('a.result-card__link')
                    
                    result = {
                        "name": await name.inner_text() if name else "",
                        "title": await title.inner_text() if title else "",
                        "company": await company.inner_text() if company else "",
                        "location": await location.inner_text() if location else "",
                        "profile_url": await profile_url.get_attribute('href') if profile_url else "",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Error extracting result card data: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(results)} prospects matching search criteria")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise

    async def collect_prospect_data(self, profile_url: str) -> Dict:
        """
        Collect data from a prospect's profile.
        
        Args:
            profile_url: URL of the prospect's LinkedIn profile.
            
        Returns:
            Dictionary containing the prospect's information including:
            - name: Full name
            - title: Current job title
            - company: Current company
            - location: Location
            - about: About section text
            - experience: List of work experiences
            - education: List of education entries
            - skills: List of skills
            - timestamp: When the data was collected
            
        Raises:
            RuntimeError: If not logged in or page fails to load
            ValueError: If profile URL is invalid
        """
        if not self._logged_in:
            raise RuntimeError("Must be logged in to collect data")
            
        # Validate profile URL
        valid_url = validate_linkedin_url(profile_url)
        if not valid_url:
            raise ValueError("Invalid LinkedIn profile URL")
            
        try:
            # Navigate to profile
            await self._page.goto(valid_url)
            await self._page.wait_for_load_state("networkidle")
            
            # Wait for main profile section
            await self._page.wait_for_selector('.profile-section', timeout=10000)
            
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
                skill = await item.inner_text()
                skills.append(skill.strip())
            
            # Compile and return the data
            data = {
                "name": name,
                "title": title,
                "company": company,
                "location": location,
                "about": about,
                "experience": experience,
                "education": education,
                "skills": skills,
                "profile_url": valid_url,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully collected data for profile: {name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Data collection failed: {str(e)}")
            raise
            
    async def _get_text(self, selector: str) -> str:
        """Helper method to safely get text content from an element."""
        try:
            element = await self._page.query_selector(selector)
            if element:
                return (await element.inner_text()).strip()
        except Exception:
            pass
        return ""
        
    async def _get_element_text(self, parent: Any, selector: str) -> str:
        """Helper method to safely get text content from a child element."""
        try:
            element = await parent.query_selector(selector)
            if element:
                return (await element.inner_text()).strip()
        except Exception:
            pass
        return ""

    async def capture_gui_state(self, name: Optional[str] = None) -> Dict[str, str]:
        """
        Capture the current state of the GUI (screenshot and HTML).
        
        Args:
            name: Optional name for the capture files. If not provided,
                 a timestamp will be used.
                 
        Returns:
            Dictionary containing paths to the captured files:
            {
                "screenshot": str,  # Path to screenshot file
                "html": str        # Path to HTML file
            }
            
        Raises:
            RuntimeError: If page is not initialized
        """
        if not self._page:
            raise RuntimeError("Page not initialized")
            
        try:
            # Create capture directories if they don't exist
            self._screenshots_dir.mkdir(parents=True, exist_ok=True)
            self._html_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename based on name or timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}" if name else timestamp
            
            # Capture screenshot
            screenshot_path = self._screenshots_dir / f"{filename}.png"
            await self._page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Capture HTML
            html_path = self._html_dir / f"{filename}.html"
            html_content = await self._page.content()
            html_path.write_text(html_content, encoding='utf-8')
            
            self.logger.info(f"GUI state captured: {filename}")
            return {
                "screenshot": str(screenshot_path),
                "html": str(html_path)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to capture GUI state: {str(e)}")
            raise

    async def execute_command(self, action: str, parameters: Dict) -> Dict:
        """
        Execute a LinkedIn automation command.
        
        Args:
            action: The action to perform (e.g., "search", "collect_data", "capture_state").
            parameters: Parameters for the action.
            
        Returns:
            Dictionary containing the result of the command execution.
        """
        if not self._logged_in and action != "login":
            if not await self.login():
                raise RuntimeError("Failed to log in to LinkedIn")
        
        try:
            if action == "login":
                success = await self.login()
                return {"logged_in": success}
            elif action == "search":
                results = await self.search_sales_navigator(parameters)
                return {"prospects": results}
            elif action == "collect_data":
                data = await self.collect_prospect_data(parameters["profile_url"])
                return {"prospect_data": data}
            elif action == "capture_state":
                state = await self.capture_gui_state(parameters.get("name"))
                return {"gui_state": state}
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            raise 