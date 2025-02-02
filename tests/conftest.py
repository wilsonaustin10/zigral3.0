import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from tortoise.contrib.test import finalizer, initializer

# Import our applications
from orchestrator.orchestrator import app as orchestrator_app
from context_manager.main import app as context_manager_app
from context_manager.config import get_settings

# Override environment variables for testing
os.environ["DATABASE_URL"] = "sqlite://:memory:"
os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["DEBUG"] = "True"

# Get settings with test configuration
settings = get_settings()
TEST_DB_URL = "sqlite://:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def initialize_tests():
    """Initialize test database"""
    initializer(
        modules={"models": ["context_manager.models"]},
        db_url=TEST_DB_URL,
        app_label="context_manager"
    )
    yield
    await finalizer()

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