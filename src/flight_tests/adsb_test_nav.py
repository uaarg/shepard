from mavctl import Navigator, ADSBVehicle, ADSBAvoidanceConfig
import time

CONN_STR = "tcp:127.0.0.1:14550"

drone = Navigator(ip = CONN_STR)

while not drone.wait_for_mode_and_arm():
    pass
drone.takeoff(15)
time.sleep(5)
drone.simple_goto_global(53.495449, -113.549463, 20)

while True:

    drone.send_adsb_vehicle(ADSBVehicle(
        icao_address = 0x123456,
        lat=53.495449,
        lon=-113.549463,
        altitude=677,
        heading=90,
        hor_velocity=0,
        ver_velocity=0,
        callsign="TEST1",
        squawk=1200,
        ))
    time.sleep(0.5)




