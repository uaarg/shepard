from time import sleep

import src.modules.autopilot.altimeter as altimeter

altimeter = altimeter.XM125()
altimeter.begin()

while True:
    result = altimeter.measure()
    if result:
        print("Average dist: ", result[0]['averaged'][0])

    sleep(0.5)
