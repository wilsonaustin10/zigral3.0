"""
Test suite for the Shaun agent's Google Sheets client.

This module contains tests for verifying the Google Sheets client initialization
and credential handling functionality.
"""

import pytest
import json
from src.agents.shaun.sheets_client import GoogleSheetsClient


@pytest.mark.asyncio
async def test_initialize_success(tmp_path):
    """
    Test successful initialization of Google Sheets client with dummy credentials.
    
    This test verifies that the client can initialize with a minimal valid credentials
    file, using a dummy credentials implementation for testing purposes.
    
    Args:
        tmp_path: Pytest fixture providing a temporary directory path
    """
    # Create a valid credentials file with dummy private key
    valid_creds = {
        "private_key": "-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----"
    }
    file_path = tmp_path / "creds.json"
    file_path.write_text(json.dumps(valid_creds))
    
    client = GoogleSheetsClient(creds_path=str(file_path))
    await client.initialize()
    assert client.client is not None


@pytest.mark.asyncio
async def test_initialize_file_not_found():
    """
    Test initialization failure when credentials file does not exist.
    
    This test verifies that the client raises an appropriate error when
    the specified credentials file cannot be found.
    """
    # Use a non-existent file path
    non_existent_path = "non_existent_credentials.json"
    client = GoogleSheetsClient(creds_path=non_existent_path)
    with pytest.raises(FileNotFoundError):
        await client.initialize()


@pytest.mark.asyncio
async def test_initialize_invalid_json(tmp_path):
    """
    Test initialization failure with invalid JSON credentials file.
    
    This test verifies that the client raises an appropriate error when
    the credentials file contains invalid JSON data.
    
    Args:
        tmp_path: Pytest fixture providing a temporary directory path
    """
    # Create a file with invalid JSON content
    invalid_file = tmp_path / "invalid_creds.json"
    invalid_file.write_text("invalid json content")
    
    client = GoogleSheetsClient(creds_path=str(invalid_file))
    with pytest.raises(json.JSONDecodeError):
        await client.initialize() 