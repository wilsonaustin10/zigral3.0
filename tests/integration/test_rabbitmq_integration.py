import asyncio
import json
import pytest
from src.common.messaging import RabbitMQClient


@pytest.mark.asyncio
async def test_rabbitmq_publish_and_subscribe():
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