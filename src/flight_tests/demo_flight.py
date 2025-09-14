from src.modules.imaging.analysis import BeaconAnalysisDelegate 
from src.modules.mavctl.mavctl.connect import conn
from src.modules.mavctl.mavctl.messages.navigator import Navigator, LandingTarget
from src.modules.mavctl.mavctl.messages.messenger import Messenger
from src.modules.mavctl.mavctl.messages import advanced
from src.modules.mavctl.mavctl.messages.location import LocationGlobal
import src.modules.autopilot.mavctl_advanced as mavctl_advanced 
import time

CONN_STR = "udp:127.0.0.1:14551"
mav = conn.connect(CONN_STR)
master = Navigator(mav)
messenger = Messenger(14553)
messenger.send("MAVCTL: Online")

while master.set_mode_wait() and master.wait_vehicle_armed():
    pass

master.takeoff(10)
time.sleep(5)
advanced.simple_goto_local(master, 50, 50, 20)
time.sleep(20)
advanced.simple_goto_local(master, 50, -50, 20)
time.sleep(10)
master.return_to_launch()
