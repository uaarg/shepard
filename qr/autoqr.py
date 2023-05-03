import cv2
import time
import qr


cam = cv2.VideoCapture(0)
cv2.namedWindow("view")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Frame grab failed.")
        break
    cv2.imwrite("inter.png", frame)
    cv2.imshow("view", frame)

    read = qr.readQRCode("inter.png")
    if read != "":
        print(read)
        break
    else:
        print("no qr code/text found.")

    time.sleep(1)


cam.release()
cv2.destroyAllWindows()

