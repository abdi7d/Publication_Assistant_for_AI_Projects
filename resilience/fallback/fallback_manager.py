from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class FallbackManager:
    def __init__(self):
        self.handlers = {}

    def register(self, key: str, handler: Callable[..., Any]) -> None:
        self.handlers[key] = handler

    async def execute(self, key: str, *args, **kwargs) -> Any:
        handler = self.handlers.get(key)
        if not handler:
            logger.warning("No fallback registered for %s", key)
            return None
        try:
            result = handler(*args, **kwargs)
            if hasattr(result, "__await__"):
                return await result
            return result
        except Exception:
            logger.exception("Fallback handler failed for %s", key)
            return None
