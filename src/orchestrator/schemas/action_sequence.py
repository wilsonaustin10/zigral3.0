"""Action sequence definitions and validation.

This module defines the schema for action sequences used by the orchestrator to coordinate
agent actions. It includes validation rules and type definitions for action steps and sequences.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ActionStep(BaseModel):
    """Model for individual action steps in a sequence."""
    
    agent: str = Field(..., description="The agent that will execute this step (e.g., 'lincoln', 'shaun')")
    action: str = Field(..., description="The action to perform (e.g., 'search', 'update')")
    target: Optional[str] = Field(None, description="The target of the action (e.g., URL, element selector)")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Search or filtering criteria")
    fields: Optional[List[str]] = Field(None, description="Fields to collect or update")
    timeout: int = Field(default=5000, description="Timeout in milliseconds for this step")
    
    model_config = ConfigDict(from_attributes=True)


class ActionSequence(BaseModel):
    """Model for a complete action sequence."""
    
    job_id: str = Field(..., description="Unique identifier for this job")
    objective: str = Field(..., description="High-level description of what this sequence aims to achieve")
    steps: List[ActionStep] = Field(..., description="List of steps to execute in sequence")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this sequence was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When this sequence was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class ActionResult(BaseModel):
    """Model for the result of an executed action step."""
    
    status: Literal["success", "error", "pending"] = Field(..., description="Status of the action execution")
    message: Optional[str] = Field(None, description="Additional information about the result")
    data: Optional[Dict[str, Any]] = Field(None, description="Any data returned by the action")
    error: Optional[str] = Field(None, description="Error message if status is 'error'")
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionResult(BaseModel):
    """Model for the complete execution result of an action sequence."""
    
    job_id: str = Field(..., description="ID of the job this result belongs to")
    objective: str = Field(..., description="Original objective of the sequence")
    steps: List[Dict[str, Any]] = Field(..., description="Results for each step in the sequence")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When execution started")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="When execution completed")
    
    model_config = ConfigDict(from_attributes=True) 