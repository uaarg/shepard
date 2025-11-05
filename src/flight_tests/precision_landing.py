from src.modules.imaging.analysis import BeaconAnalysisDelegate 
from src.modules.mavctl.mavctl.messages.navigator import Navigator, LandingTarget
from src.modules.mavctl.mavctl.connect.conn import Connect
from src.modules.mavctl.mavctl.messages.messenger import Messenger
from src.modules.mavctl.mavctl.messages import advanced
from src.modules.mavctl.mavctl.messages.location import LocationGlobal
import src.modules.autopilot.mavctl_advanced as mavctl_advanced 
import time

CONN_STR = "udp:127.0.0.1:14550"
landing_target = LandingTarget(0.5, 0.5, 5) 
print(landing_target)

connect = Connect(ip=CONN_STR)
master = Navigator(connect.mav)


while master.set_mode_wait() and master.wait_vehicle_armed():
    pass
master.takeoff(10)
time.sleep(5)
print("Takeoff complete after sleeping 5 seconds")
master.land(2)
while True:
    master.broadcast_landing_target(landing_target=landing_target)
    print("Landing Target Broadcasted")
    time.sleep(0.5)
