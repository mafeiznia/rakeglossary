"""Thread-safe rate limiter for translation providers."""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Enforce a maximum number of calls per second across all threads.

    Uses a simple "minimum interval" scheme: no two calls may start
    less than `1 / rate_per_second` seconds apart. This guarantees
    the average rate never exceeds the configured value.
    """

    def __init__(self, rate_per_second: float) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be > 0")
        self._min_interval = 1.0 / rate_per_second
        self._lock = threading.Lock()
        self._last_call = 0.0

    def acquire(self) -> None:
        """Block until the next call is allowed."""
        with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
            self._last_call = now
