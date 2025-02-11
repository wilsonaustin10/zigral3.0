"""
Google Sheets Client for the Shaun agent.

This module provides functionality for interacting with Google Sheets,
specifically for managing prospect lists and other sales-related data.
It uses the gspread library for Google Sheets API integration.
"""

import asyncio
import json
import os
import base64
import binascii
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from google.auth.credentials import Credentials as BaseCredentials
from google.auth.exceptions import InvalidValue
from unittest.mock import MagicMock

from .utils import setup_logger, validate_prospect_data, format_prospect_row, get_credentials_path

# Define the required OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

logger = setup_logger("shaun.sheets_client")

class DummyCredentials(BaseCredentials):
    def __init__(self):
        super().__init__()
        self._token = "dummy_token"
        self._trust_boundary = None
        self._use_non_blocking_refresh = False

    def refresh(self, request):
        pass

    @property
    def expired(self):
        return False

    @property
    def valid(self):
        return True

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

class GoogleSheetsClient:
    def _gs_authorize(self, creds):
        return gspread.authorize(creds)

    def __init__(self, creds_path: Optional[str] = None, creds_json: Optional[str] = None):
        """
        Initialize the Google Sheets client.

        Args:
            creds_path (Optional[str]): Path to the Google Sheets credentials file.
            creds_json (Optional[str]): Base64 encoded JSON string or direct JSON string of credentials.
                If provided, this takes precedence over creds_path.
        """
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.worksheet: Optional[gspread.Worksheet] = None
        self.logger = logger
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
        self._is_initialized = False
        self._creds_path = None
        self._creds_info = None

        # New credentials ordering:
        if (creds_json and creds_json.strip()):
            self._process_json_credentials(creds_json)
        elif (creds_path is not None and creds_path.strip()):
            self._creds_path = creds_path
        elif ((creds_path is None or not creds_path.strip()) and "GOOGLE_SHEETS_CREDENTIALS_JSON" in os.environ and os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"].strip()):
            self._process_json_credentials(os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"])
        elif ((creds_path is None or not creds_path.strip()) and "GOOGLE_SHEETS_CREDENTIALS_PATH" in os.environ and os.environ["GOOGLE_SHEETS_CREDENTIALS_PATH"].strip()):
            self._creds_path = os.environ["GOOGLE_SHEETS_CREDENTIALS_PATH"]
        else:
            home_dir = os.environ.get("HOME", str(Path.home()))
            default_path = Path(home_dir) / ".config" / "gspread" / "credentials.json"
            if default_path.exists():
                self._creds_path = str(default_path)

        # Validate that we have either credentials info or a path
        if not self._creds_info and not self._creds_path:
            raise FileNotFoundError(
                "No credentials found. Please provide either:\n"
                "1. Valid JSON credentials string (base64 encoded or direct)\n"
                "2. Path to credentials file\n"
                "3. GOOGLE_SHEETS_CREDENTIALS_PATH environment variable\n"
                "4. credentials.json in ~/.config/gspread/"
            )

    def _process_json_credentials(self, creds_json: str) -> None:
        """Process JSON credentials string and set _creds_info if valid."""
        try:
            # Check if credentials are base64 encoded
            if ';base64,' in creds_json:
                try:
                    _, b64_creds = creds_json.split(';base64,')
                    decoded_json = base64.b64decode(b64_creds).decode('utf-8')
                    creds_data = json.loads(decoded_json)
                except (binascii.Error, json.JSONDecodeError) as e:
                    raise ValueError("Invalid credentials JSON format")
            else:
                # Try parsing as direct JSON
                try:
                    creds_data = json.loads(creds_json)
                except json.JSONDecodeError as e:
                    raise ValueError("Invalid credentials JSON format")

            # Validate required fields in credentials
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            if not all(field in creds_data for field in required_fields):
                raise ValueError("Invalid credentials JSON format")

            self._creds_info = creds_data
            self._creds_path = None  # Clear the path when using JSON credentials

        except Exception as e:
            self.logger.error(f"Failed to parse credentials JSON: {str(e)}")
            raise

    @property
    def creds_info(self) -> Optional[Dict[str, Any]]:
        """Get the credentials info."""
        return self._creds_info

    @property
    def creds_path(self) -> Optional[str]:
        """Get the credentials file path. Not available when using JSON credentials."""
        if self._creds_info is not None:
            raise AttributeError("creds_path not available when using JSON credentials")
        return self._creds_path

    async def initialize(self):
        """Initialize the Google Sheets client with credentials."""
        if self._is_initialized:
            return

        try:
            if self._creds_info is not None:
                # Use credentials from JSON
                try:
                    creds = Credentials.from_service_account_info(
                        self._creds_info,
                        scopes=SCOPES
                    )
                except ValueError as e:
                    raise ValueError("Invalid credentials JSON format")
            else:
                # Use credentials from file
                if not self._creds_path or not Path(self._creds_path).exists():
                    raise FileNotFoundError("Credentials file not found")
                try:
                    with open(self._creds_path, 'r') as f:
                        content = f.read()
                    if content.startswith("data:") and ";base64," in content:
                        _, b64_creds = content.split(";base64,", 1)
                        decoded_json = base64.b64decode(b64_creds).decode('utf-8')
                        creds_data = json.loads(decoded_json)
                    else:
                        creds_data = json.loads(content)

                    creds = Credentials.from_service_account_info(
                        creds_data,
                        scopes=SCOPES
                    )
                except (ValueError, json.JSONDecodeError) as e:
                    raise ValueError("Invalid credentials file")

            self.client = self._gs_authorize(creds)
            self._is_initialized = True
            self.logger.info("Google Sheets client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    async def connect_to_sheet(self, sheet_id: str, worksheet_title: Optional[str] = None):
        """Connect to a specific Google Sheet and worksheet.

        Args:
            sheet_id (str): The ID of the Google Sheet to connect to
            worksheet_title (Optional[str]): Title of the worksheet to use. Defaults to "Sheet1"

        Returns:
            Tuple[gspread.Spreadsheet, gspread.Worksheet]: The connected spreadsheet and worksheet

        Raises:
            Exception: If client is not initialized or connection fails
        """
        if self.client is None:
            raise Exception("Client not initialized")

        try:
            spreadsheet = self.client.open_by_key(sheet_id)

            try:
                if worksheet_title:
                    worksheet = spreadsheet.worksheet(worksheet_title)
                else:
                    worksheet = spreadsheet.worksheet("Sheet1")
            except Exception:
                logger.info("Worksheet not found, creating a new one")
                title = worksheet_title if worksheet_title else "Sheet1"
                worksheet = spreadsheet.add_worksheet(title=title, rows="100", cols="20")
                worksheet.insert_row(self._headers, index=1)

            self.spreadsheet = spreadsheet
            self.worksheet = worksheet
            logger.info("Connected to spreadsheet: %s", spreadsheet.title)
            return spreadsheet, worksheet

        except Exception as e:
            self.logger.error("Failed to open spreadsheet: %s", e)
            raise e

    async def add_prospects(self, prospects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add multiple prospects to the worksheet.

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
            valid_prospects = []
            for prospect in prospects:
                if validate_prospect_data(prospect):
                    valid_prospects.append(prospect)
                    result["added"].append(prospect)
                else:
                    result["failed"].append(prospect)
            
            if valid_prospects:
                rows_data = [format_prospect_row(p) for p in valid_prospects]
                self.worksheet.append_rows(rows_data)
            
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

        try:
            cell = self.worksheet.find(email)
            # If cell is not found or does not have a valid row, treat as not found
            if not cell or not getattr(cell, 'row', None):
                return {"success": False, "error": "Prospect not found"}

            row = cell.row
            # Update the row with new data
            row_data = format_prospect_row({**updated_data, "email": email})
            for col, value in enumerate(row_data, start=1):
                self.worksheet.update_cell(row, col, value)
            self.logger.info(f"Updated prospect with email: {email}")
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Failed to update prospect: {str(e)}")
            return {"success": False, "error": str(e)}

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

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized 