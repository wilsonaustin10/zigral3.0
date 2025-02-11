import asyncio
import json
import os
import pytest
import docker
import socket
from time import sleep, time

from src.common.messaging import RabbitMQClient


@pytest.fixture(scope="module")
def rabbitmq_container():
    client = docker.from_env()
    # Use ephemeral ports by setting the host port to None
    container = client.containers.run(
        "rabbitmq:3-management",
        detach=True,
        ports={'5672/tcp': None, '15672/tcp': None}
    )
    try:
        # Wait for container to be up
        start_time = time()
        while time() - start_time < 30:
            container.reload()
            # Get the ephemeral host port for container's 5672/tcp
            ports = container.attrs['NetworkSettings']['Ports']
            if ports and ports.get('5672/tcp') and ports['5672/tcp'][0].get('HostPort'):
                host_port = ports['5672/tcp'][0]['HostPort']
                # Set the RABBITMQ_URL environment variable so that RabbitMQClient picks it up
                os.environ['RABBITMQ_URL'] = f"amqp://guest:guest@localhost:{host_port}/"
                # Try connecting to the port
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect(("localhost", int(host_port)))
                    s.close()
                    break
                except socket.error:
                    sleep(1)
            else:
                sleep(1)
        else:
            pytest.skip("RabbitMQ container did not start in expected time.")
        yield container
    finally:
        container.stop()
        container.remove()


@pytest.mark.asyncio
async def test_rabbitmq_publish_and_subscribe(rabbitmq_container):
    """Integration test for RabbitMQClient: verifies that a published message is received by a subscriber."""
    service_name = "integration_test"
    client = RabbitMQClient(service_name)
    await client.initialize()
    
    received_messages = []
    event = asyncio.Event()
    
    async def callback(message):
        async with message.process():
            body = message.body.decode("utf-8")
            received_messages.append(body)
            event.set()
    
    # Subscribe to the commands queue for the service
    await client.subscribe(f"{service_name}_commands", callback)
    
    # Publish a test message to the same queue
    test_message = {"test_key": "test_value"}
    await client.publish_message(test_message, f"{service_name}_commands")
    
    try:
        await asyncio.wait_for(event.wait(), timeout=10)
    except asyncio.TimeoutError:
        await client.cleanup()
        pytest.fail("Did not receive message within timeout period.")
    
    await client.cleanup()
    
    assert len(received_messages) > 0, "No messages received."
    received_obj = json.loads(received_messages[0])
    assert received_obj == test_message, "Received message does not match the sent message." 