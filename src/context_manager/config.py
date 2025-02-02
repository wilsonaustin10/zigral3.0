import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Configuration settings for the Context Manager"""
    
    # Service settings
    SERVICE_NAME: str = "context-manager"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API settings
    HOST: str = os.getenv("CONTEXT_MANAGER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("CONTEXT_MANAGER_PORT", "8001"))
    
    # Database settings
    DB_URL: str = os.getenv(
        "DATABASE_URL",
        "postgres://user:password@localhost:5432/zigral"
    )
    
    # Tortoise ORM settings
    TORTOISE_ORM = {
        "connections": {"default": DB_URL},
        "apps": {
            "context_manager": {
                "models": ["context_manager.models"],
                "default_connection": "default",
            }
        },
        "use_tz": False,
        "timezone": "UTC"
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns:
        Settings: Application settings
    """
    return Settings() 