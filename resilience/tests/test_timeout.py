import asyncio
import pytest
from resilience.timeout.timeout_manager import async_timeout


@pytest.mark.asyncio
async def test_timeout_cancellation():
    async def long_task():
        await asyncio.sleep(2)
        return "done"

    with pytest.raises(asyncio.TimeoutError):
        await async_timeout(0.05)(long_task)()
