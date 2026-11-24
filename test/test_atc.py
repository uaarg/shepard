"""
Tests for the ATC (telemetry server) client pieces. No drone or real server needed:
these use fake telemetry and the local MockTelemetryServer.
"""

import json
import queue
import threading
import time
from typing import List, Optional

from src.modules.atc import ATC, MessageBroker, TelemetrySender
from src.modules.atc.messages import TYPE_ACK, format_telemetry, parse_message, telemetry_to_dict
from src.modules.atc.mock_server import MockTelemetryServer
from src.modules.telemetry import TelemetryState


def wait_until(condition, timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


def make_state() -> TelemetryState:
    return TelemetryState(
        uav_id="UAARG", timestamp=1700000000.0, latitude=53.5, longitude=-113.5,
        altitude_agl=10.0, horizontal_accuracy=0.5, vertical_accuracy=1.0,
        battery_percent=80, flight_mode="armed-automatic", rc_link_quality=1.0,
        telemetry_link_quality=None, updated_at=time.monotonic(),
    )


# ----------------------
# messages.py
# ----------------------
def test_format_telemetry_fields():
    data = json.loads(format_telemetry(make_state()))
    assert data["type"] == "telemetry"
    assert data["uav_id"] == "UAARG"
    assert data["lat_deg"] == 53.5
    assert data["lon_deg"] == -113.5
    assert data["alt_agl_m"] == 10.0
    assert data["battery_percent"] == 80
    assert data["flight_mode"] == "armed-automatic"
    assert data["telemetry_link_quality"] is None  # unknown is sent as null, not made up


def test_format_telemetry_unknown_state():
    data = telemetry_to_dict(TelemetryState())
    assert data["lat_deg"] is None
    assert data["flight_mode"] == "off"


def test_parse_message():
    assert parse_message('{"type": "ack"}') == {"type": "ack"}
    assert parse_message("not json") is None
    assert parse_message("[1, 2]") is None


# ----------------------
# broker.py
# ----------------------
def test_broker_every_subscriber_gets_every_message_in_order():
    broker = MessageBroker()
    a = broker.subscribe("a")
    b = broker.subscribe("b")
    for i in range(10):
        broker.publish(str(i))
    expected = [str(i) for i in range(10)]
    assert [a.get_nowait() for _ in range(10)] == expected
    assert [b.get_nowait() for _ in range(10)] == expected


def test_broker_same_name_returns_same_queue_and_unsubscribe():
    broker = MessageBroker()
    assert broker.subscribe("a") is broker.subscribe("a")
    broker.unsubscribe("a")
    broker.publish("x")  # no subscribers, must not fail


def test_broker_drops_oldest_when_full():
    broker = MessageBroker()
    q = broker.subscribe("slow", maxsize=3)
    for i in range(5):
        broker.publish(str(i))
    assert [q.get_nowait() for _ in range(3)] == ["2", "3", "4"]


def test_broker_thread_moves_messages_from_source():
    broker = MessageBroker()
    q = broker.subscribe("a")
    source: queue.Queue = queue.Queue()
    broker.start(source)
    try:
        source.put("hello")
        assert q.get(timeout=2.0) == "hello"
    finally:
        broker.stop()


def test_broker_concurrent_subscribe_and_publish():
    broker = MessageBroker()
    queues: List[queue.Queue] = []
    lock = threading.Lock()

    def subscriber(i: int) -> None:
        q = broker.subscribe(f"s{i}", maxsize=1000)
        with lock:
            queues.append(q)

    def publisher() -> None:
        for i in range(200):
            broker.publish(str(i))

    threads = [threading.Thread(target=subscriber, args=(i,)) for i in range(20)]
    threads.append(threading.Thread(target=publisher))
    for t in threads:
        t.start()
    for t in threads:
        t.join(5.0)

    assert len(queues) == 20
    # Whatever each subscriber got must be in order (it may have joined part-way)
    for q in queues:
        got = []
        while not q.empty():
            got.append(int(q.get_nowait()))
        assert got == sorted(got)


# ----------------------
# telemetry_sender.py
# ----------------------
class FakeSource:
    def read(self) -> TelemetryState:
        return make_state()


class FakeATC:
    def __init__(self, connected: bool) -> None:
        self._connected = connected
        self.sent: List[str] = []

    @property
    def connected(self) -> bool:
        return self._connected

    def send_telemetry(self, packet: str) -> bool:
        if not self._connected:
            return False
        self.sent.append(packet)
        return True


class FakeEmu:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def send_msg(self, message: str) -> None:
        self.messages.append(message)


def test_sender_sends_at_fixed_rate():
    atc = FakeATC(connected=True)
    period_s = 0.1
    sender = TelemetrySender(FakeSource(), atc, period_s=period_s)
    sender.start()
    time.sleep(1.05)
    sender.stop()
    # About 1.05 / 0.1 + 1 (the first send happens immediately) = 11 packets
    assert 9 <= len(atc.sent) <= 12, len(atc.sent)
    assert json.loads(atc.sent[0])["uav_id"] == "UAARG"


def test_sender_skips_when_disconnected_but_still_tells_emu():
    atc = FakeATC(connected=False)
    emu = FakeEmu()
    sender = TelemetrySender(FakeSource(), atc, emu=emu)
    sender.send_once()
    assert atc.sent == []
    assert sender.skipped_count == 1
    assert len(emu.messages) == 1
    emu_msg = json.loads(emu.messages[0])
    assert emu_msg["atc_connected"] is False
    assert emu_msg["packet"]["lat_deg"] == 53.5


def test_sender_survives_source_errors():
    class BrokenSource:
        def read(self) -> TelemetryState:
            raise RuntimeError("collector exploded")

    sender = TelemetrySender(BrokenSource(), FakeATC(connected=True), period_s=0.05)
    sender.start()
    time.sleep(0.2)
    assert sender._thread is not None and sender._thread.is_alive()
    sender.stop()


# ----------------------
# End to end with the mock server
# ----------------------
def test_atc_end_to_end_with_mock_server():
    server = MockTelemetryServer(port=0)
    server.start()
    atc = ATC(server.url, reconnect_delay_s=0.2)
    broker = MessageBroker()
    acks = broker.subscribe("test")
    sender: Optional[TelemetrySender] = None
    try:
        atc.start_comms()
        broker.start(atc.get_inbox())
        assert wait_until(lambda: atc.connected), "ATC never connected"

        sender = TelemetrySender(FakeSource(), atc, period_s=0.1)
        sender.start()

        assert wait_until(lambda: len(server.get_received()) >= 3), "server got no telemetry"
        assert server.get_received()[0]["uav_id"] == "UAARG"

        ack = parse_message(acks.get(timeout=2.0))
        assert ack is not None and ack["type"] == TYPE_ACK
    finally:
        if sender is not None:
            sender.stop()
        broker.stop()
        atc.stop()
        server.stop()

    assert atc.thread is not None and not atc.thread.is_alive(), "ATC thread did not stop"


def test_atc_reconnects_after_server_restart():
    server = MockTelemetryServer(port=0)
    server.start()
    port = server.port
    atc = ATC(server.url, reconnect_delay_s=0.2)
    try:
        atc.start_comms()
        assert wait_until(lambda: atc.connected), "ATC never connected"

        server.stop()
        assert wait_until(lambda: not atc.connected), "ATC did not notice the disconnect"
        assert atc.send_telemetry("{}") is False  # must not queue while disconnected

        server = MockTelemetryServer(port=port)
        server.start()
        assert wait_until(lambda: atc.connected, timeout_s=10.0), "ATC did not reconnect"
    finally:
        atc.stop()
        server.stop()


def test_atc_stop_while_server_down():
    # Nothing listens on this port, so ATC stays in its reconnect loop
    atc = ATC("ws://127.0.0.1:1/ws", reconnect_delay_s=10.0)
    atc.start_comms()
    time.sleep(0.3)
    atc.stop(timeout=3)
    assert atc.thread is not None and not atc.thread.is_alive(), "stop() did not interrupt reconnect wait"
