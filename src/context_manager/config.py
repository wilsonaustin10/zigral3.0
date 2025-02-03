import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration settings for the Context Manager"""

    # Service settings
    SERVICE_NAME: str = "context-manager"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CONTEXT_MANAGER_HOST: str = "0.0.0.0"
    CONTEXT_MANAGER_PORT: int = 8001

    # Database settings
    DATABASE_URL: str = "postgres://user:password@localhost:5432/zigral"

    # OpenAI settings
    OPENAI_API_KEY: str = "your_api_key_here"

    # Tortoise ORM settings
    TORTOISE_ORM: Dict[str, Any] = {
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
            "context_manager": {
                "models": ["context_manager.models"],
                "default_connection": "default",
            }
        },
        "use_tz": False,
        "timezone": "UTC",
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Update Tortoise ORM config with actual DATABASE_URL
        self.TORTOISE_ORM["connections"]["default"] = {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",
                "port": 5432,
                "user": "user",
                "password": "password",
                "database": "zigral",
            },
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Application settings
    """
    return Settings()
