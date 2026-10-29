from mavctl import Navigator, ADSBVehicle, ADSBAvoidanceConfig
import time

CONN_STR = "tcp:127.0.0.1:14550"

drone = Navigator(ip = CONN_STR)

while not drone.wait_for_mode_and_arm():
    pass
drone.takeoff(15)
time.sleep(5)
drone.simple_goto_global(53.495449, -113.549463, 20)
time.sleep(5)
drone.simple_goto_global(53.495019, -113.549502, 20)
time.sleep(5)
drone.simple_goto_global(53.495019, -113.547657, 20)
