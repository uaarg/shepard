import time
import os
import sys
from image_analysis.inference_yolov5 import setup_ml, analyze_img


model, imgsz = setup_ml(weights="./tests/pytorch_yolov5_image_inference/landing_nano.pt",
                            imgsz=(512, 512),
                            device='cpu')


"""
This test analyzed 0.png using our machine learning model

It should return a blue landing pad
"""

i = 1    
while True:    

    if os.path.isfile(f"./tests/pytorch_yolov5_image_inference/image ({i}).JPG"):
        img_path = f"./tests/pytorch_yolov5_image_inference/image ({i}).JPG"
    elif os.path.isfile(f"./tests/pytorch_yolov5_image_inference/image ({i}).jpeg"):
        img_path = f"./tests/pytorch_yolov5_image_inference/image ({i}).jpeg"
    elif os.path.isfile(f"./tests/pytorch_yolov5_image_inference/image ({i}).png"):
        img_path = f"./tests/pytorch_yolov5_image_inference/image ({i}).png"
    else: break
        
            
    # Start a timer for recording inference time
    t = time.time()

    results = analyze_img(path=img_path,
                            model=model,
                            imgsz=imgsz)

    print(f"Inference Time: {time.time() - t : .3f} secs")
    i+=1
print("images tested:", i-1)