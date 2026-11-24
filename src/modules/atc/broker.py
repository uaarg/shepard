"""
MessageBroker: hands every message from the telemetry server to each subscriber.

Covers the interface for issue #91 (thread D in the systems design).

Each subscriber (e.g. the ADS-B forwarder for #99, the Emu forwarder) gets its
own queue, so a slow subscriber never holds up the ATC client or the others.

Usage:
    broker = MessageBroker()
    adsb_queue = broker.subscribe("adsb")
    broker.start(atc.get_inbox())
    ...
    msg = adsb_queue.get(timeout=1.0)
"""

import logging
import queue
import threading
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)


class MessageBroker:
    # How long the publishing thread waits on an empty source before checking
    # whether it should stop. Short enough that stop() is quick.
    POLL_TIMEOUT_S = 0.5

    DEFAULT_MAX_QUEUE_SIZE = 100

    def __init__(self) -> None:
        self._subscribers: Dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ----------------------
    # Subscribing
    # ----------------------
    def subscribe(self, name: str, maxsize: int = DEFAULT_MAX_QUEUE_SIZE) -> queue.Queue:
        """
        Registers a subscriber and returns its queue. Subscribing twice with the
        same name returns the existing queue.

        maxsize bounds memory on the Pi: when a subscriber falls behind, its
        oldest message is dropped (with a warning) to make room.
        """
        with self._lock:
            if name not in self._subscribers:
                self._subscribers[name] = queue.Queue(maxsize=maxsize)
            return self._subscribers[name]

    def unsubscribe(self, name: str) -> None:
        with self._lock:
            self._subscribers.pop(name, None)

    # ----------------------
    # Publishing
    # ----------------------
    def publish(self, msg: str) -> None:
        """Puts msg on every subscriber's queue. Never blocks."""
        # Hold the lock for the whole loop so messages reach every queue in the same order
        with self._lock:
            for name, sub_queue in self._subscribers.items():
                self._put_drop_oldest(name, sub_queue, msg)

    @staticmethod
    def _put_drop_oldest(name: str, sub_queue: queue.Queue, msg: str) -> None:
        while True:
            try:
                sub_queue.put_nowait(msg)
                return
            except queue.Full:
                try:
                    sub_queue.get_nowait()
                    LOGGER.warning("subscriber '%s' is falling behind, dropped its oldest message", name)
                except queue.Empty:
                    pass  # the subscriber emptied it in the meantime; just retry

    # ----------------------
    # Publishing thread (thread D)
    # ----------------------
    def start(self, source: queue.Queue) -> None:
        """Starts a thread that moves messages from source (e.g. ATC.inbox) to subscribers."""
        if self._thread is not None:
            LOGGER.warning("MessageBroker is already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, args=(source,), name="atc-broker", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None

    def _run(self, source: queue.Queue) -> None:
        while not self._stop_event.is_set():
            try:
                msg = source.get(timeout=self.POLL_TIMEOUT_S)
            except queue.Empty:
                continue
            try:
                self.publish(msg)
            except Exception:
                LOGGER.exception("failed to publish ATC message")
