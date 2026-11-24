"""
A fake telemetry server for development and tests. It is NOT the real AEAC server.

It accepts WebSocket connections at /ws, records each telemetry packet it gets,
replies to each one with a placeholder ACK, and can send a fake airspace message
on a timer. Everything it sends uses the placeholder format in messages.py.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from aiohttp import WSMsgType, web

from src.modules.atc.messages import TYPE_ACK, TYPE_AIRSPACE, TYPE_TELEMETRY, parse_message

LOGGER = logging.getLogger(__name__)


def fake_airspace_message() -> Dict[str, Any]:
    # ASSUMPTION: placeholder shape for simulated airspace data (issue #99).
    # Fields loosely follow the inputs of mavctl's ADSBVehicle.
    return {
        "type": TYPE_AIRSPACE,
        "vehicles": [{
            "id": "SIM1",
            "lat_deg": 53.4955,
            "lon_deg": -113.548,
            "alt_amsl_m": 677.0,
            "heading_deg": 90.0,
            "hor_speed_m_s": 0.0,
            "ver_speed_m_s": 0.0,
            "exclusion_radius_m": 50.0,
        }],
    }


class MockTelemetryServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, airspace_period_s: Optional[float] = None):
        """
        Args:
            port: 0 picks a free port; read .port after start().
            airspace_period_s: send a fake airspace message this often, or never if None.
        """
        self.host = host
        self.port = port
        self.airspace_period_s = airspace_period_s

        self.received: List[Dict[str, Any]] = []  # telemetry packets, in arrival order
        self._received_lock = threading.Lock()

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None
        self._thread: Optional[threading.Thread] = None
        self._started = threading.Event()
        self._clients: List[web.WebSocketResponse] = []

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}/ws"

    def get_received(self) -> List[Dict[str, Any]]:
        with self._received_lock:
            return list(self.received)

    # ----------------------
    # Running in a background thread
    # ----------------------
    def start(self, timeout: float = 5.0) -> None:
        self._started.clear()
        self._thread = threading.Thread(target=self._thread_main, name="mock-telemetry-server", daemon=True)
        self._thread.start()
        if not self._started.wait(timeout):
            raise RuntimeError("mock telemetry server did not start")

    def stop(self, timeout: float = 5.0) -> None:
        if self._loop is None or self._thread is None:
            return
        future = asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
        future.result(timeout)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout)
        self._thread = None
        self._loop = None

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._startup())
        self._started.set()
        loop.run_forever()
        loop.close()

    # ----------------------
    # Server
    # ----------------------
    async def _startup(self) -> None:
        app = web.Application()
        app.add_routes([web.get("/ws", self._handle)])
        runner = web.AppRunner(app)
        self._runner = runner
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        # When port=0 the OS picks one; find out which
        if self.port == 0 and runner.addresses:
            self.port = runner.addresses[0][1]
        LOGGER.info("mock telemetry server listening on %s", self.url)

    async def _shutdown(self) -> None:
        for ws in list(self._clients):
            await ws.close()
        if self._runner is not None:
            await self._runner.cleanup()

    async def _handle(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._clients.append(ws)
        LOGGER.info("client connected")

        airspace_task = None
        if self.airspace_period_s is not None:
            airspace_task = asyncio.create_task(self._send_airspace(ws, self.airspace_period_s))

        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                data = parse_message(msg.data)
                if data is None or data.get("type") != TYPE_TELEMETRY:
                    continue
                with self._received_lock:
                    self.received.append(data)
                LOGGER.info("telemetry: %s", msg.data)
                # ASSUMPTION: placeholder ACK format
                await ws.send_str(json.dumps({
                    "type": TYPE_ACK,
                    "timestamp_unix_s": data.get("timestamp_unix_s"),
                    "received_at_unix_s": time.time(),
                }))
        finally:
            if airspace_task is not None:
                airspace_task.cancel()
            self._clients.remove(ws)
            LOGGER.info("client disconnected")
        return ws

    async def _send_airspace(self, ws: web.WebSocketResponse, period_s: float) -> None:
        while not ws.closed:
            await asyncio.sleep(period_s)
            await ws.send_str(json.dumps(fake_airspace_message()))
