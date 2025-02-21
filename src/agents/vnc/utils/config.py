"""
Configuration settings for the VNC Agent Runner.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

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
    SESSION_TIMEOUT: int = 3600
    
    # Security
    JWT_SECRET: str = "your_jwt_secret_here"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]
    
    # VNC Configuration
    VNC_HOST: str = "localhost"
    VNC_PORT: int = 5900
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

# Create settings instance
settings = Settings() 