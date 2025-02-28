from time import sleep

import src.modules.autopilot.altimeter_xm125 as altimeter_module

altimeter_module = altimeter_module.XM125(average_window=5)
altimeter_module.begin()

while True:
    result = altimeter_module.measure()
    if result:
        average = result[0]['averaged']

        # Average distance will not be available until at least `average_window` measurements have been taken
        if average:
            average_distance = average[0]

            # `average_distance` can now be used in your autopilot logic
            print("Average dist: ", average_distance)

    sleep(0.5)
