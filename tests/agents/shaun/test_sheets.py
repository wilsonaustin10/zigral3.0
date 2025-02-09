"""Test Google Sheets functionality with actual credentials."""

import asyncio
from src.agents.shaun.sheets_client import GoogleSheetsClient
import pytest

@pytest.mark.asyncio
async def test_sheets_functionality():
    """Test basic Google Sheets operations."""
    # Initialize the client
    client = GoogleSheetsClient()
    print("Initializing Google Sheets client...")
    await client.initialize()
    print("Client initialized successfully!")

    try:
        # Create a new spreadsheet
        print("\nCreating new spreadsheet...")
        spreadsheet = client.client.create("Zigral Prospects Test")
        print(f"Created new spreadsheet with ID: {spreadsheet.id}")
        print(f"Spreadsheet URL: {spreadsheet.url}")

        # Connect to the sheet
        print("\nConnecting to the new sheet...")
        spreadsheet, worksheet = await client.connect_to_sheet(spreadsheet.id)
        print(f"Connected to spreadsheet: {spreadsheet.title}")
        print(f"Using worksheet: {worksheet.title}")

        # Test adding prospects
        test_prospects = [
            {
                "Full Name": "John Doe",
                "Title": "CTO",
                "Company": "Tech Corp",
                "Location": "San Francisco",
                "LinkedIn URL": "https://linkedin.com/in/johndoe",
                "Experience": "10+ years in tech",
                "Education": "BS Computer Science",
                "Last Updated": "2024-02-08"
            }
        ]

        print("\nAdding test prospect...")
        result = await client.add_prospects(test_prospects)
        print("Add prospects result:", result)
        assert result["success"] is True
        assert len(result["added"]) == 1

    finally:
        # Cleanup
        if hasattr(spreadsheet, 'id'):
            client.client.del_spreadsheet(spreadsheet.id)
        await client.cleanup()
        print("\nClient cleaned up successfully!") 