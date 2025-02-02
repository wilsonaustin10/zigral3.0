import pytest
from httpx import AsyncClient
from context_manager.models import ContextEntryDB

pytestmark = pytest.mark.asyncio

async def test_create_context(context_manager_client: AsyncClient, test_context_entry):
    """Test creating a new context entry"""
    response = await context_manager_client.post("/context", json=test_context_entry)
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == test_context_entry["job_id"]
    assert data["job_type"] == test_context_entry["job_type"]
    assert data["context_data"] == test_context_entry["context_data"]

async def test_get_context(context_manager_client: AsyncClient, test_context_entry):
    """Test retrieving a context entry"""
    # First create a context entry
    await context_manager_client.post("/context", json=test_context_entry)
    
    # Then retrieve it
    response = await context_manager_client.get(f"/context/{test_context_entry['job_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == test_context_entry["job_id"]
    assert data["context_data"] == test_context_entry["context_data"]

async def test_get_nonexistent_context(context_manager_client: AsyncClient):
    """Test retrieving a non-existent context entry"""
    response = await context_manager_client.get("/context/nonexistent_job")
    assert response.status_code == 404

async def test_update_context(context_manager_client: AsyncClient, test_context_entry):
    """Test updating a context entry"""
    # First create a context entry
    await context_manager_client.post("/context", json=test_context_entry)
    
    # Update the context
    updated_data = test_context_entry.copy()
    updated_data["context_data"]["search_criteria"]["location"] = "New York"
    
    response = await context_manager_client.put(
        f"/context/{test_context_entry['job_id']}",
        json=updated_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["context_data"]["search_criteria"]["location"] == "New York"

async def test_delete_context(context_manager_client: AsyncClient, test_context_entry):
    """Test deleting a context entry"""
    # First create a context entry
    await context_manager_client.post("/context", json=test_context_entry)
    
    # Delete the entry
    response = await context_manager_client.delete(f"/context/{test_context_entry['job_id']}")
    assert response.status_code == 200
    
    # Verify it's deleted
    response = await context_manager_client.get(f"/context/{test_context_entry['job_id']}")
    assert response.status_code == 404

async def test_list_contexts(context_manager_client: AsyncClient, test_context_entry):
    """Test listing context entries with pagination"""
    # Create multiple context entries
    entries = []
    for i in range(3):
        entry = test_context_entry.copy()
        entry["job_id"] = f"test_job_{i}"
        entries.append(entry)
        await context_manager_client.post("/context", json=entry)
    
    # Test listing with default pagination
    response = await context_manager_client.get("/contexts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    # Test pagination
    response = await context_manager_client.get("/contexts?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

async def test_list_contexts_by_job_type(context_manager_client: AsyncClient, test_context_entry):
    """Test listing context entries filtered by job type"""
    # Create entries with different job types
    entry1 = test_context_entry.copy()
    entry1["job_type"] = "prospecting"
    entry2 = test_context_entry.copy()
    entry2["job_id"] = "test_job_2"
    entry2["job_type"] = "outreach"
    
    await context_manager_client.post("/context", json=entry1)
    await context_manager_client.post("/context", json=entry2)
    
    # Test filtering by job type
    response = await context_manager_client.get("/contexts?job_type=prospecting")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["job_type"] == "prospecting"

async def test_health_check(context_manager_client: AsyncClient):
    """Test health check endpoint"""
    response = await context_manager_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "context-manager" 