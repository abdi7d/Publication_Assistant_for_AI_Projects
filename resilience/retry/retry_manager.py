"""Simple retry utilities for async functions used in tests.

Provides `retry_async` decorator which retries a coroutine function with
exponential backoff and jitter. This file intentionally keeps the API small
and dependency-light for testability.
"""
import asyncio
import functools
import inspect
import logging
from typing import Any, Awaitable, Callable, Optional

from .backoff import sleep_backoff

logger = logging.getLogger("resilience.retry")

# Use simple formatted logging messages to avoid passing unexpected kwargs


def _log_warning_safe(message: str) -> None:
    try:
        logger.warning(message)
    except Exception:
        # best-effort: degrade silently to avoid breaking retry paths
        try:
            logger.info(message)
        except Exception:
            pass


def retry_async(max_attempts: int = 3, base_delay: float = 0.1, factor: float = 2.0, max_delay: float = 10.0):
    """Decorator to retry async functions with jittered exponential backoff.

    Usage:
        @retry_async(max_attempts=5)
        async def call(...):
            ...
    """

    def decorator(fn: Callable[..., Any]):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            attempt = 0
            while attempt < max_attempts:
                try:
                    result = fn(*args, **kwargs)
                    # only await if the result is awaitable/coroutine
                    if inspect.isawaitable(result):
                        return await result  # type: ignore
                    return result
                except Exception as exc:
                    last_exc = exc
                    attempt += 1
                    _log_warning_safe(
                        f"retry attempt failed (attempt={attempt}) error={exc}")
                    if attempt >= max_attempts:
                        break
                    await sleep_backoff(attempt, base, factor, max_delay)
            try:
                logger.error(
                    f"retry exhausted func={fn.__name__} attempts={attempt}")
            except Exception:
                pass
            raise last_exc

        return wrapper

    # local closure helpers to avoid name conflicts
    base = base_delay
    return decorator


def sync_retry(*_, **__):
    raise NotImplementedError("Use retry_async for async tests")
