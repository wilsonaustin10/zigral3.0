"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
from tortoise import Tortoise

from context_manager.database import init_db, close_db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def initialize_tests():
    """Initialize test database before each test."""
    await init_db()
    yield
    await close_db()
