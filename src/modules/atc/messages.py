"""
Wire format for messages to and from the AEAC telemetry server (ATC).

This is the ONLY module that should know what the server's JSON looks like.
Once the organizers publish the real format, only this file should need to change.

ASSUMPTION: every format here is a placeholder. We don't yet have the
organizers' spec (URL, auth, field names, ACK and airspace message shapes).
Confirm with the VP Technical / Autopilot Leads before relying on it.
"""

import json
import logging
from typing import Any, Dict, Optional

from src.modules.telemetry import TelemetryState

LOGGER = logging.getLogger(__name__)

# ASSUMPTION: message "type" values used by the placeholder protocol
TYPE_TELEMETRY = "telemetry"
TYPE_ACK = "ack"
TYPE_AIRSPACE = "airspace"


def telemetry_to_dict(state: TelemetryState) -> Dict[str, Any]:
    """
    Converts a TelemetryState into the placeholder telemetry message.
    Unknown values (None) are sent as JSON null rather than made up.
    """
    # ASSUMPTION: field names and nesting are placeholders. Units are in the names.
    return {
        "type": TYPE_TELEMETRY,
        "uav_id": state.uav_id,
        "timestamp_unix_s": state.timestamp,
        "lat_deg": state.latitude,
        "lon_deg": state.longitude,
        "alt_agl_m": state.altitude_agl,
        "horizontal_accuracy_m": state.horizontal_accuracy,
        "vertical_accuracy_m": state.vertical_accuracy,
        "battery_percent": state.battery_percent,
        "flight_mode": state.flight_mode,
        "rc_link_quality": state.rc_link_quality,  # 0-1, 1 = best
        "telemetry_link_quality": state.telemetry_link_quality,  # 0-1, 1 = best
    }


def format_telemetry(state: TelemetryState) -> str:
    """Returns the JSON text to send to the telemetry server for this state."""
    return json.dumps(telemetry_to_dict(state))


def parse_message(raw: str) -> Optional[Dict[str, Any]]:
    """
    Parses a message received from the telemetry server.

    Returns None (and logs) for anything that isn't a JSON object, so a bad
    message from the server can never crash a subscriber thread.
    """
    try:
        msg = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        LOGGER.warning("Ignoring non-JSON message from ATC: %r", raw[:200] if isinstance(raw, str) else raw)
        return None

    if not isinstance(msg, dict):
        LOGGER.warning("Ignoring ATC message that is not a JSON object: %r", msg)
        return None

    return msg
