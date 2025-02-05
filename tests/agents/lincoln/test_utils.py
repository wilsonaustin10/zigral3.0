"""Tests for Lincoln agent utility functions."""

import os
import pytest
from src.agents.lincoln.utils import (
    setup_logger,
    sanitize_search_criteria,
    format_prospect_data,
    validate_linkedin_url
)

def test_setup_logger():
    """Test logger setup with default configuration."""
    logger = setup_logger("test_lincoln")
    assert logger.name == "test_lincoln"
    assert logger.level == 20  # INFO level
    assert len(logger.handlers) > 0

def test_setup_logger_with_file(tmp_path):
    """Test logger setup with file output."""
    log_file = tmp_path / "test.log"
    os.environ["LOG_FILE"] = str(log_file)
    logger = setup_logger("test_lincoln")
    assert len(logger.handlers) == 2  # Console and file handlers
    os.environ.pop("LOG_FILE")

def test_sanitize_search_criteria_valid():
    """Test sanitization of valid search criteria."""
    criteria = {
        "title": "CTO",
        "location": "San Francisco",
        "industry": "Technology",
        "invalid_field": "should be removed"
    }
    sanitized = sanitize_search_criteria(criteria)
    assert "title" in sanitized
    assert "location" in sanitized
    assert "industry" in sanitized
    assert "invalid_field" not in sanitized
    assert sanitized["title"] == "CTO"

def test_sanitize_search_criteria_empty():
    """Test sanitization of empty search criteria."""
    with pytest.raises(ValueError, match="At least one valid search criterion must be provided"):
        sanitize_search_criteria({})

def test_sanitize_search_criteria_whitespace():
    """Test sanitization of criteria with whitespace."""
    criteria = {"title": "  Software Engineer  "}
    sanitized = sanitize_search_criteria(criteria)
    assert sanitized["title"] == "Software Engineer"

def test_format_prospect_data():
    """Test formatting of prospect data."""
    raw_data = {
        "name": "John Doe",
        "title": "CTO",
        "company": "Tech Corp",
        "location": "San Francisco",
        "experience": ["Tech Corp", "Previous Corp"],
        "education": ["University"],
        "profile_url": "https://linkedin.com/in/johndoe",
        "timestamp": "2024-02-04"
    }
    formatted = format_prospect_data(raw_data)
    assert formatted["full_name"] == "John Doe"
    assert formatted["current_title"] == "CTO"
    assert formatted["current_company"] == "Tech Corp"
    assert formatted["linkedin_url"] == "https://linkedin.com/in/johndoe"
    assert len(formatted["experience"]) == 2
    assert len(formatted["education"]) == 1

def test_format_prospect_data_missing_fields():
    """Test formatting of prospect data with missing fields."""
    raw_data = {"name": "John Doe"}
    formatted = format_prospect_data(raw_data)
    assert formatted["full_name"] == "John Doe"
    assert formatted["current_title"] == ""
    assert formatted["experience"] == []
    assert formatted["education"] == []

@pytest.mark.parametrize("url,expected", [
    ("linkedin.com/in/johndoe", "https://linkedin.com/in/johndoe"),
    ("http://linkedin.com/in/johndoe", "https://linkedin.com/in/johndoe"),
    ("https://www.linkedin.com/in/johndoe", "https://www.linkedin.com/in/johndoe"),
    ("invalid-url.com", None),
    ("", None),
    (None, None),
])
def test_validate_linkedin_url(url, expected):
    """Test LinkedIn URL validation with various inputs."""
    assert validate_linkedin_url(url) == expected 