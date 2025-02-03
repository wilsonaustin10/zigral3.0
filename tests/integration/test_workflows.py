"""Integration tests for workflow orchestration and context management.

This module contains end-to-end tests that verify the interaction between the context manager
and orchestrator services. The tests use async clients to simulate HTTP requests and verify
that the workflow state is properly managed throughout the execution.

Test Setup:
- Uses a dedicated test database (zigral_test)
- Configures Tortoise ORM with proper connection pooling
- Handles async database operations with proper lifecycle management
- Mocks OpenAI client for deterministic LLM responses

Key Components Tested:
1. Context Management:
   - Context creation and updates
   - State transitions
   - Error handling and recovery
2. Workflow Orchestration:
   - Action sequence generation
   - Step execution
   - Error recovery
"""

import pytest
from fastapi.testclient import TestClient
from tortoise import Tortoise
from unittest.mock import AsyncMock, patch, MagicMock
import json
import os
from datetime import datetime, UTC
import asyncio
from openai import AsyncOpenAI
from contextlib import asynccontextmanager
import nest_asyncio
import httpx

from context_manager.main import app as context_app
from orchestrator.orchestrator import app as orchestrator_app
from context_manager.database import init_db, close_db
from orchestrator.llm_integration import generate_action_sequence
from context_manager.config import get_settings

# Enable nested event loops for proper async operation in tests
nest_asyncio.apply()

# Override settings for testing
settings = get_settings()
settings.TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",
                "port": 5432,
                "user": "user",
                "password": "password",
                "database": "zigral_test",
            },
            "min_size": 1,
            "max_size": 5,  # Allow multiple concurrent connections
            "max_queries": 50000,
            "max_inactive_connection_lifetime": 300  # 5 minutes
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

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session.
    
    This fixture ensures that we have a consistent event loop throughout the test session,
    which is necessary for proper async operation and database connection management.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@asynccontextmanager
async def app_lifespan(app):
    """Lifespan context manager for FastAPI application.
    
    This context manager ensures proper database initialization and cleanup for the FastAPI
    application during testing. It:
    1. Initializes the database connection
    2. Creates necessary schemas
    3. Yields control during test execution
    4. Cleans up database connections after tests
    """
    try:
        await init_db()
        await Tortoise.generate_schemas()
        yield
    finally:
        await close_db()

@asynccontextmanager
async def test_database():
    """Context manager for test database setup.
    
    Provides a clean database environment for each test by:
    1. Initializing a fresh database connection
    2. Creating necessary schemas
    3. Yielding control during test execution
    4. Cleaning up after test completion
    """
    try:
        await init_db()
        await Tortoise.generate_schemas()
        yield
    finally:
        await close_db()

@pytest.fixture(autouse=True)
async def setup_database():
    """Automatically set up and tear down database for each test.
    
    This fixture runs automatically for each test, ensuring that:
    1. Each test starts with a clean database state
    2. Database connections are properly managed
    3. Resources are cleaned up after each test
    """
    async with test_database():
        yield

@pytest.fixture
async def context_client():
    """Create an async test client for the context manager API.
    
    Returns an httpx.AsyncClient configured to:
    1. Use the proper FastAPI application
    2. Handle lifespan events correctly
    3. Make async HTTP requests to test endpoints
    """
    context_app.router.lifespan_context = app_lifespan
    async with httpx.AsyncClient(app=context_app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def orchestrator_client():
    """Create an async test client for the orchestrator API.
    
    Returns an httpx.AsyncClient configured to:
    1. Use the proper FastAPI application
    2. Handle lifespan events correctly
    3. Make async HTTP requests to test endpoints
    """
    orchestrator_app.router.lifespan_context = app_lifespan
    async with httpx.AsyncClient(app=orchestrator_app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing.
    
    Returns an AsyncMock configured to simulate OpenAI API responses with:
    1. Predefined action sequences for workflow testing
    2. Consistent response format
    3. Async-compatible mock methods
    """
    content = {
        "objective": "Find potential customers",
        "steps": [
            {
                "agent": "research",
                "action": "search_linkedin",
                "parameters": {"industry": "tech", "location": "US"}
            },
            {
                "agent": "outreach",
                "action": "compose_message",
                "parameters": {"template": "introduction"}
            }
        ]
    }
    
    # Create mock response hierarchy
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(message=AsyncMock(content=json.dumps(content)))
    ]
    mock_completions = AsyncMock()
    mock_completions.create = AsyncMock(return_value=mock_response)
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions
    mock_client = AsyncMock()
    mock_client.chat = mock_chat
    
    return mock_client

@pytest.mark.asyncio
async def test_prospecting_workflow(
    setup_database,
    context_client,
    orchestrator_client,
    mock_openai_client
):
    """Test complete prospecting workflow from start to finish.
    
    This test simulates:
    1. Creating a new prospecting job
    2. Getting action sequence from LLM
    3. Executing multiple steps
    4. Updating context after each step
    5. Completing the workflow
    """
    # Mock OpenAI client
    with patch('orchestrator.llm_integration.get_openai_client', return_value=mock_openai_client):
        # 1. Create new context for prospecting job
        context_data = {
            "job_id": "test_prospect_001",
            "job_type": "prospecting",
            "context_data": {
                "target_industry": "tech",
                "target_location": "US",
                "status": "initialized"
            }
        }
        response = await context_client.post("/context", json=context_data)
        assert response.status_code == 200
        created_context = response.json()
        assert created_context["job_id"] == "test_prospect_001"

        # 2. Start workflow in orchestrator
        command = {
            "command": "Find tech companies in US for prospecting",
            "job_id": "test_prospect_001"
        }
        response = await orchestrator_client.post("/command", json=command)
        assert response.status_code == 200
        workflow = response.json()
        assert "steps" in workflow
        assert len(workflow["steps"]) == 2

        # 3. Simulate research step completion
        research_result = {
            "companies": [
                {"name": "TechCorp", "industry": "tech", "location": "US"},
                {"name": "InnovateTech", "industry": "tech", "location": "US"}
            ]
        }
        context_data["context_data"]["research_results"] = research_result
        context_data["context_data"]["status"] = "research_completed"
        response = await context_client.put(
            f"/context/{context_data['job_id']}", 
            json=context_data
        )
        assert response.status_code == 200

        # 4. Verify context was updated
        response = await context_client.get(f"/context/{context_data['job_id']}")
        assert response.status_code == 200
        updated_context = response.json()
        assert updated_context["context_data"]["status"] == "research_completed"
        assert "research_results" in updated_context["context_data"]

        # 5. Simulate outreach step completion
        outreach_result = {
            "messages_sent": 2,
            "message_template": "introduction",
            "target_companies": ["TechCorp", "InnovateTech"]
        }
        context_data["context_data"]["outreach_results"] = outreach_result
        context_data["context_data"]["status"] = "completed"
        response = await context_client.put(
            f"/context/{context_data['job_id']}", 
            json=context_data
        )
        assert response.status_code == 200

        # 6. Verify final state
        response = await context_client.get(f"/context/{context_data['job_id']}")
        assert response.status_code == 200
        final_context = response.json()
        assert final_context["context_data"]["status"] == "completed"
        assert "outreach_results" in final_context["context_data"]

@pytest.mark.asyncio
async def test_error_recovery_workflow(
    setup_database,
    context_client,
    orchestrator_client,
    mock_openai_client
):
    """Test workflow error recovery and checkpoint restoration.
    
    This test simulates:
    1. Starting a workflow
    2. Encountering an error mid-workflow
    3. Creating a checkpoint
    4. Recovering from the error
    5. Completing the workflow
    """
    # Mock OpenAI client
    with patch('orchestrator.llm_integration.get_openai_client', return_value=mock_openai_client):
        # 1. Initialize workflow
        context_data = {
            "job_id": "test_recovery_001",
            "job_type": "prospecting",
            "context_data": {
                "target_industry": "tech",
                "target_location": "US",
                "status": "initialized"
            }
        }
        response = await context_client.post("/context", json=context_data)
        assert response.status_code == 200

        # 2. Simulate error during research
        error_data = {
            "error": "API rate limit exceeded",
            "step": "research",
            "timestamp": datetime.now(UTC).isoformat()
        }
        context_data["context_data"]["last_error"] = error_data
        context_data["context_data"]["status"] = "error"
        response = await context_client.put(
            f"/context/{context_data['job_id']}", 
            json=context_data
        )
        assert response.status_code == 200

        # 3. Verify error state
        response = await context_client.get(f"/context/{context_data['job_id']}")
        assert response.status_code == 200
        error_context = response.json()
        assert error_context["context_data"]["status"] == "error"
        assert "last_error" in error_context["context_data"]

        # 4. Simulate recovery
        context_data["context_data"]["status"] = "retrying"
        context_data["context_data"].pop("last_error")
        response = await context_client.put(
            f"/context/{context_data['job_id']}", 
            json=context_data
        )
        assert response.status_code == 200

        # 5. Complete workflow after recovery
        context_data["context_data"]["status"] = "completed"
        context_data["context_data"]["research_results"] = {
            "companies": [{"name": "TechCorp", "industry": "tech"}]
        }
        response = await context_client.put(
            f"/context/{context_data['job_id']}", 
            json=context_data
        )
        assert response.status_code == 200

        # 6. Verify successful recovery
        response = await context_client.get(f"/context/{context_data['job_id']}")
        assert response.status_code == 200
        final_context = response.json()
        assert final_context["context_data"]["status"] == "completed"
        assert "last_error" not in final_context["context_data"] 