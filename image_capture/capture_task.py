"""
Multiprocessing Task for Image inferences

This file contains the "Main Loop" for the image capture process
"""
from multiprocessing import Queue
from pathlib import Path
import time

def image_capture_main(new_images_queue, capture_rate, no_camera):
    """
    Multiprocessing function called in a separate process for image capture
    
    This function is executed once and should never return

    This function handles capturing images at a fixed interval and saving these
    to file. It also sends these file paths as they are generated to a queue
    for the autopilot with a timestamp
    """

    # One time required setup
    current_img_index = 1
    # TODO: Camera Initialization
    
    while True:
        timestamp = time.time()
        
        if no_camera:
            img_path = str(Path(__file__).parents[1])+"/tests/pytorch_yolov5_image_inference/0.png"
        else:
            # TODO: Capture image (if you can get a more accurate timestamp, do that)
            img_path = '/'

        # Print out the timestamp to console
        print(f"Image Captured, timestamp = {timestamp}")

        # Add the image to the queue for autopilot
        new_images_queue.put({'img_path' : img_path, 'time' : round(1000 * timestamp), 'img_num' : current_img_index})

        # Delay to next image
        current_img_index += 1
        time.sleep(max(0, (1 / capture_rate) + timestamp - time.time()))


