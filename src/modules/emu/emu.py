import threading
import queue

import asyncio
from typing import Callable

from aiohttp import web
from aiohttp import web
import aiohttp

import json


class Emu():
    """
    class representation of a connection to Emu
    """
    def __init__(self, img_dir: str):
        self.img_dir = img_dir

        self._send_queue = queue.Queue()
        self._recv_queue = queue.Queue()

        # set default onConnect to be a no-op
        self._on_connect = lambda: None
        self._is_connected = False

    def start_comms(self):
        self._comms_thread = threading.Thread(target=self._start_comms_loop, daemon=True)
        self._comms_thread.start()

    def send_image(self, path: str):
        """
        sends the image at specified path to Emu
        the path sent should be accessable from within self.img_dir so it can be accessed through
        /images/{filename}
        """
        print(path)
        img_url = "/images/" + path
        print(img_url)
        content = {
            "type": "img",
            "value": img_url
        }
        self._send_queue.put(json.dumps(content))

    def send_log(self, message: str, severity: str="normal"):
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

    def send_msg(self, message: str):
        """
        sends message as it is, follow the proper JSON API messages
        """
        self._send_queue.put(message)

    def set_on_connect(self, func: Callable):
        self._on_connect = func

    def _start_comms_loop(self):
        """
        starts connection loop with asyncio
        """
        print("start_comms loop")
        self.app = web.Application()
        self.app.add_routes([web.static('/images', self.img_dir),
                             web.get('/ws', self.handle_websocket)])

        web.run_app(self.app, handle_signals=False)

    async def producer_handler(self, ws):
        """
        handles sending messages to the client
        """
        event_loop = asyncio.get_running_loop()
        while not ws.closed:
            message = await event_loop.run_in_executor(None, self._send_queue.get)
            await ws.send_str(message)
    
    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        producer_task = asyncio.create_task(self.producer_handler(ws))
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str(msg.data + '/answer')
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                    ws.exception())
    
        print('websocket connection closed')
        producer_task.cancel()
        
        return ws
