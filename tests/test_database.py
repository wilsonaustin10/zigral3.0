"""Database test suite.

This module contains tests for database initialization, connection management,
and schema creation functionality. It verifies the proper operation of the
database layer in both normal and error conditions.

Test cases:
1. Database initialization and basic query execution
2. Connection closure and cleanup
3. Error handling for invalid configurations
4. Multiple connection closure scenarios
5. Schema creation and verification

The tests use a SQLite database in a temporary directory to ensure
isolation and reproducibility.
"""

import logging
import os
from pathlib import Path

import pytest
from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError, DBConnectionError, OperationalError
from tortoise.backends.base.client import BaseDBAsyncClient

from context_manager.database import close_db, TEST_TORTOISE_CONFIG, TEMP_DIR, init_test_db

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_database_initialization():
    """Test database initialization process.

    This test verifies that:
    1. Database connection can be established
    2. A basic query can be executed
    3. Connection can be closed properly
    """
    # Initialize database
    await init_test_db()

    # Get connection and execute a test query
    conn = Tortoise.get_connection("default")
    assert isinstance(conn, BaseDBAsyncClient)
    
    # Test query to check if context_entries table exists (SQLite compatible)
    result = await conn.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='context_entries'"
    )
    assert len(result[1]) > 0, "context_entries table not found"

    # Close connection
    await close_db()


@pytest.mark.asyncio
async def test_database_close():
    """Test database connection closing.

    This test verifies that:
    1. A connection can be established and used
    2. The connection can be closed properly
    3. After closing, the connection pool is properly cleaned up
    """
    # First initialize
    await init_test_db()

    # Get connection before closing
    conn = Tortoise.get_connection("default")
    assert await conn.execute_query("SELECT 1")  # Verify it works

    # Then close
    await close_db()

    # Verify connection is closed by checking internal state
    assert not hasattr(conn, "_pool") or conn._pool is None


@pytest.mark.asyncio
async def test_database_initialization_error():
    """Test database initialization with invalid configuration.

    This test verifies that:
    1. Invalid database configuration is properly handled
    2. Appropriate error is raised (DBConnectionError)
    3. Gracefully handles the case where no prior configuration exists
    """
    # Create a directory path that definitely doesn't exist
    nonexistent_dir = "/nonexistent/path/that/definitely/does/not/exist"
    invalid_config = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {
                    "file_path": os.path.join(nonexistent_dir, "db.sqlite")
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

    # Attempt to initialize with invalid configuration
    with pytest.raises((DBConnectionError, OperationalError)) as exc_info:
        try:
            await Tortoise.init(config=invalid_config)
            await Tortoise.generate_schemas()
        finally:
            try:
                await close_db()
            except Exception:
                pass
            Tortoise._client_routing = {}
            Tortoise._connections = {}
            Tortoise._inited = False
            Tortoise._db_config = None
            Tortoise._apps = {}

    error_msg = str(exc_info.value).lower()
    assert any(msg in error_msg for msg in ["no such file", "directory", "unable to open"])


@pytest.mark.asyncio
async def test_database_close_error():
    """Test closing an already closed database connection.

    This test verifies that:
    1. A connection can be closed normally
    2. Attempting to close an already closed connection succeeds silently
    """
    # Initialize database
    await init_test_db()

    # Get connection and verify it works
    conn = Tortoise.get_connection("default")
    assert await conn.execute_query("SELECT 1")

    # Close connection normally
    await close_db()

    # Attempt to close again - should not raise an error
    await close_db()


@pytest.mark.asyncio
async def test_database_schema_creation():
    """Test database schema creation.

    This test verifies that:
    1. Database schemas can be created successfully
    2. The required tables are present in the database
    3. Specifically checks for the 'context_entries' table
    """
    # Initialize database
    await init_test_db()

    # Get connection and check for table (SQLite compatible)
    conn = Tortoise.get_connection("default")
    result = await conn.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='context_entries'"
    )
    assert len(result[1]) > 0, "context_entries table not found"

    # Close connection
    await close_db()
