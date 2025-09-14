from src.modules.imaging.analysis import BeaconAnalysisDelegate 
from src.modules.mavctl.mavctl.connect import conn
from src.modules.mavctl.mavctl.messages.navigator import Navigator
from src.modules.mavctl.mavctl.messages.messenger import Messenger
from src.modules.mavctl.mavctl.messages import advanced
from src.modules.mavctl.mavctl.messages.location import LocationGlobal
import src.modules.autopilot.mavctl_advanced as mavctl_advanced 
import time

CONN_STR = "udp:127.0.0.1:14551"
LOCATION = LocationGlobal(lat = 53.4954, lon = -113.5512)

mav = conn.connect(CONN_STR)
master = Navigator(mav)
messenger = Messenger(14553)
#Start the debug imaging analsis delegate
#Broadcasts a fixed lat and lon to the debug imaging analysis delegate for testing purposes for precision landing
beacon_delegate = BeaconAnalysisDelegate(LOCATION, navigator=master)
beacon_delegate.start()
messenger.send("MAVCTL: Online")

while master.set_mode_wait() and master.wait_vehicle_armed():
    pass

master.takeoff(10)
time.sleep(5)
print("Takeoff complete after sleeping 5 seconds")
mavctl_advanced.do_precision_landing(master, beacon_delegate, mode="REQUIRED")
