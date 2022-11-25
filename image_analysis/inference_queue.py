"""
Multiprocessing queue for Image inferences

This process holds a queue of images to make inferences on
using our ML algorithm. This prevents other processes from being 
locked while our system is finding objects in the image.
"""
from multiprocessing import Queue
from image_analysis.inference_yolov5 import setup_ml, analyze_img

def inference_queue_handler(inference_img_queue, model):
    """
    Multiprocessing function to handle making inferences
    
    This function is continuously executed until the inference_img_queue is
    empty then blocks until a new image is added

    images are added by adding a filepath to the image, not the loaded image
    """

    # One time required setup
    model, imgsz = setup_ml(weights=model, imgsz=(512, 512), device='cpu')
    
    while True:
        # Block until a new image is available
        img_file = inference_img_queue.get()

        # Print out the results to console
        print(analyze_img(img_file, model=model, imgsz=imgsz))

