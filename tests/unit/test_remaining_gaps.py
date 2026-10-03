import os
import sys
import types

from app import validate_submission
from security.validators import input_validators as iv
from tools.web_search import WebSearchTool
from tools.rag_retriever import RAGRetriever
from tools.arxiv_scholar import ArxivScholarTool
from resilience.retry.retry_manager import RetryManager
from resilience.timeout.timeout_manager import TimeoutManager


def test_validate_submission_rejects_invalid_prompt(monkeypatch):
    monkeypatch.setattr(iv, 'settings', types.SimpleNamespace(MAX_PROMPT_LENGTH=10))
    ok, msg = iv.validate_prompt('x' * 11)
    assert ok is False
    assert 'Prompt exceeds maximum allowed length' in msg


def test_web_search_summarize_and_improve_handles_groq_provider(monkeypatch):
    class MockGroqResponse:
        class Choice:
            class Message:
                def __init__(self):
                    self.content = 'groq output'
            def __init__(self):
                self.message = self.Message()
        def __init__(self):
            self.choices = [self.Choice()]

    class MockGroqClient:
        def __init__(self):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda model, messages: MockGroqResponse()))

    tool = WebSearchTool(selected_model='x', provider='groq')
    tool.gemini_client = None
    tool.groq_client = MockGroqClient()
    tool.active_client = tool.groq_client
    out = tool.summarize_and_improve('# T', [], style='S', goal='G')
    assert 'groq output' in out


def test_rag_retriever_returns_empty_when_collection_missing(monkeypatch):
    class FakeCollection:
        def query(self, **kwargs):
            return {'documents': [['doc']]}

    class FakeClient:
        def __init__(self, path=None):
            self.collection = FakeCollection()
        def get_or_create_collection(self, name):
            return self.collection

    monkeypatch.setattr('tools.rag_retriever.chromadb', types.SimpleNamespace(PersistentClient=FakeClient))
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    retriever = RAGRetriever(db_path='.')
    assert retriever.retrieve('text') == []


def test_arxiv_scholar_sanitizes_and_returns_empty(monkeypatch):
    monkeypatch.setattr('tools.arxiv_scholar._HAS_ARXIV', True)
    monkeypatch.setattr('tools.arxiv_scholar.arxiv', types.SimpleNamespace(
        Client=lambda: object(),
        Search=lambda **kwargs: object(),
        SortCriterion=types.SimpleNamespace(Relevance=1),
    ))

    class BadClient:
        def __init__(self):
            pass
        def results(self, search):
            raise RuntimeError('boom')

    tool = ArxivScholarTool()
    tool.client = BadClient()
    assert tool.search('Hello <b>world</b>') == []


def test_retry_manager_uses_retryable_exception_and_logs(monkeypatch):
    attempts = {'n': 0}

    def flaky():
        attempts['n'] += 1
        if attempts['n'] < 2:
            raise ValueError('boom')
        return 'ok'

    monkeypatch.setattr('resilience.retry.retry_manager.time.sleep', lambda *_args, **_kwargs: None)
    manager = RetryManager(max_retries=2, backoff_base=0.0)
    assert manager.execute(flaky) == 'ok'


def test_timeout_manager_execute_raises_timeout(monkeypatch):
    def slow():
        import time
        time.sleep(0.02)
        return 'done'

    manager = TimeoutManager(timeout_seconds=0.001)
    try:
        manager.execute(slow)
    except TimeoutError:
        pass
    else:
        assert False, 'expected TimeoutError'
