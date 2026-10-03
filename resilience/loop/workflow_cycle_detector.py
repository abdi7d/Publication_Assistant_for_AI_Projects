from typing import Dict, List
import hashlib
import logging

logger = logging.getLogger(__name__)


class WorkflowCycleDetector:
    def __init__(self, window: int = 10):
        self.window = window
        self.signatures: Dict[str, List[str]] = {}

    def signature(self, state: str) -> str:
        return hashlib.sha256(state.encode("utf-8")).hexdigest()

    def push(self, workflow_id: str, state: str) -> None:
        sig = self.signature(state)
        self.signatures.setdefault(workflow_id, []).append(sig)
        if len(self.signatures[workflow_id]) > self.window:
            self.signatures[workflow_id].pop(0)
        if self.detect_cycle(workflow_id):
            logger.error("Cycle detected in workflow %s", workflow_id)
            raise RuntimeError("Workflow cycle detected")

    def detect_cycle(self, workflow_id: str) -> bool:
        items = self.signatures.get(workflow_id, [])
        return len(items) != len(set(items))

    def reset(self, workflow_id: str) -> None:
        self.signatures.pop(workflow_id, None)
