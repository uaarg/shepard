from modules.autopilot import navigator
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.camera import DebugCamera, GazeboCamera
from src.modules.imaging.detector import ArucoDetector
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.mavctl.mavctl.messages.navigator import Navigator, LandingTarget
from dep.labeller.loader import Vec2

import subprocess
import math
import time
import threading
import numpy as np

#both FOVs are in degrees
hfov = 68.75
vfov = 53.13 
image_width = 640
image_height = 480
marker_size = 0.5 # meters
alpha = 0.3
focal_length_px = (image_width / 2) / math.tan(math.radians(hfov / 2))
standoff_distance = 0.25 # meters


drone = Navigator(ip="udp:127.0.0.1:14551")


depth_image = None

def depth_callback(msg):
    global depth_image
    depth_image = np.frombuffer(msg.data, dtype=np.float32).reshape(msg.heigth, msg.width)


print(drone.master.mavlink20())

angle_x = 0
angle_y = 0

def broadcast_landing_target(image, bounding_box):
    global angle_x, angle_y, depth_image
    if bounding_box:
            with depth_lock:
                depth = latest_depth
            if depth is not None:
                (x_min, y_min) = bounding_box.position.x, bounding_box.position.y
                (width, height) = bounding_box.size.x, bounding_box.size.y
                
                cx = int(x_min + width / 2.0)
                cy = int(y_min + height / 2.0)

                alt = -drone.get_local_position().down 

                norm_x = (cx - image_width / 2.0) / image_width
                norm_y = (cy - image_height / 2.0) / image_height

                raw_angle_x = norm_x * math.radians(hfov)
                raw_angle_y = norm_y * math.radians(vfov)

                angle_x = alpha * raw_angle_x + (1 - alpha) * angle_x
                angle_y = alpha * raw_angle_y + (1 - alpha) * angle_y
                
                
                region = depth[cy-5:cy+5, cx-5:cx+5]
                valid = region[region > 0]
            
                dist = np.median(valid)


                dist_err = dist - standoff_distance
                angle_y = angle_y + math.atan2(dist_err, dist)
        
                print("Angle_X: " + str(angle_x) + "Angle_Y: " + str(angle_y))

                landing_target = LandingTarget(forward = raw_angle_x, right = -raw_angle_y, altitude = dist)
                drone.broadcast_landing_target(landing_target=landing_target)

def get_depth_frame():
    result = subprocess.run(
        ['gz', 'topic', '-e', '-t', '/depth_camera', '-n', '1'],
        capture_output=True
    )
    
    output = result.stdout
    
    # Find the data field — it's between 'data: "' and '"'
    start = output.find(b'data: "') + 7
    end   = output.rfind(b'"')
    raw   = output[start:end]
    
    # Decode escaped bytes into actual bytes
    raw_decoded = raw.decode('unicode_escape').encode('latin-1')
    
    # Convert to float32 numpy array
    depth = np.frombuffer(raw_decoded, dtype=np.float32)
    depth = depth.reshape((image_height, image_width))
    
    return depth

latest_depth = None
depth_lock = threading.Lock()

def depth_thread():
    global latest_depth
    while True:
        depth = get_depth_frame()
        if depth is not None:
            with depth_lock:
                latest_depth = depth

threading.Thread(target=depth_thread, daemon=True).start()

camera = GazeboCamera()
detector = ArucoDetector()
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(broadcast_landing_target)

analysis.start()

print("Starting analysis")
