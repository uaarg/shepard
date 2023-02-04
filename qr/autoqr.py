import cv2
import os
import qr

cam = cv2.VideoCapture(0)
cv2.namedWindow("view")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Frame grab failed.")
        break

    cv2.imwrite("inter.png", frame)
    read = qr.readQRCode("inter.png")

    cv2.imshow("view", frame)
    cv2.waitKey(1)

    if read != "":
        print(read)
        break
    else:
        pass

cam.release()
cv2.destroyAllWindows()
os.remove("inter.png")
