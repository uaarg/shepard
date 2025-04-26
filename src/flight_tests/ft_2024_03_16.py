import time from dronekit import connect, VehicleMode from src.modules.autopilot import navigator from src.modules.autopilot import lander CONN_STR = "udp:127.0.0.1:14551" MESSENGER_PORT = 14552 drone = connect(CONN_STR, wait_ready=False) nav = navigator.Navigator(drone, MESSENGER_PORT) lander = lander.Lander(nav) nav.send_status_message("Shepard is online") while not (drone.armed and drone.mode == VehicleMode("GUIDED")): pass nav.send_status_message("Executing mission") time.sleep(2) nav.takeoff(10) drone.groundspeed = 2  # m/s start_coords = drone.location.global_relative_frame
time.sleep(2)

nav.set_altitude_position_relative(20, 0, 10)
time.sleep(1)


nav.send_status_message("Executing landing pad search")
lander.generateRoute(16)

nav.send_status_message(lander.route)

for route in lander.route:
    lander.goNext(route, 10)
    time.sleep(5)

# nav.set_position(start_coords.lat, start_coords.lon)
# time.sleep(1)
# nav.land()

nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")
