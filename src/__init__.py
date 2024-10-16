"""
This program creates a stitcher(mode=SCANS) from openCV, then it downscales a list of images, then passes it onto the stitcher
"""
import cv2 as cv
import os

if __name__ == "__main__":
    file_path = "images/"
    img_list = os.listdir(file_path)
    scaled_images_list =[]
    for i in img_list:
        tmp_img = cv.imread(file_path + i)
        if tmp_img is not None:
            scaled_image = cv.resize(tmp_img, (720,480))
            scaled_images_list.append(scaled_image)

    # Create the stitcher, set mode to SCANS (instead of panorama)
    stitcher = cv.Stitcher.create(cv.Stitcher_SCANS)

    # Call stitch
    status, pano = stitcher.stitch(scaled_images_list[0:11])  # Don't give it too many images at once will crash your pc
    # Print output, if successful return pano
    if status == cv.Stitcher_OK:
        print("Stitching completed successfully.")
        cv.imwrite("pano.png", pano)
    else:
        print("Stitching failed with status code:", status)
        if status == cv.Stitcher_ERR_NEED_MORE_IMGS:
            print("Need more images to stitch.")
        elif status == cv.Stitcher_ERR_HOMOGRAPHY_ESTIMATION_FAILED:
            print("Homography estimation failed.")
        elif status == cv.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL:
            print("Camera parameters adjustment failed.")