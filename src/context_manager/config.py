"""Configuration settings for the context manager."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # Version
    VERSION: str = "3.0.0"
    
    # Service Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CONTEXT_MANAGER_HOST: str = "0.0.0.0"
    CONTEXT_MANAGER_PORT: int = 8001
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/zigral"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Service Selection
    SERVICE_NAME: str = "context-manager"
    
    # Security
    JWT_SECRET_KEY: str = "your_jwt_secret_here"
    JWT_ALGORITHM: str = "HS256"
    
    # Browser Automation Configuration
    ENABLE_VIDEO_STREAM: bool = False
    
    # VNC Configuration
    VNC_HOST: str = "34.174.193.245"
    VNC_PORT: int = 6080
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS_JSON: Optional[str] = None
    GOOGLE_SHEETS_CREDENTIALS_PATH: Optional[str] = None
    PROSPECTS_SHEET_ID: Optional[str] = None
    PROSPECTS_WORKSHEET: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
