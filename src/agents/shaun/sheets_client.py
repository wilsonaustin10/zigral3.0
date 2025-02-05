"""
Google Sheets Client for the Shaun agent.

This module provides functionality for interacting with Google Sheets,
specifically for managing prospect lists and other sales-related data.
It uses the gspread library for Google Sheets API integration.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound

from .utils import setup_logger, validate_prospect_data, format_prospect_row

# Define the required OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

logger = setup_logger("shaun.sheets_client")


class GoogleSheetsClient:
    """Client for interacting with Google Sheets.
    
    This class provides methods for connecting to Google Sheets and
    managing prospect data within specified spreadsheets.
    
    Attributes:
        client (gspread.Client): Authenticated gspread client
        spreadsheet (gspread.Spreadsheet): Active spreadsheet
        worksheet (gspread.Worksheet): Active worksheet
        
    Methods:
        initialize(): Set up Google Sheets connection
        cleanup(): Clean up resources
        connect_to_sheet(): Connect to a specific spreadsheet
        add_prospects(): Add new prospects to the sheet
        update_prospect(): Update existing prospect data
        execute_command(): Execute various sheet operations
    """

    def __init__(self, creds_path: Optional[str] = None):
        """
        Initialize the Google Sheets client.

        Args:
            creds_path (Optional[str]): Path to the Google Sheets credentials file.
                If not provided, will look for credentials in environment variables.
        """
        self.creds_path = creds_path
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.worksheet: Optional[gspread.Worksheet] = None
        self.logger = setup_logger(__name__)
        self._headers: List[str] = [
            'Full Name',
            'Title',
            'Company',
            'Location',
            'LinkedIn URL',
            'Experience',
            'Education',
            'Last Updated'
        ]

    async def initialize(self) -> None:
        """
        Initialize the Google Sheets client with credentials.

        Raises:
            FileNotFoundError: If credentials file is not found.
            Exception: If initialization fails.
        """
        try:
            credentials = Credentials.from_service_account_file(
                self.creds_path,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    async def connect_to_sheet(
        self, spreadsheet_id: str, worksheet_name: str = "Prospects"
    ) -> Tuple[gspread.Spreadsheet, gspread.Worksheet]:
        """
        Connect to a specific spreadsheet and worksheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet to connect to
            worksheet_name: Name of the worksheet (default: "Prospects")
            
        Returns:
            Tuple containing the spreadsheet and worksheet objects
            
        Raises:
            SpreadsheetNotFound: If spreadsheet doesn't exist
            WorksheetNotFound: If worksheet doesn't exist
        """
        try:
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            logger.info(f"Connected to spreadsheet: {self.spreadsheet.title}")

            try:
                # Try to get existing worksheet
                self.worksheet = self.spreadsheet.worksheet(worksheet_name)
            except WorksheetNotFound:
                # Create new worksheet if it doesn't exist
                self.worksheet = self.spreadsheet.add_worksheet(
                    worksheet_name, rows=1000, cols=len(self._headers)
                )
                # Add headers to new worksheet
                self.worksheet.insert_row(self._headers, index=1)
                logger.info(f"Created new worksheet: {worksheet_name}")

            return self.spreadsheet, self.worksheet

        except SpreadsheetNotFound:
            logger.error(f"Spreadsheet not found: {spreadsheet_id}")
            raise
        except Exception as e:
            logger.error(f"Error connecting to sheet: {str(e)}")
            raise

    async def add_prospects(self, prospects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add new prospects to the worksheet.

        Args:
            prospects (List[Dict[str, Any]]): List of prospect data to add.

        Returns:
            Dict[str, Any]: Result of the operation.

        Raises:
            ValueError: If no worksheet is connected or data is invalid.
        """
        if not self.worksheet:
            raise ValueError("No worksheet connected")

        result = {"success": False, "added": [], "failed": []}
        
        try:
            for prospect in prospects:
                if validate_prospect_data(prospect):
                    row_data = format_prospect_row(prospect)
                    self.worksheet.append_row(row_data)
                    result["added"].append(prospect)
                else:
                    result["failed"].append(prospect)
            
            result["success"] = True
            self.logger.info(f"Added {len(result['added'])} prospects")
            
        except Exception as e:
            self.logger.error(f"Failed to add prospects: {str(e)}")
            result["error"] = str(e)
        
        return result

    async def update_prospect(
        self, email: str, updated_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing prospect's data.

        Args:
            email (str): Email of the prospect to update.
            updated_data (Dict[str, Any]): New data for the prospect.

        Returns:
            Dict[str, Any]: Result of the operation.
        """
        if not self.worksheet:
            return {"success": False, "error": "No worksheet connected"}

        result = {"success": False}
        
        try:
            # Find the prospect by email
            cell = self.worksheet.find(email)
            if cell:
                row = cell.row
                # Update the row with new data
                row_data = format_prospect_row({**updated_data, "email": email})
                for col, value in enumerate(row_data, start=1):
                    self.worksheet.update_cell(row, col, value)
                result["success"] = True
                self.logger.info(f"Updated prospect with email: {email}")
            else:
                result["error"] = "Prospect not found"
                
        except Exception as e:
            self.logger.error(f"Failed to update prospect: {str(e)}")
            result["error"] = str(e)
        
        return result

    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the Google Sheets client.

        Args:
            command (Dict[str, Any]): Command to execute.

        Returns:
            Dict[str, Any]: Result of the command execution.
        """
        action = command.get("action")
        result = {"success": False}

        try:
            if action == "connect":
                spreadsheet_id = command.get("sheet_id")
                worksheet_name = command.get("worksheet")
                if not spreadsheet_id or not worksheet_name:
                    raise ValueError("sheet_id and worksheet are required")
                
                await self.connect_to_sheet(spreadsheet_id, worksheet_name)
                result["success"] = True
            elif action == "add_prospects":
                prospects = command.get("prospects", [])
                if not prospects:
                    raise ValueError("prospects list is required")
                
                result = await self.add_prospects(prospects)
            elif action == "update_prospect":
                email = command.get("email")
                updated_data = command.get("data", {})
                if not email or not updated_data:
                    raise ValueError("email and data are required")
                
                result = await self.update_prospect(email, updated_data)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Failed to execute command: {str(e)}")
            result["error"] = str(e)
        
        return result 