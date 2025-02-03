import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from tortoise import Tortoise
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test")

# Import our applications
from orchestrator.orchestrator import app as orchestrator_app
from context_manager.main import app as context_manager_app
from context_manager.config import get_settings
from context_manager import models

# Get settings with test configuration
settings = get_settings()
TEST_DB_URL = "postgres://user:password@localhost:5432/zigral_test"  # Use PostgreSQL for testing

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def initialize_tests():
    """Initialize test database"""
    # Initialize DB
    await Tortoise.init(
        db_url=None,
        config={
            "connections": {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": "localhost",
                        "port": 5432,
                        "user": "user",
                        "password": "password",
                        "database": "zigral_test",
                    }
                }
            },
            "apps": {
                "context_manager": {
                    "models": ["context_manager.models"],
                    "default_connection": "default",
                }
            },
            "use_tz": False,
            "timezone": "UTC"
        }
    )
    
    # Create schemas
    await Tortoise.generate_schemas()
    
    yield
    
    # Clean up
    await Tortoise.close_connections()

@pytest.fixture
def orchestrator_client() -> Generator:
    """Get test client for orchestrator API"""
    with TestClient(orchestrator_app) as client:
        yield client

@pytest.fixture
async def context_manager_client() -> AsyncGenerator:
    """Get async test client for context manager API"""
    async with AsyncClient(app=context_manager_app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_context_entry():
    """Get a test context entry"""
    return {
        "job_id": "test_job_123",
        "job_type": "prospecting",
        "context_data": {
            "search_criteria": {
                "title": "CTO",
                "location": "San Francisco"
            },
            "last_search_date": "2024-02-02"
        }
    }

@pytest.fixture
def test_command():
    """Get a test command"""
    return {
        "command": "Find CTOs in San Francisco",
        "context": {
            "territory": "San Francisco Bay Area",
            "target_roles": ["CTO", "Chief Technology Officer"]
        }
    } 