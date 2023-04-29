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

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]

def main(options):
    
    """
    Starts the drone application
    """
    # Get the next available log folder
    save_folder = find_available_save_folder()

    # Create Queues for interprocess Communication
    new_images_queue = Queue()
    images_to_analyze = Queue()
    image_analysis_results = Queue()
    camera_command_queue = Queue()


    # Some options will be handled by argparse
    analysis_process = Process(target=inference_main, args=(images_to_analyze, image_analysis_results, options.weights, options.imgsz, options.display, ))

    # Create separate process for autopilot scripts
    autopilot_process = Process(target=autopilot_main, args=(new_images_queue, images_to_analyze, image_analysis_results, camera_command_queue, options.port))

    # Create separate process for image capture
    image_capture_process = Process(target=image_capture_main, args=(new_images_queue, camera_command_queue, options.capture_rate, options.camera, options.camera_port, options.display, save_folder))

    # Start each process
    analysis_process.start()
    autopilot_process.start()
    image_capture_process.start()

    # Check each second if all processes are alive. If one died, we should terminate all
    while (analysis_process.is_alive() and autopilot_process.is_alive() and image_capture_process.is_alive()):
        time.sleep(1)
    
    analysis_process.terminate()
    autopilot_process.terminate()
    image_capture_process.terminate()

def find_available_save_folder():
    """Creates a new folder in the logs directory"""
    
    num_folders = len([entry for entry in os.scandir(f"{ROOT}/logs") if entry.is_dir()])
    print(f"Found {num_folders} folders in {ROOT}/logs")
    os.mkdir(f"{ROOT}/logs/flight{num_folders+1}")

    return f"{ROOT}/logs/flight{num_folders+1}"

def parse_opt():
    """
    Parses options passed in command line
    """
    parser = argparse.ArgumentParser()
    
    # Machine Learning Options
    parser.add_argument('--weights', default=str(Path(__file__).parents[0])+"/landing_nano.pt",
        help='Path to Machine Learning Model')
    parser.add_argument('--imgsz', default=640, type=int, help='Width/Height to scale images for inferencing')
    parser.add_argument('--display', default=False, action='store_true', help='Creates a window showing the capture and anaylsis results')

    # Image Capture Options
    parser.add_argument('--camera', default='none', help='Camera Name. Supported cameras: arducam, webcam')
    parser.add_argument('--camera-port', default='/dev/video0', help='file path to camera. Try 0, 1, 2 on Windows')
    parser.add_argument('--capture-rate', default=1, type=float, help='Camera Capture Rate in Seconds')
    
    # Autopilot Options
    parser.add_argument('--port', default='', help='Port to connect to Pixhawk with, leave blank for no connection')

    opts = parser.parse_args()

    # imgsz should be a tuple of pixel height and width
    opts.imgsz = (opts.imgsz, opts.imgsz)

    # For Debugging, we should print out this configuration to console
    print(vars(opts))

    return opts
    
if __name__ == "__main__":
    options = parse_opt()
    main(options)
