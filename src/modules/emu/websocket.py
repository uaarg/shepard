import aiohttp
import asyncio
import threading
import queue
import logging
import os
import json
from urllib.parse import quote
from aiohttp import web
from typing import Optional, Union
from src.modules.emu.subscriber import SubscriberList


class WebSocketBase:
    def __init__(self, name: str):
        self.log = logging.getLogger(f"shepard.ws.{name}")
        self.thread: Optional[threading.Thread] = None
        self.send_queue: queue.Queue = queue.Queue()
        self.receive_queue: queue.Queue = queue.Queue()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected = False
        self.stop_event: Optional[asyncio.Event] = None
        self.received: list[str] = []  # used for testing purposes only

    def start_comms(self):
        """
        Initializes a new thread which runs the WebSocket connection event loop.
        """
        self.thread = threading.Thread(target=self.run_event_loop, daemon=True)
        self.thread.start()

    async def main(self):
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()
        attempts = 0
        while not self.connected and attempts < 15:
            try:
                await self.run_connection()
                break
            except Exception:
                self.log.exception("connection crashed")
                self.log.debug(f"attempting to re-establish connection...")
                await asyncio.sleep(0.2)
        self.connected = False

    def stop(self, timeout: int = 5):
        """
        Stops the WebSocket event loop. Waits for the thread to finish,
        but gives up and forces disconnection if the thread
        has not terminated before the timeout.
        """
        if not self.connected:
            self.log.debug("cannot stop since a connection does not exist")
            return
        self.loop.call_soon_threadsafe(self.stop_event.set)
        self.thread.join(timeout)

    def send(self, json_str: str):
        """
        Queue a text message.
        """
        self.send_queue.put(json_str)

    def run_event_loop(self):
        asyncio.run(self.main())

    async def run_connection(self):
        """
        Obtain a socket and call 'self.handle_websocket' with it.
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
        stop_task = asyncio.create_task(self.stop_event.wait())

        # Stop the WebSocket connection when the 'stop_event' flag is triggered
        # Drop the connection if either the producer or the consumer task stops running.
        # If either task stops running this indicates that the WebSocket connection was disrupted.
        done, pending = await asyncio.wait(
            [producer_task, consumer_task, stop_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()  # Cancel unfinished tasks

        failed = False
        for task in done:
            if task.exception():
                failed = True
                exc = task.exception()
                if task != stop_task and exc is not None:
                    self.log.error("websocket task failed", exc_info=exc)

        if failed:
            self.log.debug("websocket shutting down due to failure")
        else:
            self.log.debug("websocket shutting down normally")

        await ws.close()
        self.connected = False

    async def producer(self, ws: Union[aiohttp.ClientWebSocketResponse, web.WebSocketResponse]):
        """
        Take messages off the queue and write them to the socket.
        """
        while self.connected:
            try:
                # If the queue is empty, do not block the thread
                # while waiting for an item to dequeue
                msg = self.send_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.02)
                continue
            try:
                await ws.send_str(msg)
                self.log.debug(f"sent: {msg}")
            except Exception:
                self.log.error(f"message '{msg}' could not be sent")
                self.send_queue.put_nowait(msg)
                return

    async def consumer(self, ws):
        """
        Iterates through incoming messages and sends them to subscriber handler.
        """
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await self.on_message(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.log.error(f"WebSocket error: {ws.exception()}")
            if not self.connected:
                break


class AeacClient(WebSocketBase):
    def __init__(self, name="UAARG", 
                 url: str | None = None,
                 token: str | None = None,
                 subscriber_list=SubscriberList()):
        if url == None:
            url = os.getenv("URL")
        if token == None:
            token = os.getenv("TOKEN")
        super().__init__(name)  # uavID
        self.name = name
        separator = '&' if '?' in url else '?'
        self.connection_string = f"{url}{separator}Authorization={quote(token)}"
        self.subscriber_list: SubscriberList = subscriber_list

    async def run_connection(self):
        """
        Runs a WebSocket connection to a test server. This function
        should be replaced with a connection to the real AEAC server.
        """
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.connection_string) as ws:
                await self.handle_websocket(ws)

    async def on_message(self, data):
        """
        Enqueue incoming messages onto a thread-safe queue.
        """
        data = await asyncio.to_thread(json.loads, data)  # convert JSON to dict
        self.log.debug("received " + str(data))
        self.received.append(data)
        try:
            self.receive_queue.put_nowait(data)  # Python queues are thread-safe by default

            # Create a lock on the subscriber list to avoid subscribers being added while
            # we iterate over the list.
            with self.subscriber_list.lock:
                for subscriber in self.subscriber_list.storage:
                    try:
                        subscriber.receive_queue.put_nowait(data)
                    except Exception as exc:
                        self.log.exception("could not put incoming message on subscriber queue", exc_info=exc)
        except Exception as exc:
            self.log.exception("could not put incoming message on queue", exc_info=exc)

    def telemetry_request(self):
        data = {'uavId': self.name}
        _dict = {'action': 'telemetry_request', 'data': data}
        self.send(json.dumps(_dict))
