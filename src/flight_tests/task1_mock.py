import time
import threading

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.battery import MAVLinkBatteryStatusProvider

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

mavlink = MAVLinkDelegate()
battery = MAVLinkBatteryStatusProvider(mavlink)

threading.Thread(daemon=True, target=mavlink.run).start()

nav.POSITION_TOLERANCE = 5

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
time.sleep(2)

SPEED = 10  # m/s
ALTITUDE = 20  # m
VOLTAGE_LAP_CUTOFF = 12.0
VOLTAGE_HARD_CUTOFF = 22.4

WAYPOINT_TOP = [53.497200, -113.548800]

WAYPOINT_1 = [53.497200, -113.548800]
WAYPOINT_2 = [53.497200, -113.551600]

# TODO: Set s-curve navigation
waypoints = [[WAYPOINT_1[0] - 0.000100, WAYPOINT_1[1] + 0.000050],
             [WAYPOINT_1[0] - 0.000050, WAYPOINT_1[1] + 0.000200],
             [WAYPOINT_1[0] + 0.000050, WAYPOINT_1[1] + 0.000200],
             [WAYPOINT_1[0] + 0.000100, WAYPOINT_1[1] + 0.000050],
             [WAYPOINT_2[0] + 0.000100, WAYPOINT_2[1] - 0.000050],
             [WAYPOINT_2[0] + 0.000050, WAYPOINT_2[1] - 0.000200],
             [WAYPOINT_2[0] - 0.000050, WAYPOINT_2[1] - 0.000200],
             [WAYPOINT_2[0] - 0.000100, WAYPOINT_2[1] - 0.000050]]

location_top = LocationGlobal(WAYPOINT_TOP[0], WAYPOINT_TOP[1], 30)
locations = [LocationGlobal(wp[0], wp[1], ALTITUDE) for wp in waypoints]

nav.set_position_relative(0, 0)
# nav.set_speed(SPEED)
drone.groundspeed = SPEED

# TODO: Set WPNAV_SPEEDUP param
nav.set_altitude_position(location_top.lat, location_top.lon, location_top.alt, battery, hard_cutoff_enable=False)

LAPS = 5

for i in range(LAPS):
    if not nav.sufficient_battery(battery, VOLTAGE_LAP_CUTOFF):
        nav.send_status_message("Battery lap cutoff reached")
        break
    for location in locations:
        nav.set_altitude_position(location.lat, location.lon, location.alt, battery, VOLTAGE_HARD_CUTOFF)

nav.set_altitude_position(waypoints[0].lat, waypoints[0].lon, waypoints[0].alt)

nav.return_to_launch()

drone.close()

nav.send_status_message("Shepard execution terminated")
