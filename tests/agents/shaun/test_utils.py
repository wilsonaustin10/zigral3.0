"""Tests for Shaun agent utility functions."""

import pytest
from pathlib import Path
from src.agents.shaun.utils import (
    setup_logger,
    validate_prospect_data,
    format_prospect_row,
    get_credentials_path
)

def test_setup_logger():
    """Test logger setup."""
    logger = setup_logger("test_module")
    assert logger.name == "test_module"
    assert logger.level == 20  # INFO level
    assert len(logger.handlers) > 0

def test_validate_prospect_data_valid():
    """Test validation of valid prospect data."""
    data = {
        "Full Name": "John Doe",
        "Title": "CEO",
        "Company": "Test Inc",
        "Location": "San Francisco",
        "LinkedIn URL": "https://linkedin.com/in/johndoe",
        "Experience": "10+ years",
        "Education": "MBA",
        "Last Updated": "2024-02-08"
    }
    assert validate_prospect_data(data) is True

def test_validate_prospect_data_missing_fields():
    """Test validation of prospect data with missing fields."""
    data = {
        "name": "John Doe",
        "email": "john@example.com"
        # missing company
    }
    assert validate_prospect_data(data) is False

def test_validate_prospect_data_empty_fields():
    """Test validation of prospect data with empty fields."""
    data = {
        "name": "",
        "email": "john@example.com",
        "company": "Test Inc"
    }
    assert validate_prospect_data(data) is False

def test_format_prospect_row():
    """Test formatting of prospect data into row."""
    data = {
        "Full Name": "John Doe",
        "Title": "CEO",
        "Company": "Test Inc",
        "Location": "San Francisco",
        "LinkedIn URL": "https://linkedin.com/in/johndoe",
        "Experience": "10+ years",
        "Education": "MBA",
        "Last Updated": "2024-02-08"
    }
    row = format_prospect_row(data)
    assert len(row) == 8
    assert row[0] == "John Doe"
    assert row[1] == "CEO"
    assert row[2] == "Test Inc"
    assert row[3] == "San Francisco"
    assert row[4] == "https://linkedin.com/in/johndoe"
    assert row[5] == "10+ years"
    assert row[6] == "MBA"
    assert row[7] == "2024-02-08"

def test_format_prospect_row_missing_fields():
    """Test formatting of prospect data with missing fields."""
    data = {
        "Full Name": "John Doe",
        "Title": "CEO",
        "Company": "Test Inc",
        "Location": "San Francisco",
        "LinkedIn URL": "https://linkedin.com/in/johndoe"
    }
    row = format_prospect_row(data)
    assert len(row) == 8
    assert row[0] == "John Doe"
    assert row[1] == "CEO"
    assert row[2] == "Test Inc"
    assert row[3] == "San Francisco"
    assert row[4] == "https://linkedin.com/in/johndoe"
    assert row[5] == ""
    assert row[6] == ""
    assert row[7] == ""

def test_get_credentials_path_not_found():
    """Test getting credentials path when file doesn't exist."""
    path = get_credentials_path()
    assert path is None or isinstance(path, Path) 