"""
Runs a fake telemetry server on ws://127.0.0.1:8765/ws for local development.

    samples/run.sh atc_mock_server

Then, in another terminal, run samples/atc_demo.py.
"""

import logging
import time

from src.modules.atc.mock_server import MockTelemetryServer

AIRSPACE_PERIOD_S = 5.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

server = MockTelemetryServer(port=8765, airspace_period_s=AIRSPACE_PERIOD_S)
server.start()
print(f"Mock telemetry server running at {server.url} (Ctrl+C to stop)")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()
