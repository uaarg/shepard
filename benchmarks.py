import time
import sys
from image_analysis.inference_yolov5 import setup_ml, analyze_img


model, imgsz = setup_ml(weights="./tests/pytorch_yolov5_image_inference/landing_nano.pt",
                            imgsz=(512, 512),
                            device='cpu')


"""
This test analyzed 0.png using our machine learning model

It should return a blue landing pad
"""

img_path = "./tests/pytorch_yolov5_image_inference/0.png"

# Start a timer for recording inference time
t = time.time()

results = analyze_img(path=img_path,
                        model=model,
                        imgsz=imgsz)

print(f"Inference Time: {time.time() - t : .3f} secs")