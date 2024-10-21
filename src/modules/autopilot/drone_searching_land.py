# make the drone fly in a spiral direction, starting from the middle of the field
# still needs to be tested thru some simulator

#connecting to drone
from pymavlink import mavutil
import time
import math

#connecting to drone
def connect_drone(connection_string):
    print("Connecting to drone:", connection_string)
    maindrone = mavutil.mavlink_connection(connection_string)
    print("Waiting for heartbeat")
    maindrone.wait_heartbeat()
    print("Heartbeat from system (ID {}) recieved".format(maindrone.target_system))
    return maindrone





#getting the drone ready
def arm_and_takeoff(maindrone, target_altitude):
    #Attempt to set mode to GUIDED
    print("Setting mode to GUIDED...")
    for attempt in range(3):
        maindrone.mav.set_mode_send(
            maindrone.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            4 #guided mode
        )
        ack_msg = maindrone.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack_msg and ack_msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            print("GUIDED mode set successfully.")
            break
        else:
            print(f"Attempt {attempt + 1}: Failed to set mode to GUIDED, result: {ack_msg.result if ack_msg else 'No response'}")
    else:
        print("Failed to set  mode to GUIDED afer multiple attempts.")
        return 




    #send command to arm drone
    print("Arming drone...")
    maindrone.mav.command_long_send(
        maindrone.target_system, maindrone.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 
        1, 0, 0, 0, 0, 0, 0 #arm the drone
    )
    time.sleep(2)




    print("Checking for ARMING response...")
    ack_msg = maindrone.recv_match(type='COMMAND_ACK', blocking=True, timeout = 10)
    if not ack_msg:
        print("No ACK recieved for arming command.")
        return
    if ack_msg.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
        print("Arming failed:", ack_msg.result)
        return

    


    print("Taking off...")
    maindrone.mav.command_long_send(
        maindrone.target_system, maindrone.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0,
        0, 0, 0, 0, 0, 0, target_altitude
    )
    ack_msg = maindrone.recv_match(type='COMMAND_ACK', blocking=True, timeout=10)
    if not ack_msg:
        print("No ACK recieved for takeoff command.")
        return
    if ack_msg.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
        print("Takeoff failed:", ack_msg.result)
        return
    print("Drone is in the air...")






#moving drone to specified location
#done
def goto_position(maindrone, north, east, altitude):
    print(f"Moving to position: North={north}, East={east}, Altitude={altitude}")
    msg = maindrone.mav.set_position_target_local_ned_encode(
        0, 0, 0, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b110111111000, north, east, -altitude, #the beginning of this line acts as a mask to only represent north, east, and down
        0, 0, 0, 0, 0, 0, 0, 0 #these are values (for now initialized to zero) that represent target velocity, target acceleration, target yaw angle, and target yaw rate
    )
    maindrone.mav.send(msg) #this command makes the drone fly to the specified location
    ack_msg = maindrone.recv_match(type='COMMAND_ACK', blocking=True, timeout=10)
    if ack_msg and ack_msg.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
        print(f"Move commnand failed with result: {ack_msg.result}")










#done
#the spiral mechanics
def spiral_search(maindrone, altitude, radius_increment, max_radius):
    north = 0 #since going clockwise and altitude constant, only north and east needed for now
    east = 0
    radius = 0
    angle = 0
    while radius <= max_radius:
        north = radius * math.cos(angle)
        east = radius * math.sin(angle)
        goto_position(maindrone, north, east, altitude)
        time.sleep(2)
        angle += math.pi / 4 #45 degrees clockwise
        radius += radius_increment





#done
def main():
    connection_string = 'udp:127.0.0.1:14550'
    maindrone = connect_drone(connection_string)
    target_altitude = 10
    arm_and_takeoff(maindrone, target_altitude)
    radius_incrememnt = 5
    max_radius = 50
    spiral_search(maindrone, target_altitude, radius_incrememnt, max_radius)

if __name__ == '__main__':
    main()
