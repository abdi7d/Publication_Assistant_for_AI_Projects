"""Timeout utilities for resilience."""
import asyncio
import functools
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger("resilience.timeout")


async def run_with_timeout(coro: Awaitable[T], timeout: Optional[float] = None, fallback: Optional[Callable[[], T]] = None) -> T:
    """Run a coroutine with an optional timeout."""
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
    """Decorator to enforce timeout on async functions."""

    def decorator(fn: Callable[..., Awaitable[T]]):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> T:
            return await run_with_timeout(fn(*args, **kwargs), timeout=timeout, fallback=fallback)

        return wrapper

    return decorator


class TimeoutManager:
    def __init__(self, timeout_seconds: Optional[float] = None, default_timeout: Optional[float] = None):
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else (
            default_timeout or 30.0)
        self.default_timeout = self.timeout_seconds

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        timeout = self.timeout_seconds
        if timeout is None or timeout <= 0:
            return func(*args, **kwargs)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                future.cancel()
                raise TimeoutError("Operation timed out")

    async def run(self, coro: Awaitable[T], timeout: Optional[float] = None, fallback: Optional[Callable[[], T]] = None) -> T:
        t = timeout or self.default_timeout
        return await run_with_timeout(coro, timeout=t, fallback=fallback)
