"""
Tests for the Google Sheets client functionality.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from google.oauth2.service_account import Credentials

from src.agents.shaun.sheets_client import GoogleSheetsClient

@pytest.fixture
def mock_credentials():
    """Mock Google OAuth2 credentials."""
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.__module__ = 'google.oauth2.service_account'
    mock_creds.__class__.__name__ = 'Credentials'
    with patch('src.agents.shaun.sheets_client.Credentials') as mock_creds_class:
        mock_creds_class.from_service_account_file.return_value = mock_creds
        yield mock_creds_class

@pytest.fixture
def client():
    """Create a test client instance."""
    return GoogleSheetsClient('test_creds.json')

@pytest.fixture
def mock_gspread():
    """Mock gspread client."""
    with patch('src.agents.shaun.sheets_client.gspread') as mock:
        mock.authorize.return_value = MagicMock()
        yield mock

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
async def test_initialize_success(client, mock_credentials, mock_gspread):
    """Test successful client initialization."""
    await client.initialize()
    assert client.client is not None
    mock_credentials.from_service_account_file.assert_called_once()

@pytest.mark.asyncio
async def test_initialize_missing_creds(client):
    """Test initialization with missing credentials."""
    client.creds_path = 'nonexistent.json'
    with pytest.raises(FileNotFoundError):
        await client.initialize()

@pytest.mark.asyncio
async def test_connect_to_sheet_success(client, mock_credentials, mock_spreadsheet, mock_worksheet):
    """Test successful connection to spreadsheet."""
    await client.initialize()
    await client.connect_to_sheet('test_sheet_id', 'test_worksheet')
    assert client.worksheet is not None

@pytest.mark.asyncio
async def test_connect_to_sheet_not_found(client, mock_credentials, mock_gspread):
    """Test connection to non-existent spreadsheet."""
    await client.initialize()
    mock_gspread.authorize.return_value.open_by_key.side_effect = Exception('Sheet not found')
    with pytest.raises(Exception):
        await client.connect_to_sheet('invalid_id', 'test_worksheet')

@pytest.mark.asyncio
async def test_add_prospects_success(client, mock_credentials, mock_worksheet):
    """Test successful addition of prospects."""
    await client.initialize()
    await client.connect_to_sheet('test_sheet_id', 'test_worksheet')
    
    prospects = [
        {'name': 'John Doe', 'email': 'john@example.com', 'company': 'Test Inc'},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'company': 'Demo Corp'}
    ]
    
    result = await client.add_prospects(prospects)
    assert result['success'] is True
    assert len(result['added']) == 2

@pytest.mark.asyncio
async def test_add_prospects_no_worksheet(client, mock_credentials):
    """Test adding prospects without connecting to worksheet."""
    await client.initialize()
    with pytest.raises(ValueError):
        await client.add_prospects([{'name': 'Test'}])

@pytest.mark.asyncio
async def test_update_prospect_success(client, mock_credentials, mock_worksheet):
    """Test successful prospect update."""
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
    await client.initialize()
    await client.connect_to_sheet('test_sheet_id', 'test_worksheet')
    
    mock_worksheet.find.side_effect = Exception('Cell not found')
    
    result = await client.update_prospect(
        'nonexistent@example.com',
        {'name': 'Test'}
    )
    assert result['success'] is False

@pytest.mark.asyncio
async def test_execute_command_connect(client, mock_credentials):
    """Test execute_command with connect action."""
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
    await client.initialize()
    result = await client.execute_command({
        'action': 'invalid_action'
    })
    assert result['success'] is False 