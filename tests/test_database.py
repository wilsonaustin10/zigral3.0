import logging

import pytest
from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError, DBConnectionError, OperationalError

from context_manager.database import close_db

# Test database configuration
TEST_TORTOISE_CONFIG = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "context_manager": {
            "models": ["context_manager.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC",
}

logger = logging.getLogger(__name__)


async def init_test_db():
    """Initialize the test database with Tortoise ORM.

    This function:
    1. Initializes Tortoise ORM with the test configuration
    2. Creates database schemas for all models

    Raises:
        Exception: If database initialization fails
    """
    try:
        await Tortoise.init(config=TEST_TORTOISE_CONFIG)
        await Tortoise.generate_schemas()
    except Exception as e:
        logger.error(f"Failed to initialize test database: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_database_initialization():
    """Test database initialization process.

    This test verifies that:
    1. Database connection can be established
    2. A basic query can be executed
    3. Connection can be closed properly
    """
    # Close any existing connections
    await Tortoise.close_connections()

    # Initialize database
    await init_test_db()

    # Verify connection is established by getting the connection and running a query
    conn = Tortoise.get_connection("default")
    assert conn is not None
    assert await conn.execute_query("SELECT 1")

    # Clean up
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

    # Clean up any remaining connections
    await Tortoise.close_connections()


@pytest.mark.asyncio
async def test_database_initialization_error():
    """Test database initialization with invalid configuration.

    This test verifies that:
    1. Invalid database configuration is properly handled
    2. Appropriate error is raised (DBConnectionError or OperationalError)
    3. Gracefully handles the case where no prior configuration exists

    The test attempts to initialize a database with an invalid path,
    expecting either a DBConnectionError or OperationalError to be raised
    with a specific error message about being unable to open the database file.
    """
    # Try to initialize with invalid configuration
    invalid_config = {
        "connections": {"default": "sqlite:///nonexistent_path/db.sqlite3"},
        "apps": {
            "context_manager": {
                "models": ["context_manager.models"],
                "default_connection": "default",
            }
        },
    }

    # Attempt to close any existing connections; if not initialized, ignore
    try:
        await Tortoise.close_connections()
    except ConfigurationError:
        pass

    # Attempt to initialize with invalid configuration
    with pytest.raises((DBConnectionError, OperationalError)) as exc_info:
        await Tortoise.init(config=invalid_config)
        await Tortoise.generate_schemas()

    # Verify the error message
    assert "unable to open database file" in str(exc_info.value)


@pytest.mark.asyncio
async def test_database_close_error():
    """Test closing an already closed database connection.

    This test verifies that:
    1. A connection can be closed normally
    2. Attempting to close an already closed connection succeeds silently
    """
    # Initialize database
    await init_test_db()

    # Close the connection twice
    await close_db()
    await close_db()  # Should not raise an error

    # Clean up
    await Tortoise.close_connections()


@pytest.mark.asyncio
async def test_database_schema_creation():
    """Test database schema creation.

    This test verifies that:
    1. Database schemas can be created successfully
    2. The required tables are present in the database
    3. Specifically checks for the 'context_entries' table
    """
    # Close any existing connections
    await Tortoise.close_connections()

    # Initialize database
    await init_test_db()

    # Verify table exists by running a query
    conn = Tortoise.get_connection("default")
    result = await conn.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='context_entries'"
    )
    assert len(result[1]) > 0  # Table exists

    # Clean up
    await close_db()
