from src.modules.imaging.camera import GazeboCamera
import os
from src.modules.mavctl.mavctl.connect import conn
from pymavlink import mavutil
from src.modules.mavctl.mavctl.messages.navigator import Navigator
from src.modules.mavctl.mavctl.messages.messenger import Messenger
from src.modules.mavctl.mavctl.messages import advanced
import time

CONN_STR = "udp:127.0.0.1:14551"

mav = conn.Connect(ip = CONN_STR)
master = Navigator(mav.mav)

while master.wait_vehicle_armed():
    pass

while not master.set_mode_wait():
    pass

master.takeoff(10)
time.sleep(5)
advanced.simple_goto_local(master, -10, 0, 5)
time.sleep(5)
advanced.simple_goto_local(master, -10, 1, 5)
time.sleep(5)
advanced.simple_goto_local(master, -9, 0, 5)
time.sleep(5)
advanced.simple_goto_local(master, -10, -1, 5)
time.sleep(5)
advanced.simple_goto_local(master, -11, 0, 5)
time.sleep(5)
