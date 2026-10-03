from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import asyncio
from .timeout_manager import TimeoutManager


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: float = 30.0):
        super().__init__(app)
        self.timeout_manager = TimeoutManager(default_timeout=timeout)

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_manager.default_timeout)
        except asyncio.TimeoutError:
            return Response(content="Request timed out", status_code=504)
from __future__ import annotations

import asyncio
from typing import Callable

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from resilience.logging.resilience_logger import get_resilience_logger

logger = get_resilience_logger(__name__)


class TimeoutMiddleware:
    """ASGI middleware that cancels request handling after a configured timeout.

    Configure per-route timeouts by adding `request.state.timeout = <seconds>` in
    upstream middleware or route handlers.
    """

    def __init__(self, app: ASGIApp, default_timeout: float = 30.0):
        self.app = app
        self.default_timeout = default_timeout

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = Request(scope, receive=receive)
        timeout = getattr(req.state, "timeout", self.default_timeout)

        task = asyncio.create_task(self.app(scope, receive, send))
        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Request timed out after %s seconds", timeout)
            if not task.done():
                task.cancel()
            response = Response("Request timed out", status_code=504)
            await response(scope, receive, send)
