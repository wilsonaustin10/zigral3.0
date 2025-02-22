"""Unit tests for screen parser implementation."""

import pytest
import asyncio
from PIL import Image
import io
import numpy as np
from src.agents.vnc.screen_parser import ScreenParser, ElementLocation

@pytest.fixture
def screen_parser():
    return ScreenParser()

@pytest.fixture
def sample_screenshot():
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_find_element(screen_parser, sample_screenshot):
    """Test finding a specific element."""
    element = await screen_parser.find_element(sample_screenshot, "button")
    assert element is None or isinstance(element, ElementLocation)

@pytest.mark.asyncio
async def test_get_all_elements(screen_parser, sample_screenshot):
    """Test getting all elements from screenshot."""
    elements = await screen_parser.get_all_elements(sample_screenshot)
    assert isinstance(elements, list)
    for element in elements:
        assert isinstance(element, ElementLocation)
        assert 0 <= element.confidence <= 1
        assert element.element_type in screen_parser.element_types

@pytest.mark.asyncio
async def test_analyze_layout(screen_parser, sample_screenshot):
    """Test layout analysis."""
    layout = await screen_parser.analyze_layout(sample_screenshot)
    assert isinstance(layout, dict)
    for element_type, elements in layout.items():
        assert element_type in screen_parser.element_types
        assert isinstance(elements, list)
        for element in elements:
            assert isinstance(element, ElementLocation)

@pytest.mark.asyncio
async def test_element_location_attributes():
    """Test ElementLocation dataclass attributes."""
    element = ElementLocation(
        x=100,
        y=200,
        width=300,
        height=400,
        confidence=0.95,
        element_type="button"
    )
    assert element.x == 100
    assert element.y == 200
    assert element.width == 300
    assert element.height == 400
    assert element.confidence == 0.95
    assert element.element_type == "button"

@pytest.mark.asyncio
async def test_screen_parser_initialization():
    """Test ScreenParser initialization."""
    parser = ScreenParser()
    assert parser.device in ["cuda", "cpu"]
    assert len(parser.element_types) > 0
    assert "button" in parser.element_types
    assert hasattr(parser, "model")
    assert hasattr(parser, "processor") 