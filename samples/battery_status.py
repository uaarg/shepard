from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.battery import MAVLinkBatteryStatusProvider
import time
import threading

mavlink = MAVLinkDelegate()
battery = MAVLinkBatteryStatusProvider(mavlink)


def wait_for_voltage():
    while True:
        try:
            voltage = battery.voltage()
            print("voltage: ", voltage)
        except ValueError:
            pass
            #print("no data yet")
        time.sleep(0.5)


threading.Thread(target=wait_for_voltage).start()
mavlink.run()
