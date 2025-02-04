"""Test the basic structure of the agents package."""
import os

import pytest


def test_agents_directory_structure():
    """Test that all required directories and files exist."""
    # Base directories
    assert os.path.isdir("src/agents"), "src/agents directory should exist"
    assert os.path.isdir(
        "src/agents/lincoln"
    ), "src/agents/lincoln directory should exist"
    assert os.path.isdir("src/agents/shaun"), "src/agents/shaun directory should exist"

    # Package initialization files
    assert os.path.isfile(
        "src/agents/__init__.py"
    ), "src/agents/__init__.py should exist"
    assert os.path.isfile(
        "src/agents/lincoln/__init__.py"
    ), "src/agents/lincoln/__init__.py should exist"
    assert os.path.isfile(
        "src/agents/shaun/__init__.py"
    ), "src/agents/shaun/__init__.py should exist"

    # Test directories
    assert os.path.isdir("tests/agents"), "tests/agents directory should exist"
    assert os.path.isdir(
        "tests/agents/lincoln"
    ), "tests/agents/lincoln directory should exist"
    assert os.path.isdir(
        "tests/agents/shaun"
    ), "tests/agents/shaun directory should exist"

    # Test package initialization files
    assert os.path.isfile(
        "tests/agents/__init__.py"
    ), "tests/agents/__init__.py should exist"
    assert os.path.isfile(
        "tests/agents/lincoln/__init__.py"
    ), "tests/agents/lincoln/__init__.py should exist"
    assert os.path.isfile(
        "tests/agents/shaun/__init__.py"
    ), "tests/agents/shaun/__init__.py should exist"
