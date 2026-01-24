
import time
from threading import Thread
import json


from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander
import src.modules.autopilot.altimeter as altimeter



CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()


altimeter = altimeter.XM125(average_window=5)
altimeter.begin()


RangeFinderData = []
PixHawkData = []
AltDiff = []

LoopDelay = 0.5 # seconds (s), time for the loop to sleep after each iteration

# Function to continuously check the altimeter and also the current altitude data. 

def test(drone, altimeter):
    while True:
        result = altimeter.measure()
        gps_alt = drone.location.global_relative_frame.alt
        if result:
            average = result[0]['averaged']
            # Average distance will not be available until at least `average_window` measurements have been taken
            if average:
                average_distance = average[0]
                print(average_distance)
                RangeFinderData.append(average_distance)
                PixHawkData.append(gps_alt)

                AltDiff.append(float(gps_alt) - float(average_distance))

        time.sleep(LoopDelay)


# Initialize thread to run the altitude logging tool

thread = Thread(target = test, args=(drone, altimeter))
thread.start()
thread.join()


# ... INCLUDE OTHER FLIGHT TEST CODE ....




# AT THE END OF THE FLIGHT SCRIPT FILE

# Dump the data into a json file to be saved
# CHANGE THE DATE IN THE FILE NAME TO SOME SORT OF DESCRIPTOR TO DIFFERENTIATE BETWEEN THIS FILE AND OTHER FLIGHT LOG FILES

alt_data = {
    "rangefinder_data": RangeFinderData,
    "pixhawk_data": PixHawkData,
    "alt_diff": AltDiff
}

with open("./flight_logs/altitude_data_DATE.json", mode="w", encoding="utf-i") as w_file:
    json.dump(alt_data, w_file)
