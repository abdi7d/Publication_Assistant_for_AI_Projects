from random import random
from typing import Callable


def exponential_backoff(attempt: int, base: float = 0.5, multiplier: float = 2.0, max_delay: float = 60.0) -> float:
    """Return delay seconds for attempt with jitter.

    - base: initial delay in seconds
    - multiplier: exponential multiplier
    - max_delay: maximum delay cap
    """
    delay = min(base * (multiplier ** (attempt - 1)), max_delay)
    # full jitter
    jittered = delay * random()
    return jittered


def capped_exponential_backoff_factory(base: float = 0.5, multiplier: float = 2.0, max_delay: float = 60.0) -> Callable[[int], float]:
    return lambda attempt: exponential_backoff(attempt, base=base, multiplier=multiplier, max_delay=max_delay)
from typing import Callable
import random


def exponential_backoff(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff with jitter.

    :param attempt: 1-based attempt count
    :param base: base delay in seconds
    :param factor: multiplier
    :param max_delay: maximum delay cap
    :return: delay seconds
    """
    exp = base * (factor ** (attempt - 1))
    jitter = random.uniform(0, exp * 0.1)
    delay = min(exp + jitter, max_delay)
    return delay


def capped_backoff(attempt: int, cap: float = 30.0, **kwargs) -> float:
    return min(exponential_backoff(attempt, **kwargs), cap)
import asyncio
import math
import random
from typing import Callable


def jittered_backoff(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> float:
    """Compute exponential backoff with full jitter.

    Formula: min(max_delay, base * factor ** attempt)
    then apply uniform jitter in [0, delay]
    """
    delay = min(max_delay, base * (factor ** attempt))
    return random.uniform(0, delay)


async def sleep_backoff(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> None:
    delay = jittered_backoff(attempt, base, factor, max_delay)
    await asyncio.sleep(delay)


def sync_backoff_sleep(attempt: int, base: float = 0.5, factor: float = 2.0, max_delay: float = 60.0) -> None:
    delay = jittered_backoff(attempt, base, factor, max_delay)
    import time

    time.sleep(delay)
from typing import Callable
import random

def jittered_exponential_backoff(base: float = 0.5, multiplier: float = 2.0, max_delay: float = 60.0, jitter: float = 0.1) -> Callable[[int], float]:
    def delay(retry_count: int) -> float:
        exp = base * (multiplier ** (retry_count - 1))
        exp = min(exp, max_delay)
        jitter_val = exp * jitter * (random.random() * 2 - 1)
        return max(0.0, exp + jitter_val)
    return delay
