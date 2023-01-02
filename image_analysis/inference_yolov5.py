#   UAARG - Imaging 2022
"""
This file contains functions to load our machine learning model into memory
and then make inferences on any provided image
"""

import sys
import torch
import cv2 as cv
import numpy as np

from pathlib import Path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if (str(ROOT) + "/third_party/yolov5") not in sys.path:
    sys.path.append(str(ROOT) + "/third_party/yolov5")  # add yolov5 to PATH

from models.common import DetectMultiBackend
from utils.augmentations import letterbox
from utils.general import non_max_suppression, check_img_size, xyxy2xywh, scale_coords
from utils.torch_utils import select_device
from utils.plots import Annotator

def setup_ml(weights='yolov5s.pt', imgsz=(640, 640), device='cpu', data='data/coco128.yaml',
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        ):
    """
    Loads the inference model into memory and other setup
    """

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    imgsz = check_img_size(imgsz, s=model.stride)  # check image size

    # Run inference
    model.warmup(imgsz=(1, 3, *imgsz))  # warmup

    return model, imgsz

def analyze_img(path, model, imgsz=(640, 640),
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        ):
    """
    Runs the model on the supplied images

    Returns a list with dictionary items for each prediction
    """

    # Dataloader
    im0 = cv.imread(path)
    gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh

    im = letterbox(im0, imgsz, stride=model.stride, auto=False, scaleup=False)[0]  # padded resize
    im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    im = np.ascontiguousarray(im)  # contiguous

    im = torch.from_numpy(im).to(model.device)
    im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
    im /= 255  # 0 - 255 to 0.0 - 1.0
    if len(im.shape) == 3:
        im = im[None]  # expand for batch dim
    
    # Inference
    pred = model(im, augment=False, visualize=False)
    
    # NMS
    pred = non_max_suppression(pred, conf_thres, iou_thres, classes=None, agnostic=False, max_det=max_det)

    # Second-stage classifier (optional)
    # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

    results = []
    for i, prediction in enumerate(pred): 
        prediction[:, :4] = scale_coords(im.shape[2:], prediction[:, :4], im0.shape).round()
        for *xyxy, conf, cls in reversed(prediction).tolist():
            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist() 
            results.append({'type': model.names[int(cls)], 'confidence': conf, 'x': xywh[0], 'y': xywh[1], 'w': xywh[2], 'h': xywh[3]})
    return results

def annotate_img(path, inference):
    """
    Returns an annotated image with the given inferences

    Note the inference should be a list of dictionaries 
    with keys 'x', 'y', 'w', 'h', 'type'
    """

    im0 = cv.imread(path)
    height, width = im0.shape[:2]
    im0 = np.ascontiguousarray(im0)
    annotator = Annotator(im0, line_width=3)

    for obj in inference:
        x1 = width * (obj['x'] - obj['w'] / 2)
        y1 = height * (obj['y'] - obj['h'] / 2)
        x2 = width * (obj['x'] + obj['w'] / 2)
        y2 = height * (obj['y'] + obj['h'] / 2)
        annotator.box_label((x1, y1, x2, y2), obj['type'])

    return annotator.result()