"""Configuration settings for the VNC agent."""

from functools import lru_cache
from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for the VNC agent."""
    
    # Version
    VERSION: str = "3.0.0"
    
    # Debug settings
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Service configuration
    VNC_AGENT_HOST: str = "0.0.0.0"
    VNC_AGENT_PORT: int = 8080
    
    # JWT settings
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # Browser settings
    BROWSER_EXECUTABLE: Optional[str] = None
    BROWSER_ARGS: List[str] = []
    
    # API settings
    ORCHESTRATOR_URL: str = "http://localhost:8000"
    CONTEXT_MANAGER_URL: str = "http://localhost:8001"

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create settings instance
settings = get_settings()
