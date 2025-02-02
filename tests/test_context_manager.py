import pytest
from httpx import AsyncClient
from context_manager.models import ContextEntryDB

pytestmark = pytest.mark.asyncio

# Happy Path Tests
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

# Error Cases
async def test_create_context_invalid_data(context_manager_client: AsyncClient):
    """Test creating a context entry with invalid data"""
    # Missing required fields
    invalid_entry = {
        "job_type": "prospecting"  # Missing job_id and context_data
    }
    response = await context_manager_client.post("/context", json=invalid_entry)
    assert response.status_code == 422  # Validation error
    
    # Invalid job_type
    invalid_entry = {
        "job_id": "test_123",
        "job_type": "",  # Empty string
        "context_data": {}
    }
    response = await context_manager_client.post("/context", json=invalid_entry)
    assert response.status_code == 422

async def test_get_nonexistent_context(context_manager_client: AsyncClient):
    """Test retrieving a non-existent context entry"""
    response = await context_manager_client.get("/context/nonexistent_job")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

async def test_update_nonexistent_context(context_manager_client: AsyncClient):
    """Test updating a non-existent context entry"""
    update_data = {
        "job_id": "nonexistent_job",
        "job_type": "prospecting",
        "context_data": {}
    }
    response = await context_manager_client.put("/context/nonexistent_job", json=update_data)
    assert response.status_code == 404

async def test_update_context_mismatched_id(context_manager_client: AsyncClient, test_context_entry):
    """Test updating a context entry with mismatched IDs"""
    # First create a context entry
    await context_manager_client.post("/context", json=test_context_entry)
    
    # Try to update with mismatched ID
    update_data = test_context_entry.copy()
    update_data["job_id"] = "different_id"
    response = await context_manager_client.put(
        f"/context/{test_context_entry['job_id']}",
        json=update_data
    )
    assert response.status_code == 400  # Bad request

async def test_delete_nonexistent_context(context_manager_client: AsyncClient):
    """Test deleting a non-existent context entry"""
    response = await context_manager_client.delete("/context/nonexistent_job")
    assert response.status_code == 404

# Pagination and Filtering Tests
async def test_list_contexts_pagination(context_manager_client: AsyncClient, test_context_entry):
    """Test context listing with pagination"""
    # Create multiple entries
    for i in range(5):
        entry = test_context_entry.copy()
        entry["job_id"] = f"test_job_{i}"
        await context_manager_client.post("/context", json=entry)
    
    # Test default pagination
    response = await context_manager_client.get("/contexts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10  # Default limit
    
    # Test custom limit
    response = await context_manager_client.get("/contexts?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Test skip parameter
    response = await context_manager_client.get("/contexts?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["job_id"] != "test_job_0"  # First two entries should be skipped

async def test_list_contexts_invalid_pagination(context_manager_client: AsyncClient):
    """Test listing contexts with invalid pagination parameters"""
    # Test negative skip
    response = await context_manager_client.get("/contexts?skip=-1")
    assert response.status_code == 422
    
    # Test negative limit
    response = await context_manager_client.get("/contexts?limit=-1")
    assert response.status_code == 422
    
    # Test limit exceeding maximum
    response = await context_manager_client.get("/contexts?limit=101")
    assert response.status_code == 422

# Health Check Test
async def test_health_check(context_manager_client: AsyncClient):
    """Test health check endpoint"""
    response = await context_manager_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "context-manager"
    assert "version" in data 