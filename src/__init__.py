import collections
import sys

# Dronekit compatibility for Python 3.10+
if sys.version_info >= (3, 10):
    if not hasattr(collections, 'MutableMapping'):
        import collections.abc
        collections.MutableMapping = collections.abc.MutableMapping
