import atexit
import socket
from gpiozero import Servo

servo = Servo(12)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
port = 1099
s.bind(("", port))

while True:
    try:
        data, _  = s.recvfrom(1024)

        cmd = float(data.decode('utf-8'))
        servo.value = cmd
        print(cmd)
    except KeyboardInterrupt:
        print("shutting down")
        s.close()
