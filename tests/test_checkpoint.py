import os
import json
import pytest
from pathlib import Path
from orchestrator.checkpoint import CheckpointManager

@pytest.fixture
def checkpoint_manager():
    """Create a checkpoint manager instance with a test directory"""
    manager = CheckpointManager("test_checkpoints")
    yield manager
    # Cleanup after tests
    if os.path.exists("test_checkpoints"):
        for file in os.listdir("test_checkpoints"):
            os.remove(os.path.join("test_checkpoints", file))
        os.rmdir("test_checkpoints")

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
    
    # Create multiple checkpoints
    first_path = checkpoint_manager.create_checkpoint(job_id, test_state)
    first_timestamp = os.path.basename(first_path).split('_', 1)[1].replace('.json', '')
    
    modified_state = test_state.copy()
    modified_state["current_step"] = 3
    checkpoint_manager.create_checkpoint(job_id, modified_state)
    
    # Load specific checkpoint
    loaded_data = checkpoint_manager.load_checkpoint(job_id, first_timestamp)
    assert loaded_data["state"]["current_step"] == 2

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
    states = []
    for i in range(3):
        modified_state = test_state.copy()
        modified_state["current_step"] = i
        states.append(modified_state)
        checkpoint_manager.create_checkpoint(job_id, modified_state)
    
    # List checkpoints
    checkpoints = checkpoint_manager.list_checkpoints(job_id)
    assert len(checkpoints) == 3
    
    # Load latest checkpoint
    latest_data = checkpoint_manager.load_checkpoint(job_id)
    assert latest_data["state"]["current_step"] == 2 