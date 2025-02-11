"""
Tests for the Google Sheets client functionality.
"""

import json
import os
import pytest
import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from google.oauth2.service_account import Credentials

from src.agents.shaun.sheets_client import GoogleSheetsClient, SCOPES

# Sample credentials for testing
SAMPLE_CREDS = {
    "type": "service_account",
    "project_id": "test-project",
    "private_key_id": "test-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDFuHJJHAZ+Q0qE\nPOgOb4z+0w2qZpB5wF0+UBzX7Jq4EU5hVegSqzYEBfzqHo5wQEQUZoQOXA0JQhM6\nv4KqrUHQmZtL6QFEHm+n0LsRxwbYwPUE1g9YjOJyqGRqtJF7NXqLZZEgBOxZLJXU\nw/UHvj/vlvGBUZVHlvVgrIqbGQpUBCBh0aBdHhyp6c3NNyGEJz5sJTDUQJEK2FaF\nIJOCLw4L3Kpz0XkRZz1RtYtCGz1POr0p6JJQ7gGwQA9qJE2HnWKV4qGJ3YC7EJH6\nZpYh4QK5WkK1dUJHH3Z8QFxqDR4XxzZJ0SYf9KL3xhvq5C2jQ5UvV1gD0QQZQWOy\nAgMBAAECggEABLURDWVv7CAqL5XmKYeJJHaVW8+HcH4QGj6nXv+4rP7dZK9rGSVr\nX9sZ6j1B6yh/9P6gKkm5QDX+FjbRPQH5xKFVRFH8qG6IqpQGY/o5aNZQ5vTP9nLP\nZH5kZo8Mu7QE8TBxFO+/Hs72FqQOh7dGo1kX8Ir5vAqsqvqCjH8bC6WqcYC0Qg8I\nQE5kHuHGQH5HJWLxEqQf9gYyYNK5cP8hEXEps/p+7CYVlGZQX8D1qZqHrwKpvYOm\nYg1V/9LjVQzBEqKzHXGPQVpvvCXO4UZHNjkPJLm6HpNBvZMH1/l4ckJLSf0vEVwC\nJZMLENPZQkBuKPUv3oGMEQKBgQDFuHJJHAZ+Q0qEPOgOb4z+0w2qZpB5wF0+UBzX\n7Jq4EU5hVegSqzYEBfzqHo5wQEQUZoQOXA0JQhM6v4KqrUHQmZtL6QFEHm+n0LsR\nxwbYwPUE1g9YjOJyqGRqtJF7NXqLZZEgBOxZLJXUw/UHvj/vlvGBUZVHlvVgrIqb\nGQpUBCBh0aBdHhyp6c3NNyGEJz5sJTDUQJEK2FaFIJOCLw4L3Kpz0XkRZz1RtYtC\nGz1POr0p6JJQ7gGwQA9qJE2HnWKV4qGJ3YC7EJH6ZpYh4QK5WkK1dUJHH3Z8QFxq\nDR4XxzZJ0SYf9KL3xhvq5C2jQ5UvV1gD0QQZQWOy",
    "client_email": "test@test-project.iam.gserviceaccount.com",
    "client_id": "test-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

@pytest.fixture(autouse=True)
def patch_google_credentials(monkeypatch):
    """Mock Google credentials."""
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.__module__ = 'google.oauth2.service_account'
    mock_creds.__class__.__name__ = 'Credentials'
    
    def mock_from_file(path, **kwargs):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Credentials file not found: {path}")
        if os.path.getsize(path) == 0:
            raise ValueError("Invalid credentials file")
        return mock_creds
    
    monkeypatch.setattr(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        mock_from_file
    )
    return mock_creds

@pytest.fixture
def mock_credentials():
    """Mock credentials factory."""
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.__module__ = 'google.oauth2.service_account'
    mock_creds.__class__.__name__ = 'Credentials'
    
    with patch('google.oauth2.service_account.Credentials.from_service_account_info') as mock_from_info:
        mock_from_info.return_value = mock_creds
        with patch('gspread.authorize') as mock_auth:
            mock_auth.return_value = MagicMock()
            yield mock_from_info

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
    # Write the credentials in base64 format
    creds_json = json.dumps(SAMPLE_CREDS)
    b64_creds = base64.b64encode(creds_json.encode()).decode()
    creds_file.write_text(f"data:application/json;base64,{b64_creds}")
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
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "/env/path/credentials.json")
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_JSON", raising=False)
    client = GoogleSheetsClient()
    assert client.creds_path == "/env/path/credentials.json"

@pytest.mark.asyncio
async def test_init_with_default_location(tmp_path):
    """Test initializing with default credentials location."""
    # Create a mock home directory in tmp_path
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    config_dir = mock_home / ".config" / "gspread"
    config_dir.mkdir(parents=True)
    
    default_path = config_dir / "credentials.json"
    with open(default_path, "w") as f:
        json.dump(SAMPLE_CREDS, f)
    
    with patch.dict(os.environ, {"HOME": str(mock_home)}):
        # Ensure no JSON credentials env var interferes
        if "GOOGLE_SHEETS_CREDENTIALS_JSON" in os.environ:
            del os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"]
        client = GoogleSheetsClient()
        assert client.creds_path == str(default_path.resolve())

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
    with pytest.raises(FileNotFoundError, match="Credentials file not found"):
        await client.initialize()

@pytest.mark.asyncio
async def test_initialize_invalid_credentials(tmp_path):
    """Test initialization fails with invalid credentials file."""
    # Create empty credentials file
    invalid_creds_file = tmp_path / "invalid_credentials.json"
    invalid_creds_file.touch()  # Creates an empty file
    
    client = GoogleSheetsClient(creds_path=str(invalid_creds_file))
    with pytest.raises(ValueError, match="Invalid credentials file"):
        await client.initialize()

@pytest.mark.asyncio
async def test_cleanup(tmp_path):
    """Test cleanup properly resets client state."""
    # Create a temporary credentials file
    creds_file = tmp_path / "credentials.json"
    with open(creds_file, "w") as f:
        json.dump(SAMPLE_CREDS, f)
    
    client = GoogleSheetsClient(creds_path=str(creds_file))
    client.client = MagicMock()
    client.spreadsheet = MagicMock()
    client.worksheet = MagicMock()
    
    await client.cleanup()
    
    assert client.client is None
    assert client.spreadsheet is None
    assert client.worksheet is None
    assert not client._is_initialized

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

@pytest.fixture
def base64_creds():
    return f"data:application/json;base64,{base64.b64encode(json.dumps(SAMPLE_CREDS).encode()).decode()}"

@pytest.mark.asyncio
async def test_init_with_base64_credentials(base64_creds, mock_credentials):
    """Test initializing client with base64 encoded credentials."""
    # Set up environment
    os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"] = base64_creds
    
    # Create client
    client = GoogleSheetsClient()
    
    # Verify credentials were properly decoded
    assert hasattr(client, 'creds_info')
    assert client.creds_info["type"] == "service_account"
    assert client.creds_info["project_id"] == "test-project"
    
    # Test initialization
    await client.initialize()
    mock_credentials.assert_called_once_with(SAMPLE_CREDS, scopes=SCOPES)

@pytest.mark.asyncio
async def test_init_with_invalid_base64_credentials():
    """Test initializing client with invalid base64 encoded credentials."""
    # Set invalid base64 string
    os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"] = "invalid;base64,not_valid_base64"
    
    with pytest.raises(ValueError, match="Invalid credentials JSON format"):
        client = GoogleSheetsClient()

@pytest.mark.asyncio
async def test_init_with_invalid_json_credentials():
    """Test initializing client with invalid JSON credentials."""
    # Set invalid JSON string
    invalid_json = base64.b64encode("not valid json".encode()).decode()
    os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"] = f"data:application/json;base64,{invalid_json}"
    
    with pytest.raises(ValueError, match="Invalid credentials JSON format"):
        client = GoogleSheetsClient()

@pytest.mark.asyncio
async def test_init_with_direct_json_credentials(mock_credentials):
    """Test initializing client with direct JSON credentials."""
    # Set JSON string directly
    os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"] = json.dumps(SAMPLE_CREDS)
    
    # Create and initialize client
    client = GoogleSheetsClient()
    assert hasattr(client, 'creds_info')
    assert client.creds_info["type"] == "service_account"
    
    await client.initialize()
    mock_credentials.assert_called_once_with(SAMPLE_CREDS, scopes=SCOPES)

@pytest.mark.asyncio
async def test_credential_priority(tmp_path, mock_credentials):
    """Test that base64 credentials take priority over file path."""
    # Create a credentials file
    creds_file = tmp_path / "credentials.json"
    with open(creds_file, "w") as f:
        json.dump(SAMPLE_CREDS, f)
    
    # Set both environment variables
    os.environ["GOOGLE_SHEETS_CREDENTIALS_PATH"] = str(creds_file)
    os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"] = json.dumps(SAMPLE_CREDS)
    
    # Create client
    client = GoogleSheetsClient()
    
    # Verify it used the JSON credentials
    assert hasattr(client, 'creds_info')
    assert not hasattr(client, 'creds_path')
    
    await client.initialize()
    mock_credentials.assert_called_once_with(SAMPLE_CREDS, scopes=SCOPES)

@pytest.fixture(autouse=True)
def mock_env_credentials(monkeypatch):
    """Mock environment credentials for tests."""
    mock_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDFuHJJHAZ+Q0qE\nPOgOb4z+0w2qZpB5wF0+UBzX7Jq4EU5hVegSqzYEBfzqHo5wQEQUZoQOXA0JQhM6\nv4KqrUHQmZtL6QFEHm+n0LsRxwbYwPUE1g9YjOJyqGRqtJF7NXqLZZEgBOxZLJXU\nw/UHvj/vlvGBUZVHlvVgrIqbGQpUBCBh0aBdHhyp6c3NNyGEJz5sJTDUQJEK2FaF\nIJOCLw4L3Kpz0XkRZz1RtYtCGz1POr0p6JJQ7gGwQA9qJE2HnWKV4qGJ3YC7EJH6\nZpYh4QK5WkK1dUJHH3Z8QFxqDR4XxzZJ0SYf9KL3xhvq5C2jQ5UvV1gD0QQZQWOy\nAgMBAAECggEABLURDWVv7CAqL5XmKYeJJHaVW8+HcH4QGj6nXv+4rP7dZK9rGSVr\nX9sZ6j1B6yh/9P6gKkm5QDX+FjbRPQH5xKFVRFH8qG6IqpQGY/o5aNZQ5vTP9nLP\nZH5kZo8Mu7QE8TBxFO+/Hs72FqQOh7dGo1kX8Ir5vAqsqvqCjH8bC6WqcYC0Qg8I\nQE5kHuHGQH5HJWLxEqQf9gYyYNK5cP8hEXEps/p+7CYVlGZQX8D1qZqHrwKpvYOm\nYg1V/9LjVQzBEqKzHXGPQVpvvCXO4UZHNjkPJLm6HpNBvZMH1/l4ckJLSf0vEVwC\nJZMLENPZQkBuKPUv3oGMEQKBgQDFuHJJHAZ+Q0qEPOgOb4z+0w2qZpB5wF0+UBzX\n7Jq4EU5hVegSqzYEBfzqHo5wQEQUZoQOXA0JQhM6v4KqrUHQmZtL6QFEHm+n0LsR\nxwbYwPUE1g9YjOJyqGRqtJF7NXqLZZEgBOxZLJXUw/UHvj/vlvGBUZVHlvVgrIqb\nGQpUBCBh0aBdHhyp6c3NNyGEJz5sJTDUQJEK2FaFIJOCLw4L3Kpz0XkRZz1RtYtC\nGz1POr0p6JJQ7gGwQA9qJE2HnWKV4qGJ3YC7EJH6ZpYh4QK5WkK1dUJHH3Z8QFxq\nDR4XxzZJ0SYf9KL3xhvq5C2jQ5UvV1gD0QQZQWOy",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    # Base64 encode the credentials
    creds_json = json.dumps(mock_creds)
    b64_creds = base64.b64encode(creds_json.encode()).decode()
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", f"data:application/json;base64,{b64_creds}") 