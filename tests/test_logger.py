import os
import pytest
from pathlib import Path
from src.orchestrator.logger import get_logger as get_orch_logger
from src.context_manager.logger import get_logger as get_cm_logger

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up log files before and after each test"""
    # Clean up before test
    for log_file in Path("logs").glob("*.log"):
        log_file.unlink(missing_ok=True)
    
    yield
    
    # Clean up after test
    for log_file in Path("logs").glob("*.log"):
        log_file.unlink(missing_ok=True)

def test_orchestrator_logger_creation():
    """Test creating an orchestrator logger"""
    logger = get_orch_logger("test_module")
    assert logger is not None
    
    # Test that logging works and includes the module name
    logger.info("Test message")
    
    with open("logs/zigral.log", "r") as f:
        content = f.read()
        assert "test_module" in content
        assert "Test message" in content

def test_context_manager_logger_creation():
    """Test creating a context manager logger"""
    logger = get_cm_logger("test_module")
    assert logger is not None
    
    # Test that logging works and includes the module name
    logger.info("Test message")
    
    with open("logs/zigral.log", "r") as f:
        content = f.read()
        assert "test_module" in content
        assert "Test message" in content

def test_log_file_creation():
    """Test that log files are created"""
    logger = get_orch_logger("test_module")
    logger.info("Test info message")
    logger.error("Test error message")

    # Check that log files exist
    assert os.path.exists("logs/zigral.log")
    assert os.path.exists("logs/error.log")

    # Check file contents
    with open("logs/zigral.log", "r") as f:
        content = f.read()
        assert "Test info message" in content
        assert "test_module" in content

    with open("logs/error.log", "r") as f:
        content = f.read()
        assert "Test error message" in content
        assert "test_module" in content

def test_context_manager_log_file_creation():
    """Test that context manager log files are created"""
    logger = get_cm_logger("test_module")
    logger.info("Test info message")
    logger.error("Test error message")

    # Check that log files exist
    assert os.path.exists("logs/zigral.log")
    assert os.path.exists("logs/error.log")

    # Check file contents
    with open("logs/zigral.log", "r") as f:
        content = f.read()
        assert "Test info message" in content
        assert "test_module" in content

    with open("logs/error.log", "r") as f:
        content = f.read()
        assert "Test error message" in content
        assert "test_module" in content

def test_log_level_from_env(monkeypatch):
    """Test that log level is correctly set from environment variable"""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logger = get_orch_logger("test_module")

    # Log messages at different levels
    logger.debug("Debug message")
    logger.info("Info message")

    with open("logs/zigral.log", "r") as f:
        content = f.read()
        assert "Debug message" in content
        assert "Info message" in content
        assert "test_module" in content 