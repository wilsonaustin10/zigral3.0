"""
Context Manager API

This module provides a FastAPI application for managing context entries with robust validation
and error handling. It implements CRUD operations with proper status codes and error responses.

API Endpoints:
1. POST /context
   - Create new context entry
   - Validates input data structure and content
   - Returns 201 on success, 422 on validation error

2. GET /context/{job_id}
   - Retrieve context entry by job ID
   - Returns 404 if not found
   - Returns 200 with context data on success

3. PUT /context/{job_id}
   - Update existing context entry by completely replacing context data
   - Preserves job_id and job_type while updating context_data
   - Validates input data structure and content
   - Returns 404 if not found, 422 on validation error
   - Example: Updating workflow status from "initialized" to "completed"

4. DELETE /context/{job_id}
   - Delete context entry by job ID
   - Returns 404 if not found
   - Returns 200 on successful deletion

5. GET /contexts
   - List context entries with pagination
   - Query parameters: skip, limit, job_type
   - Returns paginated list of contexts

Error Handling:
- 400: Bad Request (e.g., job ID mismatch)
- 404: Not Found (resource doesn't exist)
- 422: Validation Error (invalid input data)
- 500: Internal Server Error

Validation:
1. Existence Validation: Checks if resources exist before operations
2. Data Validation: Ensures input data meets schema requirements
3. Business Logic Validation: Verifies business rules (e.g., job ID matching)
4. Context Data Validation: Verifies context_data is a valid dictionary

Example Request/Response:
PUT /context/job123
Request:
{
    "context_data": {
        "status": "completed",
        "results": {"key": "value"}
    }
}
Response:
{
    "job_id": "job123",
    "job_type": "analysis",
    "context_data": {
        "status": "completed",
        "results": {"key": "value"}
    }
}

Lifecycle Management:
- Database connections are managed via FastAPI lifespan events
- Automatic initialization on startup
- Proper cleanup on shutdown
"""

from contextlib import asynccontextmanager
from typing import List, Optional
import os

from fastapi import FastAPI, HTTPException, Query

from .config import get_settings
from .crud import (
    create_context,
    delete_context,
    get_context,
    list_contexts,
    update_context,
)
from .database import close_db, init_db
from .logger import get_logger
from .models import ContextEntryCreate, ContextEntryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and cleanup"""
    # Initialize database on startup, using test mode if TESTING env var is set
    if os.getenv("TESTING", "false").lower() == "true":
        await init_db(test_mode=True)
    else:
        await init_db(test_mode=False)
    yield
    # Close database on shutdown
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title="Zigral Context Manager",
    version="1.0.0",
    description=__doc__,
    lifespan=lifespan,
)
logger = get_logger(__name__)
settings = get_settings()


@app.post("/context", response_model=ContextEntryResponse)
async def create_context_entry(context: ContextEntryCreate):
    """Create a new context entry"""
    try:
        return await create_context(context)
    except Exception as e:
        logger.error(f"Error creating context entry: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating context entry: {str(e)}"
        )


@app.get("/context/{job_id}", response_model=ContextEntryResponse)
async def get_context_entry(job_id: str):
    """Get a context entry by job ID"""
    try:
        context_entry = await get_context(job_id)
        if not context_entry:
            raise HTTPException(
                status_code=404, detail=f"Context entry not found for job {job_id}"
            )
        return context_entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving context entry: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving context entry: {str(e)}"
        )


@app.put("/context/{job_id}", response_model=ContextEntryResponse)
async def update_context_entry(job_id: str, context_data: dict):
    """Update a context entry by replacing its context data.

    This endpoint completely replaces the context_data of an existing entry while
    preserving its job_id and job_type. This allows for atomic updates of the
    entire context state, which is crucial for maintaining consistency in workflow
    state transitions.

    Args:
        job_id (str): The ID of the job to update
        context_data (dict): The new context data containing the complete updated state.
            Can be in either format:
            1. {"context_data": {...}} - Direct context data update
            2. {"job_id": "...", "job_type": "...", "context_data": {...}} - Full entry update

    Returns:
        ContextEntryResponse: The updated context entry

    Raises:
        HTTPException:
            - 400: If job ID in URL doesn't match job ID in payload
            - 404: If context entry not found
            - 422: If input validation fails
            - 500: If update operation fails
    """
    try:
        # First check if the context entry exists
        existing_context = await get_context(job_id)
        if not existing_context:
            raise HTTPException(
                status_code=404, detail=f"Context entry not found for job {job_id}"
            )

        # Check for job ID mismatch
        if "job_id" in context_data and context_data["job_id"] != job_id:
            raise HTTPException(
                status_code=400,
                detail=f"Job ID mismatch: URL has '{job_id}' but payload has '{context_data['job_id']}'",
            )

        # Handle both request formats
        actual_context_data = context_data.get("context_data", context_data)
        if "context_data" not in actual_context_data:  # If it's the full entry format
            actual_context_data = {"context_data": actual_context_data}

        # Create update data with new context data
        update_data = {
            "job_id": job_id,
            "job_type": context_data.get("job_type", existing_context.job_type),
            "context_data": actual_context_data["context_data"],
        }

        # Validate the update data
        try:
            context = ContextEntryCreate(**update_data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Update the context entry
        context_entry = await update_context(job_id, context)
        if not context_entry:
            # This should never happen since we checked existence above
            raise HTTPException(
                status_code=500, detail=f"Error updating context entry for job {job_id}"
            )
        return context_entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context entry: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating context entry: {str(e)}"
        )


@app.delete("/context/{job_id}")
async def delete_context_entry(job_id: str):
    """Delete a context entry"""
    try:
        deleted = await delete_context(job_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Context entry not found for job {job_id}"
            )
        return {"message": f"Context entry for job {job_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting context entry: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting context entry: {str(e)}"
        )


@app.get("/contexts", response_model=List[ContextEntryResponse])
async def list_context_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    job_type: Optional[str] = None,
):
    """List context entries with pagination"""
    try:
        return await list_contexts(skip, limit, job_type)
    except Exception as e:
        logger.error(f"Error listing context entries: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error listing context entries: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
    }
