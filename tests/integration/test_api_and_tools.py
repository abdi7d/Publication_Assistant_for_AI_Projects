import pytest
import asyncio
from fastapi import status


def test_health_and_readiness(test_client):
    r = test_client.get('/health')
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_tool_pipeline_with_retries():
    # simulate tool function with retries and fallback
    from tests.mocks.mock_llm import MockGoogleLLM
    from resilience.retry.retry_manager import retry_async

    llm = MockGoogleLLM(responses=["a", "b", "c"])

    async def tool_call():
        r = await llm.generate("x")
        if r["text"] == "a":
            raise RuntimeError("transient")
        return r

    res = await retry_async(max_attempts=3, base_delay=0.01)(tool_call)()
    assert res["provider"] == "google"
