from dronekit import connect, VehicleMode
from time import sleep


print('Connecting to 127.0.0.1:14550')
vehicle = connect('127.0.0.1:14550', wait_ready = False)

while True:
    roll = vehicle.attitude.roll
    print(roll)
    
    if roll < 0:
        vehicle.mode = 'MANUAL'
    else:
        vehicle.mode = 'RTL'

    sleep(1)
