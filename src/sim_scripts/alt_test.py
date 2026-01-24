import src.modules.autopilot.altimeter_xm125 as altimeter
import time

altimeter = altimeter.XM125(average_window=5)
altimeter.begin()

