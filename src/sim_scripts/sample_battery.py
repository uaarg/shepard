import threading
import time

from dronekit import connect

from src.modules.autopilot import navigator
from src.modules.autopilot import lander
from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.battery import MAVLinkBatteryStatusProvider

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

nav.send_status_message("Shepard is online")

mavlink = MAVLinkDelegate()
battery = MAVLinkBatteryStatusProvider(mavlink)


def wait_for_voltage():
    while True:
        try:
            voltage = battery.voltage()
            print("voltage: ", voltage)
        except ValueError:
            pass
            # print("no data yet")
        time.sleep(0.5)


threading.Thread(daemon=True, target=mavlink.run).start()

while True:
    nav.send_status_message(nav.sufficient_battery(battery))
    time.sleep(1)
