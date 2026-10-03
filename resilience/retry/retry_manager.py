"""Retry utilities for sync and async functions used in tests."""
import functools
import inspect
import logging
import time
from typing import Any, Awaitable, Callable, Optional, Tuple

from .backoff import sleep_backoff

logger = logging.getLogger("resilience.retry")


def _log_warning_safe(message: str) -> None:
    try:
        logger.warning(message)
    except Exception:
        try:
            logger.info(message)
        except Exception:
            pass


class RetryManager:
    """Simple retry manager with optional backoff and exception filtering."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 0.1,
        backoff_multiplier: float = 2.0,
        max_delay: float = 10.0,
        retryable_exceptions: Tuple[type[BaseException], ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions

    def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        last_exc: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    _log_warning_safe(
                        f"retry exhausted after {attempt} attempts")
                    raise
                delay = min(
                    self.backoff_base * (self.backoff_multiplier ** (attempt)), self.max_delay)
                time.sleep(delay)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("RetryManager finished without a result")


def retry_async(max_attempts: int = 3, base_delay: float = 0.1, factor: float = 2.0, max_delay: float = 10.0):
    """Decorator to retry async functions with jittered exponential backoff."""

    def decorator(fn: Callable[..., Any]):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            attempt = 0
            while attempt < max_attempts:
                try:
                    result = fn(*args, **kwargs)
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
                    await sleep_backoff(attempt, base_delay, factor, max_delay)
            try:
                logger.error(
                    f"retry exhausted func={fn.__name__} attempts={attempt}")
            except Exception:
                pass
            raise last_exc

        return wrapper

    return decorator


def sync_retry(*_, **__):
    raise NotImplementedError("Use retry_async for async tests")
