from typing import Dict
import time
import logging

logger = logging.getLogger(__name__)


class IterationManager:
    def __init__(self, max_iterations: int = 1000):
        self.max_iterations = max_iterations
        self.meta: Dict[str, Dict[str, int]] = {}

    def start(self, workflow_id: str) -> None:
        self.meta[workflow_id] = {"count": 0, "started": int(time.time())}

    def increment(self, workflow_id: str) -> int:
        if workflow_id not in self.meta:
            self.start(workflow_id)
        self.meta[workflow_id]["count"] += 1
        c = self.meta[workflow_id]["count"]
        if c > self.max_iterations:
            logger.error("Iteration limit reached for %s", workflow_id)
            raise RuntimeError("Iteration limit reached")
        return c

    def stop(self, workflow_id: str) -> None:
        self.meta.pop(workflow_id, None)
