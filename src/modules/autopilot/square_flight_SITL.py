# flight_test.py
from src.modules.autopilot.navigator import Navigator
from dronekit import connect, VehicleMode
import time
import subprocess
import socket
from collections.abc import MutableMapping

# Function to check if UDP port is open (i.e., SITL running)
def is_sitl_running(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()

# SITL default settings
host = '127.0.0.1'
port = 14550
connection_string = f'{host}:{port}'
messenger_port = f'{host}:{port}'

# Start SITL automatically if not running
if not is_sitl_running(host, port):
    print("Starting SITL...")
    sitl_process = subprocess.Popen([
        "sim_vehicle.py", "-v", "ArduCopter", "-f", "quad", "--console", "--map"
    ])
    # Give SITL a few seconds to start and open the port
    time.sleep(10)
else:
    sitl_process = None
    print("SITL already running")

# Connect to drone
print("Connecting to vehicle...")
vehicle = connect(connection_string, wait_ready=True)
navigator = Navigator(vehicle, messenger_port=messenger_port)

# Takeoff
vehicle.mode = VehicleMode('GUIDED')
vehicle.armed = True
while not vehicle.armed:
    print('Waiting for arming...')
    time.sleep(1)

navigator.takeoff(5)

square_size = 20

# Fly in a square
navigator.set_position_relative(square_size, 0)
navigator.set_position_relative(0, square_size)
navigator.set_position_relative(-square_size, 0)
navigator.set_position_relative(0, -square_size)

# Land
navigator.land()

# Optional: shut down SITL if we started it
if sitl_process:
    print("Stopping SITL...")
    sitl_process.terminate()
