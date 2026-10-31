import logging
import time
from datetime import datetime

from mavctl import Navigator

from src.modules.telemetry import TelemetryService

# Show the service's own INFO/ERROR logs; hide mavctl's per-reading DEBUG lines
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logging.getLogger("mavctl.messages.navigator").setLevel(logging.INFO)

# Port the SITL drone is forwarded to
CONN_STR = "udp:127.0.0.1:14551"

# Competition requires one telemetry packet per second
SEND_PERIOD_S = 1.0

drone = Navigator(ip=CONN_STR)

# Collector runs on its own thread from here on
telemetry = TelemetryService(drone, uav_id="UAARG")
telemetry.start()

next_send = time.monotonic()

while True:
    # Lock-protected copy of the latest state
    state = telemetry.read()

    # Millisecond timestamp so you can check the spacing is 1.000 s
    now_text = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{now_text}  mode={state.flight_mode}  "
          f"lat={state.latitude}  lon={state.longitude}  agl={state.altitude_agl}  "
          f"h_acc={state.horizontal_accuracy}  v_acc={state.vertical_accuracy}  "
          f"batt={state.battery_percent}  rc={state.rc_link_quality}  "
          f"ts={state.timestamp}")

    # Schedule from the previous target time, not from now, so delays don't add up
    next_send = next_send + SEND_PERIOD_S
    sleep_time = next_send - time.monotonic()
    if sleep_time > 0:
        time.sleep(sleep_time)
