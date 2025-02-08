import asyncio
from src.agents.shaun.sheets_client import GoogleSheetsClient
import gspread

async def test_sheets_functionality():
    # Initialize the client
    client = GoogleSheetsClient()
    print("Initializing Google Sheets client...")
    await client.initialize()
    print("Client initialized successfully!")

    # Create a new spreadsheet
    print("\nCreating new spreadsheet...")
    spreadsheet = client.client.create("Zigral Prospects")
    print(f"Created new spreadsheet with ID: {spreadsheet.id}")
    print(f"Spreadsheet URL: {spreadsheet.url}")

    # Share the spreadsheet with a specific email (optional)
    share_email = input("\nEnter email to share the spreadsheet with (press Enter to skip): ")
    if share_email:
        spreadsheet.share(share_email, perm_type='user', role='writer')
        print(f"Shared spreadsheet with {share_email}")

    # Connect to the newly created sheet
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

    # Cleanup
    await client.cleanup()
    print("\nClient cleaned up successfully!")

if __name__ == "__main__":
    asyncio.run(test_sheets_functionality()) 