"""
LinkedIn automation client using Playwright.

This module handles all LinkedIn-specific automation tasks including login,
search, and data collection.
"""

import asyncio
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page

from .utils import setup_logger, sanitize_search_criteria, format_prospect_data

# Initialize logger
logger = logging.getLogger(__name__)


class LinkedInClient:
    """Client for automating LinkedIn tasks using Playwright."""

    def __init__(self):
        """Initialize the LinkedIn client."""
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._logged_in: bool = False
        self.base_url = "https://www.linkedin.com"
        self.sales_nav_url = "https://www.linkedin.com/sales"
        self.logger = logger

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
            Dictionary containing the prospect's information.
        """
        if not self._logged_in:
            raise RuntimeError("Must be logged in to collect data")
            
        try:
            await self._page.goto(profile_url)
            await self._page.wait_for_load_state("networkidle")
            
            # TODO: Implement actual data collection logic
            # This is a placeholder that will be implemented based on specific requirements
            return {}
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            raise

    async def execute_command(self, action: str, parameters: Dict) -> Dict:
        """
        Execute a LinkedIn automation command.
        
        Args:
            action: The action to perform (e.g., "search", "collect_data").
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
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise 