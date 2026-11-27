from threading import Lock
import queue


class Subscriber:
    def __init__(self, name):
        self.name: str = name
        self.receive_queue: queue.Queue = None


class SubscriberList:
    """
    A list of individual subscribers to which the client sends
    each message it receives.
    """
    def __init__(self):
        self.storage: list = []
        self.lock = Lock()

    def subscribe(self, name):
        """
        Returns a 'Subscriber' object whose queue attribute is updated
        whenever the WebSocket client recieves a new message. We ensure
        that a lock is used whenever adding a subscriber to the list to
        avoid the WebSocket client misreading the number of current subscribers.
        """
        with self.lock:
            subscriber = Subscriber(name)
            subscriber.receive_queue = queue.Queue()
            self.storage.append(subscriber)
            return subscriber
