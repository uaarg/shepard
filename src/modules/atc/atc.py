"""
ATC ("Air Traffic Control"): Shepard's WebSocket client for the AEAC telemetry server.

Covers issue #89 and provides the inbox queue interface for #90.

Thread A (receive) is the event-loop thread that WebSocketBase starts. It
connects to the server, keeps reconnecting if the connection drops, and puts
every incoming text message on `inbox` without waiting for anyone to process it.
"""

import asyncio
import queue
from typing import Optional

import aiohttp

from src.modules.emu.websocket import WebSocketBase


class ATC(WebSocketBase):
    # Wait this long between reconnect attempts so a dead server isn't hammered
    DEFAULT_RECONNECT_DELAY_S = 2.0

    # Give up on a single connection attempt after this long
    CONNECT_TIMEOUT_S = 5.0

    # aiohttp sends a ping this often and drops the connection if no pong comes
    # back. This is how we notice a silently dead link (e.g. Wi-Fi out of range).
    HEARTBEAT_S = 5.0

    def __init__(self, url: str, reconnect_delay_s: float = DEFAULT_RECONNECT_DELAY_S):
        """
        Args:
            url: WebSocket URL of the telemetry server, e.g. "ws://host:port/path".
                 ASSUMPTION: no auth. Update once the organizers' spec is known.
            reconnect_delay_s: seconds to wait between reconnect attempts.
        """
        super().__init__("atc")
        self.url = url
        self.reconnect_delay_s = reconnect_delay_s

        # Issue #90: every message received from the server goes on this queue,
        # in the order it arrived. queue.Queue is thread-safe.
        self.inbox: queue.Queue = queue.Queue()

    # ----------------------
    # Public interface
    # ----------------------
    def get_inbox(self) -> queue.Queue:
        """The shared queue of raw (text) messages received from the server."""
        return self.inbox

    def send_telemetry(self, packet: str) -> bool:
        """
        Sends a telemetry packet if we are connected right now.

        Returns False (and does NOT queue it) when disconnected. Old telemetry is
        useless to the server, and queueing it would make us replay a burst of
        stale positions when the connection comes back.
        """
        if not self.connected:
            return False
        self.send(packet)
        return True

    # ----------------------
    # WebSocketBase hooks
    # ----------------------
    async def run_connection(self):
        """Connect, run until the connection drops, then retry until stop() is called."""
        while not self.stopping:
            try:
                timeout = aiohttp.ClientTimeout(total=None, connect=self.CONNECT_TIMEOUT_S)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.ws_connect(self.url, heartbeat=self.HEARTBEAT_S) as ws:
                        self.log.info(f"connected to {self.url}")
                        self._clear_send_queue()
                        await self.handle_websocket(ws)
                if not self.stopping:
                    self.log.warning("connection to telemetry server closed")
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
                self.log.warning(f"could not connect to {self.url}: {exc!r}")
            except Exception:
                # Never let one bad connection kill the thread; log and retry
                self.log.exception("unexpected error in telemetry server connection")

            self.connected = False
            if self.stopping:
                break
            await self._wait_before_reconnect()

        self.log.info("ATC client stopped")

    def on_message(self, data: str):
        """Called on thread A for each text message. Must not block."""
        self.log.debug(f"received: {data}")
        self.inbox.put_nowait(data)

    # ----------------------
    # Helpers
    # ----------------------
    async def _wait_before_reconnect(self) -> None:
        """Sleep reconnect_delay_s, but wake up immediately if stop() is called."""
        stop_event: Optional[asyncio.Event] = self.stop_event
        if stop_event is None:
            await asyncio.sleep(self.reconnect_delay_s)
            return
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=self.reconnect_delay_s)
        except asyncio.TimeoutError:
            pass

    def _clear_send_queue(self) -> None:
        """Drop anything left over from a previous connection (it's stale)."""
        dropped = 0
        while True:
            try:
                self.send_queue.get_nowait()
                dropped += 1
            except queue.Empty:
                break
        if dropped:
            self.log.info(f"dropped {dropped} stale outgoing message(s) on reconnect")
