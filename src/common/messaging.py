"""
Common messaging module for RabbitMQ integration.

This module provides a common interface for agents to communicate via RabbitMQ.
It handles connection management, message publishing, and subscription.
"""

import json
import os
from typing import Any, Callable, Dict, Optional
import logging
from functools import partial

import aio_pika
from aio_pika import Message, connect_robust, ExchangeType
from aio_pika.abc import AbstractIncomingMessage

from orchestrator.logger import get_logger

# Initialize logger
logger = logging.getLogger(__name__)

class RabbitMQClient:
    """RabbitMQ client for agent communication."""

    def __init__(self, service_name: str):
        """
        Initialize RabbitMQ client.

        Args:
            service_name: Name of the service using this client
        """
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self._connect_func = connect_robust
        self._command_queue: Optional[aio_pika.Queue] = None
        self._response_queue: Optional[aio_pika.Queue] = None
        self.logger = logger

    def set_connect_func(self, func: Callable):
        """Set the connection function for testing.
        
        Args:
            func: Function to use for connecting to RabbitMQ.
        """
        self._connect_func = func

    async def initialize(self) -> None:
        """
        Initialize RabbitMQ connection and channels.

        Raises:
            Exception: If connection fails
        """
        try:
            # Get RabbitMQ URL from environment or use default
            rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
            
            # Connect to RabbitMQ
            self.connection = await self._connect_func(rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare queues
            self._command_queue = await self.channel.declare_queue(
                f"{self.service_name}_commands",
                durable=True
            )
            self._response_queue = await self.channel.declare_queue(
                f"{self.service_name}_responses",
                durable=True
            )
            
            self.logger.info(f"RabbitMQ client initialized for {self.service_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize RabbitMQ client: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Clean up RabbitMQ resources."""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            self.logger.info("RabbitMQ resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up RabbitMQ resources: {str(e)}")

    async def publish_message(
        self, 
        message: Dict[str, Any],
        routing_key: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish a message to RabbitMQ.

        Args:
            message: Message to publish
            routing_key: Routing key for the message
            correlation_id: Optional correlation ID for request-response pattern
        """
        try:
            if not self.channel:
                raise RuntimeError("RabbitMQ channel not initialized")

            # Create message
            message_body = json.dumps(message).encode()
            message = Message(
                message_body,
                content_type="application/json",
                correlation_id=correlation_id
            )

            # Publish message
            await self.channel.default_exchange.publish(
                message,
                routing_key=routing_key
            )
            self.logger.info(f"Published message to {routing_key}")
        except Exception as e:
            self.logger.error(f"Error publishing message: {str(e)}")
            raise

    async def subscribe(
        self,
        queue_name: str,
        callback: Callable[[AbstractIncomingMessage], Any]
    ) -> None:
        """
        Subscribe to a queue.

        Args:
            queue_name: Name of the queue to subscribe to
            callback: Callback function to handle messages
        """
        try:
            if not self.channel:
                raise RuntimeError("RabbitMQ channel not initialized")

            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.consume(callback)
            self.logger.info(f"Subscribed to queue: {queue_name}")
        except Exception as e:
            self.logger.error(f"Error subscribing to queue: {str(e)}")
            raise

    async def handle_command(self, message: AbstractIncomingMessage) -> None:
        """
        Default command handler.

        Args:
            message: Incoming message to handle
        """
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                self.logger.info(f"Received command: {body}")
                
                # Process command and send response
                response = {
                    "status": "received",
                    "command": body,
                    "service": self.service_name
                }
                
                await self.publish_message(
                    response,
                    routing_key=f"{self.service_name}_responses",
                    correlation_id=message.correlation_id
                )
            except Exception as e:
                self.logger.error(f"Error handling command: {str(e)}")
                # Send error response
                error_response = {
                    "status": "error",
                    "error": str(e),
                    "service": self.service_name
                }
                await self.publish_message(
                    error_response,
                    routing_key=f"{self.service_name}_responses",
                    correlation_id=message.correlation_id
                ) 