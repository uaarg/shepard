from src.modules.emu import Emu
import time

emu = Emu("res")

emu.start_comms()
time.sleep(2)

# test different logs
for i in range(6):
    print(f"sending log {i}")
    if i % 3 == 0:
        severity = "normal"
    elif i % 3 == 1:
        severity = "warning"
    else:
        severity = "error"
    emu.send_log(f"log text {i}", severity)
    time.sleep(1)

while True:
    print("sending image")
    emu.send_log("sending image")
    emu.send_image("test-image.jpeg")
    time.sleep(2)
