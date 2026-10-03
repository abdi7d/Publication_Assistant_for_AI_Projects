from typing import Dict
import logging

logger = logging.getLogger(__name__)


class LoopGuard:
    def __init__(self, max_iterations: int = 1000):
        self.max_iterations = max_iterations
        self.counters: Dict[str, int] = {}

    def tick(self, workflow_id: str) -> None:
        self.counters.setdefault(workflow_id, 0)
        self.counters[workflow_id] += 1
        logger.debug("LoopGuard tick %s -> %s", workflow_id, self.counters[workflow_id])
        if self.counters[workflow_id] > self.max_iterations:
            logger.error("Max iterations exceeded for %s", workflow_id)
            raise RuntimeError(f"Max iterations exceeded for {workflow_id}")

    def reset(self, workflow_id: str) -> None:
        if workflow_id in self.counters:
            del self.counters[workflow_id]
from __future__ import annotations

import threading
import time
from typing import Dict


class LoopGuard:
    """Protect workflows from runaway iterations by tracking counters.

    This implementation is in-memory and thread-safe. For distributed systems,
    back this with Redis or a durable store to share state between workers.
    """

    def __init__(self, max_iterations: int = 1000, window_seconds: int = 60):
        self.max_iterations = max_iterations
        self.window_seconds = window_seconds
        self._counters: Dict[str, int] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

    def increment(self, workflow_id: str) -> int:
        now = time.time()
        with self._lock:
            ts = self._timestamps.get(workflow_id, 0)
            if now - ts > self.window_seconds:
                self._counters[workflow_id] = 0
                self._timestamps[workflow_id] = now
            cnt = self._counters.get(workflow_id, 0) + 1
            self._counters[workflow_id] = cnt
            return cnt

    def is_exceeded(self, workflow_id: str) -> bool:
        return self._counters.get(workflow_id, 0) > self.max_iterations

    def reset(self, workflow_id: str) -> None:
        with self._lock:
            self._counters.pop(workflow_id, None)
            self._timestamps.pop(workflow_id, None)
