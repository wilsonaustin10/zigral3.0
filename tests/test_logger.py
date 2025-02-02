import os
import pytest
from pathlib import Path
from orchestrator.logger import get_logger
from context_manager.logger import get_logger as get_cm_logger

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Clean up log files after each test"""
    yield
    log_files = [
        "logs/zigral.log",
        "logs/error.log",
        "logs/context_manager.log",
        "logs/context_manager_error.log"
    ]
    for log_file in log_files:
        if os.path.exists(log_file):
            os.remove(log_file)

def test_orchestrator_logger_creation():
    """Test creating an orchestrator logger"""
    logger = get_logger("test_module")
    assert logger is not None
    assert logger._core.extra["name"] == "test_module"

def test_context_manager_logger_creation():
    """Test creating a context manager logger"""
    logger = get_cm_logger("test_module")
    assert logger is not None
    assert logger._core.extra["name"] == "test_module"

def test_log_file_creation():
    """Test that log files are created"""
    logger = get_logger("test_module")
    logger.info("Test info message")
    logger.error("Test error message")
    
    # Check that log files exist
    assert os.path.exists("logs/zigral.log")
    assert os.path.exists("logs/error.log")
    
    # Check file contents
    with open("logs/zigral.log", "r") as f:
        content = f.read()
        assert "Test info message" in content
    
    with open("logs/error.log", "r") as f:
        content = f.read()
        assert "Test error message" in content

def test_context_manager_log_file_creation():
    """Test that context manager log files are created"""
    logger = get_cm_logger("test_module")
    logger.info("Test info message")
    logger.error("Test error message")
    
    # Check that log files exist
    assert os.path.exists("logs/context_manager.log")
    assert os.path.exists("logs/context_manager_error.log")
    
    # Check file contents
    with open("logs/context_manager.log", "r") as f:
        content = f.read()
        assert "Test info message" in content
    
    with open("logs/context_manager_error.log", "r") as f:
        content = f.read()
        assert "Test error message" in content

def test_log_level_from_env(monkeypatch):
    """Test that log level is correctly set from environment variable"""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logger = get_logger("test_module")
    
    # Create a test log file
    log_file = "logs/test.log"
    logger.add(log_file, level="DEBUG")
    
    # Log messages at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    
    with open(log_file, "r") as f:
        content = f.read()
        assert "Debug message" in content
        assert "Info message" in content
    
    os.remove(log_file) 