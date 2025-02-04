"""
Tests for LinkedIn Browser Automation.
"""

from unittest.mock import AsyncMock, patch

import pytest
from playwright.async_api import Browser, Page, Playwright

from agents.lincoln.browser import LinkedInBrowser


@pytest.fixture
async def browser():
    """Create a LinkedInBrowser instance for testing."""
    browser = LinkedInBrowser()
    yield browser
    await browser.cleanup()


@pytest.mark.asyncio
async def test_browser_initialization():
    """Test browser initialization."""
    browser = LinkedInBrowser()
    assert browser.playwright is None
    assert browser.browser is None
    assert browser.page is None


@pytest.mark.asyncio
async def test_browser_initialize():
    """Test initializing the browser with Playwright."""
    browser = LinkedInBrowser()

    mock_page = AsyncMock(spec=Page)
    mock_browser = AsyncMock(spec=Browser)
    mock_browser.new_page.return_value = mock_page
    mock_playwright = AsyncMock(spec=Playwright)
    mock_playwright.chromium.launch.return_value = mock_browser

    with patch(
        "agents.lincoln.browser.async_playwright",
        return_value=AsyncMock(start=AsyncMock(return_value=mock_playwright)),
    ):
        await browser.initialize()
        assert browser.page is not None
        assert browser.browser is not None
        assert browser.playwright is not None


@pytest.mark.asyncio
async def test_browser_navigation():
    """Test browser navigation."""
    browser = LinkedInBrowser()
    mock_page = AsyncMock(spec=Page)
    browser.page = mock_page

    test_url = "https://www.linkedin.com"
    await browser.navigate(test_url)
    mock_page.goto.assert_called_once_with(test_url)


@pytest.mark.asyncio
async def test_browser_click():
    """Test browser click action."""
    browser = LinkedInBrowser()
    mock_page = AsyncMock(spec=Page)
    browser.page = mock_page

    test_selector = "#test-button"
    await browser.click(test_selector)
    mock_page.click.assert_called_once_with(test_selector)


@pytest.mark.asyncio
async def test_browser_type():
    """Test browser type action."""
    browser = LinkedInBrowser()
    mock_page = AsyncMock(spec=Page)
    browser.page = mock_page

    test_selector = "#test-input"
    test_text = "test text"
    await browser.type(test_selector, test_text)
    mock_page.fill.assert_called_once_with(test_selector, test_text)


@pytest.mark.asyncio
async def test_browser_cleanup():
    """Test browser cleanup."""
    browser = LinkedInBrowser()
    mock_browser = AsyncMock(spec=Browser)
    mock_playwright = AsyncMock(spec=Playwright)
    browser.browser = mock_browser
    browser.playwright = mock_playwright

    await browser.cleanup()
    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()
