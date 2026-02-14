"""
benchmark the speed of different trained yolo models
"""

from ultralytics import YOLO
import os
import time
import math
import json


class ModelStats:

    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0

    def update(self, t):
        self.n += 1
        delta = t - self.mean
        self.mean += delta / self.n
        delta2 = t - self.mean
        self.M2 += delta * delta2

    def get_mean(self):
        return self.mean

    def get_stddev(self):
        return math.sqrt(self.M2 / self.n) if self.n > 1 else 0.0


models = os.listdir("models")

images = os.listdir("images")
images = [os.path.join("images", file_name) for file_name in images]

stats = {}

for model_name in models:
    print(model_name)
    model = YOLO(os.path.join("models", model_name))

    model_stats = ModelStats()

    for img_name in images:
        start = time.time()
        results = model(img_name)
        end = time.time()
        model_stats.update(end - start)
    print(f"\tmean: {model_stats.get_mean()}")
    stats[model_name] = {"mean": model_stats.get_mean(), "stddev": model_stats.get_stddev()}


with open("results.json", "w") as f:
    json.dump(stats, f)
