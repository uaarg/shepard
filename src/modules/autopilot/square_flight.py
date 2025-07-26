# This will be a flight test script utlizing the navigator class built in navigator.py!

from src.modules.autopilot.navigator import Navigator
from dronekit import connect, VehicleMode
import time

connection_string = '127.0.0.1:14550' # these are just examples and would be replaced with the drones real connection string
messenger_port = 'COM3'# this is also just an example and would be replaced with the real messenger port

# Initialize connection to drone
vehicle = connect(connection_string, wait_ready=True)
navigator = Navigator(vehicle, messenger_port = messenger_port)

# takeoff
vehicle.mode = VehicleMode('GUIDED')
vehicle.armed = True
while not vehicle.armed:
    print('waiting for arming...')
    time.sleep(1)


navigator.takeoff(5)

square_size =10

navigator.set_position_relative(square_size,0)
navigator.set_position_relative(0, square_size)
navigator.set_position_relative(-square_size,0)
navigator.set_position_relative(0, -square_size)

navigator.land()




