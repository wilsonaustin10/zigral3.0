"""LinkedIn Client Test Suite.

This module contains tests for the LinkedIn automation client, verifying its
initialization, authentication, and command execution capabilities.

Test Coverage:
1. Client Initialization
   - Browser initialization
   - Resource cleanup
2. Authentication
   - Successful login with valid credentials
   - Failed login with invalid credentials
3. Command Execution
   - Error handling for unknown commands

Environment Requirements:
- LINKEDIN_USERNAME: LinkedIn account email/username
- LINKEDIN_PASSWORD: LinkedIn account password

Note: All tests are asynchronous and use pytest-asyncio for execution.
The test suite properly handles browser cleanup through fixture teardown.

Example:
    To run these tests:
    ```bash
    pytest tests/test_linkedin_client.py -v
    ```
"""

import os
import pytest
from src.agents.lincoln.linkedin_client import LinkedInClient

# Set correct environment variable
os.environ['LINKEDIN_USERNAME'] = 'test@example.com'
os.environ['LINKEDIN_PASSWORD'] = 'test_password'  # Add password env var


@pytest.fixture
async def linkedin_client():
    """Create a LinkedIn client instance and handle cleanup."""
    client = LinkedInClient()
    await client.initialize()  # Explicitly initialize the client
    yield client
    if client._browser:
        await client.cleanup()


@pytest.mark.asyncio
async def test_initialize(linkedin_client):
    """Test that LinkedInClient initializes with a non-null _browser attribute."""
    assert linkedin_client._browser is not None


@pytest.mark.asyncio
async def test_cleanup(linkedin_client):
    """Test that cleanup properly closes the browser."""
    await linkedin_client.cleanup()
    assert linkedin_client._browser is None


@pytest.mark.asyncio
async def test_login_failure(linkedin_client):
    """Test that login fails when credentials are missing or invalid."""
    # Set invalid credentials
    os.environ['LINKEDIN_USERNAME'] = ''
    os.environ['LINKEDIN_PASSWORD'] = ''
    with pytest.raises(ValueError):
        await linkedin_client.login()


@pytest.mark.asyncio
async def test_login_success(linkedin_client):
    """Test that login succeeds with valid credentials."""
    os.environ['LINKEDIN_USERNAME'] = 'test@example.com'
    os.environ['LINKEDIN_PASSWORD'] = 'test_password'
    result = await linkedin_client.login()
    assert result is True


@pytest.mark.asyncio
async def test_execute_command_unknown_action(linkedin_client):
    """Test that executing an unknown command raises a ValueError."""
    with pytest.raises(ValueError):
        await linkedin_client.execute_command('unknown_action', parameters={}) 