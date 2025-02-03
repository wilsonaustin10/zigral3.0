from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional
from datetime import datetime
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

class ContextEntryBase(BaseModel):
    """Base Pydantic model for context entries"""
    job_id: str = Field(..., min_length=1, description="Unique identifier for the job")
    job_type: str = Field(..., min_length=1, description="Type of job (e.g., 'prospecting', 'outreach')")
    context_data: Dict = Field(..., description="Arbitrary context data for the job")

    @field_validator('job_type')
    def validate_job_type(cls, v):
        if not v.strip():
            raise ValueError("job_type cannot be empty")
        return v.strip()

    @field_validator('context_data')
    def validate_context_data(cls, v):
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

    class Config:
        from_attributes = True

class ContextEntryDB(models.Model):
    """Tortoise ORM model for context entries"""
    id = fields.IntField(pk=True)
    job_id = fields.CharField(max_length=255, index=True)
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