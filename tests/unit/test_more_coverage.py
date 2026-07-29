import sys
import types
import os
import time
import asyncio
import importlib
import pytest

from resilience.retry import backoff as rb
from resilience.retry.retry_manager import retry_async


def test_backoff_all_variants():
    # exercise various backoff helpers
    assert isinstance(rb.exponential_backoff(1, base=0.1), float)
    assert isinstance(rb.jittered_backoff(1, base=0.1), float)
    # Use capped_backoff which is safe across versions
    assert isinstance(rb.capped_backoff(1, cap=0.5, base=0.1), float)
    gbe = rb.jittered_exponential_backoff()
    assert isinstance(gbe(2), float)


@pytest.mark.asyncio
async def test_retry_async_exhaustion_and_success():
    # function that always raises
    calls = {'n': 0}

    def always_fail():
        calls['n'] += 1
        raise ValueError('boom')

    wrapped = retry_async(max_attempts=3, base_delay=0.001)(always_fail)
    with pytest.raises(ValueError):
        await wrapped()

    # sync then success
    calls2 = {'n': 0}

    def flaky_sync():
        calls2['n'] += 1
        if calls2['n'] < 2:
            raise RuntimeError('try')
        return 'ok'

    wrapped2 = retry_async(max_attempts=3, base_delay=0.001)(flaky_sync)
    res = await wrapped2()
    assert res == 'ok'


def test_web_search_search_similar_variants(monkeypatch):
    # Prepare fake tavily module
    mod_name = 'langchain_community.tools.tavily_search'
    fake_mod = types.ModuleType(mod_name)

    class FakeTav:
        def __init__(self, max_results=5):
            self.max = max_results

        def invoke(self, q):
            if 'str' in q:
                return 'a string'
            if 'nonlist' in q:
                return {'k': 'v'}
            return [{'title': 'T', 'url': 'U', 'content': 'C'}]

    fake_mod.TavilySearchResults = FakeTav
    monkeypatch.setitem(sys.modules, mod_name, fake_mod)
    monkeypatch.setenv('TAVILY_API_KEY', '1')

    from tools.web_search import WebSearchTool
    w = WebSearchTool()
    # string result
    assert w.search is not None
    res = w.search.invoke('str')
    assert isinstance(res, str)
    # non-list
    res2 = w.search.invoke('nonlist')
    assert isinstance(res2, dict)
    # proper list
    res3 = w.search.invoke('ok')
    assert isinstance(res3, list)


def test_main_cli_runs_and_prints(monkeypatch, tmp_path, capfd):
    # Monkeypatch tools to simple fakes to avoid external calls
    import tools

    class P:
        def __init__(self, *a, **k):
            pass

        def parse(self, src):
            return {'files': {'README.md': '# X'}, 'README.md': '# X'}

    monkeypatch.setattr(tools, 'RepoParser', P)
    monkeypatch.setattr(tools, 'KeywordExtractor', lambda: object())
    monkeypatch.setattr(tools, 'WebSearchTool', lambda *a, **k: object())
    monkeypatch.setattr(tools, 'RAGRetriever', lambda *a, **k: object())
    monkeypatch.setattr(tools, 'ArxivScholarTool', lambda *a, **k: object())

    # Patch Orchestrator to return a minimal result
    import orchestration

    class FakeOrch:
        def run_pipeline(self, agents=None, repo_source=None, style=None, goal=None):
            class Meta:
                title_suggestions = ['t']
                tags = ['a']

            class Analysis:
                missing_sections = ['Install']

            class Review:
                score = 5

            class Fact:
                flagged = []

            return {'metadata': Meta(), 'analysis': Analysis(), 'review': Review(), 'fact_check': Fact()}

    monkeypatch.setattr(orchestration, 'Orchestrator', FakeOrch)

    # run main.main with argv
    import main
    monkeypatch.setenv('GOOGLE_API_KEY', '')
    argv = sys.argv
    sys.argv = ['main.py', '--repo-path', str(tmp_path)]
    try:
        main.main()
    finally:
        sys.argv = argv

    out = capfd.readouterr()
    assert 'Publication Assistant Report' in out.out
