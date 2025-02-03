"""Integration tests for workflow orchestration and context management.

This module contains end-to-end tests that verify the interaction between the context manager
and orchestrator services. The tests use async clients to simulate HTTP requests and verify
that the workflow state is properly managed throughout the execution.

Test Setup:
- Uses an in-memory SQLite database for testing
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
   - Command validation and processing

Command Payload Structure:
1. Context Creation:
   {
       "job_id": str,
       "job_type": str,
       "context_data": {
           "target_industry": str,
           "target_location": str,
           "status": str,
           ...
       }
   }

2. Command Request:
   {
       "command": str,
       "context": {
           "job_id": str,
           "target_industry": str,
           "target_location": str,
           ...additional fields...
       }
   }

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
from httpx import AsyncClient
from typing import AsyncGenerator

from context_manager.main import app as context_app
from orchestrator.orchestrator import app as orchestrator_app
from context_manager.models import ContextEntryDB


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
        await Tortoise.close_connections()


async def init_db():
    """Initialize test database with SQLite."""
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

    # Execute query and await the result
    result = await connection.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row[0] for row in result[1]]
    assert "context_entries" in tables

    # Verify models are registered
    assert "models" in Tortoise.apps
    assert ContextEntryDB in Tortoise.apps["models"].values()

    # Clean up
    await Tortoise.close_connections()


@pytest.fixture
async def context_client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Get a test client for the context manager API."""
    context_app.router.lifespan_context = app_lifespan
    async with AsyncClient(app=context_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def orchestrator_client() -> AsyncGenerator[AsyncClient, None]:
    """Get a test client for the orchestrator API."""
    async with AsyncClient(app=orchestrator_app, base_url="http://test") as client:
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
        data = response.json()
        assert data["job_id"] == context_data["job_id"]
        assert data["context_data"]["status"] == "initialized"

        # 2. Get action sequence from LLM
        response = await orchestrator_client.post(
            "/command",
            json={
                "command": "research tech companies in US",
                "context": {
                    "job_id": context_data["job_id"],
                    "target_industry": "tech",
                    "target_location": "US",
                    "status": "initialized",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "objective" in data
        assert "steps" in data
        assert len(data["steps"]) > 0

        # 3. Execute research step
        research_update = {
            "context_data": {
                "status": "research_completed",
                "target_industry": "tech",
                "target_location": "US",
                "research_results": data["steps"],
            }
        }
        response = await context_client.put(
            f"/context/{context_data['job_id']}", json=research_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context_data"]["status"] == "research_completed"

        # 4. Execute outreach step
        response = await orchestrator_client.post(
            "/command",
            json={
                "command": "prepare outreach messages",
                "context": {
                    "job_id": context_data["job_id"],
                    "target_industry": "tech",
                    "target_location": "US",
                    "research_results": json.dumps(
                        data["context_data"]["research_results"]
                    ),
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "objective" in data
        assert "steps" in data

        # 5. Update context with completion
        completion_update = {
            "context_data": {
                "status": "completed",
                "target_industry": "tech",
                "target_location": "US",
                "research_results": data["steps"],
                "outreach_messages": data["steps"],
            }
        }
        response = await context_client.put(
            f"/context/{context_data['job_id']}", json=completion_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context_data"]["status"] == "completed"


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
        data = response.json()
        assert data["job_id"] == context_data["job_id"]
        assert data["context_data"]["status"] == "initialized"

        # 2. Simulate error during execution
        error_update = {
            "job_id": context_data["job_id"],
            "job_type": "prospecting",
            "context_data": {
                "status": "error",
                "error": "API rate limit exceeded",
                "error_timestamp": datetime.now(UTC).isoformat(),
            },
        }
        response = await context_client.put(
            f"/context/{context_data['job_id']}", json=error_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context_data"]["status"] == "error"
        assert "error" in data["context_data"]

        # 3. Attempt recovery
        retry_update = {
            "job_id": context_data["job_id"],
            "job_type": "prospecting",
            "context_data": {
                "status": "retrying",
                "target_industry": "tech",
                "target_location": "US",
            },
        }
        response = await context_client.put(
            f"/context/{context_data['job_id']}", json=retry_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context_data"]["status"] == "retrying"
        assert "error" not in data["context_data"]

        # 4. Complete workflow after recovery
        completion_update = {
            "job_id": context_data["job_id"],
            "job_type": "prospecting",
            "context_data": {
                "status": "completed",
                "target_industry": "tech",
                "target_location": "US",
                "results": ["Company A", "Company B"],
            },
        }
        response = await context_client.put(
            f"/context/{context_data['job_id']}", json=completion_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context_data"]["status"] == "completed"
        assert "results" in data["context_data"]
