import asyncio
import json
import os
import time
import socket
from contextlib import closing

import pytest

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
def rabbitmq_container():
    """Fixture to create a RabbitMQ container for testing."""
    import docker
    client = docker.from_env()
    container = client.containers.run(
        "rabbitmq:3-management",
        detach=True,
        remove=True,
        ports={'5672/tcp': None, '15672/tcp': None}
    )
    try:
        # Give container time to start
        time.sleep(2)
        container.reload()
        amqp_port = int(container.ports['5672/tcp'][0]['HostPort'])
        if not wait_for_port(amqp_port):
            pytest.skip(f"RabbitMQ port {amqp_port} not available")
        os.environ["RABBITMQ_URL"] = f"amqp://guest:guest@localhost:{amqp_port}/"
        yield container
    finally:
        try:
            container.stop()
        except Exception:
            pass
        if "RABBITMQ_URL" in os.environ:
            del os.environ["RABBITMQ_URL"]


@pytest.mark.asyncio
async def test_end_to_end_agent_workflow(rabbitmq_container):
    """End-to-end test for agent workflow:

    - Orchestrator sends a command to agent1_commands queue.
    - Agent1 receives the command, processes it, and publishes a response to agent1_responses queue.
    - Orchestrator receives the response and it is verified.
    """
    # Create agent client (simulate agent 'agent1')
    agent_client = RabbitMQClient("agent1")
    await agent_client.initialize()

    # Define command handler for agent: it processes the command and sends a response
    async def command_handler(message):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                # Simulate processing: echo the data with status 'done'
                response = {"status": "done", "data": data.get("data")}
                await agent_client.publish_message(response, "agent1_responses")
            except Exception as e:
                response = {"status": "error", "error": str(e)}
                await agent_client.publish_message(response, "agent1_responses")

    # Agent subscribes to its command queue
    await agent_client.subscribe("agent1_commands", command_handler)

    # Create orchestrator client to send command and receive response
    orchestrator_client = RabbitMQClient("orchestrator")
    await orchestrator_client.initialize()

    # Setup an event to capture the response
    response_event = asyncio.Event()
    response_holder = {}

    async def response_handler(message):
        async with message.process():
            try:
                resp = json.loads(message.body.decode())
                response_holder.update(resp)
                response_event.set()
            except Exception:
                pass

    # Orchestrator subscribes to agent1_responses queue
    await orchestrator_client.subscribe("agent1_responses", response_handler)

    # Orchestrator sends a command to agent1_commands queue
    command_message = {"command": "do_action", "data": "test_payload"}
    await orchestrator_client.publish_message(command_message, "agent1_commands")

    # Wait for the response, with a timeout
    await asyncio.wait_for(response_event.wait(), timeout=5)

    # Assert that the response is as expected
    assert response_holder.get("status") == "done"
    assert response_holder.get("data") == "test_payload"

    # Cleanup clients
    await agent_client.cleanup()
    await orchestrator_client.cleanup() 