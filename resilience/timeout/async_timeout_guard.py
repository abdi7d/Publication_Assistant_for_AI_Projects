import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional


@asynccontextmanager
async def async_timeout_guard(timeout_seconds: Optional[float]):
    """Context manager that cancels inner tasks after timeout_seconds.

    Usage:
    async with async_timeout_guard(10):
        await some_long_task()
    """
    if timeout_seconds is None:
        yield
        return

    task = asyncio.current_task()
    loop = asyncio.get_event_loop()
    handle = loop.call_later(timeout_seconds, lambda: task.cancel())
    try:
        yield
    except asyncio.CancelledError:
        raise asyncio.TimeoutError("Operation timed out (guard)")
    finally:
        handle.cancel()
from typing import Callable, Coroutine, Any, Optional
import asyncio
import contextlib
import logging

logger = logging.getLogger(__name__)


class AsyncTimeoutGuard:
    def __init__(self, timeout: float):
        self.timeout = timeout

    async def __aenter__(self):
        self._task = asyncio.current_task()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is asyncio.CancelledError:
            logger.warning("Task cancelled due to timeout")
        return False

    async def run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout)
        except asyncio.TimeoutError as e:
            logger.warning("AsyncTimeoutGuard: cancelled after %s seconds", self.timeout)
            raise
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional


class TimeoutExceededError(asyncio.TimeoutError):
    pass


@asynccontextmanager
async def async_timeout_guard(timeout: Optional[float]):
    """Async context manager that cancels the current task after `timeout` seconds.

    This guard cancels the running task if it exceeds the timeout and raises
    `TimeoutExceededError`. Prefer `asyncio.wait_for` for awaiting coroutines
    where you want strict cancellation semantics; this utility is useful for
    guarding blocks and integrating with tracing/logging.
    """
    if timeout is None or timeout <= 0:
        yield
        return

    current = asyncio.current_task()
    if current is None:
        yield
        return

    loop = asyncio.get_event_loop()
    handle = loop.call_later(timeout, lambda: current.cancel())
    try:
        yield
    except asyncio.CancelledError as exc:
        raise TimeoutExceededError("Operation exceeded timeout") from exc
    finally:
        handle.cancel()
