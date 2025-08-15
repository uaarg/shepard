from http.server import HTTPServer, SimpleHTTPRequestHandler
from PIL import Image
import io
import os

DUMMY_IMAGE_PATH = "dummy.jpg"

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Requested path: {self.path}")  # Debugging output

        if self.path == "/":
            self.path = "index.html"
            return super().do_GET()

        elif self.path.startswith("/latest.jpg"):
            print("Serving latest image...")
            try:
                image_data = get_dummy_image()  # Get dummy image
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(image_data)))
                self.end_headers()
                self.wfile.write(image_data)
            except Exception as e:
                self.send_error(500, f"Error: {str(e)}")
            return

        return super().do_GET()  # Serve other static files

def get_dummy_image() -> bytes:
    """Creates a dummy image in memory and returns it as a byte stream."""
    image = DUMMY_IMAGE_PATH
    if not os.path.exists(image):
        raise FileNotFoundError(f"Image not found: {image}")
    
    with open(image, "rb") as img_file:
        return img_file.read()  # Read the image as raw bytes


class WebServer:
    def __init__(self, port):
        self.port = port
        self.server = None

    def run(self):
        self.server = HTTPServer(('', self.port), MyHandler)
        print(f"Server running on http://localhost:{self.port}")
        self.server.serve_forever()

if __name__ == "__main__":
    server = WebServer(8000)
    server.run()
