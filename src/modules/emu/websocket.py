import aiohttp
import asyncio
import threading
import queue
import logging
from aiohttp import web
from typing import Optional, Union

class WebSocketBase:
    def __init__(self, name: str):
        self.log = logging.getLogger(f"shepard.ws.{name}")
        self.thread: Optional[threading.Thread] = None
        self.send_queue: queue.Queue = queue.Queue()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected = False

    def start_comms(self):
        """
        Initializes a new thread which runs the WebSocket connection event loop.
        """
        self.thread = threading.Thread(target=self.run_event_loop, daemon=True)
        self.thread.start()

    async def main(self):
        """
        Defines the WebSocket event loop.
        """
        self.loop = asyncio.get_running_loop()
        self.run_connection()
        
    def stop(self):
        """
        Stops the WebSocket event loop.
        """
        self.loop.call_soon_threadsafe(self.loop.stop)

    def send(self, msg: str):
        """
        Queue a text message.
        """
        self.send_queue.put(msg)

    def run_event_loop(self):
        asyncio.run(self.main())

    async def run_connection(self):
        """
        Obtain a socket an call 'self.handle_websocket' with it.
        This function must be implemented by each subclass.
        """
        raise NotImplementedError

    def on_message(self, data: str):
        """
        Called whenever recieving a message. This function only logs the message
        but issue #91 should distribute the data to subscriber queues. 
        """
        self.log.debug(f"received: {data}")

    async def handle_websocket(self, ws: aiohttp.ClientWebSocketResponse):
        """
        Run the producer and handler functions as asynchronous tasks.
        """
        self.connected = True

        producer_task = asyncio.create_task(self.producer(ws))
        consumer_task = asyncio.create_task(self.consumer(ws))

        # Drop the connection once either the producer of the consumer task stops running.
        # If either task stops running this indicates that the WebSocket connection was disrupted.
        _, pending = await asyncio.wait(
            [producer_task, consumer_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()  # Cancel unfinished tasks

        self.connected = False

    async def producer(self, ws: Union[aiohttp.ClientWebSocketResponse, web.WebSocketResponse]):
        """
        Take messages off the queue and write them to the socket.
        """
        while self.connected:
            # Dequeue on a separate thread to avoid blocking the WebSocket loop.
            msg = await asyncio.to_thread(self.send_queue.get)
            await ws.send_str(msg)

    async def consumer(self, ws):
        """
        Iterates through incoming messages and sends them to subscriber handler.
        """
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                self.on_message(msg.data, ws)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.log.error(f"WebSocket error: {ws.exception()}")
            if self.connected == False:
                break