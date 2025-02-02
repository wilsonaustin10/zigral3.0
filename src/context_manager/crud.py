from typing import List, Optional
from .models import ContextEntryDB, ContextEntryCreate
from .logger import get_logger

logger = get_logger(__name__)

async def create_context(context: ContextEntryCreate) -> ContextEntryDB:
    """
    Create a new context entry
    
    Args:
        context (ContextEntryCreate): Context entry to create
        
    Returns:
        ContextEntryDB: Created context entry
    """
    try:
        context_entry = await ContextEntryDB.create(**context.model_dump())
        logger.info(f"Created context entry for job {context.job_id}")
        return context_entry
    except Exception as e:
        logger.error(f"Error creating context entry: {str(e)}")
        raise

async def get_context(job_id: str) -> Optional[ContextEntryDB]:
    """
    Get context entry by job ID
    
    Args:
        job_id (str): Job ID to get context for
        
    Returns:
        Optional[ContextEntryDB]: Context entry if found, None otherwise
    """
    try:
        context_entry = await ContextEntryDB.filter(job_id=job_id).first()
        if context_entry:
            logger.info(f"Retrieved context entry for job {job_id}")
        else:
            logger.info(f"No context entry found for job {job_id}")
        return context_entry
    except Exception as e:
        logger.error(f"Error retrieving context entry: {str(e)}")
        raise

async def update_context(job_id: str, context: ContextEntryCreate) -> Optional[ContextEntryDB]:
    """
    Update an existing context entry
    
    Args:
        job_id (str): Job ID to update context for
        context (ContextEntryCreate): New context data
        
    Returns:
        Optional[ContextEntryDB]: Updated context entry if found, None otherwise
    """
    try:
        context_entry = await ContextEntryDB.filter(job_id=job_id).first()
        if not context_entry:
            logger.info(f"No context entry found for job {job_id}")
            return None
            
        await context_entry.update_from_dict(context.model_dump()).save()
        logger.info(f"Updated context entry for job {job_id}")
        return context_entry
    except Exception as e:
        logger.error(f"Error updating context entry: {str(e)}")
        raise

async def delete_context(job_id: str) -> bool:
    """
    Delete a context entry
    
    Args:
        job_id (str): Job ID to delete context for
        
    Returns:
        bool: True if deleted, False if not found
    """
    try:
        deleted_count = await ContextEntryDB.filter(job_id=job_id).delete()
        if deleted_count:
            logger.info(f"Deleted context entry for job {job_id}")
            return True
        logger.info(f"No context entry found for job {job_id}")
        return False
    except Exception as e:
        logger.error(f"Error deleting context entry: {str(e)}")
        raise

async def list_contexts(
    skip: int = 0,
    limit: int = 10,
    job_type: Optional[str] = None
) -> List[ContextEntryDB]:
    """
    List context entries with pagination
    
    Args:
        skip (int): Number of entries to skip
        limit (int): Maximum number of entries to return
        job_type (Optional[str]): Filter by job type
        
    Returns:
        List[ContextEntryDB]: List of context entries
    """
    try:
        query = ContextEntryDB.all()
        if job_type:
            query = query.filter(job_type=job_type)
            
        contexts = await query.offset(skip).limit(limit)
        logger.info(f"Retrieved {len(contexts)} context entries")
        return contexts
    except Exception as e:
        logger.error(f"Error listing context entries: {str(e)}")
        raise 