# square_flight_qgc.py
from dronekit import connect, VehicleMode
import time
from src.modules.autopilot.navigator import Navigator

# --- CONNECTION SETTINGS ---
# QGC listens here
connection_string = "udp:127.0.0.1:5770"
messenger_port = 5780  # match your proxy.sh port

# --- CONNECT TO VEHICLE ---
print("Connecting to vehicle...")
vehicle = connect(connection_string, wait_ready=True)

navigator = Navigator(vehicle, messenger_port=messenger_port)

# --- ARM AND TAKEOFF ---
vehicle.mode = VehicleMode('GUIDED')
vehicle.armed = True
while not vehicle.armed:
    print("Waiting for arming...")
    time.sleep(1)

navigator.takeoff(5)  # Take off to 5 meters altitude

# --- FLY IN A SQUARE ---
square_size = 20  # meters

navigator.set_position_relative(square_size, 0)
navigator.set_position_relative(0, square_size)
navigator.set_position_relative(-square_size, 0)
navigator.set_position_relative(0, -square_size)

# --- LAND ---
navigator.land()

print("Flight complete. Vehicle disarmed.")
