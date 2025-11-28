from src.modules.emu import Emu
import time
import json

emu = Emu("res")

def onConnect():
    loadCurrent = {
        "type": "load",
        "uavStatus": {
            "connection": "no",
            "mode": "test",
            "imageCount": "2",
            "timeSinceMessage": "3"
        },
        "imageName": "res/sample1.jpg"
    }
    emu.send_msg(json.dumps(loadCurrent))


emu.set_on_connect(onConnect)
emu.start_comms()
print("done start comms")
time.sleep(0.5)

# test different logs
for i in range(6):
    if i % 3 == 0: severity = "normal"
    elif i % 3 == 1: severity = "warning"
    else: severity = "error"
    emu.send_log(f"log text {i}", severity)
    time.sleep(0.5)

# send new photo
emu.send_image("test-image.jpeg")

# change mode
print("asdfasdf")
while True:
    pass
