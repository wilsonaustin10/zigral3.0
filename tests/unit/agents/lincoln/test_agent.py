"""Unit tests for Lincoln (LinkedIn) agent."""

import pytest
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.agents.lincoln.agent import (
    LincolnAgent,
    LinkedInCredentials,
    SearchCriteria,
    ProspectData
)

@pytest.fixture
async def lincoln_agent():
    """Create a Lincoln agent instance for testing."""
    agent = LincolnAgent(headless=True)
    await agent.initialize()
    yield agent
    await agent.cleanup()

@pytest.fixture
def mock_credentials():
    """Create mock LinkedIn credentials."""
    return LinkedInCredentials(
        username="test@example.com",
        password="test_password"
    )

@pytest.fixture
def mock_search_criteria():
    """Create mock search criteria."""
    return SearchCriteria(
        title="CTO",
        location="San Francisco",
        company="Tech Corp",
        industry="Software"
    )

@pytest.mark.asyncio
async def test_login_success(lincoln_agent, mock_credentials):
    """Test successful login without 2FA."""
    # Mock the navigation and element interactions
    lincoln_agent._navigate = AsyncMock()
    lincoln_agent._type = AsyncMock()
    lincoln_agent._click = AsyncMock()
    lincoln_agent._page.wait_for_selector = AsyncMock()
    
    result = await lincoln_agent.login(mock_credentials)
    
    assert result["logged_in"] is True
    assert result["requires_2fa"] is False
    assert lincoln_agent._logged_in is True

@pytest.mark.asyncio
async def test_login_with_2fa(lincoln_agent, mock_credentials):
    """Test login that requires 2FA."""
    # Mock the navigation and element interactions
    lincoln_agent._navigate = AsyncMock()
    lincoln_agent._type = AsyncMock()
    lincoln_agent._click = AsyncMock()
    
    # Mock 2FA field detection
    async def mock_wait_for_selector(selector, **kwargs):
        if selector == "input[name='pin']":
            return AsyncMock()
        return None
    
    lincoln_agent._page.wait_for_selector = mock_wait_for_selector
    
    result = await lincoln_agent.login(mock_credentials)
    
    assert result["logged_in"] is False
    assert result["requires_2fa"] is True

@pytest.mark.asyncio
async def test_search_sales_navigator(lincoln_agent, mock_search_criteria):
    """Test Sales Navigator search functionality."""
    # Set up mock data
    mock_card = AsyncMock()
    mock_card.query_selector = AsyncMock(return_value=AsyncMock(
        text_content=AsyncMock(return_value="Test Value"),
        get_attribute=AsyncMock(return_value="https://linkedin.com/profile")
    ))
    
    # Mock page interactions
    lincoln_agent._logged_in = True
    lincoln_agent._navigate = AsyncMock()
    lincoln_agent._click = AsyncMock()
    lincoln_agent._type = AsyncMock()
    lincoln_agent.wait_for_navigation = AsyncMock()
    lincoln_agent._page.query_selector_all = AsyncMock(return_value=[mock_card])
    
    results = await lincoln_agent.search_sales_navigator(mock_search_criteria)
    
    assert len(results) > 0
    assert isinstance(results[0], ProspectData)
    assert results[0].profile_url == "https://linkedin.com/profile"

@pytest.mark.asyncio
async def test_collect_prospect_data(lincoln_agent):
    """Test prospect data collection."""
    # Set up mock data
    profile_url = "https://linkedin.com/in/test-profile"
    
    # Mock page interactions
    lincoln_agent._logged_in = True
    lincoln_agent._navigate = AsyncMock()
    lincoln_agent._get_text = AsyncMock(return_value="Test Value")
    lincoln_agent._page.query_selector_all = AsyncMock(return_value=[])
    
    result = await lincoln_agent.collect_prospect_data(profile_url)
    
    assert isinstance(result, ProspectData)
    assert result.name == "Test Value"
    assert result.profile_url == profile_url

@pytest.mark.asyncio
async def test_verify_2fa_success(lincoln_agent):
    """Test successful 2FA verification."""
    # Mock page interactions
    lincoln_agent._type = AsyncMock()
    lincoln_agent._click = AsyncMock()
    lincoln_agent._page.wait_for_selector = AsyncMock()
    
    result = await lincoln_agent.verify_2fa("123456")
    
    assert result["success"] is True
    assert lincoln_agent._logged_in is True

@pytest.mark.asyncio
async def test_verify_2fa_failure(lincoln_agent):
    """Test failed 2FA verification."""
    # Mock page interactions to simulate failure
    lincoln_agent._type = AsyncMock()
    lincoln_agent._click = AsyncMock()
    lincoln_agent._page.wait_for_selector = AsyncMock(side_effect=Exception("2FA failed"))
    
    result = await lincoln_agent.verify_2fa("invalid")
    
    assert result["success"] is False
    assert "error" in result 