import threading
import queue

import asyncio

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from websockets.asyncio.server import ServerConnection


import json


class EmuConnection():
    """
    class representation of a connection to Emu
    """
    
    def __init__(self, hostname: str, port: int):
        self.hostname = hostname
        self.port = port

        self._send_queue = queue.Queue()
        self._recv_queue = queue.Queue()

        # set default onConnect to be a no-op
        self.onConnect = lambda: None

        self.comms_thread = threading.Thread(target=self._start_comms_loop)
        self.comms_thread.start()

    def send_image(self, path: str):
        """
        sends the image at specified path to Emu
        sends as a binary frame
        https://websockets.readthedocs.io/en/stable/reference/asyncio/server.html#websockets.asyncio.server.ServerConnection.send
        ensure text=false. this is however done implicitly when passing bytes like object
        """
        pass

    def send_log(self, message: str, severity: str=""):
        """
        sends a log message to Emu
        message: string of flog
        severity: "normal", "warning", "error"
        """
        content = {
            "type": "log",
            "message": message,
            "severity": severity
        }
        self._send_queue.put(json.dumps(content))

    def _start_comms_loop(self):
        """
        starts connection loop with asyncio
        """
        asyncio.run(self._connect())
        pass

    async def _connect(self):
        """
        starts the server and waits for clients to connect. Once they do,
        self._handler handles each client
        """
        async with serve(self._handler, self.hostname, self.port) as server:
            await server.serve_forever()
    

    async def _handler(self, websocket: ServerConnection):
        """
        manages a single client connection. websocket represents the specific client connection.
        When a client disconnects the handler stops. This does not stop the server
        """
        if self.isConnected:
            print("Connection refused: already connected")
            await websocket.close(code=1000, reason="Already connected")
            return
        self.isConnected = True
        print("Connected to client")
        
        # specified function to do on startup, likely for sending UAV status in bulk
        self.onConnect()

        # exit and close websocket as soon as either task terminates
        consumer_task = asyncio.create_task(self._consumer_handler(websocket))
        producer_task = asyncio.create_task(self._producer_handler(websocket))
        # create two infinite loops. one sends messages in send_queue, other recieves
        # messages and puts into recv_queue
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        print("Client disconnected")
        self.isConnected = False

    
    async def _consumer_handler(self, websocket: ServerConnection):
        """
        handles messages received from the client
        """
        try:
            async for message in websocket:
                # ensure putting does not block event loop
                self._recv_queue.put_nowait(message)
        except ConnectionClosed:
            print("frontend websocket connection lost")


    async def _producer_handler(self, websocket: ServerConnection):
        """
        handles sending messages to the client
        """
        while True:
            try:
                # ensure getting does not block event loop
                message = self._send_queue.get_nowait()
                await websocket.send(message)
            except ConnectionClosedOK:
                break # will shutdown the program
            except queue.Empty:
                # if queue is empty will raise error, catch it and wait
                await asyncio.sleep(0.1)
