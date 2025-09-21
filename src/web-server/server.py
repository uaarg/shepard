from http.server import HTTPServer, SimpleHTTPRequestHandler


class MyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # If the request is for the root, serve index.html
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()


class WebServer:

    def __init__(self, port):
        self.port = port
        self.server = None

    def run(self):
        # setup server
        self.server = HTTPServer(('', self.port), MyHandler)  # Empty string means localhost
        print(f"Server running on http://localhost:{self.port}")
        self.server.serve_forever()


if __name__ == "__main__":
    server = WebServer(8080)
    server.run()
