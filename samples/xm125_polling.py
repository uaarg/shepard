from time import sleep

import src.modules.autopilot.altimeter as altimeter

altimeter = altimeter.XM125(average_window=5)
altimeter.begin()

while True:
    result = altimeter.measure()
    if result:
        average = result[0]['averaged']

        # Average distance will not be available until at least `average_window` measurements have been taken
        if average:
            average_distance = average[0]

            # `average_distance` can now be used in your autopilot logic
            print("Average dist: ", average_distance)

    sleep(0.5)
