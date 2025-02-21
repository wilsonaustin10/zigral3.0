"""Lincoln agent for LinkedIn automation.

This module provides LinkedIn-specific automation capabilities, including
login handling, Sales Navigator search, and data collection.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from ..base.browser import BaseBrowser, BrowserCommand

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
    """LinkedIn automation agent using Playwright."""
    
    def __init__(self, headless: bool = False):
        super().__init__(headless=headless)
        self.base_url = "https://www.linkedin.com"
        self.sales_nav_url = "https://www.linkedin.com/sales"
        self._logged_in = False
    
    async def login(self, credentials: Optional[LinkedInCredentials] = None) -> Dict[str, Any]:
        """Log in to LinkedIn with 2FA support."""
        if not credentials:
            credentials = LinkedInCredentials(
                username=os.environ.get("LINKEDIN_USERNAME", ""),
                password=os.environ.get("LINKEDIN_PASSWORD", "")
            )
        
        if not credentials.username or not credentials.password:
            raise ValueError("LinkedIn credentials not found")
        
        try:
            # Navigate to login page
            await self._navigate(url=f"{self.base_url}/login")
            
            # Fill credentials
            await self._type(selector="input[name='session_key']", text=credentials.username)
            await self._type(selector="input[name='session_password']", text=credentials.password)
            await self._click(selector="button[type='submit']")
            
            # Check for 2FA
            try:
                pin_field = await self._page.wait_for_selector("input[name='pin']", timeout=5000)
                if pin_field:
                    return {'logged_in': False, 'requires_2fa': True}
            except:
                pass
            
            # Wait for successful login
            await self._page.wait_for_selector("nav.global-nav", timeout=10000)
            self._logged_in = True
            return {'logged_in': True, 'requires_2fa': False}
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {'logged_in': False, 'error': str(e)}
    
    async def verify_2fa(self, code: str) -> Dict[str, Any]:
        """Verify 2FA code."""
        try:
            await self._type(selector="input[name='pin']", text=code)
            await self._click(selector="button[type='submit']")
            
            # Wait for successful login
            await self._page.wait_for_selector("nav.global-nav", timeout=10000)
            self._logged_in = True
            return {"success": True}
        except Exception as e:
            logger.error(f"2FA verification failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
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