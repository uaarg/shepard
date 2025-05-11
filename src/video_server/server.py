from http.server import HTTPServer, SimpleHTTPRequestHandler 
import os

# from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.camera import WebcamCamera


class MyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # If the request is for the root, serve index.html
        if self.path == '/':
            self.path = 'src/video_server/index.html'
        else:
            img = cam.capture()
            img.resize((960, 540))
            img.save(IMG_DIR)

        print(self.path)

        return super().do_GET()

class WebServer:

    def __init__(self, port):

        self.port = port
        self.server = None
    
    def run(self):

        #setup server
        self.server = HTTPServer(('', self.port), MyHandler) # Empty string means localhost
        print(f"Server running on http://localhost:{self.port}")
        self.server.serve_forever()

if __name__ == "__main__":
    img_interval = 1 # seconds

    IMG_DIR = "tmp/current_img.jpg"

    # make sure directory exists
    os.makedirs("video_server/tmp/", exist_ok=True)
    
    # cam = RPiCamera(0)
    cam = WebcamCamera()


    # start the webserver
    server = WebServer(8081)
    server.run()
