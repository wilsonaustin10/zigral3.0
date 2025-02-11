import asyncio
import json
import os
import pytest
import docker
import socket
import time
from contextlib import closing
from unittest.mock import patch

from src.common.messaging import RabbitMQClient


def wait_for_port(port, host='localhost', timeout=30):
    """Wait for a port to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(1)
    return False


@pytest.fixture(scope="function")
async def rabbitmq_container():
    """Fixture to create a RabbitMQ container for testing."""
    client = docker.from_env()
    
    # Create container with port bindings
    container = client.containers.run(
        "rabbitmq:3-management",
        detach=True,
        remove=True,
        ports={
            '5672/tcp': None,  # Let Docker assign a random port
            '15672/tcp': None
        }
    )
    
    try:
        # Give container time to start
        time.sleep(2)
        
        # Wait for container to be ready and get port mapping
        container.reload()
        amqp_port = int(container.ports['5672/tcp'][0]['HostPort'])
        
        # Wait for the port to be available
        if not wait_for_port(amqp_port):
            pytest.skip(f"RabbitMQ port {amqp_port} not available after timeout")
        
        # Set environment variable for the client
        os.environ["RABBITMQ_URL"] = f"amqp://guest:guest@localhost:{amqp_port}/"
        
        yield container
    
    finally:
        # Cleanup
        try:
            container.stop()
        except:
            pass
        if "RABBITMQ_URL" in os.environ:
            del os.environ["RABBITMQ_URL"]


@pytest.mark.asyncio
async def test_rabbitmq_publish_and_subscribe(rabbitmq_container):
    """Test basic publish and subscribe functionality."""
    client = RabbitMQClient("test_service")
    await client.initialize()
    
    try:
        # Subscribe to test queue
        test_queue = "test_queue"
        received_messages = []
        
        async def message_handler(message):
            received_messages.append(json.loads(message.body.decode()))
            await message.ack()
        
        await client.subscribe(test_queue, message_handler)
        
        # Publish test message
        test_message = {"test": "message"}
        await client.publish_message(test_message, test_queue)
        
        # Wait for message to be received
        await asyncio.sleep(1)
        
        assert len(received_messages) == 1
        assert received_messages[0] == test_message
    
    finally:
        await client.cleanup()


@pytest.mark.asyncio
async def test_invalid_message_format(rabbitmq_container):
    """Test that the client handles invalid message formats appropriately."""
    client = RabbitMQClient("invalid_message_test")
    await client.initialize()
    
    try:
        # Try to publish an invalid message (not JSON serializable)
        test_queue = "test_invalid_queue"
        invalid_message = {"test": lambda x: x}  # Functions are not JSON serializable
        
        with pytest.raises(TypeError):
            await client.publish_message(invalid_message, test_queue)
    
    finally:
        await client.cleanup()


@pytest.mark.asyncio
async def test_connection_timeout(rabbitmq_container):
    """Test that the client handles connection timeouts appropriately."""
    # Stop the RabbitMQ container to simulate a connection timeout
    rabbitmq_container.stop()
    
    client = RabbitMQClient("timeout_test")
    with pytest.raises(ConnectionError):
        await client.initialize()


@pytest.mark.asyncio
async def test_cleanup_during_error(rabbitmq_container):
    """Test that resources are properly cleaned up when an error occurs."""
    client = RabbitMQClient("cleanup_test")
    await client.initialize()
    
    try:
        # Simulate an error during message processing
        test_queue = "test_cleanup_queue"
        event = asyncio.Event()
        
        async def error_handler(message):
            try:
                raise Exception("Simulated error")
            finally:
                event.set()
                await message.ack()
        
        await client.subscribe(test_queue, error_handler)
        
        # Publish a message that will trigger the error
        await client.publish_message({"test": "cleanup"}, test_queue)
        
        # Wait for error to occur
        await asyncio.wait_for(event.wait(), timeout=5)
        
        # Give time for error to propagate
        await asyncio.sleep(0.1)
        
        # Get references to connection and channel
        connection = client.connection
        channel = client.channel
        
        # Cleanup should still work
        await client.cleanup()
        
        # Verify cleanup was successful by checking if connection and channel are closed
        assert connection.is_closed
        assert channel.is_closed
        assert not client.initialized
    
    finally:
        # Ensure cleanup happens even if test fails
        await client.cleanup() 