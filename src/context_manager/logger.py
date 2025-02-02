import os
import sys
from loguru import logger

def get_logger(name: str):
    """
    Configure and return a logger instance
    
    Args:
        name (str): The name of the module requesting the logger
        
    Returns:
        Logger: Configured logger instance
    """
    # Remove default logger
    logger.remove()
    
    # Get log level from environment variable, default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for error logs
    logger.add(
        "logs/context_manager_error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="1 day",
        retention="7 days",
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for all logs
    logger.add(
        "logs/context_manager.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation="1 day",
        retention="7 days"
    )
    
    # Bind the module name to the logger
    return logger.bind(name=name) 