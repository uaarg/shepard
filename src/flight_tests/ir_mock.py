from typing import Optional
from src.modules.imaging.detector import IrDetector
import time
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.location import DebugLocationProvider
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector
from src.modules.georeference import inference_georeference
from src.modules.imaging.kml import KMLGenerator, LatLong


from PIL import Image, ImageDraw
from src.modules.autopilot import lander
from src.modules.autopilot import navigator

from dronekit import connect, VehicleMode

import json

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

MAX_VELOCITY = 1

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)


with open('./samples/geofence.json', 'r') as f:
    geofence = json.load(f)['features'][0]['geometry']['coordinates'][0]

time.sleep(2)

origin = (drone.location.global_relative_frame.lon, drone.location.global_relative_frame.lat)

geofence = inference_georeference.Geofence_to_XY(origin, geofence) 

if not geofence:
    # Error handling as origin sometimes returns None, must be something to do with initialization
    time.sleep(2) 
    geofence = inference_georeference.Geofence_to_XY((drone.location.global_relative_frame.lon, drone.location.global_relative_frame.lat), geofence) 

lander = lander.Lander(nav, MAX_VELOCITY, geofence)

print(geofence)

camera = RPiCamera(0)
detector = IrDetector()
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(lander.detectBoundingBox)

analysis.start()

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
drone.groundspeed = 5  # m/s
# start_coords = drone.location.global_relative_frame
time.sleep(2)

nav.send_status_message("Executing landing pad search")
lander.generateSpiralSearch(1)

nav.send_status_message(lander.route)

bounding_boxes = lander.executeSearch(10)

bounding_boxes_meters = bounding_boxes

bounding_boxes = inference_georeference.meters_to_LonLat(origin, bounding_boxes)

kml = KMLGenerator()

for hotspot in bounding_boxes:
    spot = LatLong(hotspot[0], hotspot[1])

    kml.push(spot)

kml.set_source("Crashed Drone", LatLong(24, 24))

kml.generate("out.kml")

nav.send_status_message("Generated KML File!")

nav.send_status_message("Bounding Box coordinates: " + str(bounding_boxes))

nav.send_status_message("Boudning Box Coordinates (meters): " + str(bounding_boxes_meters))



nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")

