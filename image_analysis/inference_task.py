"""
Multiprocessing Task for Image inferences

This file contains the "Main Loop" for the image analysis process
"""
from multiprocessing import Queue
from image_analysis.inference_yolov5 import setup_ml, analyze_img

def inference_main(inference_img_queue, image_analysis_results, model, imgsz):
    """
    Multiprocessing function to handle making inferences
    
    This function is continuously executed until the inference_img_queue is
    empty then blocks until a new image is added

    images are added by adding a filepath to the image, not the loaded image
    """

    # One time required setup
    model, imgsz = setup_ml(weights=model, imgsz=imgsz, device='cpu')
    
    while True:
        # Block until a new image is available
        img_dict = inference_img_queue.get()
        
        # Print out the results to console
        print(analyze_img(img_dict['img_path'], model=model, imgsz=imgsz))

