"""
Unit Testing for Pytorch Inferences

This unit test verifies that our code can indentify objects in the images we take
using the pytorch model we created
"""

import time
import sys
import unittest

from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if (str(ROOT)) not in sys.path:
    sys.path.append(str(ROOT))  # add root directory to PATH

from image_analysis.inference_yolov5 import setup_ml, analyze_img


class TestPytorchInference(unittest.TestCase):

    # Setup our model to make inferences
    model, imgsz = setup_ml(weights=str(FILE.parents[0]) + "/landing_nano.pt",
                            imgsz=(512, 512),
                            device='cpu')

    def test_blue_landing_pad(self):
        """
        This test analyzed 0.png using our machine learning model

        It should return a blue landing pad
        """

        img_path = str(FILE.parent) + "/0.png"

        # Start a timer for recording inference time
        t = time.time()

        results = analyze_img(path=img_path,
                              model=self.model,
                              imgsz=self.imgsz)

        print(f"Inference Time: {time.time() - t : .3f} secs")

        # check that there is only one detection
        self.assertEqual(
            len(results),
            1,
            msg=f"Inference Model Detected {len(results)} objects, expected 1")

        result = results[0]

        # Check that the type of inference is correct
        self.assertEqual(
            result['type'],
            'blue landing pad',
            msg=
            f"Inference Model Detected {result['type']} objects, expected blue landing pad"
        )

    def test_orange_landing_pad(self):
        """
        This test analyzed 1.png using our machine learning model

        It should return a orange landing pad
        """

        img_path = str(FILE.parent) + "/1.png"

        # Start a timer for recording inference time
        t = time.time()

        results = analyze_img(path=img_path,
                              model=self.model,
                              imgsz=self.imgsz)

        print(f"Inference Time: {time.time() - t : .3f} secs")

        # check that there is only one detection
        self.assertEqual(
            len(results),
            1,
            msg=f"Inference Model Detected {len(results)} objects, expected 1")

        result = results[0]

        # Check that the type of inference is correct
        self.assertEqual(
            result['type'],
            'orange landing pad',
            msg=
            f"Inference Model Detected {result['type']} objects, expected orange landing pad"
        )


if __name__ == '__main__':
    unittest.main()
