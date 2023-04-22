"""
Multiprocessing Task for Autopilot Functions

This file contains the "Main Loop" which sets up all autopilot 
functions to be executed by our script
"""
from multiprocessing import Queue
from queue import Empty
from enum import Enum
import dronekit
from pymavlink import mavutil
from PIL import Image
import sys, os
import json
from math import ceil
import time
from autopilot.led_controls import setup_leds, set_color

IMAGE_SEND_PERIOD = 30 # no. of seconds to wait before sending each image

DroneStates = Enum('State', ['IDLE', 'TAKEOFF', 'FOLLOW_MISSION', 'LANDING_SEARCH', 'LANDING'])

class AutopilotVars:
    state = DroneStates.IDLE
    # Add any additional variables being tracked here

def autopilot_main(new_images_queue : Queue, images_to_analyze : Queue, image_analysis_results : Queue, 
                   camera_command_queue : Queue, connection_string : str):
    """
    Multiprocessing function called in a separate process for autopilot
    
    This function is executed once and should never return

    This function handles saving GPS information for new images, forwarding
    images for analysis if we are in a "searching" state, and sending waypoints
    to the autopilot controller (PixHawk)
    """

    # One time required setup
    if connection_string != '':
        try:
            vehicle = dronekit.connect(connection_string, source_system=1, source_component=2)

        # Bad TTY connection
        except OSError as e:
            print(f"Autopilot Connection Error: {e.strerror}")
            sys.exit()

        # API Error
        except dronekit.APIException as e:
            print(f"Autopilot Timeout Error: {e}")
            sys.exit()
    else:
        print('No connection was specified for PixHawk, ignoring connection...')
        vehicle = None
    
    led = setup_leds()
    transmit_next_img = Ref(False)
    last_image = None
    #last_image_send = time.time()
    
    if vehicle:
        @vehicle.on_message('MAV_CMD_IMAGE_START_CAPTURE')
        def listener(self, name, message):
            print(f"Recieved {name}")
            camera_command_queue.put("START_CAPTURE")

        @vehicle.on_message('MAV_CMD_IMAGE_STOP_CAPTURE')
        def listener(self, name, message):
            print(f"Recieved {name}")
            camera_command_queue.put("STOP_CAPTURE")
            
        @vehicle.on_message('COMMAND_LONG')
        def listener(self, name, message):
            if message.command == mavutil.mavlink.MAV_CMD_IMAGE_START_CAPTURE:
                camera_command_queue.put("START_CAPTURE")
            elif message.command == mavutil.mavlink.MAV_CMD_IMAGE_STOP_CAPTURE:
                camera_command_queue.put("STOP_CAPTURE")
            elif message.command == 255: # Custom command
                print(f"Recieved Custom Command {int(message.param1)}")
                if int(message.param1) == 1: # Set Mode
                    print(f"Setting Mode to {DroneStates(int(message.param2)).name}")
                    AutopilotVars.state = DroneStates(int(message.param2))
                elif int(message.param1) == 2: # Set Lights
                    print(f"Setting lights {message.param2}")
                    if int(message.param2) == 0:
                        set_color(led, 255, 255, 255)
                    else:
                        set_color(led, 0, 255, 0)
                elif int(message.param1) == 3: # Send Image
                    print(f"Sending Image")
                    transmit_next_img.set(True)
                

    # intermediate variables used in the event loop below
    while True:

        # Check if there are new images to get GPS
        while True:
            try:
                img_data = new_images_queue.get(block=False)
            except Empty:
                break
            
            transmit_text(vehicle, "Hi")
            last_image = img_data['img_path']

            log_image_georeference_data(vehicle, img_data['img_path'], img_data['img_num'], img_data['time'])

            # If the drone is searching for a landing pad or landing, we should analyze these images
            if (AutopilotVars.state == DroneStates.LANDING_SEARCH):
                images_to_analyze.put({'img_path' : img_data['img_path'], 'img_num' : img_data['img_num']})

        # Check if there are new results to analyze
        while True:
            try:
                new_img_results = image_analysis_results.get(block=False)
            except Empty:
                break

            if (AutopilotVars.state == DroneStates.LANDING_SEARCH):
                # handle each found object in the image
                for object in new_img_results['results']:
                    if object['type'] == 'blue landing pad':
                        print('Landing Pad Found, Updating Waypoints...')

                        # TODO: Implement Communication of the new waypoint at object['lat'], object['lon']
                        AutopilotVars.state = DroneStates.LANDING
        
        # This works, but not used for flight test due to message delays
        #should_send = time.time() - last_image_send > IMAGE_SEND_PERIOD
        #if should_send and last_image is not None:
        #    transmit_image(vehicle, last_image)
        #    last_image_send = time.time()
        
        # Check for transmit_next_img
        if transmit_next_img.get() and last_image is not None:
            transmit_image(vehicle, last_image)
            transmit_next_img.set(False)
            
        time.sleep(0.1)

def transmit_text(vehicle, text : str):
    """
    Transmits the provided status string over the Mavlink Connection
    """
    vehicle.message_factory.statustext_send(severity=5, text=text.encode())

class Ref:
    def __init__(self, value):
        self.value = value
        
    def set(self, new_val):
        self.value = new_val
        
    def get(self):
        return self.value

def wait_for_ack(vehicle, cmd_id) -> bool:
    """Waits for an ack for the specific command"""
    done = Ref(False)
    def command_ack(self, name, message):
        print(message)
        if message.command == cmd_id:
            done.set(True)
    print("Waiting for ACK")
    vehicle.add_message_listener("COMMAND_ACK", command_ack)
    try:
        vehicle.wait_for(lambda: done.get(), timeout=5)
        print("Got ACK")
    except dronekit.TimeoutError:
        print("ACK timed out")
        
    vehicle.remove_message_listener("COMMAND_ACK", command_ack)
    return done.get()

def transmit_image(vehicle: dronekit.Vehicle, image_path : str):
    """
    Transmits the provided status string over the Mavlink Connection
    """
    
    # Compress image
    im = Image.open(image_path)
    im = im.resize((200,150), Image.ANTIALIAS)
    im.save(f"{image_path}_cmp.jpg", quality=75)

    with open(f"{image_path}_cmp.jpg", 'rb') as f:
        blob_data = bytearray(f.read())
    
    vehicle.message_factory.camera_image_captured_send(
        time_boot_ms=int(time.time()),
        time_utc=0,
        camera_id=0,
        lat=0,
        lon=0,
        alt=0,
        relative_alt=0,
        q=(1, 0, 0, 0),
        image_index=-1,
        capture_result=1,
        file_url="".encode())
        
    if not wait_for_ack(vehicle, 263):
        return

    ENCAPSULATED_DATA_LEN = 253
    
    vehicle.message_factory.data_transmission_handshake_send(0, len(blob_data), 0, 0, ceil(len(blob_data) / ENCAPSULATED_DATA_LEN), ENCAPSULATED_DATA_LEN, 0)

    if not wait_for_ack(vehicle, 130):
        return

    data = []
    for start in range(0, len(blob_data), ENCAPSULATED_DATA_LEN):
        data_seg = blob_data[start:start+ENCAPSULATED_DATA_LEN]
        data.append(data_seg)
    
    for msg_index, data_seg in enumerate(data):
        if len(data_seg) < ENCAPSULATED_DATA_LEN:
            data_seg.extend(bytearray(ENCAPSULATED_DATA_LEN - len(data_seg)))
        vehicle.message_factory.encapsulated_data_send(msg_index + 1, data_seg)
        time.sleep(0.5)

    vehicle.message_factory.data_transmission_handshake_send(
        0, 
        len(blob_data),
        0, 
        0, 
        ceil(len(blob_data) / ENCAPSULATED_DATA_LEN), 
        ENCAPSULATED_DATA_LEN, 
        0,
        )

    def resend_image_packets(name, message):
        msg_index = message.seqnr
        data_seg = data[msg_index]
        vehicle.message_factory.encapsulated_data_send(msg_index, data_seg)

    #vehicle.add_message_listener("ENCAPSULATED_DATA", resend_image_packets)
    #wait_for_ack(vehicle, 130)
    #vehicle.remove_message_listener("ENCAPSULATED_DATA", resend_image_packets)

def log_image_georeference_data(vehicle, img_path, img_num, timestamp):
    """
    Polls the Pixhawk for the latest GPS information for any image just taken

    This function sends a command to the PixHawk and returns the latest GPS position
    This position is then written to a text file '{img_num}.json' saving all the GPS positions
    """

    if vehicle is None:
        # We are not connected to a vehicle, this function should do nothing
        return

    json_file_path = f"{os.path.dirname(img_path)}/{img_num}.json"

    log = {
        'time'          : timestamp,
        'fixtype'       : vehicle.gps_0.fix_type,
        'lat'           : vehicle.location.global_frame.lat,
        'lon'           : vehicle.location.global_frame.lon,
        'relative_alt'  : vehicle.location.global_relative_frame.alt,
        'alt'           : vehicle.location.global_frame.alt,
        'pitch'         : vehicle.attitude.pitch,
        'roll'          : vehicle.attitude.roll,
        'yaw'           : vehicle.attitude.yaw
    }

    with open(json_file_path, "w") as json_file:
        json.dump(log, json_file, indent=2)


