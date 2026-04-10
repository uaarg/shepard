from src.modules.imaging.camera import WebcamCamera
# from src.modules.imaging.camera import RPiCamera
import time
import struct
import pickle
import socket


# interval in seconds
interval = 1

cam = WebcamCamera()
# cam = RPiCamera(0)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 8080))

while True:
    img = cam.capture()
    data = pickle.dumps(img)
    message = struct.pack("Q", len(data)) + data

    client_socket.sendall(message)

    time.sleep(interval)
