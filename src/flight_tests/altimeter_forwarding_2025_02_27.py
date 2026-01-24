import time

from dronekit import connect

from src.modules.autopilot import navigator
from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider

import json

# Connection settings
CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14550
MAVLINK_ALTITUDE_CONN_STR = "udp:127.0.0.1:14553"

AltimeterData = []
PixHawkData = []
Delta = []

# Test settings
STATUS_INTERVAL = 0.5  # seconds
TEST_DURATION = 600  # 10 minutes

# Connect to the drone
drone = connect(CONN_STR, wait_ready=False)

# Initialize navigator
nav = navigator.Navigator(drone, MESSENGER_PORT)
nav.send_status_message("Altimeter test initializing")

# Initialize the XM125 radar altimeter
radar_sensor = XM125(
    sensor_id=0,
    min_distance=250,
    max_distance=10000,
    average_window=5
)

if not radar_sensor.begin():
    nav.send_status_message("ERROR: Failed to initialize radar sensor")
    drone.close()
    exit(1)

# Create and start the MAVLink altimeter provider
mavlink_altimeter = MavlinkAltimeterProvider(radar_sensor, MAVLINK_ALTITUDE_CONN_STR)
mavlink_altimeter.start()
nav.send_status_message("XM125 Altimeter test starting")

try:
    nav.send_status_message("Forwarding altitude data to Pixhawk")
    # Main loop - forward altitude data and print status
    last_status_time = time.time()
    end_time = time.time() + TEST_DURATION

    while time.time() < end_time:
        # Check if it's time to send a status message
        current_time = time.time()
        if current_time - last_status_time >= STATUS_INTERVAL:
            # Get the latest altimeter reading and log
            result = radar_sensor.measure()
            print(result)
            if result:
                average = result[0]['averaged']
                if average:
                    print(average)
                    AltimeterData.append(average[0])
            
                # Get the latest altitude reading and log
                altitude_m = mavlink_altimeter.get_latest_altitude_meters()
                if altitude_m is not None and average:
                    status_msg = f"Radar Altitude: {altitude_m:.2f} m"
                    nav.send_status_message(status_msg)
                    PixHawkData.append(altitude_m)
                    Delta.append(float(altitude_m) - float(average[0]))

                
            else:
                nav.send_status_message("No valid altitude reading")

            last_status_time = current_time

        # Sleep to avoid consuming too much CPU
        time.sleep(0.05)

except KeyboardInterrupt:
    nav.send_status_message("Test interrupted by user")
except Exception as e:
    nav.send_status_message(f"ERROR: {str(e)}")
finally:
    # Clean up
    nav.send_status_message("Stopping altitude provider")
    mavlink_altimeter.stop()

    nav.send_status_message("Altimeter test completed")
    drone.close()
