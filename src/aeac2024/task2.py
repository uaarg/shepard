import time

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator


CALLSIGN = "ALBERTA1"
CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")

nav.takeoff(107)
time.sleep(2)

MAX_GROUND_SPEED = 20
time = navigator.Navigator.time_left("11:20:00")

approach_start = [48.5094444, -71.6450000, 107]
step2 = [48.5091667, -71.6433333, 76]
step3 = [48.5075000, 71.6441667, 61]
point1 = [48.507659, -71.646130, 46]
point2 = [48.507637, -71.646410, 43]
point3 = [48.507541, -71.646732, 40]
point4 = [48.507421, -71.646972, 37]
point5 = [48.507252, -71.647134, 34]
point6 = [48.507105, -71.647211, 32]
approach_end = [48.5069444, -71.6472222, 30.5]

landing_zone = [48.506819, -71.646804, 30]

waypoints = [approach_start, step2, step3, step3, point1, point2, point3, point4, point5, point6, approach_end]
locations = [LocationGlobal(wp[0], wp[1], wp[2]) for wp in waypoints]
landing_zone_location = LocationGlobal(landing_zone[0], landing_zone[1], landing_zone[2])

speed = nav.optimum_speed(time, locations)

if speed > MAX_GROUND_SPEED:
    speed = MAX_GROUND_SPEED

nav.set_position_relative(0, 0)
nav.set_speed(speed)
# nav.set_speed(speed)

time.sleep(1)

nav.set_altitude_position(locations[0].lat, locations[0].lon, locations[0].alt)
time.sleep(30)

for i, location in enumerate(locations[1:]):
    nav.set_altitude_position(location.lat, location.lon, location.alt)

nav.set_altitude_position(landing_zone_location.lat, landing_zone_location.lon, landing_zone_location.alt)
nav.set_heading(100)
time.sleep(5)

nav.land()
drone.close()
