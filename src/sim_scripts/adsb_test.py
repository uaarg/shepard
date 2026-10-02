from mavctl import Navigator, ADSBVehicle, ADSBAvoidanceConfig
import time

CONN_STR = "udp:127.0.0.1:14551"

drone = Navigator(ip = CONN_STR)

while not drone.wait_for_mode_and_arm():
    pass
while True:

    drone.send_adsb_vehicle(ADSBVehicle(
        icao_address = 0x123456
        lat=53.4955,
        lon=-113.548,
        altitude=1000,
        heading=90,
        hor_velocity=0,
        ver_velocity=1,
        callsign="TEST1",
        squawk=1200,
        ))

    drone.set_adsb_avoidance_params(ADSBAvoidanceConfig(fail_dist_xy=100, fail_dist_z=100, fail_time=5))

    time.sleep(1)



