"""
TelemetrySender: sends telemetry to the telemetry server at 1 Hz (issue #93),
and copies each packet to Emu (issue #104).

This is thread B in the systems design. It reads the latest state from the
telemetry collector (thread C, TelemetryService) and never talks to the
Pixhawk itself.
"""

import json
import logging
import threading
import time
from typing import Optional, Protocol

from src.modules.atc.messages import telemetry_to_dict
from src.modules.telemetry import TelemetryState

LOGGER = logging.getLogger(__name__)


class TelemetrySource(Protocol):
    """Anything that can give a snapshot of telemetry, e.g. TelemetryService."""

    def read(self) -> TelemetryState:
        ...


class TelemetrySink(Protocol):
    """Where telemetry packets go, e.g. ATC."""

    @property
    def connected(self) -> bool:
        ...

    def send_telemetry(self, packet: str) -> bool:
        ...


class EmuSink(Protocol):
    """Anything with Emu's send_msg(), e.g. src.modules.emu.Emu."""

    def send_msg(self, message: str):
        ...


class TelemetrySender:
    # The competition wants telemetry at 1 Hz, not much faster or slower
    SEND_PERIOD_S = 1.0

    # If the collector hasn't updated in this long, its data is stale
    STALE_STATE_S = 3.0

    def __init__(self, source: TelemetrySource, atc: TelemetrySink,
                 emu: Optional[EmuSink] = None, period_s: float = SEND_PERIOD_S):
        """
        Args:
            source: telemetry collector (thread C).
            atc: connection to the telemetry server.
            emu: optional Emu connection; gets a copy of every packet so the
                 ground station still sees telemetry if the server link drops.
            period_s: time between packets. Only change this for tests.
        """
        self._source = source
        self._atc = atc
        self._emu = emu
        self._period_s = period_s

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Counters, handy for logging and for Emu's link status display
        self.sent_count = 0
        self.skipped_count = 0

    def start(self) -> None:
        if self._thread is not None:
            LOGGER.warning("TelemetrySender is already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="atc-telemetry-sender", daemon=True)
        self._thread.start()
        LOGGER.info("Telemetry sender started, period %.2f s", self._period_s)

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None

    def send_once(self) -> None:
        """Reads the current state and sends one packet. Called once per period."""
        state = self._source.read()

        if state.updated_at is None or time.monotonic() - state.updated_at > self.STALE_STATE_S:
            # Still send: the server penalizes gaps, and the packet's fields show what's unknown.
            # ASSUMPTION: sending stale data is better than sending nothing. Confirm with Autopilot Leads.
            LOGGER.warning("telemetry state is stale (collector not updating)")

        packet = telemetry_to_dict(state)
        sent = self._atc.send_telemetry(json.dumps(packet))
        if sent:
            self.sent_count += 1
        else:
            self.skipped_count += 1
            LOGGER.warning("telemetry server not connected, packet not sent")

        if self._emu is not None:
            # ASSUMPTION: placeholder Emu message format. Match it to uaarg/emu#58.
            self._emu.send_msg(json.dumps({
                "type": "telemetry",
                "packet": packet,
                "atc_connected": sent,
            }))

    def _run(self) -> None:
        # Drift-free schedule (same as TelemetryService._run): each target time is the
        # previous target plus one period, so small delays don't add up over a flight.
        next_run = time.monotonic()
        while not self._stop_event.is_set():
            try:
                self.send_once()
            except Exception:
                # One bad cycle must not stop telemetry for the rest of the flight
                LOGGER.exception("telemetry send failed, retrying next period")

            next_run += self._period_s
            wait_time = next_run - time.monotonic()
            if wait_time < 0:
                next_run = time.monotonic()
                wait_time = 0
            self._stop_event.wait(wait_time)
