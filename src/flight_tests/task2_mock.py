import time

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander
from src.modules.autopilot import precision_landing

from src.modules import imaging
from dep.labeller.benchmarks.colorfilter import ColorFilterDetector

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

ALTITUDE = 15
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
start_coords = drone.location.global_relative_frame
time.sleep(2)

MAX_GROUND_SPEED = 20
TIME = 5 * 60  # 5 minutes

waypoints = [
                [53.497332, -113.550619, 30],
                [53.496801, -113.550650, 25],
                [53.496801, -113.549702, 20],
                [53.496917, -113.549702, 19],
                [53.496975, -113.549616, 18],
                [53.497028, -113.549499, 17],
                [53.497061, -113.549299, 16],
                [53.497056, -113.549003, 15],
                [53.497302, -113.548999, 12.5],
                [start_coords.lat, start_coords.lon, 10]
            ]

locations = [LocationGlobal(wp[0], wp[1], wp[2]) for wp in waypoints]

speed = nav.optimum_speed(TIME, locations)

#checking to ensure ground speed is safe
assert speed > 0
assert speed < MAX_GROUND_SPEED

#drone.groundspeed = speed
#nav.send_status_message(f"Ground speed set to {speed} m/s")

# workaround to get the speed to set properly for the actual waypoints
nav.set_position_relative(0, 0)

time.sleep(1)
nav.set_speed(speed)
time.sleep(1)

hold_time = 5
accept_radius = 5
pass_radius = 10
yaw = 0



for i, location in enumerate(locations):
    nav.send_status_message(f"Moving to waypoint {i + 1} of {len(locations)}")
    #nav.set_altitude_position(location.lat, location.lon, location.alt, battery=None, hard_cutoff_enable=False)
    nav.circular_waypoint(hold_time, accept_radius, pass_radius, yaw, location.lat, location.lon, location.alt)


nav.send_status_message("Executing landing pad search")
lander.generateRoute(4)

land = analysis.start() # Execute precision landing whenever landing is started
for route in lander.route:
    
    if land:
        break
    lander.goNext(nav, route, 10)
    time.sleep(3)


nav.land()

while drone.armed:
    pass

drone.close()
nav.send_status_message("Flight test script execution terminated")