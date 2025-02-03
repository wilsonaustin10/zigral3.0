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
   - State transitions (initialized -> research_completed -> completed)
   - Error handling (error -> retrying -> completed)
   - Complete context data replacement during updates
2. Workflow Orchestration:
   - Action sequence generation from LLM
   - Step execution and state tracking
   - Error recovery with proper state management

State Transitions:
1. Normal Flow:
   - initialized: Initial state when context is created
   - research_completed: After research step is done
   - completed: Final state after all steps are done

2. Error Recovery Flow:
   - initialized: Initial state
   - error: When an error occurs (includes error details)
   - retrying: During recovery attempt
   - completed: After successful recovery
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
            "max_inactive_connection_lifetime": 300,  # 5 minutes
        }
    },
    "apps": {
        "context_manager": {
            "models": ["context_manager.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC",
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
        asyncio.set_event_loop(loop)

    yield loop

    # Clean up the loop
    if not loop.is_closed():
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    asyncio.set_event_loop(None)


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


@pytest.mark.asyncio
async def test_database():
    """Test database initialization and cleanup.

    Verifies that:
    1. Database connection can be established
    2. Schemas can be created
    3. Connection can be closed properly
    """
    await init_db()
    await Tortoise.generate_schemas()

    # Verify database is initialized
    connection = Tortoise.get_connection("default")
    assert connection is not None
    assert connection.capabilities.dialect == "postgres"

    # Verify models are registered
    assert "context_manager" in Tortoise.apps
    assert len(Tortoise.apps["context_manager"].keys()) > 0

    await close_db()


@pytest.fixture(autouse=True)
async def setup_database():
    """Automatically set up and tear down database for each test.

    This fixture runs automatically for each test, ensuring that:
    1. Each test starts with a clean database state
    2. Database connections are properly managed
    3. Resources are cleaned up after each test
    """
    await init_db()
    await Tortoise.generate_schemas()
    try:
        yield
    finally:
        await close_db()


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
    async with httpx.AsyncClient(
        app=orchestrator_app, base_url="http://test"
    ) as client:
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
                "parameters": {"industry": "tech", "location": "US"},
            },
            {
                "agent": "outreach",
                "action": "compose_message",
                "parameters": {"template": "introduction"},
            },
        ],
    }

    # Create mock response hierarchy
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content=json.dumps(content)))]
    mock_completions = AsyncMock()
    mock_completions.create = AsyncMock(return_value=mock_response)
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions
    mock_client = AsyncMock()
    mock_client.chat = mock_chat

    return mock_client


@pytest.mark.asyncio
async def test_prospecting_workflow(
    setup_database, context_client, orchestrator_client, mock_openai_client
):
    """Test complete prospecting workflow from start to finish.

    This test verifies the normal workflow execution path with proper state transitions:
    1. Creating a new prospecting job (status: initialized)
    2. Getting action sequence from LLM
    3. Executing research step (status: research_completed)
    4. Executing outreach step (status: completed)
    5. Verifying final state and results

    The test ensures that context updates completely replace the context data,
    maintaining a clean state at each step of the workflow.
    """
    # Mock OpenAI client
    with patch(
        "orchestrator.llm_integration.get_openai_client",
        return_value=mock_openai_client,
    ):
        # 1. Create new context for prospecting job
        context_data = {
            "job_id": "test_prospect_001",
            "job_type": "prospecting",
            "context_data": {
                "target_industry": "tech",
                "target_location": "US",
                "status": "initialized",
            },
        }
        response = await context_client.post("/context", json=context_data)
        assert response.status_code == 200
        created_context = response.json()
        assert created_context["job_id"] == "test_prospect_001"

        # 2. Start workflow in orchestrator
        command = {
            "command": "Find tech companies in US for prospecting",
            "job_id": "test_prospect_001",
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
                {"name": "InnovateTech", "industry": "tech", "location": "US"},
            ]
        }
        update_data = {
            "job_id": "test_prospect_001",
            "job_type": "prospecting",
            "context_data": {
                "target_industry": "tech",
                "target_location": "US",
                "status": "research_completed",
                "research_results": research_result,
            },
        }
        response = await context_client.put(
            f"/context/{update_data['job_id']}", json=update_data
        )
        assert response.status_code == 200

        # 4. Verify context was updated
        response = await context_client.get(f"/context/{update_data['job_id']}")
        assert response.status_code == 200
        updated_context = response.json()
        assert updated_context["context_data"]["status"] == "research_completed"
        assert "research_results" in updated_context["context_data"]

        # 5. Simulate outreach step completion
        outreach_result = {
            "messages_sent": 2,
            "message_template": "introduction",
            "target_companies": ["TechCorp", "InnovateTech"],
        }
        update_data["context_data"]["outreach_results"] = outreach_result
        update_data["context_data"]["status"] = "completed"
        response = await context_client.put(
            f"/context/{update_data['job_id']}", json=update_data
        )
        assert response.status_code == 200

        # 6. Verify final state
        response = await context_client.get(f"/context/{update_data['job_id']}")
        assert response.status_code == 200
        final_context = response.json()
        assert final_context["context_data"]["status"] == "completed"
        assert "outreach_results" in final_context["context_data"]


@pytest.mark.asyncio
async def test_error_recovery_workflow(
    setup_database, context_client, orchestrator_client, mock_openai_client
):
    """Test workflow error recovery and checkpoint restoration.

    This test verifies the error recovery path with proper state transitions:
    1. Starting a workflow (status: initialized)
    2. Encountering an error (status: error, with error details)
    3. Attempting recovery (status: retrying, error details removed)
    4. Completing the workflow (status: completed, with results)

    The test ensures that error states are properly managed and that the context
    can be cleaned up during recovery by completely replacing the context data.
    """
    # Mock OpenAI client
    with patch(
        "orchestrator.llm_integration.get_openai_client",
        return_value=mock_openai_client,
    ):
        # 1. Initialize workflow
        context_data = {
            "job_id": "test_recovery_001",
            "job_type": "prospecting",
            "context_data": {
                "target_industry": "tech",
                "target_location": "US",
                "status": "initialized",
            },
        }
        response = await context_client.post("/context", json=context_data)
        assert response.status_code == 200

        # 2. Simulate error during research
        error_data = {
            "error": "API rate limit exceeded",
            "step": "research",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        update_data = {
            "job_id": "test_recovery_001",
            "job_type": "prospecting",
            "context_data": {
                "target_industry": "tech",
                "target_location": "US",
                "status": "error",
                "last_error": error_data,
            },
        }
        response = await context_client.put(
            f"/context/{update_data['job_id']}", json=update_data
        )
        assert response.status_code == 200

        # 3. Verify error state
        response = await context_client.get(f"/context/{update_data['job_id']}")
        assert response.status_code == 200
        error_context = response.json()
        assert error_context["context_data"]["status"] == "error"
        assert "last_error" in error_context["context_data"]

        # 4. Simulate recovery
        update_data["context_data"]["status"] = "retrying"
        update_data["context_data"].pop("last_error")
        response = await context_client.put(
            f"/context/{update_data['job_id']}", json=update_data
        )
        assert response.status_code == 200

        # 5. Complete workflow after recovery
        update_data["context_data"]["status"] = "completed"
        update_data["context_data"]["research_results"] = {
            "companies": [{"name": "TechCorp", "industry": "tech"}]
        }
        response = await context_client.put(
            f"/context/{update_data['job_id']}", json=update_data
        )
        assert response.status_code == 200

        # 6. Verify successful recovery
        response = await context_client.get(f"/context/{update_data['job_id']}")
        assert response.status_code == 200
        final_context = response.json()
        assert final_context["context_data"]["status"] == "completed"
        assert "last_error" not in final_context["context_data"]
