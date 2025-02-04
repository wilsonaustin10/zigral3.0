"""Test the agents directory structure."""

import os

def test_agents_directory_structure():
    """Test that the agents directory has the expected structure."""
    # Test src/agents directory
    src_agents_dir = os.path.join("src", "agents")
    assert os.path.exists(src_agents_dir)
    assert os.path.isdir(src_agents_dir)

    # Test tests/agents directory
    tests_agents_dir = os.path.join("tests", "agents")
    assert os.path.exists(tests_agents_dir)
    assert os.path.isdir(tests_agents_dir)

    # Test presence of agent subdirectories
    agents = ["lincoln", "shaun"]
    for agent in agents:
        src_agent_dir = os.path.join(src_agents_dir, agent)
        tests_agent_dir = os.path.join(tests_agents_dir, agent)
        
        assert os.path.exists(src_agent_dir)
        assert os.path.isdir(src_agent_dir)
        assert os.path.exists(tests_agent_dir)
        assert os.path.isdir(tests_agent_dir)
