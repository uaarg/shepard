"""
Runs companion software for handling autopilot scripting, image gathering and analysis

This will will initialize the image analysis, image capture and autopilot scripting 
based on the parsed arguments

Usage:
    $ python main.py (future options here)
"""

import argparse
import os
import sys
from pathlib import Path
import time
from multiprocessing import Process, Queue
from image_analysis.inference_task import inference_main
from image_capture.capture_task import image_capture_main
from autopilot.autopilot_task import autopilot_main
def main(options):
    
    """
    Starts the drone application
    """
    # Create Queues for interprocess Communication
    new_images_queue = Queue()
    images_to_analyze = Queue()
    image_analysis_results = Queue()

    # Some options will be handled by argparse
    analysis_process = Process(target=inference_main, args=(images_to_analyze, image_analysis_results, options.weights, options.imgsz, ))

    # Create separate process for autopilot scripts
    autopilot_process = Process(target=autopilot_main, args=(new_images_queue, images_to_analyze, image_analysis_results, ))

    # Create separate process for image capture
    image_capture_process = Process(target=image_capture_main, args=(new_images_queue, options.capture_rate, options.no_camera, ))

    # Start each process
    analysis_process.start()
    autopilot_process.start()
    image_capture_process.start()

def parse_opt():
    """
    Parses options passed in command line
    """
    parser = argparse.ArgumentParser()
    
    # Machine Learning Options
    parser.add_argument('--weights', default=str(Path(__file__).parents[0])+"/landing_nano.pt",
        help='Path to Machine Learning Model')
    parser.add_argument('--imgsz', default=640, type=int, help='Width/Height to scale images for inferencing')

    # Image Capture Options
    parser.add_argument('--no-camera', default=False, action='store_true', help='Chooses if the script will use the camera')
    parser.add_argument('--capture-rate', default=1, type=float, help='Camera Capture Rate in Seconds')
    
    opts = parser.parse_args()

    # imgsz should be a tuple of pixel height and width
    opts.imgsz = (opts.imgsz, opts.imgsz)

    # For Debugging, we should print out this configuration to console
    print(vars(opts))

    return opts
    
if __name__ == "__main__":
    options = parse_opt()
    main(options)