"""
Utility functions for the LinkedIn agent.

This module provides helper functions for logging, data processing,
and other common operations used by the LinkedIn agent.
"""

import logging
import os
import sys
from typing import Dict, Optional
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with the specified name.

    Args:
        name: The name for the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Set default level to INFO

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if LOG_FILE is set
    log_file = os.getenv("LOG_FILE")
    if log_file:
        # Ensure log directory exists
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def sanitize_search_criteria(criteria: Dict) -> Dict:
    """
    Sanitize and validate search criteria for LinkedIn searches.
    
    Args:
        criteria: Raw search criteria dictionary.
        
    Returns:
        Sanitized search criteria dictionary.
        
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    valid_fields = {
        "keywords", "title", "company", "location", 
        "industry", "relationship", "geography"
    }
    
    sanitized = {}
    
    for key, value in criteria.items():
        if key in valid_fields and value:
            # Remove any special characters that might cause issues
            if isinstance(value, str):
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
    
    # Ensure at least one valid search criterion is provided
    if not sanitized:
        raise ValueError("At least one valid search criterion must be provided")
    
    return sanitized


def extract_profile_data(html_content: str) -> Dict:
    """
    Extract relevant data from a LinkedIn profile page.
    
    Args:
        html_content: HTML content of the profile page.
        
    Returns:
        Dictionary containing extracted profile data.
    """
    # TODO: Implement profile data extraction logic
    # This is a placeholder that will be implemented based on specific requirements
    return {
        "name": "",
        "title": "",
        "company": "",
        "location": "",
        "experience": [],
        "education": []
    }


def format_prospect_data(raw_data: Dict) -> Dict:
    """
    Format raw prospect data into a standardized structure.
    
    Args:
        raw_data: Raw data extracted from LinkedIn.
        
    Returns:
        Formatted prospect data dictionary.
    """
    return {
        "full_name": raw_data.get("name", ""),
        "current_title": raw_data.get("title", ""),
        "current_company": raw_data.get("company", ""),
        "location": raw_data.get("location", ""),
        "experience": raw_data.get("experience", []),
        "education": raw_data.get("education", []),
        "linkedin_url": raw_data.get("profile_url", ""),
        "last_updated": raw_data.get("timestamp", "")
    }


def validate_linkedin_url(url: str) -> Optional[str]:
    """
    Validate and normalize a LinkedIn profile URL.
    
    Args:
        url: LinkedIn profile URL to validate.
        
    Returns:
        Normalized URL if valid, None otherwise.
    """
    if not url:
        return None
        
    url = url.strip().lower()
    
    # Basic validation for LinkedIn URLs
    valid_domains = {"linkedin.com", "www.linkedin.com"}
    try:
        # Extract domain and ensure it's a LinkedIn URL
        if any(domain in url for domain in valid_domains):
            # Ensure it starts with https://
            if not url.startswith("https://"):
                url = "https://" + url.lstrip("http://")
            return url
    except Exception:
        pass
    
    return None 