import asyncio
import pytest
from resilience.retry.retry_manager import retry_async


class TransientError(Exception):
    pass


attempts = 0


async def flaky_operation():
    global attempts
    attempts += 1
    if attempts < 3:
        raise TransientError("temporary failure")
    return "ok"


@pytest.mark.asyncio
async def test_retry_async_success():
    # should succeed after retries
    result = await retry_async(max_attempts=5, base_delay=0.01)(flaky_operation)()
    assert result == "ok"


@pytest.mark.asyncio
async def test_retry_exhaustion():
    async def always_fail():
        raise TransientError("oops")

    with pytest.raises(TransientError):
        await retry_async(max_attempts=2, base_delay=0.01)(always_fail)()
