"""
Context Manager Models

This module defines the data models for the context manager, including Pydantic models
for validation and Tortoise ORM models for persistence.

Validation Rules:
1. Job ID:
   - Required string field
   - Must be non-empty (min_length=1)
   - Used as a unique identifier

2. Job Type:
   - Required string field
   - Must be non-empty and non-whitespace
   - Examples: 'prospecting', 'outreach'

3. Context Data:
   - Required dictionary field
   - Must be non-empty
   - Can contain arbitrary key-value pairs

Database Schema:
- Primary key: Auto-incrementing integer ID
- Indexed fields: job_id (for faster lookups)
- Timestamps: created_at, updated_at (auto-managed)
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Optional
from datetime import datetime
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

class ContextEntryBase(BaseModel):
    """Base Pydantic model for context entries with validation"""
    job_id: str = Field(..., min_length=1, description="Unique identifier for the job")
    job_type: str = Field(..., min_length=1, description="Type of job (e.g., 'prospecting', 'outreach')")
    context_data: Dict = Field(..., description="Arbitrary context data for the job")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('job_type')
    @classmethod
    def validate_job_type(cls, v):
        """Ensure job_type is non-empty and stripped of whitespace"""
        if not v.strip():
            raise ValueError("job_type cannot be empty")
        return v.strip()

    @field_validator('context_data')
    @classmethod
    def validate_context_data(cls, v):
        """Ensure context_data is non-empty"""
        if not v:
            raise ValueError("context_data cannot be empty")
        return v

class ContextEntryCreate(ContextEntryBase):
    """Pydantic model for creating context entries"""
    pass

class ContextEntry(ContextEntryBase):
    """Pydantic model for complete context entries"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ContextEntryDB(models.Model):
    """Tortoise ORM model for context entries"""
    id = fields.IntField(primary_key=True)
    job_id = fields.CharField(max_length=255, db_index=True)
    job_type = fields.CharField(max_length=50)
    context_data = fields.JSONField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "context_entries"

    def __str__(self):
        return f"Context for job {self.job_id} ({self.job_type})"

# Create Pydantic models from Tortoise model
ContextEntryInDB = pydantic_model_creator(
    ContextEntryDB,
    name="ContextEntryInDB",
    exclude=("created_at", "updated_at")
)

ContextEntryResponse = pydantic_model_creator(
    ContextEntryDB,
    name="ContextEntryResponse"
) 