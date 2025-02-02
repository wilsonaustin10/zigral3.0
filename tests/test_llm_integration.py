import pytest
from orchestrator.llm_integration import generate_action_sequence, _prepare_prompt, _get_system_prompt

pytestmark = pytest.mark.asyncio

async def test_generate_action_sequence():
    """Test generating an action sequence"""
    command = "Find CTOs in San Francisco"
    context = {
        "territory": "San Francisco Bay Area",
        "target_roles": ["CTO", "Chief Technology Officer"]
    }
    
    result = await generate_action_sequence(command, context)
    
    assert isinstance(result, dict)
    assert "objective" in result
    assert "steps" in result
    assert isinstance(result["steps"], list)
    assert len(result["steps"]) > 0
    
    # Verify step structure
    step = result["steps"][0]
    assert "agent" in step
    assert "action" in step
    assert step["agent"] in ["LinkedIn", "GoogleSheets", "Email", "Calendar"]

async def test_generate_action_sequence_without_context():
    """Test generating an action sequence without context"""
    command = "Find CTOs in San Francisco"
    
    result = await generate_action_sequence(command)
    
    assert isinstance(result, dict)
    assert "objective" in result
    assert "steps" in result

def test_prepare_prompt():
    """Test prompt preparation"""
    command = "Find CTOs"
    context = {"territory": "San Francisco"}
    
    prompt = _prepare_prompt(command, context)
    
    assert command in prompt
    assert "territory" in prompt
    assert "San Francisco" in prompt

def test_prepare_prompt_without_context():
    """Test prompt preparation without context"""
    command = "Find CTOs"
    
    prompt = _prepare_prompt(command)
    
    assert command in prompt
    assert "Context" not in prompt

def test_get_system_prompt():
    """Test system prompt retrieval"""
    system_prompt = _get_system_prompt()
    
    assert isinstance(system_prompt, str)
    assert "LinkedIn" in system_prompt
    assert "GoogleSheets" in system_prompt
    assert "Email" in system_prompt
    assert "Calendar" in system_prompt
    assert "JSON" in system_prompt 