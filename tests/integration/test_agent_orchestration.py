import asyncio
import pytest
from tests.mocks.mock_llm import MockGroqLLM


@pytest.mark.asyncio
async def test_agent_chain_with_mock_llm():
    # Simulate two agents passing messages
    llm = MockGroqLLM(responses=["result1", "result2"])

    async def agent_a(input_text: str) -> str:
        r = await llm.generate(input_text)
        return r["text"] + "-a"

    async def agent_b(input_text: str) -> str:
        r = await llm.generate(input_text)
        return r["text"] + "-b"

    a_out = await agent_a("start")
    b_out = await agent_b(a_out)
    assert b_out.endswith("-b")
