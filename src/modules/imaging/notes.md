baseline: simple.py implements just Stitcher.stitch(), which takes ~43 seconds to complete the 30 images found in sample_images
detailed.py takes ~49 to do the same, however is laid out in such a not-so-performant way, upside is we now have (much) more control over the stitching process
simple_sequential tries to tkeep adding stitching the next photo onto a finished version of the previous. it gets up to image 4 on a normal confidence threshold, ~16 at 0.2. On higher thresholds / after more attempts the blending part of stitch() seems to work a little too good lol
manual_stitching.py only does translation: it is fast however innacurate and the smallest change in orientation or camera view can distort the entire image and propogate to subsequent images
## Resources
[OpenCV Feature Detection and Description](https://docs.opencv.org/4.10.0/db/d27/tutorial_py_table_of_contents_feature2d.html)
[OpenCV image stitching tutorial](https://docs.opencv.org/4.x/d8/d19/tutorial_stitcher.html)
