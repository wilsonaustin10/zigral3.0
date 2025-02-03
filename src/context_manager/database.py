"""Database configuration and initialization."""
from tortoise import Tortoise
from .config import get_settings
from .logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Default Tortoise ORM configuration
TORTOISE_ORM = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["context_manager.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC",
}


async def init_db():
    """Initialize database connection and create schemas."""
    try:
        logger.info("Initializing database connection...")
        await Tortoise.init(config=settings.TORTOISE_ORM)

        # Generate schemas
        logger.info("Creating database schemas...")
        await Tortoise.generate_schemas()

        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_db():
    """Close database connection."""
    try:
        logger.info("Closing database connection...")
        await Tortoise.close_connections()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}")
        raise
