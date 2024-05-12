import pymavlink.dialects.v20.all as dialect
from mavlink import MAVLinkDelegate

class StatusLeds:
    
    "stores the state of LED lights"

    def __init__(self, mavlink: MAVLinkDelegate, RGB=[0,0,0]):
        self.RGB = RGB
        self.mavlinkDelegate = mavlink

    def change_color(self, RGB: list):
        self.RGB = RGB
        #print current color of LED
        if (self.RGB[0] == 255 and self.RGB[1] == 0 and self.RGB[2] == 0): print("RED COLOR")
        elif (self.RGB[0] == 0 and self.RGB[1] == 255 and self.RGB[2] == 0): print("GREEN COLOR")
        elif (self.RGB[0] == 0 and self.RGB[1] == 0 and self.RGB[2] == 255): print("BLUE COLOR")
        else: print(f"RGB values: {self.RGB}")
        self.send_message()

    def send_message(self):
        message =  dialect.MAVLink_debug_vect_message(name=bytes("LED_STATUS", 'utf-8'), 
                                           time_usec=0,
                                           x=self.RGB[0],
                                           y=self.RGB[1],
                                           z=self.RGB[2])
        self.mavlinkDelegate.send(message)
        