"""
Telemetry collection service.

Runs on its own thread, collects telemetry from the Pixhawk through
mavctl-python, and keeps it in a lock-protected state variable. Other parts
of Shepard (e.g. the competition-server sender) get a copy with read().
"""

import copy
import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

from mavctl import Navigator
from mavctl.messages.location import PositionAccuracy

LOGGER = logging.getLogger(__name__)


@dataclass
class TelemetryState:
    """One snapshot of the telemetry the competition server needs. None = unknown."""
    uav_id: str = ""
    timestamp: Optional[float] = None               # unix time, seconds
    latitude: Optional[float] = None                # decimal degrees
    longitude: Optional[float] = None               # decimal degrees
    altitude_agl: Optional[float] = None            # metres above takeoff point
    horizontal_accuracy: Optional[float] = None     # metres
    vertical_accuracy: Optional[float] = None       # metres
    battery_percent: Optional[int] = None           # 0-100
    flight_mode: str = "off"                        # off/idle/link-lost/failsafe/armed-pilot/armed-automatic
    rc_link_quality: Optional[float] = None         # 0-1, 1 = best RC link (CONOPS 3.b.viii)
    telemetry_link_quality: Optional[float] = None  # 0-1, TODO: depends on our radio link
    updated_at: Optional[float] = None              # time.monotonic() of the last update


class TelemetryService:
    """Collects Pixhawk telemetry on a background thread into a shared state."""

    # How often the state is refreshed; stops the thread from spinning the CPU
    COLLECT_RATE_HZ = 4.0

    # A message older than this is treated as missing, so stale data isn't reported
    MAX_MESSAGE_AGE_S = 3.0

    def __init__(self, navigator, uav_id: str, rc_rssi_is_crsf_lq: bool = False):
        """
        Args:
            navigator: Connected mavctl Navigator for the drone.
            uav_id: UAV identifier string sent in every telemetry packet.
        """
        self._navigator = navigator
        self._uav_id = uav_id

        # The shared state; only touched while holding self._lock
        self._state = TelemetryState(uav_id=uav_id)
        self._lock = threading.Lock()

        # Adds to time.monotonic() to give GPS-based unix time; None until GPS time arrives
        self._gps_clock_offset: Optional[float] = None

        self._stop_event = threading.Event()

        self._thread: Optional[threading.Thread] = None
        self._rc_rssi_is_crsf_lq = rc_rssi_is_crsf_lq

    # ----------------------
    # Public interface
    # ----------------------
    def start(self) -> None:
        """Starts the collection thread."""
        if self._thread is not None:
            LOGGER.warning("Telemetry service is already running")
            return

        self._stop_event.clear()
        # daemon=True so a stuck thread can never stop Shepard from exiting
        self._thread = threading.Thread(target=self._run, name="telemetry-service", daemon=True)
        self._thread.start()
        LOGGER.info("Telemetry service started at %.1f Hz", self.COLLECT_RATE_HZ)

    def stop(self, timeout: float = 2.0) -> None:
        """Stops the collection thread and waits up to timeout seconds for it."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None
        LOGGER.info("Telemetry service stopped")

    def read(self) -> TelemetryState:
        """Returns a copy of the current telemetry state, timestamped now."""
        # Copy under the same lock the collector uses, so we never see half an update
        with self._lock:
            snapshot = copy.copy(self._state)
            gps_clock_offset = self._gps_clock_offset

        # Stamp the time of reading, so packets read 1 s apart are exactly 1 s apart
        snapshot.timestamp = self._unix_time(gps_clock_offset)
        return snapshot

    # ----------------------
    # Collection thread
    # ----------------------
    def _run(self) -> None:
        """Thread body: refresh the state COLLECT_RATE_HZ times per second."""
        period = 1.0 / self.COLLECT_RATE_HZ
        next_run = time.monotonic()

        while not self._stop_event.is_set():
            try:
                self._collect_once()
            except Exception:  # pylint: disable=broad-exception-caught
                # Log and keep going: one bad cycle must not kill this thread or Shepard
                LOGGER.exception("Telemetry collection failed, retrying next cycle")

            # Rate limit: schedule from the previous target so timing doesn't drift
            next_run = next_run + period
            wait_time = next_run - time.monotonic()
            if wait_time < 0:
                # Fell behind (slow cycle): restart the schedule from now
                next_run = time.monotonic()
                wait_time = 0

            # Event.wait instead of sleep so stop() takes effect immediately
            self._stop_event.wait(wait_time)

    def _collect_once(self) -> None:
        """Reads the newest telemetry and replaces the shared state."""
        # Build the new state outside the lock so read() is never kept waiting
        new_state = TelemetryState(uav_id=self._uav_id)

        gps_clock_offset = self._read_gps_clock_offset()
        new_state.timestamp = self._unix_time(gps_clock_offset)
        self._read_position(new_state)
        self._read_accuracy(new_state)
        self._read_battery(new_state)
        new_state.flight_mode = self._navigator.get_flight_mode()
        rc_link_percent = self._navigator.get_rc_link_percent(
            crsf_lq=self._rc_rssi_is_crsf_lq,
            max_age=self.MAX_MESSAGE_AGE_S,
        )

        if rc_link_percent is None:
            new_state.rc_link_quality = None
        else:
            # CONOPS wants 0-1, 1 = best link
            new_state.rc_link_quality = rc_link_percent / 100.0

        # link-lost: armed, but the RC receiver has lost the transmitter
        # (checked after RC, so it overrides 'failsafe' when the cause is the link)
        if new_state.flight_mode != Navigator.FLIGHT_MODE_OFF:
            if new_state.flight_mode != Navigator.FLIGHT_MODE_IDLE:
                if new_state.rc_link_quality == 0.0:
                    new_state.flight_mode = Navigator.FLIGHT_MODE_LINK_LOST
        # TODO: also link-lost when the telemetry link is lost, once that link is defined

        new_state.telemetry_link_quality = None
        new_state.updated_at = time.monotonic()

        # Swap in the whole new state (and clock offset) at once, under the lock
        with self._lock:
            self._state = new_state
            self._gps_clock_offset = gps_clock_offset

    # ----------------------
    # Field readers (non-blocking: they read mavctl's latest-message cache)
    # ----------------------
    def _latest(self, message_type: str):
        """Newest message of this type, or None if missing or too old."""
        return self._navigator.get_latest_message(message_type, max_age=self.MAX_MESSAGE_AGE_S)

    # Re-sync to GPS time only if it disagrees with our clock by more than this (seconds)
    GPS_CLOCK_RESYNC_S = 1.0

    def _read_gps_clock_offset(self) -> Optional[float]:
        """
        Offset that turns time.monotonic() into GPS-based unix time,
        or None if the autopilot has no GPS time yet.
        """
        # Only the collector thread changes the offset, so reading it here is safe
        current_offset = self._gps_clock_offset
        system_time = self._latest("SYSTEM_TIME")

        # time_unix_usec is 0 until the autopilot has GPS time
        if system_time is None or system_time.time_unix_usec == 0:
            return current_offset

        gps_time = system_time.time_unix_usec / 1_000_000  # microseconds -> seconds
        # Add the time since the message arrived, so the value isn't stale
        message_age = time.time() - system_time._timestamp  # pylint: disable=protected-access
        new_offset = gps_time + message_age - time.monotonic()

        # Set the offset once; only move it for a real jump, not small jitter
        if current_offset is None:
            LOGGER.info("Telemetry timestamps now use GPS time")
            return new_offset

        if abs(new_offset - current_offset) > self.GPS_CLOCK_RESYNC_S:
            LOGGER.warning("GPS time jumped, re-synced telemetry clock")
            return new_offset

        return current_offset

    @staticmethod
    def _unix_time(gps_clock_offset: Optional[float]) -> float:
        """Current unix time in seconds: GPS-based if we have an offset."""
        # Monotonic clock + GPS offset: advances smoothly, never jumps back
        if gps_clock_offset is not None:
            return time.monotonic() + gps_clock_offset

        # No GPS time yet: fall back to the companion computer's clock
        return time.time()

    def _read_position(self, state: TelemetryState) -> None:
        """Latitude/longitude (degrees) and altitude above takeoff point (metres)."""
        position = self._latest("GLOBAL_POSITION_INT")
        if position is None:
            return

        # Before the EKF has a position, ArduPilot sends lat=0, lon=0 as placeholders
        if position.lat == 0 and position.lon == 0:
            return

        state.latitude = position.lat / 1e7    # degE7 -> degrees
        state.longitude = position.lon / 1e7   # degE7 -> degrees
        # relative_alt is height above home (takeoff), used as AGL on a flat field
        state.altitude_agl = position.relative_alt / 1000  # mm -> m

    def _read_accuracy(self, state: TelemetryState) -> None:
        """GPS horizontal/vertical accuracy in metres."""
        gps = self._latest("GPS_RAW_INT")
        if gps is None:
            return

        # h_acc/v_acc are MAVLink 2 extension fields; default 0 = "not provided"
        accuracy = PositionAccuracy(getattr(gps, "h_acc", 0), getattr(gps, "v_acc", 0))
        state.horizontal_accuracy = accuracy.horizontal
        state.vertical_accuracy = accuracy.vertical

    def _read_battery(self, state: TelemetryState) -> None:
        """Battery remaining, 0-100 %."""
        sys_status = self._latest("SYS_STATUS")
        if sys_status is None:
            return

        # -1 means the autopilot doesn't estimate remaining battery
        if sys_status.battery_remaining != -1:
            state.battery_percent = sys_status.battery_remaining
