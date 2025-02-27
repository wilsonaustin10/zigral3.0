#!/usr/bin/env python3
"""
Demo Shaun Agent with VNC Browser Controller

This script demonstrates how to use the Shaun agent with VNC browser controller
to automate Google Sheets tasks. The script will:

1. Connect to the VNC browser via the frontend
2. Initialize the Shaun agent in VNC mode
3. Log in to Google account
4. Open a Google spreadsheet
5. Perform basic spreadsheet operations
6. Take screenshots at key steps
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.agents.shaun.agent import ShaunAgent, GoogleCredentials, SheetRange, SheetData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('demo_shaun_vnc.log')
    ]
)
logger = logging.getLogger(__name__)

async def run_demo():
    """Run the Shaun Agent VNC demo."""
    logger.info("Starting Shaun Agent VNC Demo")
    
    # Create output directory for screenshots
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # Frontend URL
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:8090")
    logger.info(f"Using frontend at {frontend_url}")
    
    # Initialize the Shaun agent in VNC mode
    logger.info("Initializing Shaun agent in VNC mode...")
    agent = ShaunAgent(headless=False, use_vnc=True, frontend_url=frontend_url)
    
    try:
        # Initialize the agent
        await agent.initialize()
        logger.info("Shaun agent initialized successfully")
        
        # Log in to Google account
        logger.info("Logging in to Google account...")
        credentials = GoogleCredentials(
            email=os.environ.get("GOOGLE_EMAIL", "demo@example.com"),
            password=os.environ.get("GOOGLE_PASSWORD", "demopassword")
        )
        
        login_result = await agent.login(credentials)
        if not login_result.get('logged_in', False):
            if login_result.get('requires_2fa', False):
                logger.info("2FA required, checking if a verification code is provided...")
                verification_code = os.environ.get("GOOGLE_2FA_CODE")
                if verification_code:
                    logger.info("Verifying 2FA code...")
                    verify_result = await agent.verify_2fa(verification_code)
                    if not verify_result.get('success', False):
                        logger.error("2FA verification failed")
                        return
                else:
                    logger.error("2FA required but no verification code provided")
                    return
            else:
                logger.error(f"Login failed: {login_result.get('error', 'Unknown error')}")
                return
        
        logger.info("Successfully logged in to Google account")
        
        # Take a screenshot after login
        logger.info("Taking screenshot after login...")
        if agent.vnc_controller:
            screenshot = await agent.vnc_controller.take_screenshot()
            if screenshot:
                with open(output_dir / "01_logged_in.png", "wb") as f:
                    f.write(screenshot)
                logger.info("Screenshot saved")
        
        # Open a Google spreadsheet
        # Use a test spreadsheet ID - replace with a real one in production
        test_sheet_id = os.environ.get("TEST_SHEET_ID", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
        logger.info(f"Opening spreadsheet with ID: {test_sheet_id}")
        
        try:
            sheet_info = await agent.open_spreadsheet(test_sheet_id)
            logger.info(f"Opened spreadsheet: {sheet_info.get('title', 'Unknown')}")
            
            # Take a screenshot of the opened spreadsheet
            logger.info("Taking screenshot of the opened spreadsheet...")
            if agent.vnc_controller:
                screenshot = await agent.vnc_controller.take_screenshot()
                if screenshot:
                    with open(output_dir / "02_spreadsheet.png", "wb") as f:
                        f.write(screenshot)
                    logger.info("Screenshot saved")
            
            # Placeholder for additional spreadsheet operations
            # In a full implementation, we would add more operations here
            # such as reading/writing data, formatting cells, etc.
            
            logger.info("Demo completed successfully")
        except Exception as e:
            logger.error(f"Error working with spreadsheet: {e}")
            
    except Exception as e:
        logger.error(f"Error during demo: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        await agent.cleanup()
        logger.info("Resources cleaned up")

def main():
    """Main entry point."""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)

if __name__ == "__main__":
    main() 