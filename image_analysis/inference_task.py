"""
Multiprocessing Task for Image inferences

This file contains the "Main Loop" for the image analysis process
"""
import os
import cv2 as cv
from multiprocessing import Queue
from image_analysis.inference_yolov5 import setup_ml, analyze_img, annotate_img
from image_analysis.inference_georeference import get_object_location

def inference_main(inference_img_queue, image_analysis_results, model, imgsz, display):
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
        img_data = inference_img_queue.get()
        
        # Print out the results to console
        inference = analyze_img(img_data['img_path'], model=model, imgsz=imgsz, conf_thres=0.10)

        if display:
            print(f"Inference Results: {inference}")
            cv.imshow('Inference Results', annotate_img(img_data['img_path'], inference))
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

        analysis_data = {'img_num' : img_data['img_num'], 'results' : []}
        for obj in inference:
            data_file = f"{os.path.dirname(img_data['img_path'])}/{img_data['img_num']}.json"
            lat, lon = get_object_location(path=data_file, inference=obj)
            if (None in (lat, lon)):
                # This is a false detection, offsets arent real
                continue
            
            analysis_data['results'].append({
                'confidence'    : obj['confidence'],
                'type'          : obj['type'],
                'lat'           : lat,
                'lon'           : lon
            })
        
        # Return this data to the autopilot loop
        image_analysis_results.put(analysis_data)
            


