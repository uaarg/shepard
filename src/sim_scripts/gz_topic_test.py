import subprocess
import struct
import numpy as np
import time

IMAGE_WIDTH  = 640
IMAGE_HEIGHT = 480

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
    depth = depth.reshape((IMAGE_HEIGHT, IMAGE_WIDTH))
    
    print(depth)


while True:
    get_depth_frame()
    print("\n\n\n\n\n\n")
    time.sleep(0.5)
