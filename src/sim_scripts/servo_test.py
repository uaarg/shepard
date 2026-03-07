from src.modules.mavctl.navigator import Navigator
import time

CONN_STR = "tcp:127.0.0.1:14550"

drone = Navigator(ip=CONN_STR)

time.sleep(2)

drone.set_servo(1, 1000)

time.sleep(1)
drone.set_servo(1, 1500)
time.sleep(1)
drone.set_servo(1, 2000)

