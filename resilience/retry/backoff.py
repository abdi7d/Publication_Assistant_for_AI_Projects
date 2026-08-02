import asyncio
import random
import time
from typing import Callable, Optional


def _resolve_multiplier(multiplier: Optional[float] = None, factor: Optional[float] = None) -> float:
    if multiplier is not None:
        return float(multiplier)
    if factor is not None:
        return float(factor)
    return 2.0


def exponential_backoff(
    attempt: int,
    base: float = 0.5,
    multiplier: Optional[float] = None,
    max_delay: float = 60.0,
    factor: Optional[float] = None,
    jitter: bool = False,
) -> float:
    """Return an exponential backoff delay for a given attempt number."""
    attempt = max(0, int(attempt))
    multiplier_value = _resolve_multiplier(
        multiplier=multiplier, factor=factor)
    delay = min(base * (multiplier_value ** attempt), max_delay)
    if not jitter:
        return delay
    if delay <= 0:
        return 0.0
    return delay + random.uniform(-0.1 * delay, 0.1 * delay)


class ExponentialBackoff:
    """Small convenience wrapper for generating delays across attempts."""

    def __init__(self, base: float = 0.5, multiplier: float = 2.0, max_delay: float = 60.0, jitter: bool = False):
        self.base = base
        self.multiplier = multiplier
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        return exponential_backoff(
            attempt,
            base=self.base,
            multiplier=self.multiplier,
            max_delay=self.max_delay,
            jitter=self.jitter,
        )


def calculate_jitter(base_delay: float) -> float:
    """Return a jittered version of the provided base delay."""
    if base_delay <= 0:
        return 0.0
    return base_delay + random.uniform(-0.2 * base_delay, 0.2 * base_delay)


def jittered_backoff(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> float:
    """Compute exponential backoff with jitter."""
    return exponential_backoff(attempt, base=base, factor=factor, max_delay=max_delay, jitter=True)


async def sleep_backoff(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> None:
    delay = jittered_backoff(
        attempt, base=base, factor=factor, max_delay=max_delay)
    await asyncio.sleep(delay)


def sync_backoff_sleep(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> None:
    delay = jittered_backoff(
        attempt, base=base, factor=factor, max_delay=max_delay)
    time.sleep(delay)


def capped_backoff(attempt: int, cap: float = 30.0, **kwargs) -> float:
    return min(exponential_backoff(attempt, **kwargs), cap)


def capped_exponential_backoff_factory(base: float = 0.5, multiplier: float = 2.0, max_delay: float = 60.0) -> Callable[[int], float]:
    return lambda attempt: exponential_backoff(attempt, base=base, multiplier=multiplier, max_delay=max_delay)


def jittered_exponential_backoff(base: float = 0.5, multiplier: float = 2.0, max_delay: float = 60.0, jitter: float = 0.1) -> Callable[[int], float]:
    def delay(retry_count: int) -> float:
        exp = min(base * (multiplier ** max(0, retry_count - 1)), max_delay)
        jitter_val = exp * jitter * (random.random() * 2 - 1)
        return max(0.0, exp + jitter_val)

    return delay
