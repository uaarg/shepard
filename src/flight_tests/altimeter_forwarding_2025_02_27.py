import time

from src.modules.mavctl.navigator import Navigator

from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider
from src.modules.autopilot.messenger import Messenger

# Connection settings (see mavctl first_flight example)
CONN_STR = "udp:127.0.0.1:14550"
MAVLINK_ALTITUDE_CONN_STR = CONN_STR
MESSENGER_PORT = 14550

AltimeterData = []
PixHawkData = []
Delta = []

# Test settings
STATUS_INTERVAL = 2.0  # seconds
TEST_DURATION = 600  # 10 minutes

# Establish MAVLink connection to the vehicle using mavctl
drone = Navigator(ip=CONN_STR)

messenger = Messenger(MESSENGER_PORT)
messenger.send("Altimeter test initializing")

# Initialize the XM125 radar altimeter
radar_sensor = XM125(
    sensor_id=0,
    min_distance=250,
    max_distance=10000,
    average_window=5,
)

if not radar_sensor.begin():
    messenger.send("ERROR: Failed to initialize radar sensor")
    raise SystemExit(1)

# Create and start the MAVLink altimeter provider
mavlink_altimeter = MavlinkAltimeterProvider(
    radar_sensor, MAVLINK_ALTITUDE_CONN_STR
)
mavlink_altimeter.start()

messenger.send("XM125 Altimeter test starting")

try:
    messenger.send("Forwarding altitude data to Pixhawk")

    # Main loop - forward altitude data and print status
    last_status_time = time.time()
    end_time = time.time() + TEST_DURATION

    while time.time() < end_time:
        # Check if it's time to send a status message
        current_time = time.time()
        if current_time - last_status_time >= STATUS_INTERVAL:
            # Get the latest altimeter reading and log
            result = radar_sensor.measure()
            if result:
                average = result[0]["averaged"]

                if average:
                    AltimeterData.append(average[0])

            # Get the latest altitude reading and log
            altitude_m = mavlink_altimeter.get_latest_altitude_meters()
            if altitude_m is not None:
                status_msg = f"Radar Altitude: {altitude_m:.2f} m"
                messenger.send(status_msg)
                PixHawkData.append(altitude_m)
                Delta.append(float(altitude_m) - float(average[0]))
            else:
                messenger.send("No valid altitude reading")

            last_status_time = current_time

        # Sleep to avoid consuming too much CPU
        time.sleep(0.5)

except KeyboardInterrupt:
    messenger.send("Test interrupted by user")
except Exception as e:  # pylint: disable=broad-exception-caught
    messenger.send(f"ERROR: {str(e)}")
finally:
    # Clean up
    messenger.send("Stopping altitude provider")
    mavlink_altimeter.stop()

    messenger.send("Altimeter test completed")
