"""
Multiprocessing Task for Image inferences

This file contains the "Main Loop" for the image capture process
"""
from multiprocessing import Queue
from pathlib import Path
import time
import cv2

def image_capture_main(new_images_queue : Queue, camera_commands_queue : Queue, capture_rate : float, camera : str, camera_port : str, display : bool):
    """
    Multiprocessing function called in a separate process for image capture
    
    This function is executed once and should never return

    This function handles capturing images at a fixed interval and saving these
    to file. It also sends these file paths as they are generated to a queue
    for the autopilot with a timestamp
    """

    # One time required setup
    current_img_index = 1
    
    # open video0
    if camera == "arducam":
        cap = cv2.VideoCapture(camera_port)
        # set width and height, fps
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3264)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2448)
        cap.set(cv2.CAP_PROP_FPS, 15)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    elif camera == "webcam":
        # Used for debugging application
        cap = cv2.VideoCapture(camera_port)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    elif camera == "rpicam2":
        from picamera2 import Picamera2
        cap = Picamera2()
        config = cap.create_still_configuration(main={"size": (800, 600), 'format': 'RGB888'})
        cap.configure(config)
        cap.start()
        
    else:
        cap = None
        print("No Camera Specified: Using Test Images Instead...")
    # add statements for additional camera as supported
        
    capture_enabled = True
    while True:
        while ~(camera_commands_queue.empty()):
            cmd = camera_commands_queue.get()

            if cmd == "START_CAPTURE":
                capture_enabled = True
            elif cmd == "STOP_CAPTURE":
                capture_enabled = False
            else:
                print(f"Unknown Camera Command {cmd}")

            
        if ~capture_enabled:
            time.sleep(1 / capture_rate)
            continue

        timestamp = time.time()
        
        if cap == None:
            img_path = str(Path(__file__).parents[1])+"/tests/pytorch_yolov5_image_inference/0.png"
        elif camera == 'rpicam2':
            frame = cap.capture_array()
            
            img_path = f"logs/{current_img_index}.png"
            cv2.imwrite(img_path, frame)
            if display:
                # Help debug by adding webcam display
                cv2.imshow('Camera', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        else:
            cap.grab()
            ret, frame = cap.read()
            if not ret:
                # Frame is invalid
                print("Failed to capture image!")
                time.sleep(max(0, (1 / capture_rate) + timestamp - time.time()))
                continue
            
            img_path = f"logs/{current_img_index}.png"
            cv2.imwrite(img_path, frame)
            if display:
                # Help debug by adding webcam display
                cv2.imshow('Camera', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


        # Print out the timestamp to console
        print(f"Image Captured, timestamp = {timestamp}")

        # Add the image to the queue for autopilot
        new_images_queue.put({'img_path' : img_path, 'time' : round(1000 * timestamp), 'img_num' : current_img_index})

        # Delay to next image
        current_img_index += 1
        time.sleep(max(0, (1 / capture_rate) + timestamp - time.time()))


