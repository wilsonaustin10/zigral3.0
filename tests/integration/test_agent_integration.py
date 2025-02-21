"""Integration tests for Lincoln and Shaun agents working together in VM."""

import pytest
import os
from datetime import datetime
from typing import Dict, List

from src.agents.lincoln.agent import LincolnAgent, SearchCriteria
from src.agents.shaun.agent import ShaunAgent, SheetRange, SheetData

@pytest.fixture(scope="module")
async def lincoln_agent():
    """Create a Lincoln agent instance for the test module."""
    agent = LincolnAgent(headless=False)  # Use visible browser in VM
    await agent.initialize()
    yield agent
    await agent.cleanup()

@pytest.fixture(scope="module")
async def shaun_agent():
    """Create a Shaun agent instance for the test module."""
    agent = ShaunAgent(headless=False)  # Use visible browser in VM
    await agent.initialize()
    yield agent
    await agent.cleanup()

@pytest.fixture
def linkedin_credentials():
    """Get LinkedIn credentials from environment."""
    return {
        "username": os.environ.get("LINKEDIN_USERNAME"),
        "password": os.environ.get("LINKEDIN_PASSWORD")
    }

@pytest.fixture
def google_credentials():
    """Get Google credentials from environment."""
    return {
        "email": os.environ.get("GOOGLE_EMAIL"),
        "password": os.environ.get("GOOGLE_PASSWORD")
    }

@pytest.fixture
def sheet_id():
    """Get test spreadsheet ID from environment."""
    return os.environ.get("TEST_SHEET_ID")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_prospect_workflow(
    lincoln_agent,
    shaun_agent,
    linkedin_credentials,
    google_credentials,
    sheet_id
):
    """Test complete prospect workflow from LinkedIn to Google Sheets."""
    # Skip if credentials are not configured
    if not all([linkedin_credentials["username"], google_credentials["email"], sheet_id]):
        pytest.skip("Required credentials or sheet ID not configured")
    
    try:
        # 1. Login to LinkedIn
        login_result = await lincoln_agent.login(linkedin_credentials)
        if login_result.get("requires_2fa"):
            # Handle 2FA if needed - in real tests, this might need manual intervention
            # or a configured authenticator app
            pytest.skip("2FA required for LinkedIn")
        assert login_result["logged_in"], "Failed to log in to LinkedIn"
        
        # 2. Search for prospects
        search_criteria = SearchCriteria(
            title="CTO",
            location="San Francisco Bay Area",
            industry="Software"
        )
        prospects = await lincoln_agent.search_sales_navigator(search_criteria)
        assert len(prospects) > 0, "No prospects found"
        
        # 3. Collect detailed data for first prospect
        detailed_data = await lincoln_agent.collect_prospect_data(prospects[0].profile_url)
        assert detailed_data.name, "Failed to collect prospect data"
        
        # 4. Login to Google
        login_result = await shaun_agent.login(google_credentials)
        if login_result.get("requires_2fa"):
            pytest.skip("2FA required for Google")
        assert login_result["logged_in"], "Failed to log in to Google"
        
        # 5. Open the spreadsheet
        sheet_result = await shaun_agent.open_spreadsheet(sheet_id)
        assert sheet_result["sheet_id"] == sheet_id, "Failed to open spreadsheet"
        
        # 6. Create a new sheet for test data
        sheet_name = f"Prospects_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await shaun_agent.create_sheet(sheet_name)
        
        # 7. Write headers
        headers = [
            "Name", "Title", "Company", "Location", "Profile URL",
            "About", "Current Role", "Education", "Skills"
        ]
        header_data = SheetData(
            values=[headers],
            range=SheetRange(
                sheet_name=sheet_name,
                start_cell="A1",
                end_cell=f"{chr(65 + len(headers) - 1)}1"  # Calculate last column
            )
        )
        await shaun_agent.write_range(header_data)
        
        # 8. Format headers
        await shaun_agent.format_range(
            header_data.range,
            {"bold": True, "background_color": "light gray"}
        )
        
        # 9. Write prospect data
        prospect_row = [
            detailed_data.name,
            detailed_data.title,
            detailed_data.company,
            detailed_data.location,
            detailed_data.profile_url,
            detailed_data.about,
            detailed_data.experience[0]["title"] if detailed_data.experience else "",
            detailed_data.education[0]["school"] if detailed_data.education else "",
            ", ".join(detailed_data.skills[:3])  # First 3 skills
        ]
        prospect_data = SheetData(
            values=[prospect_row],
            range=SheetRange(
                sheet_name=sheet_name,
                start_cell="A2",
                end_cell=f"{chr(65 + len(prospect_row) - 1)}2"
            )
        )
        result = await shaun_agent.write_range(prospect_data)
        assert result["rows"] == 1, "Failed to write prospect data"
        
    except Exception as e:
        pytest.fail(f"Integration test failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_operation(lincoln_agent, shaun_agent):
    """Test both agents operating concurrently in the VM."""
    try:
        # Start navigation tasks concurrently
        linkedin_task = lincoln_agent._navigate(url="https://www.linkedin.com")
        sheets_task = shaun_agent._navigate(url="https://docs.google.com/spreadsheets")
        
        # Wait for both tasks to complete
        await asyncio.gather(linkedin_task, sheets_task)
        
        # Verify both pages loaded
        linkedin_title = await lincoln_agent._page.title()
        sheets_title = await shaun_agent._page.title()
        
        assert "LinkedIn" in linkedin_title
        assert "Google Sheets" in sheets_title
        
    except Exception as e:
        pytest.fail(f"Concurrent operation test failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_resource_cleanup(lincoln_agent, shaun_agent):
    """Test proper cleanup of browser resources."""
    try:
        # Perform some operations
        await lincoln_agent._navigate(url="https://www.linkedin.com")
        await shaun_agent._navigate(url="https://docs.google.com/spreadsheets")
        
        # Take screenshots to verify state
        lincoln_screenshot = await lincoln_agent._take_screenshot("linkedin_cleanup")
        shaun_screenshot = await shaun_agent._take_screenshot("sheets_cleanup")
        
        assert os.path.exists(lincoln_screenshot["screenshot"])
        assert os.path.exists(shaun_screenshot["screenshot"])
        
        # Cleanup
        await lincoln_agent.cleanup()
        await shaun_agent.cleanup()
        
        # Verify cleanup
        assert not lincoln_agent._browser
        assert not lincoln_agent._page
        assert not shaun_agent._browser
        assert not shaun_agent._page
        
    except Exception as e:
        pytest.fail(f"Resource cleanup test failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling(lincoln_agent, shaun_agent):
    """Test error handling and recovery."""
    try:
        # Test invalid navigation
        with pytest.raises(Exception):
            await lincoln_agent._navigate(url="invalid://url")
        
        # Verify agents can continue operating
        await lincoln_agent._navigate(url="https://www.linkedin.com")
        assert await lincoln_agent._page.title()
        
        # Test invalid spreadsheet operation
        with pytest.raises(RuntimeError):
            await shaun_agent.write_range(SheetData(
                values=[["test"]],
                range=SheetRange(sheet_name="NonexistentSheet", start_cell="A1")
            ))
        
        # Verify agent can continue operating
        await shaun_agent._navigate(url="https://docs.google.com/spreadsheets")
        assert await shaun_agent._page.title()
        
    except Exception as e:
        pytest.fail(f"Error handling test failed: {str(e)}") 