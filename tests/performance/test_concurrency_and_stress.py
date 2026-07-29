import asyncio
import pytest
from resilience.concurrency.concurrency_manager import ConcurrencyManager


@pytest.mark.asyncio
async def test_concurrency_semaphore_limits():
    cm = ConcurrencyManager(max_concurrent=3)

    async def work(i):
        async with cm.acquire():
            await asyncio.sleep(0.01)
            return i

    tasks = [asyncio.create_task(work(i)) for i in range(10)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
