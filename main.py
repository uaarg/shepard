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
from image_analysis.inference_queue import inference_queue_handler
def main(options):
    """
    Starts the drone application
    """
    # Create separate process for making inferences on images
    inference_img_queue = Queue()

    # Some options will be handled by argparse
    inference_process = Process(target=inference_queue_handler, args=(inference_img_queue, options.weights, options.imgsz, ))

    # Create separate process for autopilot scripts


    # Create separate process for image capture


    # Start each process
    inference_process.start()

    #testing
    inference_img_queue.put("tests/pytorch_yolov5_image_inference/0.png")
    time.sleep(1)
    inference_img_queue.put("tests/pytorch_yolov5_image_inference/1.png")


def parse_opt():
    """
    Parses options passed in command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', default=str(Path(__file__).parents[0])+"/landing_nano.pt",
        help='Path to Machine Learning Model')
    parser.add_argument('--imgsz', default=640, type=int, help='Width/Height to scale images for inferencing')
    parser.add_argument('--use-camera', default=True, type=bool, help='Chooses if the script will use the camera')
    opts = parser.parse_args()

    # imgsz should be a tuple of pixel height and width
    opts.imgsz = (opts.imgsz, opts.imgsz)

    # For Debugging, we should print out this configuration to console
    print(vars(opts))

    return opts
    
if __name__ == "__main__":
    options = parse_opt()
    main(options)