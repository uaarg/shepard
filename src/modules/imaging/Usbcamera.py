import cv2

#intialize camera
cap = cv2.VideoCapture(0)

#check if opened
if not cap.isOpened():
    print('errorl Could not open camera')
    exit()

#take 3 sample photos
for i in range(3):
    #capture 1 fram
    ret, frame = cap.read()

    if ret:
        #save captured image to a file
        filename = f'photo{i+1}.jpg'
        cv2.imwrite(filename, frame)
        print(f"image saved as {filename}")
    else:
        print('error: failed to capture image')

cap.release()
print('camera released')