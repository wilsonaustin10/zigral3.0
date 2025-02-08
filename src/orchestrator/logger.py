import os
import sys
from pathlib import Path

from loguru import logger


def get_logger(name: str):
    """
    Configure and return a logger instance

    Args:
        name (str): The name of the module requesting the logger

    Returns:
        Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create a new logger instance
    new_logger = logger.opt(depth=1)

    # Remove default handler
    new_logger.remove()

    # Get log level from environment variable, default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Add console handler with custom format
    new_logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
        level=log_level,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for error logs
    new_logger.add(
        str(logs_dir / "error.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
        level="ERROR",
        rotation="1 day",
        retention="7 days",
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for all logs
    new_logger.add(
        str(logs_dir / "zigral.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
        level=log_level,
        rotation="1 day",
        retention="7 days",
    )

    # Create a contextualized logger with module name
    contextualized_logger = new_logger.bind(module=name)

    # Test the logger to ensure it's working
    contextualized_logger.debug(f"Logger initialized for module: {name}")

    # Ensure that the logs directory exists
    logs_path = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)

    # Add a file sink to log errors if not already added
    file_sink = os.path.join(logs_path, "error.log")
    # Check if a sink with this path is already configured (this is heuristic)
    sinks = [handler._sink for handler in new_logger._core.handlers.values() if hasattr(handler, '_sink')]
    if file_sink not in sinks:
        new_logger.add(file_sink, level="ERROR")

    return contextualized_logger
