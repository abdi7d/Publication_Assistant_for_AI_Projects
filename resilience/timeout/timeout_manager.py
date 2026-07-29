"""Timeout utilities for resilience.

Provides async timeout helpers and a decorator to enforce time limits on
coroutines. Designed to be simple, async-safe, and to cancel stalled tasks
to free resources.
"""
import asyncio
import functools
import logging
from typing import Any, Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger("resilience.timeout")


async def run_with_timeout(coro: Awaitable[T], timeout: Optional[float] = None, fallback: Optional[Callable[[], T]] = None) -> T:
    """Run a coroutine with an optional timeout. If timeout occurs and a
    fallback is supplied, return fallback(); otherwise raise asyncio.TimeoutError.
    The underlying task is cancelled on timeout to release resources.
    """
    if timeout is None or timeout <= 0:
        return await coro

    task = asyncio.create_task(coro)
    try:
        return await asyncio.wait_for(task, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Operation timed out after %s seconds", timeout)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.debug("Task cancelled after timeout")
        if fallback is not None:
            try:
                return fallback()
            except Exception:
                logger.exception("Fallback raised an exception")
        raise


def async_timeout(timeout: float, fallback: Optional[Callable[[], Any]] = None):
    """Decorator to enforce timeout on async functions.

    Example:
        @async_timeout(5.0)
        async def call(): ...
    """

    def decorator(fn: Callable[..., Awaitable[T]]):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> T:
            return await run_with_timeout(fn(*args, **kwargs), timeout=timeout, fallback=fallback)

        return wrapper

    return decorator


class TimeoutManager:
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout

    async def run(self, coro: Awaitable[T], timeout: Optional[float] = None, fallback: Optional[Callable[[], T]] = None) -> T:
        t = timeout or self.default_timeout
        return await run_with_timeout(coro, timeout=t, fallback=fallback)
