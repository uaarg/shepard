import threading
import time
import aiohttp
import logging
from aiohttp import web
from src.modules.emu.websocket import WebSocketBase


# Define a WebSocket subclass for testing
class EchoClient(WebSocketBase):
    def __init__(self, name: str, url: str):
        super().__init__(name)
        self.url: str = url
        self.received: list[str] = []

    async def run_connection(self):
        """
        Obtain a socket and call 'self.handle_websocket' with it.
        This function must be implemented by each subclass.
        """
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.url) as ws:
                await self.handle_websocket(ws)

    def on_message(self, data: str):
        self.received.append(data)


async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s'
                  % ws.exception())

    print('websocket connection closed')

    return ws


def start_test_server(port: int):
    """
    Run the test server on a background thread.
    """
    def run():
        app = web.Application()
        app.add_routes([web.get('/ws', websocket_handler)])
        web.run_app(app, port=port, handle_signals=False)

    threading.Thread(target=run, daemon=True).start()


def test_send_and_receive():
    start_test_server(8080)
    test_client = EchoClient("test", 'http://localhost:8080/ws')

    # Print the client's log to the terminal
    client_logger = test_client.log
    client_logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    client_logger.addHandler(console_handler)

    # Try stopping before a WebSocket connection exists
    test_client.stop()

    test_client.start_comms()

    timer = 0
    while not test_client.connected and timer < 5:
        time.sleep(0.05)
        timer += 0.05

    assert test_client.connected, "client never connected"

    test_client.send("hello")
    test_client.send("world")

    time.sleep(2)

    assert test_client.received == ["hello/answer", "world/answer"], "did not receive response from server"

    test_client.stop()

    assert test_client.connected is False, "client is still connected after calling 'stop' function"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_send_and_receive()
