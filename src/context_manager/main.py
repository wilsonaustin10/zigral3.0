"""
Context Manager API

This module provides a FastAPI application for managing context entries with robust validation
and error handling. It implements CRUD operations with proper status codes and error responses.

Error Handling:
- 400: Bad Request (e.g., job ID mismatch)
- 404: Not Found (resource doesn't exist)
- 422: Validation Error (invalid input data)
- 500: Internal Server Error

Validation:
1. Existence Validation: Checks if resources exist before operations
2. Data Validation: Ensures input data meets schema requirements
3. Business Logic Validation: Verifies business rules (e.g., job ID matching)

Example Error Responses:
{
    "detail": "Context entry not found for job example_job"
}
{
    "detail": "Job ID mismatch: URL has 'job1' but payload has 'job2'"
}
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from .models import ContextEntryCreate, ContextEntryResponse
from .database import init_db, close_db
from .config import get_settings
from .crud import (
    create_context,
    get_context,
    update_context,
    delete_context,
    list_contexts
)
from .logger import get_logger

# Initialize FastAPI app
app = FastAPI(
    title="Zigral Context Manager",
    version="1.0.0",
    description=__doc__
)
logger = get_logger(__name__)
settings = get_settings()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_db()

@app.post("/context", response_model=ContextEntryResponse)
async def create_context_entry(context: ContextEntryCreate):
    """Create a new context entry"""
    try:
        return await create_context(context)
    except Exception as e:
        logger.error(f"Error creating context entry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating context entry: {str(e)}"
        )

@app.get("/context/{job_id}", response_model=ContextEntryResponse)
async def get_context_entry(job_id: str):
    """Get a context entry by job ID"""
    try:
        context_entry = await get_context(job_id)
        if not context_entry:
            raise HTTPException(
                status_code=404,
                detail=f"Context entry not found for job {job_id}"
            )
        return context_entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving context entry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving context entry: {str(e)}"
        )

@app.put("/context/{job_id}", response_model=ContextEntryResponse)
async def update_context_entry(job_id: str, context_data: dict):
    """Update a context entry"""
    try:
        # First check if the context entry exists
        existing_context = await get_context(job_id)
        if not existing_context:
            raise HTTPException(
                status_code=404,
                detail=f"Context entry not found for job {job_id}"
            )

        # Validate the update data
        try:
            context = ContextEntryCreate(**context_data)
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=str(e)
            )

        # Check for job ID mismatch
        if job_id != context.job_id:
            raise HTTPException(
                status_code=400,
                detail=f"Job ID mismatch: URL has '{job_id}' but payload has '{context.job_id}'"
            )

        # Update the context entry
        context_entry = await update_context(job_id, context)
        if not context_entry:
            # This should never happen since we checked existence above
            raise HTTPException(
                status_code=500,
                detail=f"Error updating context entry for job {job_id}"
            )
        return context_entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context entry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating context entry: {str(e)}"
        )

@app.delete("/context/{job_id}")
async def delete_context_entry(job_id: str):
    """Delete a context entry"""
    try:
        deleted = await delete_context(job_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Context entry not found for job {job_id}"
            )
        return {"message": f"Context entry for job {job_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting context entry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting context entry: {str(e)}"
        )

@app.get("/contexts", response_model=List[ContextEntryResponse])
async def list_context_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    job_type: Optional[str] = None
):
    """List context entries with pagination"""
    try:
        return await list_contexts(skip, limit, job_type)
    except Exception as e:
        logger.error(f"Error listing context entries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing context entries: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION
    } 