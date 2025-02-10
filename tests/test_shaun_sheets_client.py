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
    # Create a valid credentials file with all required fields
    valid_creds = {
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