"""Tests for checkpoint functionality."""

import json
import os

import pytest

from orchestrator.checkpoint import CheckpointManager

@pytest.fixture
def checkpoint_manager(tmp_path):
    """Create a checkpoint manager instance for testing."""
    return CheckpointManager(checkpoint_dir=str(tmp_path))

@pytest.fixture
def test_state():
    """Create a test state for checkpointing."""
    return {
        "job_id": "test_123",
        "current_step": 1,
        "total_steps": 3,
        "status": "in_progress",
    }

def test_checkpoint_directory_creation(tmp_path):
    """Test that the checkpoint directory is created."""
    checkpoint_dir = os.path.join(str(tmp_path), "checkpoints")
    CheckpointManager(checkpoint_dir=checkpoint_dir)
    assert os.path.exists(checkpoint_dir)
    assert os.path.isdir(checkpoint_dir)

def test_create_checkpoint(checkpoint_manager, test_state):
    """Test creating a checkpoint."""
    job_id = test_state["job_id"]
    checkpoint_path = checkpoint_manager.create_checkpoint(job_id, test_state)

    assert os.path.exists(checkpoint_path)
    with open(checkpoint_path, "r") as f:
        saved_state = json.load(f)
    assert saved_state["job_id"] == test_state["job_id"]
    assert saved_state["state"] == test_state
    assert "timestamp" in saved_state

def test_load_checkpoint(checkpoint_manager, test_state):
    """Test loading a checkpoint."""
    job_id = test_state["job_id"]
    checkpoint_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    
    loaded_data = checkpoint_manager.load_checkpoint(job_id)
    assert loaded_data["state"] == test_state

def test_load_nonexistent_checkpoint(checkpoint_manager):
    """Test loading a checkpoint that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        checkpoint_manager.load_checkpoint("nonexistent_job")

def test_load_specific_checkpoint(checkpoint_manager, test_state):
    """Test loading a specific checkpoint."""
    job_id = test_state["job_id"]
    checkpoint_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    checkpoint_name = os.path.basename(checkpoint_path)
    timestamp = checkpoint_name.replace(f"{job_id}_", "").replace(".json", "")

    loaded_data = checkpoint_manager.load_checkpoint(job_id, timestamp)
    assert loaded_data["job_id"] == test_state["job_id"]
    assert loaded_data["state"] == test_state
    assert "timestamp" in loaded_data

def test_list_checkpoints(checkpoint_manager, test_state):
    """Test listing checkpoints for a job."""
    job_id = test_state["job_id"]
    checkpoint_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    checkpoint_name = os.path.basename(checkpoint_path)

    checkpoints = checkpoint_manager.list_checkpoints(job_id)
    assert len(checkpoints) == 1
    assert checkpoint_name in checkpoints

def test_multiple_checkpoints_same_job(checkpoint_manager, test_state):
    """Test creating multiple checkpoints for the same job."""
    job_id = test_state["job_id"]
    first_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    
    # Create a modified state
    modified_state = test_state.copy()
    modified_state["current_step"] = 2
    checkpoint_manager.create_checkpoint(job_id, modified_state)
    
    # Load the latest checkpoint
    loaded_data = checkpoint_manager.load_checkpoint(job_id)
    assert loaded_data["state"]["current_step"] == modified_state["current_step"]
