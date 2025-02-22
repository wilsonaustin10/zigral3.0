"""Tests for action sequence schema models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from orchestrator.schemas.action_sequence import (
    ActionStep,
    ActionSequence,
    ActionResult,
    ExecutionResult
)


def test_action_step_creation():
    """Test creating a valid ActionStep."""
    step = ActionStep(
        agent="lincoln",
        action="search",
        target="https://linkedin.com",
        criteria={"keywords": ["CTO", "tech"]},
        fields=["name", "company"]
    )
    
    assert step.agent == "lincoln"
    assert step.action == "search"
    assert step.target == "https://linkedin.com"
    assert step.criteria == {"keywords": ["CTO", "tech"]}
    assert step.fields == ["name", "company"]
    assert step.timeout == 5000  # default value


def test_action_step_validation():
    """Test validation of required fields in ActionStep."""
    with pytest.raises(ValidationError) as exc_info:
        ActionStep()  # Missing required fields
    
    errors = exc_info.value.errors()
    assert len(errors) == 2  # agent and action are required
    assert any(error["loc"] == ("agent",) for error in errors)
    assert any(error["loc"] == ("action",) for error in errors)


def test_action_sequence_creation():
    """Test creating a valid ActionSequence."""
    sequence = ActionSequence(
        job_id="test-job-123",
        objective="Find tech CTOs",
        steps=[
            ActionStep(
                agent="lincoln",
                action="search",
                criteria={"keywords": ["CTO", "tech"]}
            )
        ]
    )
    
    assert sequence.job_id == "test-job-123"
    assert sequence.objective == "Find tech CTOs"
    assert len(sequence.steps) == 1
    assert isinstance(sequence.created_at, datetime)
    assert isinstance(sequence.updated_at, datetime)


def test_action_result_creation():
    """Test creating different types of ActionResult."""
    # Success result
    success_result = ActionResult(
        status="success",
        message="Profile found",
        data={"name": "John Doe", "title": "CTO"}
    )
    assert success_result.status == "success"
    assert success_result.message == "Profile found"
    assert success_result.data == {"name": "John Doe", "title": "CTO"}
    
    # Error result
    error_result = ActionResult(
        status="error",
        error="Profile not found",
        message="Failed to locate profile"
    )
    assert error_result.status == "error"
    assert error_result.error == "Profile not found"
    
    # Pending result
    pending_result = ActionResult(status="pending")
    assert pending_result.status == "pending"


def test_action_result_validation():
    """Test validation of ActionResult status field."""
    with pytest.raises(ValidationError) as exc_info:
        ActionResult(status="invalid")  # Invalid status
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "literal_error"


def test_execution_result_creation():
    """Test creating a valid ExecutionResult."""
    result = ExecutionResult(
        job_id="test-job-123",
        objective="Find tech CTOs",
        steps=[
            {
                "step": {
                    "agent": "lincoln",
                    "action": "search"
                },
                "result": {
                    "status": "success",
                    "data": {"profiles": ["John Doe"]}
                }
            }
        ]
    )
    
    assert result.job_id == "test-job-123"
    assert result.objective == "Find tech CTOs"
    assert len(result.steps) == 1
    assert isinstance(result.started_at, datetime)
    assert isinstance(result.completed_at, datetime) 