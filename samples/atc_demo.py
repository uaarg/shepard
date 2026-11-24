"""
Wires the ATC pieces together so you can watch them work.

    # Terminal 1: fake server
    samples/run.sh atc_mock_server
    # Terminal 2: fake telemetry (no drone needed)
    PYTHONPATH=. python3 samples/atc_demo.py
    # Or with real telemetry from SITL (Software In The Loop). Never a real drone.
    PYTHONPATH=. python3 samples/atc_demo.py --sitl tcp:127.0.0.1:14550

Threads:
    A  ATC client: receives server messages onto atc.inbox
    B  TelemetrySender: sends a packet every 1 s
    C  TelemetryService (SITL mode only) or FakeTelemetrySource: collects telemetry
    D  MessageBroker: copies each inbox message to every subscriber queue
"""

import argparse
import logging
import queue
import threading
import time

from src.modules.atc import ATC, MessageBroker, TelemetrySender
from src.modules.atc.messages import TYPE_AIRSPACE, parse_message
from src.modules.telemetry import TelemetryState


class FakeTelemetrySource:
    """Pretends to be TelemetryService: a drone slowly flying north."""

    def __init__(self) -> None:
        self._start = time.monotonic()

    def read(self) -> TelemetryState:
        elapsed_s = time.monotonic() - self._start
        return TelemetryState(
            uav_id="UAARG",
            timestamp=time.time(),
            latitude=53.4955 + elapsed_s * 1e-5,
            longitude=-113.548,
            altitude_agl=10.0,
            horizontal_accuracy=0.8,
            vertical_accuracy=1.2,
            battery_percent=max(0, 100 - int(elapsed_s / 10)),
            flight_mode="armed-automatic",
            rc_link_quality=1.0,
            telemetry_link_quality=None,
            updated_at=time.monotonic(),
        )


def print_subscriber(messages: queue.Queue, stop: threading.Event) -> None:
    """Example subscriber: prints everything the server sends."""
    while not stop.is_set():
        try:
            raw = messages.get(timeout=0.5)
        except queue.Empty:
            continue
        print(f"[print subscriber] {raw}")


def adsb_subscriber(messages: queue.Queue, stop: threading.Event) -> None:
    """
    Placeholder for issue #99: turn airspace messages into ADS-B for ArduPilot.
    The real version would build mavctl ADSBVehicle objects and call
    Navigator.send_adsb_vehicle() (see src/sim_scripts/adsb_test.py).
    """
    while not stop.is_set():
        try:
            raw = messages.get(timeout=0.5)
        except queue.Empty:
            continue
        msg = parse_message(raw)
        if msg is not None and msg.get("type") == TYPE_AIRSPACE:
            print(f"[adsb subscriber] would send {len(msg.get('vehicles', []))} vehicle(s) as ADS-B (TODO #99)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ws://127.0.0.1:8765/ws", help="telemetry server WebSocket URL")
    parser.add_argument("--sitl", metavar="CONN", help="read real telemetry from SITL at this mavctl connection string")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if args.sitl:
        # Imported here so the fake mode doesn't need a MAVLink connection
        from mavctl import Navigator
        from src.modules.telemetry import TelemetryService
        telemetry = TelemetryService(Navigator(ip=args.sitl), uav_id="UAARG")
        telemetry.start()
        source = telemetry
    else:
        source = FakeTelemetrySource()

    atc = ATC(args.url)
    broker = MessageBroker()
    stop = threading.Event()
    threading.Thread(target=print_subscriber, args=(broker.subscribe("print"), stop), daemon=True).start()
    threading.Thread(target=adsb_subscriber, args=(broker.subscribe("adsb"), stop), daemon=True).start()

    atc.start_comms()
    broker.start(atc.get_inbox())
    sender = TelemetrySender(source, atc)
    sender.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        sender.stop()
        broker.stop()
        atc.stop()


if __name__ == "__main__":
    main()
