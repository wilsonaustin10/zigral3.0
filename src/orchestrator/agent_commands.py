"""
Agent command handling and RabbitMQ communication for the orchestrator.

This module manages the communication between the orchestrator and individual agents
via RabbitMQ, handling command dispatch and response collection.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime
import logging

from common.messaging import RabbitMQClient
from .logger import get_logger
from .schemas.action_sequence import ActionSequence, ActionResult, ExecutionResult

logger = logging.getLogger(__name__)

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
    
    async def execute_action_sequence(self, sequence: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a sequence of actions across multiple agents.
        
        Args:
            sequence: The action sequence to execute, containing steps for each agent
            
        Returns:
            ExecutionResult containing the results of each step in the sequence
        """
        # Convert dict to ActionSequence model for validation
        action_sequence = ActionSequence(**sequence)
        results = []
        started_at = datetime.utcnow()
        
        for step in action_sequence.steps:
            agent = step.agent.lower()
            action = step.action
            
            try:
                if agent == "lincoln":
                    data = {
                        "search_params": step.criteria or {},
                        "profile_urls": [step.target] if step.target else [],
                        "fields": step.fields or []
                    }
                    raw_result = await self.execute_lincoln_command(action, data)
                    
                elif agent == "shaun":
                    data = {
                        "prospects": step.criteria.get("prospects", []) if step.criteria else [],
                        "filters": step.criteria.get("filters", {}) if step.criteria else {}
                    }
                    raw_result = await self.execute_shaun_command(action, data)
                    
                else:
                    logger.warning(f"Unknown agent: {agent}")
                    raw_result = {"status": "error", "error": f"Unknown agent: {agent}"}
                
                # Convert raw result to ActionResult model
                result = ActionResult(
                    status=raw_result.get("status", "error"),
                    message=raw_result.get("message"),
                    data=raw_result.get("data"),
                    error=raw_result.get("error")
                )
                
                results.append({
                    "step": step.model_dump(),
                    "result": result.model_dump()
                })
                
                # If a step fails, stop the sequence
                if result.status == "error":
                    logger.error(f"Step failed: {result.error}")
                    break
                    
            except Exception as e:
                logger.error(f"Error executing step: {str(e)}")
                error_result = ActionResult(
                    status="error",
                    error=str(e),
                    message="Exception during execution"
                )
                results.append({
                    "step": step.model_dump(),
                    "result": error_result.model_dump()
                })
                break
        
        return ExecutionResult(
            job_id=action_sequence.job_id,
            objective=action_sequence.objective,
            steps=results,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
    
    async def cleanup(self):
        """Clean up RabbitMQ resources."""
        await self.mq_client.cleanup() 