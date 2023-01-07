# importing the python open cv library
import cv2

# intialize the webcam and pass a constant which is 0
webcam = cv2.VideoCapture(0)

# title of the app
cv2.namedWindow('Python Webcam Image Capture App')

# let's assume the number of images gotten is 0
img_counter = 0

# while loop
while True:
    # intializing the frame, ret
    # frame will get the next frame in the camera  
    # ret will obtain return value from getting the camera frame, either true of false
    ret, frame = webcam.read()

    # if statement
    if not ret:
        print('Failed to capture frame.')
        break
    # the frame will show with a title of test
    cv2.imshow('test', frame)

    #to get continuous live video feed from your laptop's webcam
    k  = cv2.waitKey(1)

    # if the escape key is been pressed, the app will stop
    if k % 256 == 27:
        print('Escape hit, closing the app.')
        break

    # if the spacebar key is been pressed
    # screenshots will be taken
    elif k%256  == 32:
        # the format for storing the images scrreenshotted
        img_name = f'opencv_frame_{img_counter}.png'
        
        # saves the image as a png file
        cv2.imwrite(img_name, frame)
        print('Image Captured from Webcam.')
        # the number of images automaticallly increases by 1
        img_counter += 1

# release the camera
webcam.release()

# stops the camera window
webcam.destoryAllWindows()
