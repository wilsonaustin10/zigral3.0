"""Test Google Sheets functionality with actual credentials."""

import asyncio
from src.agents.shaun.sheets_client import GoogleSheetsClient
import pytest
import json
from unittest.mock import patch, MagicMock
from google.oauth2.service_account import Credentials
import gspread

@pytest.fixture(autouse=True)
def mock_env_credentials(monkeypatch):
    """Mock environment credentials for tests."""
    mock_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDFuHJJHAZ+Q0qE\nPOgOb4z+0w2qZpB5wF0+UBzX7Jq4EU5hVegSqzYEBfzqHo5wQEQUZoQOXA0JQhM6\nv4KqrUHQmZtL6QFEHm+n0LsRxwbYwPUE1g9YjOJyqGRqtJF7NXqLZZEgBOxZLJXU\nw/UHvj/vlvGBUZVHlvVgrIqbGQpUBCBh0aBdHhyp6c3NNyGEJz5sJTDUQJEK2FaF\nIJOCLw4L3Kpz0XkRZz1RtYtCGz1POr0p6JJQ7gGwQA9qJE2HnWKV4qGJ3YC7EJH6\nZpYh4QK5WkK1dUJHH3Z8QFxqDR4XxzZJ0SYf9KL3xhvq5C2jQ5UvV1gD0QQZQWOy\nAgMBAAECggEABLURDWVv7CAqL5XmKYeJJHaVW8+HcH4QGj6nXv+4rP7dZK9rGSVr\nX9sZ6j1B6yh/9P6gKkm5QDX+FjbRPQH5xKFVRFH8qG6IqpQGY/o5aNZQ5vTP9nLP\nZH5kZo8Mu7QE8TBxFO+/Hs72FqQOh7dGo1kX8Ir5vAqsqvqCjH8bC6WqcYC0Qg8I\nQE5kHuHGQH5HJWLxEqQf9gYyYNK5cP8hEXEps/p+7CYVlGZQX8D1qZqHrwKpvYOm\nYg1V/9LjVQzBEqKzHXGPQVpvvCXO4UZHNjkPJLm6HpNBvZMH1/l4ckJLSf0vEVwC\nJZMLENPZQkBuKPUv3oGMEQKBgQDFuHJJHAZ+Q0qEPOgOb4z+0w2qZpB5wF0+UBzX\n7Jq4EU5hVegSqzYEBfzqHo5wQEQUZoQOXA0JQhM6v4KqrUHQmZtL6QFEHm+n0LsR\nxwbYwPUE1g9YjOJyqGRqtJF7NXqLZZEgBOxZLJXUw/UHvj/vlvGBUZVHlvVgrIqb\nGQpUBCBh0aBdHhyp6c3NNyGEJz5sJTDUQJEK2FaFIJOCLw4L3Kpz0XkRZz1RtYtC\nGz1POr0p6JJQ7gGwQA9qJE2HnWKV4qGJ3YC7EJH6ZpYh4QK5WkK1dUJHH3Z8QFxq\nDR4XxzZJ0SYf9KL3xhvq5C2jQ5UvV1gD0QQZQWOyAgMBAAECggEABLURDWVv7CAq\nL5XmKYeJJHaVW8+HcH4QGj6nXv+4rP7dZK9rGSVrX9sZ6j1B6yh/9P6gKkm5QDX+\nFjbRPQH5xKFVRFH8qG6IqpQGY/o5aNZQ5vTP9nLPZH5kZo8Mu7QE8TBxFO+/Hs72\nFqQOh7dGo1kX8Ir5vAqsqvqCjH8bC6WqcYC0Qg8IQE5kHuHGQH5HJWLxEqQf9gYy\nYNK5cP8hEXEps/p+7CYVlGZQX8D1qZqHrwKpvYOmYg1V/9LjVQzBEqKzHXGPQVpv\nvCXO4UZHNjkPJLm6HpNBvZMH1/l4ckJLSf0vEVwCJZMLENPZQkBuKPUv3oGMEQKB\ngQDFuHJJHAZ+Q0qEPOgOb4z+0w2qZpB5wF0+UBzX7Jq4EU5hVegSqzYEBfzqHo5w\nQEQUZoQOXA0JQhM6v4KqrUHQmZtL6QFEHm+n0LsRxwbYwPUE1g9YjOJyqGRqtJF7\nNXqLZZEgBOxZLJXUw/UHvj/vlvGBUZVHlvVgrIqbGQpUBCBh0aBdHhyp6c3NNyGE\nJz5sJTDUQJEK2FaFIJOCLw4L3Kpz0XkRZz1RtYtCGz1POr0p6JJQ7gGwQA9qJE2H\nnWKV4qGJ3YC7EJH6ZpYh4QK5WkK1dUJHH3Z8QFxqDR4XxzZJ0SYf9KL3xhvq5C2j\nQ5UvV1gD0QQZQWOy\n-----END PRIVATE KEY-----",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", json.dumps(mock_creds))

@pytest.mark.asyncio
async def test_sheets_functionality():
    """Test basic Google Sheets operations."""
    with patch("google.oauth2.service_account.Credentials.from_service_account_info") as mock_creds, \
         patch("gspread.authorize") as mock_authorize:
        
        # Create a proper mock Credentials object
        mock_cred_obj = MagicMock(spec=Credentials)
        mock_cred_obj.valid = True
        mock_cred_obj.expired = False
        mock_cred_obj._service_account_email = "test@test-project.iam.gserviceaccount.com"
        mock_cred_obj.project_id = "test-project"
        mock_creds.return_value = mock_cred_obj
        
        # Create mock gspread client
        mock_client = MagicMock()
        mock_authorize.return_value = mock_client
        
        # Create mock spreadsheet and worksheet
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.url = "https://docs.google.com/spreadsheets/d/test_sheet_id"
        mock_spreadsheet.title = "Test Sheet"
        
        mock_worksheet = MagicMock()
        mock_worksheet.title = "Prospects"
        mock_worksheet.get_all_records.return_value = []
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_spreadsheet.worksheets.return_value = [mock_worksheet]
        
        # Set up client methods
        mock_client.create.return_value = mock_spreadsheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        # Initialize the client
        client = GoogleSheetsClient()
        await client.initialize()
        
        # Test basic operations
        assert client.is_initialized
        assert client.client is not None
        
        # Test connecting to a sheet
        spreadsheet, worksheet = await client.connect_to_sheet("test_sheet_id")
        assert spreadsheet.title == "Test Sheet"
        assert worksheet.title == "Prospects"
        
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
        
        result = await client.add_prospects(test_prospects)
        assert result["success"] is True
        assert len(result["added"]) == 1
        
        # Test cleanup
        await client.cleanup()
        assert client.client is None
        assert client.spreadsheet is None
        assert client.worksheet is None 