import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from orchestrator.checkpoint import CheckpointManager
import time

@pytest.fixture
def checkpoint_manager(tmp_path):
    """Create a checkpoint manager instance with a temporary test directory"""
    # Use pytest's tmp_path fixture for a unique temporary directory
    checkpoint_dir = tmp_path / "test_checkpoints"
    manager = CheckpointManager(str(checkpoint_dir))
    yield manager
    # Cleanup happens automatically as tmp_path is managed by pytest

@pytest.fixture
def test_state():
    """Create a test state"""
    return {
        "current_step": 2,
        "completed_steps": ["step1", "step2"],
        "pending_steps": ["step3", "step4"],
        "results": {
            "step1": {"status": "success", "data": {"key": "value"}},
            "step2": {"status": "success", "data": {"key2": "value2"}}
        }
    }

def test_checkpoint_directory_creation(checkpoint_manager):
    """Test that the checkpoint directory is created"""
    assert os.path.exists(checkpoint_manager.checkpoint_dir)

def test_create_checkpoint(checkpoint_manager, test_state):
    """Test creating a checkpoint"""
    job_id = "test_job_123"
    checkpoint_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    
    assert os.path.exists(checkpoint_path)
    
    # Verify checkpoint content
    with open(checkpoint_path, 'r') as f:
        checkpoint_data = json.load(f)
        assert checkpoint_data["job_id"] == job_id
        assert checkpoint_data["state"] == test_state
        assert "timestamp" in checkpoint_data

def test_load_checkpoint(checkpoint_manager, test_state):
    """Test loading a checkpoint"""
    job_id = "test_job_123"
    checkpoint_manager.create_checkpoint(job_id, test_state)
    
    # Load the checkpoint
    loaded_data = checkpoint_manager.load_checkpoint(job_id)
    
    assert loaded_data["job_id"] == job_id
    assert loaded_data["state"] == test_state

def test_load_nonexistent_checkpoint(checkpoint_manager):
    """Test loading a non-existent checkpoint"""
    with pytest.raises(FileNotFoundError):
        checkpoint_manager.load_checkpoint("nonexistent_job")

def test_load_specific_checkpoint(checkpoint_manager, test_state):
    """Test loading a specific checkpoint by timestamp"""
    job_id = "test_job_123"
    
    # Create first checkpoint with initial state
    first_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    time.sleep(1)  # Ensure unique timestamps
    
    # Create second checkpoint with modified state
    modified_state = test_state.copy()
    modified_state["current_step"] = 3
    second_path = checkpoint_manager.create_checkpoint(job_id, modified_state)
    
    # Extract timestamp from first checkpoint path
    first_timestamp = os.path.basename(first_path).split(f"{job_id}_")[1].replace('.json', '')
    
    # Load and verify first checkpoint
    loaded_data = checkpoint_manager.load_checkpoint(job_id, first_timestamp)
    assert loaded_data["state"]["current_step"] == test_state["current_step"], \
        f"Expected step {test_state['current_step']}, got {loaded_data['state']['current_step']}"
    
    # Verify we can load latest (second) checkpoint
    latest_data = checkpoint_manager.load_checkpoint(job_id)
    assert latest_data["state"]["current_step"] == 3, \
        "Latest checkpoint should have current_step = 3"

def test_list_checkpoints(checkpoint_manager, test_state):
    """Test listing checkpoints"""
    # Create checkpoints for different jobs
    job1 = "test_job_1"
    job2 = "test_job_2"
    
    checkpoint_manager.create_checkpoint(job1, test_state)
    checkpoint_manager.create_checkpoint(job2, test_state)
    
    # List all checkpoints
    all_checkpoints = checkpoint_manager.list_checkpoints()
    assert len(all_checkpoints) == 2
    
    # List checkpoints for specific job
    job1_checkpoints = checkpoint_manager.list_checkpoints(job1)
    assert len(job1_checkpoints) == 1
    assert all(cp.startswith(job1) for cp in job1_checkpoints)

def test_multiple_checkpoints_same_job(checkpoint_manager, test_state):
    """Test creating multiple checkpoints for the same job"""
    job_id = "test_job_123"
    
    # Create multiple checkpoints with different states
    expected_steps = []
    for i in range(3):
        modified_state = test_state.copy()
        modified_state["current_step"] = i
        expected_steps.append(i)
        checkpoint_manager.create_checkpoint(job_id, modified_state)
        time.sleep(1)  # Ensure unique timestamps
    
    # List and verify checkpoints
    checkpoints = checkpoint_manager.list_checkpoints(job_id)
    assert len(checkpoints) == 3, f"Expected 3 checkpoints, got {len(checkpoints)}"
    
    # Load and verify each checkpoint in order
    for idx, checkpoint in enumerate(sorted(checkpoints)):
        timestamp = checkpoint.split(f"{job_id}_")[1].replace('.json', '')
        loaded_data = checkpoint_manager.load_checkpoint(job_id, timestamp)
        assert loaded_data["state"]["current_step"] == expected_steps[idx], \
            f"Checkpoint {idx} should have step {expected_steps[idx]}" 