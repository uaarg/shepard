from mavctl import Navigator, ADSBVehicle, ADSBAvoidanceConfig
import time

CONN_STR = "udp:127.0.0.1:14551"

drone = Navigator(ip = CONN_STR)

while not drone.wait_for_mode_and_arm():
    pass
drone.takeoff(10)
time.sleep(5)
drone.simple_goto_global(53.4955, -113.548, 10)

while True:
    drone.send_adsb_vehicle(ADSBVehicle(
        icao_address = 0x123456,
        lat=53.4955,
        lon=-113.548,
        altitude=677,
        heading=90,
        hor_velocity=0,
        ver_velocity=0,
        callsign="TEST1",
        squawk=1200,
        ))

    drone.set_adsb_avoidance_params(ADSBAvoidanceConfig(fail_dist_xy=100, fail_dist_z=100, fail_time=0))

    time.sleep(1)


