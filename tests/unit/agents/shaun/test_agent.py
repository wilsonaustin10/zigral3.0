"""Unit tests for Shaun (Google Sheets) agent."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.agents.shaun.agent import (
    ShaunAgent,
    GoogleCredentials,
    SheetRange,
    SheetData
)

@pytest.fixture
async def shaun_agent():
    """Create a Shaun agent instance for testing."""
    agent = ShaunAgent(headless=True)
    await agent.initialize()
    yield agent
    await agent.cleanup()

@pytest.fixture
def mock_credentials():
    """Create mock Google credentials."""
    return GoogleCredentials(
        email="test@example.com",
        password="test_password"
    )

@pytest.fixture
def mock_sheet_range():
    """Create mock sheet range."""
    return SheetRange(
        sheet_name="Sheet1",
        start_cell="A1",
        end_cell="B2"
    )

@pytest.fixture
def mock_sheet_data(mock_sheet_range):
    """Create mock sheet data."""
    return SheetData(
        values=[["Header1", "Header2"], ["Value1", "Value2"]],
        range=mock_sheet_range
    )

@pytest.mark.asyncio
async def test_login_success(shaun_agent, mock_credentials):
    """Test successful login without 2FA."""
    # Mock the navigation and element interactions
    shaun_agent._navigate = AsyncMock()
    shaun_agent._type = AsyncMock()
    shaun_agent._click = AsyncMock()
    shaun_agent._page.wait_for_selector = AsyncMock()
    
    result = await shaun_agent.login(mock_credentials)
    
    assert result["logged_in"] is True
    assert result["requires_2fa"] is False
    assert shaun_agent._logged_in is True

@pytest.mark.asyncio
async def test_login_with_2fa(shaun_agent, mock_credentials):
    """Test login that requires 2FA."""
    # Mock the navigation and element interactions
    shaun_agent._navigate = AsyncMock()
    shaun_agent._type = AsyncMock()
    shaun_agent._click = AsyncMock()
    
    # Mock 2FA challenge detection
    async def mock_wait_for_selector(selector, **kwargs):
        if selector == "#challengePickerList":
            return AsyncMock()
        return None
    
    shaun_agent._page.wait_for_selector = mock_wait_for_selector
    
    result = await shaun_agent.login(mock_credentials)
    
    assert result["logged_in"] is False
    assert result["requires_2fa"] is True

@pytest.mark.asyncio
async def test_open_spreadsheet(shaun_agent):
    """Test opening a spreadsheet."""
    # Set up test data
    sheet_id = "test_sheet_id"
    sheet_title = "Test Sheet"
    
    # Mock interactions
    shaun_agent._logged_in = True
    shaun_agent._navigate = AsyncMock()
    shaun_agent._page.wait_for_selector = AsyncMock()
    shaun_agent._get_text = AsyncMock(return_value=sheet_title)
    
    result = await shaun_agent.open_spreadsheet(sheet_id)
    
    assert result["sheet_id"] == sheet_id
    assert result["title"] == sheet_title
    assert shaun_agent.current_sheet_id == sheet_id

@pytest.mark.asyncio
async def test_read_range(shaun_agent, mock_sheet_range):
    """Test reading data from a range."""
    # Set up test data
    test_data = "Header1\tHeader2\nValue1\tValue2"
    
    # Mock interactions
    shaun_agent.current_sheet_id = "test_sheet_id"
    shaun_agent._click = AsyncMock()
    shaun_agent._type = AsyncMock()
    shaun_agent._page.keyboard = AsyncMock()
    shaun_agent._page.evaluate = AsyncMock(return_value=test_data)
    
    result = await shaun_agent.read_range(mock_sheet_range)
    
    assert isinstance(result, SheetData)
    assert len(result.values) == 2
    assert result.values[0] == ["Header1", "Header2"]
    assert result.values[1] == ["Value1", "Value2"]

@pytest.mark.asyncio
async def test_write_range(shaun_agent, mock_sheet_data):
    """Test writing data to a range."""
    # Mock interactions
    shaun_agent.current_sheet_id = "test_sheet_id"
    shaun_agent._click = AsyncMock()
    shaun_agent._type = AsyncMock()
    shaun_agent._page.keyboard = AsyncMock()
    shaun_agent._page.evaluate = AsyncMock()
    
    result = await shaun_agent.write_range(mock_sheet_data)
    
    assert result["rows"] == 2
    assert result["columns"] == 2
    assert result["range"] == mock_sheet_data.range.dict()

@pytest.mark.asyncio
async def test_create_sheet(shaun_agent):
    """Test creating a new sheet."""
    # Set up test data
    sheet_title = "New Sheet"
    
    # Mock interactions
    shaun_agent.current_sheet_id = "test_sheet_id"
    shaun_agent._click = AsyncMock()
    shaun_agent._page.wait_for_selector = AsyncMock()
    
    result = await shaun_agent.create_sheet(sheet_title)
    
    assert result["title"] == sheet_title

@pytest.mark.asyncio
async def test_format_range(shaun_agent, mock_sheet_range):
    """Test applying formatting to a range."""
    # Set up test data
    formatting = {
        "bold": True,
        "background_color": "yellow"
    }
    
    # Mock interactions
    shaun_agent.current_sheet_id = "test_sheet_id"
    shaun_agent._click = AsyncMock()
    shaun_agent._type = AsyncMock()
    shaun_agent._page.keyboard = AsyncMock()
    
    result = await shaun_agent.format_range(mock_sheet_range, formatting)
    
    assert result["range"] == mock_sheet_range.dict()
    assert result["formatting"] == formatting

@pytest.mark.asyncio
async def test_verify_2fa_success(shaun_agent):
    """Test successful 2FA verification."""
    # Mock interactions
    shaun_agent._type = AsyncMock()
    shaun_agent._click = AsyncMock()
    shaun_agent._page.wait_for_selector = AsyncMock()
    
    result = await shaun_agent.verify_2fa("123456")
    
    assert result["success"] is True
    assert shaun_agent._logged_in is True

@pytest.mark.asyncio
async def test_verify_2fa_failure(shaun_agent):
    """Test failed 2FA verification."""
    # Mock interactions to simulate failure
    shaun_agent._type = AsyncMock()
    shaun_agent._click = AsyncMock()
    shaun_agent._page.wait_for_selector = AsyncMock(side_effect=Exception("2FA failed"))
    
    result = await shaun_agent.verify_2fa("invalid")
    
    assert result["success"] is False
    assert "error" in result 