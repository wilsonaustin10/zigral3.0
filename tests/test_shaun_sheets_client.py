"""
Test suite for the Shaun agent's Google Sheets client.

This module contains tests for verifying the Google Sheets client initialization
and credential handling functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from google.auth.credentials import Credentials
from src.agents.shaun.sheets_client import GoogleSheetsClient


class MockCredentials(Credentials):
    """Mock credentials class for testing."""
    def refresh(self, request):
        pass

    @property
    def expired(self):
        return False

    @property
    def valid(self):
        return True

    @property
    def token(self):
        return "test_token"

    @token.setter
    def token(self, value):
        pass


@pytest.mark.asyncio
async def test_initialize_success(tmp_path):
    """
    Test successful initialization of Google Sheets client with dummy credentials.
    
    This test verifies that the client can initialize with a minimal valid credentials
    file, using a dummy credentials implementation for testing purposes.
    
    Args:
        tmp_path: Pytest fixture providing a temporary directory path
    """
    # Create a valid credentials file with all required fields
    valid_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "test-private-key",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    file_path = tmp_path / "creds.json"
    file_path.write_text(json.dumps(valid_creds))
    
    # Mock the Credentials class
    mock_creds = MockCredentials()
    with patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=mock_creds):
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
    with pytest.raises(ValueError):
        await client.initialize() 