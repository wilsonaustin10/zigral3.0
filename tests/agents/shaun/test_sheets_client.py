"""
Tests for the Google Sheets client functionality.
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from google.oauth2.service_account import Credentials

from src.agents.shaun.sheets_client import GoogleSheetsClient

@pytest.fixture(autouse=True)
def patch_google_credentials(monkeypatch):
    monkeypatch.setattr(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        lambda path, **kwargs: MagicMock()
    )

@pytest.fixture
def mock_credentials():
    """Sample credentials for testing."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC9QFxXxbJEvxB8\nZc5LRL4IP4TGXtEVUgJ/5YPrqD3SxqyRR8iJI8L1C9uZKXSNzIIj8O2Ua4bD0fgS\nkX+4wbKjvbqZnDGZz8rGJ7P0/qNRqHN2TD6R9G+XP+kHgPut5PGZwsV4rKxjFYWk\nHlEImhYw9g8P32pK7kQX3j0Vw2lq6WAxpQB3tZsOWZYkw9gJ97ALJoQLnuZxZEeZ\nXJwYuVxnpZXnOfIws+af6Z5qqWf4ptDGvj8PRqKFZRPyixZ5AJJxY7e0UP8cFVN5\nLJwgv5GXtcGZLBQEQfu+Y1K4k9PDLkqm2tcg8yEm/yAB9CGpW0mZIotRqGoqnqG4\n0q3CAgMBAAECggEABQ4Jl1iNvz0KKm8Qg5FGRxGZJGBI7P0y39Sj5Pg8I8Aq3Znk\nzwZ3vQm7gTRpHZPJP4gM6YCw6Xt6Ux5rvHVAVYH+kZHiN0yjEj5r5WcH8E8sN0Jm\nk3UhB7Q9yP0xGjOF6ewJZpNtv4YLDhzhp5VhvwqQ9p5yCXl7yEBBQa0JUDwjFQyR\n1Y4rWGUcOG1GKJ6kE+PqoIWHLzDjr8wX1hk9MNy8LH6HFgQfnPdH5zkqoGp1fL+B\n0YWkzKJ2H5x+exZMhkBXPCwCsbEyEVLO9mZkJ4QKGKBUHaR/v+QpR8dXGTOAs7mz\nLjUML4UJXOVkYAg51Yv8aM+2qXpkZCUvz3gZAoGBAMQKBXWnRaXqRHeBsZdPw/on\n7PxG5Uw7+Qz6Pxn45LS3mZGRmgJvFV6HCqH2jQhqM7sDuutkGwIqOmJXjG0p5/eC\nGzj8UxY+YhqYxqjfGf7eQBRxZkP5yWvi2C2uKHsSBY4iNVXLhNFzleLNd4nACTrF\nSxGxovJ7UxOfXaM9AoGBAO/0Gv2HcXGjhJHYFEm1XwJ4JGnifHvwlXcrvp0+YgaD\nQqYZ5VUYw7VAG3oBBCxKGAFwzziY7ZVm6TfGDxn5DQIR4VUSWgBqNMZHwkOBXy3q\nY4EZ8R7OW2UpxwL1dxJ7TXBIjP96BFYt2dvYm2pW1CjF1ePvYaFgCJxDAoGBAL1J\n5A3vsE2hQwJJxY+wFjKGlwKdxQVj6R7HqW/Z7G4wXXm+mz9VhQhC6MMn0LBOhbVh\nVhU8YbRYBDNJz7tW5zZ6UI7gVjzNJFYZuWcTrGK1y0NlGKhEqPf6MCp9UQtFzPqL\nLX8QhqNzqn5KkTcZXlwHRlJWBgKqxQKBAoGBAO7K2WC7VmgMK3Z7XhTBQN5TqiV6\nELTZL1+YzRvN++8VJxN6TL5LVd/rsMX0BqT6wpTJALZF1D6IBqS+XNljkuI8mdLx\n2SSfVX7mQFHE7WCJfGPqIhbRDOJrsC/AYHYgXuPVNEj5HmxDvVX1uBvZN4/5pYGg\nZfwpiJ0h\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }

@pytest.fixture
def mock_gspread():
    """Create a mock gspread client."""
    mock = MagicMock()
    mock.authorize.return_value = MagicMock()
    return mock

@pytest.fixture
def temp_credentials_file(tmp_path, mock_credentials):
    """Create a temporary credentials file."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(json.dumps(mock_credentials, indent=2))
    return str(creds_file)

@pytest.fixture
def client(temp_credentials_file):
    """Create a test client instance."""
    return GoogleSheetsClient(temp_credentials_file)

@pytest.fixture
def mock_spreadsheet(mock_gspread):
    """Mock spreadsheet."""
    spreadsheet = MagicMock()
    mock_gspread.authorize.return_value.open_by_key.return_value = spreadsheet
    return spreadsheet

@pytest.fixture
def mock_worksheet(mock_spreadsheet):
    """Mock worksheet."""
    worksheet = MagicMock()
    mock_spreadsheet.worksheet.return_value = worksheet
    return worksheet

@pytest.mark.asyncio
async def test_init_with_creds_path():
    """Test initializing with explicit credentials path."""
    client = GoogleSheetsClient(creds_path="test/path/credentials.json")
    assert Path(client.creds_path).resolve() == Path("test/path/credentials.json").resolve()

@pytest.mark.asyncio
async def test_init_with_env_var(monkeypatch):
    """Test initializing with credentials path from environment variable."""
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS", "/env/path/credentials.json")
    client = GoogleSheetsClient()
    assert client.creds_path == "/env/path/credentials.json"

@pytest.mark.asyncio
async def test_init_with_default_location(monkeypatch, tmp_path):
    """Test initializing with credentials in default location."""
    # Create a simulated home directory within tmp_path
    temp_home = tmp_path / "home"
    temp_home.mkdir()

    # Create the .config/gspread directory structure
    config_dir = temp_home / ".config" / "gspread"
    config_dir.mkdir(parents=True)

    # Path for the credentials file
    credentials_file = config_dir / "credentials.json"

    # Write valid credentials JSON content
    valid_credentials = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "abc123",
        "private_key": "-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test@test-project.iam.gserviceaccount.com"
    }
    credentials_file.write_text(json.dumps(valid_credentials, indent=2))

    # Ensure GOOGLE_SHEETS_CREDENTIALS is not set
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS", raising=False)
    # Set the HOME environment variable to our temp_home
    monkeypatch.setenv("HOME", str(temp_home))

    # Import the GoogleSheetsClient from the module
    from src.agents.shaun.sheets_client import GoogleSheetsClient

    # Initialize the client without explicitly passing a creds_path, so it uses get_credentials_path
    client = GoogleSheetsClient()
    with patch("gspread.authorize", return_value=MagicMock()):
        await client.initialize()

    # Assert that the client picked up the credentials file from the default location
    assert Path(client.creds_path).resolve() == credentials_file.resolve()

    await client.cleanup()

@pytest.mark.asyncio
async def test_initialize_with_valid_credentials(temp_credentials_file, mock_gspread):
    """Test successful initialization with valid credentials."""
    with patch("gspread.authorize", mock_gspread.authorize):
        client = GoogleSheetsClient(creds_path=temp_credentials_file)
        await client.initialize()
        assert client.client is not None
        mock_gspread.authorize.assert_called_once()

@pytest.mark.asyncio
async def test_initialize_missing_credentials():
    """Test initialization fails with missing credentials file."""
    client = GoogleSheetsClient(creds_path="/nonexistent/path/credentials.json")
    with pytest.raises(FileNotFoundError):
        await client.initialize()

@pytest.mark.asyncio
async def test_initialize_invalid_credentials(tmp_path):
    """Test initialization fails with invalid credentials file."""
    # Create invalid credentials file
    invalid_creds_file = tmp_path / "invalid_credentials.json"
    invalid_creds_file.write_text("invalid json content")
    
    client = GoogleSheetsClient(creds_path=str(invalid_creds_file))
    with pytest.raises(Exception):
        await client.initialize()

@pytest.mark.asyncio
async def test_cleanup():
    """Test cleanup properly resets client state."""
    client = GoogleSheetsClient()
    client.client = MagicMock()
    client.spreadsheet = MagicMock()
    client.worksheet = MagicMock()
    
    await client.cleanup()
    assert client.client is None
    assert client.spreadsheet is None
    assert client.worksheet is None

@pytest.mark.asyncio
async def test_connect_to_sheet(temp_credentials_file, mock_gspread):
    """Test connecting to a specific spreadsheet."""
    mock_spreadsheet = MagicMock()
    mock_worksheet = MagicMock()
    mock_spreadsheet.worksheet.return_value = mock_worksheet
    mock_gspread.authorize.return_value.open_by_key.return_value = mock_spreadsheet
    
    with patch("gspread.authorize", mock_gspread.authorize):
        client = GoogleSheetsClient(creds_path=temp_credentials_file)
        await client.initialize()
        spreadsheet, worksheet = await client.connect_to_sheet("test-spreadsheet-id")
        
        assert spreadsheet == mock_spreadsheet
        assert worksheet == mock_worksheet

@pytest.mark.asyncio
async def test_connect_to_sheet_creates_worksheet(temp_credentials_file, mock_gspread):
    """Test worksheet creation when it doesn't exist."""
    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheet.side_effect = Exception("Worksheet not found")
    mock_worksheet = MagicMock()
    mock_spreadsheet.add_worksheet.return_value = mock_worksheet
    mock_gspread.authorize.return_value.open_by_key.return_value = mock_spreadsheet
    
    with patch("gspread.authorize", mock_gspread.authorize):
        client = GoogleSheetsClient(creds_path=temp_credentials_file)
        await client.initialize()
        spreadsheet, worksheet = await client.connect_to_sheet("test-spreadsheet-id")
        
        assert spreadsheet == mock_spreadsheet
        assert worksheet == mock_worksheet
        mock_spreadsheet.add_worksheet.assert_called_once()
        mock_worksheet.insert_row.assert_called_once_with(client._headers, index=1)

@pytest.mark.asyncio
async def test_add_prospects_success(client, mock_credentials, mock_worksheet):
    """Test successful addition of prospects."""
    mock_client = MagicMock()
    spreadsheet_mock = MagicMock()
    spreadsheet_mock.worksheet.return_value = mock_worksheet
    mock_client.open_by_key.return_value = spreadsheet_mock

    # Mock the append_rows method to return successfully
    mock_worksheet.append_rows.return_value = None

    with patch("src.agents.shaun.sheets_client.GoogleSheetsClient._gs_authorize", new=lambda self, x: mock_client):
        await client.initialize()
        await client.connect_to_sheet('test_sheet_id', 'test_worksheet')

        prospects = [
            {
                'Full Name': 'John Doe',
                'Title': 'CEO',
                'Company': 'Test Inc',
                'Location': 'San Francisco',
                'LinkedIn URL': 'https://linkedin.com/in/johndoe',
                'Experience': '10+ years',
                'Education': 'MBA',
                'Last Updated': '2024-02-08'
            },
            {
                'Full Name': 'Jane Smith',
                'Title': 'CTO',
                'Company': 'Demo Corp',
                'Location': 'New York',
                'LinkedIn URL': 'https://linkedin.com/in/janesmith',
                'Experience': '15+ years',
                'Education': 'PhD',
                'Last Updated': '2024-02-08'
            }
        ]

        result = await client.add_prospects(prospects)
        assert result['success'] is True
        assert len(result['added']) == 2
        mock_worksheet.append_rows.assert_called_once()

@pytest.mark.asyncio
async def test_add_prospects_no_worksheet(client, mock_credentials):
    """Test adding prospects without connecting to worksheet."""
    with patch("gspread.authorize", return_value=MagicMock()):
        await client.initialize()
        with pytest.raises(ValueError):
            await client.add_prospects([{'name': 'Test'}])

@pytest.mark.asyncio
async def test_update_prospect_success(client, mock_credentials, mock_worksheet):
    """Test successful prospect update."""
    mock_client = MagicMock()
    spreadsheet_mock = MagicMock()
    spreadsheet_mock.worksheet.return_value = mock_worksheet
    mock_client.open_by_key.return_value = spreadsheet_mock
    with patch("src.agents.shaun.sheets_client.GoogleSheetsClient._gs_authorize", new=lambda self, x: mock_client):
        await client.initialize()
        await client.connect_to_sheet('test_sheet_id', 'test_worksheet')
        
        mock_worksheet.find.return_value = MagicMock(row=2)
        
        result = await client.update_prospect(
            'john@example.com',
            {'name': 'John Updated', 'company': 'New Corp'}
        )
        assert result['success'] is True

@pytest.mark.asyncio
async def test_update_prospect_not_found(client, mock_credentials, mock_worksheet):
    """Test updating non-existent prospect."""
    mock_client = MagicMock()
    spreadsheet_mock = MagicMock()
    mock_worksheet.find.return_value = None  # Simulate not found
    spreadsheet_mock.worksheet.return_value = mock_worksheet
    mock_client.open_by_key.return_value = spreadsheet_mock
    with patch("src.agents.shaun.sheets_client.GoogleSheetsClient._gs_authorize", new=lambda self, x: mock_client):
        await client.initialize()
        await client.connect_to_sheet('test_sheet_id', 'test_worksheet')
        
        result = await client.update_prospect(
            'nonexistent@example.com',
            {'name': 'Test'}
        )
        assert result['success'] is False

@pytest.mark.asyncio
async def test_execute_command_connect(client, mock_credentials):
    """Test execute_command with connect action."""
    with patch("gspread.authorize", return_value=MagicMock()):
        await client.initialize()

    # Mock the gspread client's open_by_key method
    mock_spreadsheet = MagicMock()
    mock_spreadsheet.title = "Test Spreadsheet"
    mock_worksheet = MagicMock()
    mock_worksheet.title = "Test Worksheet"
    mock_spreadsheet.worksheet.return_value = mock_worksheet
    client.client = MagicMock()
    client.client.open_by_key.return_value = mock_spreadsheet

    result = await client.execute_command({
        'action': 'connect',
        'sheet_id': 'test_sheet_id',
        'worksheet': 'test_worksheet'
    })
    
    assert result['success'] is True
    assert client.spreadsheet == mock_spreadsheet
    assert client.worksheet == mock_worksheet

@pytest.mark.asyncio
async def test_execute_command_invalid_action(client, mock_credentials):
    """Test execute_command with invalid action."""
    with patch("gspread.authorize", return_value=MagicMock()):
        await client.initialize()
    result = await client.execute_command({
        'action': 'invalid_action'
    })
    assert result['success'] is False 