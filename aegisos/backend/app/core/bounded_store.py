"""
Bounded Store — Phase 50 Security Fix

Mixin/utilities for bounding in-memory stores with max size and TTL eviction.
Prevents unbounded memory growth.
"""

import time
import threading
from typing import Optional, Any
from datetime import datetime, timedelta
from collections import OrderedDict
from app.core.logging import get_logger

logger = get_logger("core.bounded_store")


class BoundedDict:
    """Dictionary with max size and optional TTL eviction."""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 0):
        self._data: OrderedDict = OrderedDict()
        self._timestamps: dict = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._evicted = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._data:
                return None
            if self.ttl_seconds > 0:
                ts = self._timestamps.get(key)
                if ts and (datetime.utcnow() - ts).total_seconds() > self.ttl_seconds:
                    del self._data[key]
                    del self._timestamps[key]
                    return None
            self._data.move_to_end(key)
            return self._data[key]

    def set(self, key: str, value: Any):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            self._timestamps[key] = datetime.utcnow()

            while len(self._data) > self.max_size:
                oldest_key, _ = self._data.popitem(last=False)
                self._timestamps.pop(oldest_key, None)
                self._evicted += 1

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._timestamps.pop(key, None)
                return True
            return False

    def size(self) -> int:
        return len(self._data)

    def evicted_count(self) -> int:
        return self._evicted

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        if self.ttl_seconds <= 0:
            return 0
        removed = 0
        now = datetime.utcnow()
        with self._lock:
            expired = [k for k, ts in self._timestamps.items()
                       if (now - ts).total_seconds() > self.ttl_seconds]
            for k in expired:
                self._data.pop(k, None)
                self._timestamps.pop(k, None)
                removed += 1
        return removed

    def stats(self) -> dict:
        return {
            "size": self.size(),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "evicted": self._evicted,
        }


class BoundedList:
    """List with max size (ring buffer)."""

    def __init__(self, max_size: int = 10000):
        from collections import deque
        self._data = deque(maxlen=max_size)
        self.max_size = max_size
        self._lock = threading.Lock()
        self._total_added = 0

    def append(self, item: Any):
        with self._lock:
            self._data.append(item)
            self._total_added += 1

    def list_all(self) -> list:
        with self._lock:
            return list(self._data)

    def size(self) -> int:
        return len(self._data)

    def stats(self) -> dict:
        return {
            "size": self.size(),
            "max_size": self.max_size,
            "total_added": self._total_added,
        }
