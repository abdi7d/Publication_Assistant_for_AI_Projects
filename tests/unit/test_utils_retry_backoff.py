import asyncio
import pytest
from tests.mocks.mock_llm import MockGoogleLLM
from resilience.retry.retry_manager import retry_async


@pytest.mark.asyncio
async def test_mock_google_llm_and_retry():
    mock = MockGoogleLLM(responses=["a", "b"])

    async def flaky():
        res = await mock.generate("hi")
        if res["text"] == "a":
            raise RuntimeError("transient")
        return res

    # should recover with retries
    out = await retry_async(max_attempts=3, base_delay=0.01)(flaky)()
    assert out["provider"] == "google"


@pytest.mark.asyncio
async def test_sync_retry_simple_async():
    called = {"n": 0}

    def flaky_sync():
        called["n"] += 1
        if called["n"] < 2:
            raise ValueError("boom")
        return "ok"

    wrapped = retry_async(max_attempts=3, base_delay=0.01)(flaky_sync)
    # call via async wrapper
    result = await wrapped()
    assert result == "ok"
