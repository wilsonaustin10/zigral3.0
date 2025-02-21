"""
Configuration settings for the VNC Agent Runner.
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # Version
    VERSION: str = "1.0.0"
    
    # Service Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # VNC Agent Configuration
    VNC_AGENT_HOST: str = "0.0.0.0"
    VNC_AGENT_PORT: int = 8080
    VNC_AGENT_KEY: str = "secure_key_here"
    
    # Browser Configuration
    CHROME_FLAGS: str = "--no-sandbox --start-maximized"
    MAX_SESSIONS: int = 5
    SESSION_TIMEOUT: int = 3600  # 1 hour in seconds
    COMMAND_TIMEOUT: int = 30  # 30 seconds
    SCREENSHOT_DIR: str = "screenshots"
    ELEMENT_IMAGES_DIR: str = "element_images"
    
    # Security
    JWT_SECRET: str = "your_jwt_secret_here"
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]
    
    # VNC Configuration
    VNC_HOST: str = "localhost"
    VNC_PORT: int = 5900
    VNC_PASSWORD: Optional[str] = None
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 