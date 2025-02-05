"""Tests for LinkedIn client functionality."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from playwright.async_api import Page, Browser

from src.agents.lincoln.linkedin_client import LinkedInClient


@pytest.fixture
async def mock_page():
    """Create a mock Playwright page."""
    page = AsyncMock(spec=Page)
    page.set_default_timeout = MagicMock()
    page.on = MagicMock()
    return page


@pytest.fixture
async def mock_browser():
    """Create a mock Playwright browser."""
    browser = AsyncMock(spec=Browser)
    browser.new_page = AsyncMock()
    return browser


@pytest.fixture
async def client(mock_browser, mock_page):
    """Create a LinkedIn client with mocked browser and page."""
    mock_browser.new_page.return_value = mock_page
    
    with patch("src.agents.lincoln.linkedin_client.async_playwright") as mock_playwright:
        mock_context = AsyncMock()
        mock_context.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_context)
        
        client = LinkedInClient()
        await client.initialize()
        return client


@pytest.mark.asyncio
async def test_initialize(client, mock_page):
    """Test client initialization."""
    assert client.browser is not None
    assert client.page is not None
    mock_page.set_default_timeout.assert_called_once_with(30000)
    mock_page.on.assert_called()


@pytest.mark.asyncio
async def test_cleanup(client):
    """Test client cleanup."""
    assert client.browser is not None
    await client.cleanup()
    assert client.browser is None
    assert client.page is None
    assert not client.logged_in


@pytest.mark.asyncio
async def test_login_success(client, mock_page):
    """Test successful login."""
    # Set up environment variables
    os.environ["LINKEDIN_EMAIL"] = "test@example.com"
    os.environ["LINKEDIN_PASSWORD"] = "password123"
    
    # Mock successful login
    mock_page.is_visible.return_value = True
    
    success = await client.login()
    
    assert success
    assert client.logged_in
    mock_page.goto.assert_called_once_with("https://www.linkedin.com/login")
    mock_page.fill.assert_any_call('input[name="session_key"]', "test@example.com")
    mock_page.fill.assert_any_call('input[name="session_password"]', "password123")
    
    # Clean up environment
    os.environ.pop("LINKEDIN_EMAIL")
    os.environ.pop("LINKEDIN_PASSWORD")


@pytest.mark.asyncio
async def test_login_missing_credentials(client):
    """Test login with missing credentials."""
    # Clear environment variables
    os.environ.pop("LINKEDIN_USERNAME", None)
    os.environ.pop("LINKEDIN_PASSWORD", None)
    
    # Attempt to login
    with pytest.raises(ValueError, match="LinkedIn credentials not found in environment variables"):
        await client.login()


@pytest.mark.asyncio
async def test_login_failure(client, mock_page):
    """Test failed login."""
    # Set up environment variables
    os.environ["LINKEDIN_EMAIL"] = "test@example.com"
    os.environ["LINKEDIN_PASSWORD"] = "password123"
    
    # Mock failed login
    mock_page.is_visible.return_value = False
    
    success = await client.login()
    
    assert not success
    assert not client.logged_in
    
    # Clean up environment
    os.environ.pop("LINKEDIN_EMAIL")
    os.environ.pop("LINKEDIN_PASSWORD")


@pytest.mark.asyncio
async def test_search_sales_navigator_not_logged_in(client):
    """Test search without being logged in."""
    with pytest.raises(RuntimeError, match="Must be logged in to search"):
        await client.search_sales_navigator({})


@pytest.mark.asyncio
async def test_collect_prospect_data_not_logged_in(client):
    """Test data collection without being logged in."""
    with pytest.raises(RuntimeError, match="Must be logged in to collect data"):
        await client.collect_prospect_data("https://linkedin.com/in/test")


@pytest.mark.asyncio
async def test_execute_command_unknown_action(client):
    """Test executing unknown command."""
    client.logged_in = True
    with pytest.raises(ValueError, match="Unknown action"):
        await client.execute_command("invalid_action", {})


@pytest.mark.asyncio
async def test_search_sales_navigator_success(client, mock_page):
    """Test successful Sales Navigator search."""
    # Set up test data
    client._logged_in = True
    search_criteria = {
        "title": "CTO",
        "location": "San Francisco",
        "industry": "Technology"
    }
    
    # Mock page interactions
    mock_page.wait_for_selector = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[
        AsyncMock(**{
            "query_selector": AsyncMock(return_value=AsyncMock(**{
                "inner_text": AsyncMock(return_value="John Doe"),
                "get_attribute": AsyncMock(return_value="https://linkedin.com/in/johndoe")
            }))
        })
    ])
    
    # Execute search
    results = await client.search_sales_navigator(search_criteria)
    
    # Verify results
    assert len(results) > 0
    assert "name" in results[0]
    assert "title" in results[0]
    assert "company" in results[0]
    assert "location" in results[0]
    assert "profile_url" in results[0]
    assert "timestamp" in results[0]
    
    # Verify page interactions
    mock_page.goto.assert_called_with(client.sales_nav_url)
    mock_page.click.assert_any_call('button[aria-label="Search"]')
    mock_page.wait_for_selector.assert_any_call('.advanced-search-modal', state='visible')


@pytest.mark.asyncio
async def test_search_sales_navigator_invalid_criteria(client):
    """Test search with invalid criteria."""
    client._logged_in = True
    with pytest.raises(ValueError):
        await client.search_sales_navigator({})


@pytest.mark.asyncio
async def test_search_sales_navigator_extraction_error(client, mock_page):
    """Test handling of data extraction errors during search."""
    client._logged_in = True
    search_criteria = {"title": "CTO"}
    
    # Mock page interactions with error during data extraction
    mock_page.wait_for_selector = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[
        AsyncMock(**{
            "query_selector": AsyncMock(side_effect=Exception("Failed to extract data"))
        })
    ])
    
    # Execute search
    results = await client.search_sales_navigator(search_criteria)
    
    # Verify empty results due to extraction error
    assert len(results) == 0 