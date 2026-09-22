"""In-memory progress tracking for long-running pipeline jobs.

Designed for single-process deployment. Thread-safe producers (pipeline
running in a worker thread) push events; consumers (SSE endpoint running
in asyncio) read via a thread-safe queue.

A bounded history is kept so late subscribers can replay past events.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

EventLevel = Literal["info", "success", "warning", "error"]


@dataclass
class ProgressEvent:
    """A single progress event emitted by the pipeline."""

    project_id: str
    level: EventLevel = "info"
    message: str = ""
    step: str = ""
    current: int = 0
    total: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgressTracker:
    """Publishes progress events; supports multiple subscribers per project."""

    _HISTORY_LIMIT = 100
    _SENTINEL = object()

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._history: dict[str, list[ProgressEvent]] = {}
        self._subscribers: dict[str, list[queue.Queue]] = {}

    # -- lifecycle --------------------------------------------------------

    def create(self, project_id: str) -> None:
        """Initialize tracking for a new project."""
        with self._lock:
            self._history[project_id] = []
            self._subscribers.setdefault(project_id, [])

    def close(self, project_id: str) -> None:
        """Signal all subscribers that the project has finished."""
        with self._lock:
            subs = list(self._subscribers.get(project_id, []))
        for q in subs:
            try:
                q.put_nowait(self._SENTINEL)
            except queue.Full:
                pass

    def reset(self, project_id: str) -> None:
        """Remove all tracking data for a project."""
        with self._lock:
            self._history.pop(project_id, None)
            self._subscribers.pop(project_id, None)

    # -- publishing -------------------------------------------------------

    def publish(self, event: ProgressEvent) -> None:
        """Record and broadcast an event. Safe to call from any thread."""
        with self._lock:
            history = self._history.setdefault(event.project_id, [])
            history.append(event)
            if len(history) > self._HISTORY_LIMIT:
                del history[: len(history) - self._HISTORY_LIMIT]
            subs = list(self._subscribers.get(event.project_id, []))

        for q in subs:
            try:
                q.put_nowait(event)
            except queue.Full:
                # slow subscriber; drop event rather than blocking pipeline
                pass

    # -- subscribing ------------------------------------------------------

    def subscribe(self, project_id: str) -> queue.Queue:
        """Return a queue that will receive future events for `project_id`."""
        q: queue.Queue = queue.Queue(maxsize=1000)
        with self._lock:
            self._subscribers.setdefault(project_id, []).append(q)
        return q

    def unsubscribe(self, project_id: str, q: queue.Queue) -> None:
        with self._lock:
            subs = self._subscribers.get(project_id, [])
            if q in subs:
                subs.remove(q)

    def history(self, project_id: str) -> list[ProgressEvent]:
        with self._lock:
            return list(self._history.get(project_id, []))

    # -- helpers ----------------------------------------------------------

    @classmethod
    def is_sentinel(cls, obj: object) -> bool:
        return obj is cls._SENTINEL


# Module-level singleton
tracker = ProgressTracker()
