import time

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator
from src.modules.autopilot import lander
from src.modules.autopilot import precision_landing


from src.modules import imaging
from dep.labeller.benchmarks.colorfilter import ColorFilterDetector

CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

altitude = 15 # meters
landing_pad = (5, 5) # Dimesnions of the landing pad in meters

detector = ColorFilterDetector()
camera = imaging.camera.RPiCamera()
debugger = imaging.debug.ImageAnalysisDebugger()
analysis = imaging.analysis.ImageAnalysisDelegate(detector, camera, debugger)
landing = precision_landing.PrecisionLanding(drone, landing_pad)

analysis.subscribe(landing.send)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
drone.groundspeed = 2  # m/s
# start_coords = drone.location.global_relative_frame
time.sleep(2)

nav.set_altitude_position_relative(-10, 0, 10)
time.sleep(1)

nav.set_position_relative(0, -10)
time.sleep(1)

nav.send_status_message("Executing landing pad search")
lander.generateRoute(4)

for route in lander.route:
    land = analysis.start() # Execute precision landing whenever landing is started
    if land:
        break
    lander.goNext(nav, route, 10)
    time.sleep(3)
    

nav.land()

drone.close()
nav.send_status_message("Flight test script execution terminated")


