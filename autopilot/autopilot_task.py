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
import sys
from math import ceil
import time
from autopilot.led_controls import setup_leds, set_color
from autopilot.control_scripts import (transmit_text, takeoff, follow_mission,
                                       initiate_landing_search, land,
                                       get_horizontal_dist_to_location)
from autopilot.autopilot_imaging_integration import log_image_georeference_data

IMAGE_SEND_PERIOD = 30  # no. of seconds to wait before sending each image

DroneStates = Enum(
    'State', ['IDLE', 'TAKEOFF', 'FOLLOW_MISSION', 'LANDING_SEARCH', 'LAND'])


class AutopilotVars:
    state = DroneStates.IDLE
    img_being_processed = None
    next_destination = None
    # Add any additional variables being tracked here


def autopilot_main(new_images_queue: Queue, images_to_analyze: Queue,
                   image_analysis_results: Queue, camera_command_queue: Queue,
                   connection_string: str):
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
            vehicle = dronekit.connect(connection_string,
                                       source_system=1,
                                       source_component=2)

        # Bad TTY connection
        except OSError as e:
            print(f"Autopilot Connection Error: {e.strerror}")
            sys.exit()

        # API Error
        except dronekit.APIException as e:
            print(f"Autopilot Timeout Error: {e}")
            sys.exit()
    else:
        print(
            'No connection was specified for PixHawk, ignoring connection...')
        vehicle = None

    led = setup_leds()
    transmit_next_img = Ref(False)
    state_change = Ref(None)
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
            elif message.command == 255:  # Custom command
                print(f"Recieved Custom Command {int(message.param1)}")
                if int(message.param1) == 1:  # Set Mode
                    print(
                        f"Setting Mode to {DroneStates(int(message.param2)).name}"
                    )
                    state_change.set(DroneStates(int(message.param2)))
                elif int(message.param1) == 2:  # Set Lights
                    print(f"Setting lights {message.param2}")
                    if int(message.param2) == 0:
                        set_color(led, 255, 255, 255)
                    else:
                        set_color(led, 0, 255, 0)
                elif int(message.param1) == 3:  # Send Image
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

            last_image = img_data['img_path']

            log_image_georeference_data(vehicle, img_data['img_path'],
                                        img_data['img_num'], img_data['time'])

            # If the drone is searching for a landing pad or landing, we should analyze these images
            if AutopilotVars.state == DroneStates.LANDING_SEARCH:
                images_to_analyze.put({
                    'img_path': img_data['img_path'],
                    'img_num': img_data['img_num']
                })

        # Check if there are new results to analyze
        while True:
            try:
                new_img_results = image_analysis_results.get(block=False)
            except Empty:
                break

            if AutopilotVars.state == DroneStates.LANDING_SEARCH:
                autopilot_handle_inference_results(vehicle, new_img_results)

        # This works, but not used for flight test due to message delays
        #should_send = time.time() - last_image_send > IMAGE_SEND_PERIOD
        #if should_send and last_image is not None:
        #    transmit_image(vehicle, last_image)
        #    last_image_send = time.time()

        # Check for transmit_next_img
        if transmit_next_img.get() and last_image is not None:
            transmit_image(vehicle, last_image)
            transmit_next_img.set(False)

        # Check for state change
        if state_change.get() is not None:
            AutopilotVars.state = state_change.get()
            state_change.set(None)
            if AutopilotVars.state == DroneStates.IDLE:
                pass
            elif AutopilotVars.state == DroneStates.TAKEOFF:
                takeoff(vehicle)
            elif AutopilotVars.state == DroneStates.FOLLOW_MISSION:
                follow_mission(vehicle)
            elif AutopilotVars.state == DroneStates.LANDING_SEARCH:
                initiate_landing_search(vehicle)
            elif AutopilotVars.state == DroneStates.LAND:
                land(vehicle)

        time.sleep(0.1)


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


def transmit_image(vehicle: dronekit.Vehicle, image_path: str):
    """
    Transmits the provided status string over the Mavlink Connection
    """

    # Compress image
    im = Image.open(image_path)
    im = im.resize((200, 150), Image.ANTIALIAS)
    im.save(f"{image_path}_cmp.jpg", quality=75)

    with open(f"{image_path}_cmp.jpg", 'rb') as f:
        blob_data = bytearray(f.read())

    vehicle.message_factory.camera_image_captured_send(time_boot_ms=int(
        time.time()),
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

    vehicle.message_factory.data_transmission_handshake_send(
        0, len(blob_data), 0, 0, ceil(len(blob_data) / ENCAPSULATED_DATA_LEN),
        ENCAPSULATED_DATA_LEN, 0)

    if not wait_for_ack(vehicle, 130):
        return

    data = []
    for start in range(0, len(blob_data), ENCAPSULATED_DATA_LEN):
        data_seg = blob_data[start:start + ENCAPSULATED_DATA_LEN]
        data.append(data_seg)

    for msg_index, data_seg in enumerate(data):
        if len(data_seg) < ENCAPSULATED_DATA_LEN:
            data_seg.extend(bytearray(ENCAPSULATED_DATA_LEN - len(data_seg)))
        vehicle.message_factory.encapsulated_data_send(msg_index + 1, data_seg)
        time.sleep(0.2)

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
        if message.command == mavutil.mavlink.MAV_CMD_REQUEST_IMAGE_CAPTURE:
            msg_index = message.param1
            data_seg = data[msg_index]
            if len(data_seg) < ENCAPSULATED_DATA_LEN:
                data_seg.extend(
                    bytearray(ENCAPSULATED_DATA_LEN - len(data_seg)))
            vehicle.message_factory.encapsulated_data_send(msg_index, data_seg)

    vehicle.add_message_listener("COMMAND_LONG", resend_image_packets)
    wait_for_ack(vehicle, 130)
    vehicle.remove_message_listener("COMMAND_LONG", resend_image_packets)


def autopilot_handle_inference_results(vehicle, new_img_results: dict):
    """
    Takes the output from the imaging analysis and determines next steps
    for our drone to take
    """

    # We should now filter our results so that only objects that are blue landing
    # pads are considered
    new_img_results['results'] = [
        obj for obj in new_img_results['results']
        if obj['type'] == 'blue landing pad'
    ]

    if new_img_results['results'] == []:
        # There were no objects located by our search
        transmit_text(vehicle, "No Landing Pad Found")
        return

    # Our image results must have at least 1 orange landing pad
    # We need to get the result with the highest confidence
    best_landing_pad = max(new_img_results['results'],
                           key=lambda obj: obj['confidence'])

    # Determine the altitude we should make our next waypoint
    target = dronekit.LocationGlobalRelative(lat=best_landing_pad['lat'],
                                             lon=best_landing_pad['lon'])
    #distance = get_horizontal_dist_to_location(vehicle, target)  TODO: what did this compute?
    get_horizontal_dist_to_location(
        vehicle, target)  # The above line, but without the assign
    target.alt = 30

    vehicle.simple_goto(target)
