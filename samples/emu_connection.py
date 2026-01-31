from src.modules.emu import Emu
import time
import json

emu = Emu("res")

# def onConnect():
#     loadCurrent = {
#         "type": "load",
#         "uavStatus": {
#             "connection": "no",
#             "mode": "test",
#             "imageCount": "2",
#             "timeSinceMessage": "3"
#         },
#         "imageName": "res/sample1.jpg"
#     }
#     emu.send_msg(json.dumps(loadCurrent))


# emu.set_on_connect(onConnect)
emu.start_comms()
time.sleep(2)

# test different logs
for i in range(6):
    print(f"sending log {i}")
    if i % 3 == 0: severity = "normal"
    elif i % 3 == 1: severity = "warning"
    else: severity = "error"
    emu.send_log(f"log text {i}", severity)
    time.sleep(0.5)

# send new photo
print("sending image")
emu.send_image("test-image.jpeg")

time.sleep(500)
