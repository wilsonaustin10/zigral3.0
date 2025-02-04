"""Test configuration and fixtures.

This module provides pytest fixtures for testing the Zigral application,
particularly focusing on database and API testing configurations.

Key Fixtures:
1. event_loop: Creates an event loop for async tests
2. initialize_tests: Sets up and tears down the test database
3. client: Creates a synchronous test client
4. context_client: Creates an async test client with proper lifespan management
5. test_context_entry: Provides sample test data
6. reset_tortoise: Manages Tortoise ORM state between tests

Database Management:
- Uses SQLite for testing with connection string format
- Automatically resets database state between tests
- Handles connection lifecycle through FastAPI's lifespan events
- Ensures test isolation through proper connection management

Environment Configuration:
- Sets TESTING=true to enable test mode
- Uses asgi_lifespan for proper FastAPI startup/shutdown event handling
- Configures pytest-asyncio for async test support
"""

import asyncio
from typing import AsyncGenerator
import os

import pytest
from tortoise import Tortoise
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.context_manager.main import app
from src.context_manager.database import init_test_db, TEST_TORTOISE_CONFIG
from asgi_lifespan import LifespanManager

from context_manager.database import init_db, close_db

os.environ["TESTING"] = "true"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def initialize_tests():
    """Initialize test database before each test."""
    await init_test_db()
    yield
    await Tortoise.close_connections()

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
async def context_client():
    """Create an async test client for context manager with lifespan events."""
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

@pytest.fixture
def test_context_entry():
    """Create a test context entry."""
    return {
        "job_id": "test_job_123",
        "job_type": "prospecting",
        "context_data": {
            "search_criteria": {
                "title": "Software Engineer",
                "location": "San Francisco",
                "company": "Tech Corp"
            }
        }
    }

@pytest.fixture(autouse=True)
async def reset_tortoise():
    """Reset Tortoise ORM state between tests.
    
    This fixture ensures that:
    1. Any existing connections are closed
    2. Tortoise's internal state is reset
    3. Each test starts with a clean Tortoise instance
    """
    # Close any existing connections first
    try:
        await Tortoise.close_connections()
    except Exception:
        pass
    
    # Reset Tortoise state
    Tortoise._client_routing = {}
    Tortoise._connections = {}
    Tortoise._inited = False
    Tortoise._db_config = None
    Tortoise._apps = {}
    
    yield
    
    # After the test, close connections
    try:
        await Tortoise.close_connections()
    except Exception:
        pass
