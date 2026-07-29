from typing import Any, Dict


class MockGoogleLLM:
    def __init__(self, responses=None):
        self._responses = responses or ["mocked google response"]
        self._i = 0

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # simple cyclic mock
        r = self._responses[self._i % len(self._responses)]
        self._i += 1
        return {"text": r, "provider": "google"}


class MockGroqLLM:
    def __init__(self, responses=None):
        self._responses = responses or ["mocked groq response"]
        self._i = 0

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        r = self._responses[self._i % len(self._responses)]
        self._i += 1
        return {"text": r, "provider": "groq"}
