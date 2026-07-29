import types
import os
import pytest

from tools.keyword_extractor import KeywordExtractor
from tools.arxiv_scholar import ArxivScholarTool, _HAS_ARXIV
from utils.mcp import MCPBus, MCPMessage


def test_keyword_extractor_heuristic():
    ke = KeywordExtractor(top_k=5)
    text = "This project uses pytorch and transformers for deep learning. It demonstrates training and evaluation."
    kws = ke._heuristic_extract(text)
    assert 'pytorch' in kws or 'transformers' in kws


def test_arxiv_tool_no_arxiv(monkeypatch):
    # Ensure arxiv not available path
    monkeypatch.setattr('tools.arxiv_scholar._HAS_ARXIV', False)
    at = ArxivScholarTool()
    res = at.search('topic')
    assert res == []


def test_arxiv_tool_with_fake_client(monkeypatch):
    # Simulate arxiv available with a fake client
    fake_client = types.SimpleNamespace()

    def fake_results(search):
        class R:
            title = 'T'
            summary = 'S'
            entry_id = 'id'
            pdf_url = 'http://pdf'
            published = '2020-01-01'

        return [R()]

    fake_client.results = lambda search: fake_results(search)
    monkeypatch.setattr('tools.arxiv_scholar._HAS_ARXIV', True)
    monkeypatch.setattr('tools.arxiv_scholar.arxiv', types.SimpleNamespace(
        Client=lambda: fake_client, Search=lambda **k: object(), SortCriterion=types.SimpleNamespace(Relevance=1)))
    at = ArxivScholarTool()
    at.client = fake_client
    res = at.search('query')
    assert isinstance(res, list)
    assert res[0]['title'] == 'T'


def test_mcpbus_pub_sub_and_error(monkeypatch):
    bus = MCPBus()
    received = []

    def cb(msg: MCPMessage):
        received.append((msg.topic, msg.payload))

    bus.subscribe('t', cb)
    bus.publish('t', {'a': 1})
    assert received and received[0][1]['a'] == 1

    # subscriber that throws
    def bad_cb(msg):
        raise RuntimeError('boom')

    bus.subscribe('t', bad_cb)
    # Should not raise when publishing
    bus.publish('t', {'b': 2})
