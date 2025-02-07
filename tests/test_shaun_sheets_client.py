import pytest
import json
from src.agents.shaun.sheets_client import GoogleSheetsClient


@pytest.mark.asyncio
async def test_initialize_success(tmp_path):
    # Create a valid credentials file with dummy private key
    valid_creds = {
        "private_key": "-----BEGIN PRIVATE KEY-----\nkey\n-----END PRIVATE KEY-----"
    }
    file_path = tmp_path / "creds.json"
    file_path.write_text(json.dumps(valid_creds))
    
    client = GoogleSheetsClient(creds_path=str(file_path))
    await client.initialize()
    assert client.client is not None


@pytest.mark.asyncio
async def test_initialize_file_not_found():
    # Use a non-existent file path
    non_existent_path = "non_existent_credentials.json"
    client = GoogleSheetsClient(creds_path=non_existent_path)
    with pytest.raises(FileNotFoundError):
        await client.initialize()


@pytest.mark.asyncio
async def test_initialize_invalid_json(tmp_path):
    # Create a file with invalid JSON content
    invalid_file = tmp_path / "invalid_creds.json"
    invalid_file.write_text("invalid json content")
    
    client = GoogleSheetsClient(creds_path=str(invalid_file))
    with pytest.raises(json.JSONDecodeError):
        await client.initialize() 