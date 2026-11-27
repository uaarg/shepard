import time
import logging
import dotenv
import os
from queue import Queue
from src.modules.emu.websocket import AeacClient
from src.modules.emu.subscriber import Subscriber


def wait_until(condition, timeout=5.0, interval=0.5):
    """
    Sleeps until the condition is satisfied or the timer runs out.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()

def find_event(q: Queue, event, timeout=5.0):
    """
    Get from the queue until a message with the given event is found
    or the timer runs out.
    """
    deadline = time.monotonic() + timeout
    seen = []
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AssertionError(f"No message of type {event} found in {timeout}s, seen: {seen}")
        if q.empty():
            continue
        msg: dict = q.get(timeout=remaining)
        if msg.get('event') == 'error':
            raise AssertionError(f"Server returned 'error': {msg.get('message')}")
        if msg.get('event') == event:
            return msg
        else:
            seen.append(msg)

def test_aeac_client():
    """
    Establish a connection to the AEAC telemetry server and test communications 
    between the server and client.
    """
    dotenv.load_dotenv()
    assert os.getenv("URL"), "URL .env variable does not exist"
    assert os.getenv("TOKEN"), "TOKEN .env variable does not exist"

    aeac_client = AeacClient()

    client_logger = aeac_client.log
    client_logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    client_logger.addHandler(console_handler)

    client_logger.debug(aeac_client.name)

    # Try stopping before a WebSocket connection exists
    aeac_client.stop()

    time.sleep(0.5)
    aeac_client.start_comms()
    
    try:
        assert wait_until(lambda: aeac_client.connected), "client never connected"
        subscriber_list = aeac_client.subscriber_list
        subscriber1 = subscriber_list.subscribe("subscriber1")
        subscriber2 = subscriber_list.subscribe("subscriber2")
        
        assert isinstance(subscriber1, Subscriber), \
            f"Expected type 'Subscriber', got subscriber1: '{type(subscriber1).__name__}'"
        
        assert isinstance(subscriber2, Subscriber), \
            f"Expected type 'Subscriber', got subscriber2: '{type(subscriber2).__name__}'"

        aeac_client.telemetry_request()

        sub1_msg = find_event(subscriber1.receive_queue, "telemetry_ack")
        sub2_msg = find_event(subscriber2.receive_queue, "telemetry_ack")

        assert sub1_msg == sub2_msg, "subscribers received different acks"
    finally:
        aeac_client.stop()
    
    assert wait_until(lambda: not aeac_client.connected), "client is still connected after calling stop()"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_aeac_client()
