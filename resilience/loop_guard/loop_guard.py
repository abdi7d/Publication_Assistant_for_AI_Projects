from dataclasses import dataclass, field
from typing import Dict
import time


@dataclass
class LoopGuard:
    max_iterations: int = 100
    window_seconds: int = 60
    _counters: Dict[str, int] = field(default_factory=dict)
    _timestamps: Dict[str, float] = field(default_factory=dict)

    def allow(self, workflow_id: str) -> bool:
        now = time.time()
        ts = self._timestamps.get(workflow_id, now)
        if now - ts > self.window_seconds:
            self._timestamps[workflow_id] = now
            self._counters[workflow_id] = 1
            return True
        count = self._counters.get(workflow_id, 0) + 1
        self._counters[workflow_id] = count
        if count > self.max_iterations:
            return False
        return True

    def reset(self, workflow_id: str) -> None:
        self._counters.pop(workflow_id, None)
        self._timestamps.pop(workflow_id, None)
