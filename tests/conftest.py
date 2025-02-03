"""Test configuration and fixtures."""
import os
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from tortoise import Tortoise
from context_manager.main import app as context_app
from orchestrator.orchestrator import app as orchestrator_app
from context_manager.database import TORTOISE_ORM
from context_manager.models import ContextEntryDB


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Initialize test database."""
    config = {
        "connections": {"default": "sqlite://:memory:"},
        "apps": {
            "models": {
                "models": ["context_manager.models"],
                "default_connection": "default",
            }
        },
    }
    await Tortoise.init(config=config)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def context_client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Get a test client for the context manager API."""
    async with AsyncClient(app=context_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def orchestrator_client() -> AsyncGenerator[AsyncClient, None]:
    """Get a test client for the orchestrator API."""
    async with AsyncClient(app=orchestrator_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client for testing."""
    mock_client = mocker.Mock()
    mock_chat = mocker.AsyncMock()
    mock_chat.choices = [
        mocker.Mock(
            message=mocker.Mock(
                content="""1. Research companies
2. Prepare outreach messages"""
            )
        )
    ]
    mock_client.chat.completions.create = mocker.AsyncMock(return_value=mock_chat)
    return mock_client


@pytest.fixture
def test_context_entry():
    """Sample context entry for testing."""
    return {
        "job_id": "test_123",
        "job_type": "prospecting",
        "context_data": {
            "status": "initialized",
            "search_criteria": {"industry": "technology", "location": "San Francisco"},
        },
    }
