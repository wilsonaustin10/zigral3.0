"""
Agent command handling and RabbitMQ communication for the orchestrator.

This module manages the communication between the orchestrator and individual agents
via RabbitMQ, handling command dispatch and response collection.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from uuid import uuid4

from common.messaging import RabbitMQClient
from .logger import get_logger

logger = get_logger(__name__)

class AgentCommandManager:
    """Manages communication with agents via RabbitMQ."""
    
    def __init__(self):
        """Initialize the command manager."""
        self.mq_client = RabbitMQClient("orchestrator")
        self.response_futures: Dict[str, asyncio.Future] = {}
        
    async def initialize(self):
        """Initialize RabbitMQ connections and set up message handlers."""
        await self.mq_client.initialize()
        
        # Subscribe to response queues from both agents
        await self.mq_client.subscribe("lincoln_responses", self.handle_lincoln_response)
        await self.mq_client.subscribe("shaun_responses", self.handle_shaun_response)
        
    async def handle_lincoln_response(self, message):
        """Handle responses from the Lincoln agent."""
        async with message.process():
            correlation_id = message.correlation_id
            if correlation_id in self.response_futures:
                try:
                    response = json.loads(message.body.decode())
                    self.response_futures[correlation_id].set_result(response)
                except Exception as e:
                    self.response_futures[correlation_id].set_exception(e)
                finally:
                    del self.response_futures[correlation_id]
    
    async def handle_shaun_response(self, message):
        """Handle responses from the Shaun agent."""
        async with message.process():
            correlation_id = message.correlation_id
            if correlation_id in self.response_futures:
                try:
                    response = json.loads(message.body.decode())
                    self.response_futures[correlation_id].set_result(response)
                except Exception as e:
                    self.response_futures[correlation_id].set_exception(e)
                finally:
                    del self.response_futures[correlation_id]
    
    async def execute_lincoln_command(self, command: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the Lincoln agent.
        
        Args:
            command: The command to execute (e.g., "search_profiles", "get_profile_data")
            data: Command-specific parameters
            
        Returns:
            The response from the Lincoln agent
        """
        correlation_id = str(uuid4())
        future = asyncio.get_event_loop().create_future()
        self.response_futures[correlation_id] = future
        
        message = {
            "command": command,
            "data": data
        }
        
        await self.mq_client.publish_message(
            message,
            routing_key="lincoln_commands",
            correlation_id=correlation_id
        )
        
        try:
            return await asyncio.wait_for(future, timeout=60.0)
        except asyncio.TimeoutError:
            del self.response_futures[correlation_id]
            raise TimeoutError(f"Timeout waiting for Lincoln agent response to {command}")
    
    async def execute_shaun_command(self, command: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the Shaun agent.
        
        Args:
            command: The command to execute (e.g., "update_prospects", "get_prospects")
            data: Command-specific parameters
            
        Returns:
            The response from the Shaun agent
        """
        correlation_id = str(uuid4())
        future = asyncio.get_event_loop().create_future()
        self.response_futures[correlation_id] = future
        
        message = {
            "command": command,
            "data": data
        }
        
        await self.mq_client.publish_message(
            message,
            routing_key="shaun_commands",
            correlation_id=correlation_id
        )
        
        try:
            return await asyncio.wait_for(future, timeout=60.0)
        except asyncio.TimeoutError:
            del self.response_futures[correlation_id]
            raise TimeoutError(f"Timeout waiting for Shaun agent response to {command}")
    
    async def execute_action_sequence(self, sequence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a sequence of actions across multiple agents.
        
        Args:
            sequence: The action sequence to execute, containing steps for each agent
            
        Returns:
            List of responses from each step in the sequence
        """
        results = []
        
        for step in sequence.get("steps", []):
            agent = step.get("agent", "").lower()
            action = step.get("action", "")
            
            try:
                if agent == "lincoln":
                    data = {
                        "search_params": step.get("criteria", {}),
                        "profile_urls": step.get("target", []) if isinstance(step.get("target"), list) else [step.get("target")] if step.get("target") else [],
                        "fields": step.get("fields", [])
                    }
                    result = await self.execute_lincoln_command(action, data)
                    
                elif agent == "shaun":
                    data = {
                        "prospects": step.get("data", {}).get("prospects", []),
                        "filters": step.get("criteria", {})
                    }
                    result = await self.execute_shaun_command(action, data)
                    
                else:
                    logger.warning(f"Unknown agent: {agent}")
                    result = {"status": "error", "error": f"Unknown agent: {agent}"}
                
                results.append({
                    "step": step,
                    "result": result
                })
                
                # If a step fails, we might want to stop the sequence
                if result.get("status") == "error":
                    logger.error(f"Step failed: {result.get('error')}")
                    break
                    
            except Exception as e:
                logger.error(f"Error executing step: {str(e)}")
                results.append({
                    "step": step,
                    "result": {
                        "status": "error",
                        "error": str(e)
                    }
                })
                break
        
        return results
    
    async def cleanup(self):
        """Clean up RabbitMQ resources."""
        await self.mq_client.cleanup() 