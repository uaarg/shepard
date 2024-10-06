# make the drone fly in a spiral direction, starting from the middle of the field
# still needs to be tested thru some simulator


from pymavlink import mavutil
import time
import math

#connecting to drone
def connect_drone(connection_string):
    #create connection to drone
    maindrone = mavutil.mavlink_connection(connection_string)
    # wait for heatbeat message from dron
    maindrone.wait_heartbeat()
    return maindrone

#arm drone and take off
def arm_and_takeoff(maindrone, target_altitude):
    #send connection to drone motors
    maindrone.arducopter_arm()
    # wait till motors are ready
    maindrone.motors_armed_wait()
    maindrone.mav.command_long_send(
        maindrone.target_system, maindrone.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0,
        0, 0, 0, 0, 0, 0, target_altitude)
    time.sleep(10) #waiting for drone to takeoff

# moving drone to specific location
def goto_position(maindrone, north, east, altitude):
    msg = maindrone.mav.set_position_target_local_ned_encode(
        0,0,0, maindrone.mavlink.MAV_FRAME_LOCAL_NED,
        0b110111111000, north, east, -altitude,
        0, 0, 0, 0, 0, 0, 0, 0)
    maindrone.send_mavlink(msg)
    maindrone.recv_match(type='COMMAND_ACK', blocking=True)

def spiral_search(maindrone, altitude, radius_increment, max_radius):
    north, east = 0, 0
    radius = 0
    angle = 0
    while radius <= max_radius:
        north = radius * math.cos(angle)
        east = radius * math.sin(angle)
        goto_position(maindrone, north, east, altitude)
        time.sleep(2)
        angle += math.pi / 4 #angle of spiral tightness
        radius += radius_increment

def main():
    connection_string = 'udp:127.0.0.1:14550' 
    maindrone = connect_drone(connection_string)
    target_altitude = 10 #meters
    arm_and_takeoff(maindrone, target_altitude)
    radius_increment = 5 #meters
    max_radius = 50 #meters
    spiral_search(maindrone, target_altitude, radius_increment, max_radius)



if __name__ == "__main__":
    main()
    