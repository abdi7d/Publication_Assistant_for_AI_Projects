import asyncio
import pytest
from resilience.circuit_breaker.circuit_breaker import CircuitBreaker, CircuitOpenError


@pytest.mark.asyncio
async def test_circuit_breaker_open_close_cycle():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.5)

    async def fail():
        raise RuntimeError("down")

    # trip the breaker
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await cb.call(fail)

    # now circuit open
    with pytest.raises(CircuitOpenError):
        await cb.call(fail)

    # wait for recovery window
    await asyncio.sleep(0.6)

    # half-open attempt should call through (and fail)
    with pytest.raises(RuntimeError):
        await cb.call(fail)
