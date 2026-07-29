import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


class ConcurrencyManager:
    """Manage concurrency with an asyncio.Semaphore and async context manager.

    Usage:
        cm = ConcurrencyManager(max_concurrent=5)
        async with cm.acquire():
            await do_work()
    """

    def __init__(self, max_concurrent: int = 10) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        await self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()
