import time
import sys

from pathlib import Path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if (str(ROOT)) not in sys.path:
    sys.path.append(str(ROOT))  # add root directory to PATH
    
from image_analysis.inference_yolov5 import setup_ml, analyze_img

# Setup our model to make inferences
model, imgsz = setup_ml(weights=str(FILE.parents[0]) + "/landing_nano.pt", imgsz=(512, 512), device='cpu')
print(f"Using actual image size {imgsz}")

# Start a timer for recording inference time
t = time.time()

# Make a prediction on a given image
pred = analyze_img(path=str(FILE.parents[0]) + "/0.png", model=model, imgsz=imgsz)
print(f"Execution Time: {time.time() - t : .3f} secs")
print(f"Image Analysis Results: {pred}")
