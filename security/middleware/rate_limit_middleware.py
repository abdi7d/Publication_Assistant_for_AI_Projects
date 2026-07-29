import time
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable, Dict
from ..configs.config_loader import settings


class InMemoryRateLimiter:
    def __init__(self):
        self._buckets: Dict[str, Dict] = {}

    def _now(self) -> int:
        return int(time.time())

    def allow(self, key: str) -> bool:
        window = 60
        limit = settings.RATE_LIMIT_PER_MINUTE
        burst = settings.RATE_LIMIT_BURST
        now = self._now()
        bucket = self._buckets.get(key)
        if not bucket or bucket["reset"] <= now:
            self._buckets[key] = {"count": 1, "reset": now + window}
            return True
        if bucket["count"] < limit + burst:
            bucket["count"] += 1
            return True
        return False


_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Derive client key
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rl:{client_ip}:{path}"
        allowed = _limiter.allow(key)
        if not allowed:
            return Response(content="Too many requests", status_code=429)
        return await call_next(request)
