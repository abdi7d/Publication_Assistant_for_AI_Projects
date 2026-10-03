import asyncio
import pytest
from resilience.timeout.timeout_manager import async_timeout


@pytest.mark.asyncio
async def test_async_timeout_decorator():
    @async_timeout(0.05)
    async def slow():
        await asyncio.sleep(1)
        return "done"

    with pytest.raises(asyncio.TimeoutError):
        await slow()
