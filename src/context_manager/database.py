"""Database configuration and initialization.

This module provides database configuration and initialization utilities for both
production and test environments. It uses Tortoise ORM with support for both
PostgreSQL (production) and SQLite (testing/development).

Key components:
- TORTOISE_ORM: Production configuration for PostgreSQL
- TEST_TORTOISE_CONFIG: Test configuration using SQLite
- TORTOISE_CONFIG: Development configuration using SQLite file database

The module ensures proper database initialization, connection management,
and cleanup across different environments.
"""
import logging
import os
import tempfile
from pathlib import Path
from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError
from typing import Optional
import copy

from .config import get_settings
from .logger import get_logger

logger = logging.getLogger(__name__)
settings = get_settings()

# Create a temporary directory for SQLite files
TEMP_DIR = tempfile.mkdtemp(prefix="zigral_test_")
os.makedirs(TEMP_DIR, exist_ok=True)  # Ensure directory exists

# Default Tortoise ORM configuration for PostgreSQL
TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",
                "port": 5432,
                "user": "user",
                "password": "password",
                "database": "zigral",
            },
        }
    },
    "apps": {
        "models": {
            "models": ["context_manager.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC",
}

# Test configuration using SQLite in-memory database
TEST_TORTOISE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": str(Path(TEMP_DIR) / "test.sqlite3")
            }
        }
    },
    "apps": {
        "models": {
            "models": ["context_manager.models"],
            "default_connection": "default",
        }
    }
}

# Production configuration using SQLite file database
db_file = Path(TEMP_DIR) / "db.sqlite3"
TORTOISE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": str(db_file)
            }
        }
    },
    "apps": {
        "models": {
            "models": ["context_manager.models"],
            "default_connection": "default",
        }
    }
}

async def init_db(test_mode: bool = False) -> None:
    """Initialize the database connection.
    
    This function handles database initialization for both production and test environments.
    It ensures proper cleanup of existing connections before initializing new ones and
    handles the creation of necessary directories for file-based databases.
    
    Args:
        test_mode: If True, use SQLite database for testing. Defaults to False.
        
    Raises:
        Exception: If database initialization fails for any reason.
    """
    try:
        # Close any existing connections first
        try:
            await Tortoise.close_connections()
        except ConfigurationError:
            pass

        # Initialize with appropriate config
        config = TEST_TORTOISE_CONFIG if test_mode else TORTOISE_CONFIG
        
        # If using file database, ensure directory exists
        if not test_mode:
            db_path = Path(config["connections"]["default"]["credentials"]["file_path"])
            os.makedirs(db_path.parent, exist_ok=True)
        
        await Tortoise.init(config=config)
        await Tortoise.generate_schemas()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

async def close_db() -> None:
    """Close all active database connections.
    
    This function safely closes all active database connections and performs cleanup.
    It can be called multiple times safely, making it suitable for both normal
    operation and error handling scenarios.
    
    Raises:
        Exception: If there is an error during connection closure.
    """
    try:
        await Tortoise.close_connections()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}")
        raise

async def init_test_db():
    """Initialize test database with SQLite database.
    
    This function sets up a clean test database environment by:
    1. Closing any existing connections
    2. Resetting Tortoise ORM's internal state
    3. Initializing a new database with test configuration
    4. Creating necessary database schemas
    
    The function uses a deep copy of the test configuration to prevent
    state leakage between test cases.
    
    Raises:
        Exception: If database initialization fails.
    """
    try:
        # Close any existing connections
        try:
            await Tortoise.close_connections()
        except ConfigurationError:
            pass

        # Reset Tortoise state
        Tortoise._client_routing = {}
        Tortoise._connections = {}
        Tortoise._inited = False
        Tortoise._db_config = None
        Tortoise._apps = {}

        logger.info("Initializing test database...")
        await Tortoise.init(config=copy.deepcopy(TEST_TORTOISE_CONFIG))
        await Tortoise.generate_schemas()
        logger.info("Test database initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize test database: {str(e)}")
        raise
