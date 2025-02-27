#!/usr/bin/env python3
"""
Demo VNC Browser Controller with LinkedIn

This script demonstrates how to use the VNC Browser Controller to automate
browsing tasks in a VNC session. The script will:

1. Connect to the VNC browser via the frontend
2. Navigate to LinkedIn
3. Perform a search for "CTOs in San Francisco"
4. Take a screenshot of the results
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from playwright.async_api import async_playwright
from src.agents.vnc.browser_controller import connect_to_vnc_browser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('demo_vnc.log')
    ]
)
logger = logging.getLogger(__name__)

async def run_demo():
    """Run the VNC Browser Controller demo."""
    logger.info("Starting VNC Browser Controller Demo")
    
    # Create output directory for screenshots
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # Frontend URL
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:8090")
    logger.info(f"Connecting to frontend at {frontend_url}")
    
    # Initialize Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Connect to the VNC browser via the frontend
            logger.info("Connecting to VNC browser...")
            controller = await connect_to_vnc_browser(browser, frontend_url)
            
            if not controller:
                logger.error("Failed to connect to VNC browser. Exiting.")
                return
            
            logger.info("Successfully connected to VNC browser")
            
            # Get the screen resolution
            resolution = await controller.get_resolution()
            logger.info(f"VNC display resolution: {resolution}")
            
            # Take a screenshot of the initial state
            logger.info("Taking screenshot of initial state...")
            screenshot = await controller.take_screenshot()
            if screenshot:
                with open(output_dir / "01_initial.png", "wb") as f:
                    f.write(screenshot)
                logger.info("Screenshot saved")
            
            # Navigate to Google (as a simple test)
            logger.info("Navigating to Google...")
            await controller.navigate("https://www.google.com")
            await asyncio.sleep(3)
            
            # Take a screenshot after navigation
            logger.info("Taking screenshot after navigation...")
            screenshot = await controller.take_screenshot()
            if screenshot:
                with open(output_dir / "02_google.png", "wb") as f:
                    f.write(screenshot)
                logger.info("Screenshot saved")
            
            # Type a search query
            logger.info("Typing search query...")
            # Click in the search box first
            await controller.click(resolution[0] // 2, resolution[1] // 2 - 100)
            await asyncio.sleep(1)
            await controller.type_text("LinkedIn CTOs in San Francisco")
            await asyncio.sleep(1)
            
            # Press Enter to search
            logger.info("Pressing Enter to search...")
            await controller._send_keys("Enter")
            await asyncio.sleep(3)
            
            # Take a screenshot of search results
            logger.info("Taking screenshot of search results...")
            screenshot = await controller.take_screenshot()
            if screenshot:
                with open(output_dir / "03_search_results.png", "wb") as f:
                    f.write(screenshot)
                logger.info("Screenshot saved")
            
            # Find and click on the LinkedIn result
            logger.info("Clicking on LinkedIn result...")
            # This is an approximation - real implementation would need to 
            # use screen parsing to find the exact coordinates
            await controller.click(resolution[0] // 2, resolution[1] // 2)
            await asyncio.sleep(5)
            
            # Take a final screenshot
            logger.info("Taking final screenshot...")
            screenshot = await controller.take_screenshot()
            if screenshot:
                with open(output_dir / "04_linkedin.png", "wb") as f:
                    f.write(screenshot)
                logger.info("Screenshot saved")
            
            logger.info("Demo completed successfully")
            
        except Exception as e:
            logger.error(f"Error during demo: {e}", exc_info=True)
        finally:
            await browser.close()
            logger.info("Browser closed")

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