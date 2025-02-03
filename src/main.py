import os
import uvicorn
from dotenv import load_dotenv
from orchestrator.orchestrator import app
from orchestrator.logger import get_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger(__name__)


def main():
    """
    Main entry point for the Zigral orchestrator
    """
    try:
        # Get configuration from environment
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8000"))

        # Log startup
        logger.info(f"Starting Zigral orchestrator on {host}:{port}")

        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Start the FastAPI application
        uvicorn.run(
            app, host=host, port=port, log_level=os.getenv("LOG_LEVEL", "info").lower()
        )

    except Exception as e:
        logger.error(f"Failed to start orchestrator: {str(e)}")
        raise


if __name__ == "__main__":
    main()
