"""
Utility functions for the Shaun Google Sheets agent.

This module provides helper functions and utilities for the Shaun agent,
including logging setup and data validation functions.
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

def setup_logger(module_name: str) -> logging.Logger:
    """
    Set up a logger for the specified module.

    Args:
        module_name (str): Name of the module to create logger for.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def validate_prospect_data(data: Dict[str, Any]) -> bool:
    """
    Validate prospect data before adding to sheets.

    Args:
        data (Dict[str, Any]): Prospect data to validate.

    Returns:
        bool: True if data is valid, False otherwise.
    """
    required_fields = ['name', 'email', 'company']
    return all(field in data and data[field] for field in required_fields)

def format_prospect_row(data: Dict[str, Any]) -> List[str]:
    """
    Format prospect data into a row for Google Sheets.

    Args:
        data (Dict[str, Any]): Prospect data to format.

    Returns:
        List[str]: Formatted row data.
    """
    fields = ['name', 'email', 'company', 'phone', 'linkedin', 'notes']
    return [str(data.get(field, '')) for field in fields]

def get_credentials_path() -> Optional[Path]:
    """
    Get the path to Google Sheets credentials file.

    Returns:
        Optional[Path]: Path to credentials file if found, None otherwise.
    """
    creds_path = Path.home() / '.config' / 'gspread' / 'credentials.json'
    return creds_path if creds_path.exists() else None 