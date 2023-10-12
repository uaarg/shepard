import cv2
import sys
from image_analysis.inference_yolov5 import setup_ml, annotate_img, analyze_img
# program runs from command line and takes an image file argument which it runs YOLOv5 to annotate
model, imgsz = setup_ml()

try:
    filename = str(sys.argv[1])
    inference = analyze_img(filename, model)
    annotated_image = annotate_img(filename, inference)
    cv2.imwrite("result.png", annotated_image)
except FileNotFoundError:
    print()
    print("Use the tab key to ensure your filepath is correct")
except IndexError:
    print()
    print("Program must be run from command line in the form 'python3 do_inference.py <filepath>'")
    