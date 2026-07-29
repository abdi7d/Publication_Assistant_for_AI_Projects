import io
import sys
import os
import asyncio
import builtins
import importlib

import pytest

from resilience.retry import backoff as rb
from resilience.timeout.timeout_manager import run_with_timeout, async_timeout, TimeoutManager
from tools import list_available_models
from tools.web_search import WebSearchTool
from tools.arxiv_scholar import ArxivScholarTool
import main as main_mod


def test_backoff_functions_basic():
    # exercise several backoff helpers
    d1 = rb.exponential_backoff(1, base=0.1, factor=2.0, max_delay=1.0)
    assert isinstance(d1, float)
    d2 = rb.jittered_backoff(2, base=0.1, factor=2.0, max_delay=2.0)
    assert 0.0 <= d2 <= 2.0
    d3 = rb.capped_backoff(3, cap=0.5, base=0.1, factor=2.0)
    assert d3 <= 0.5


@pytest.mark.asyncio
async def test_run_with_timeout_and_fallback():
    async def fast():
        await asyncio.sleep(0.01)
        return "done"

    # completes under timeout
    res = await run_with_timeout(fast(), timeout=1.0)
    assert res == "done"

    async def slow():
        await asyncio.sleep(0.2)
        return "slow"

    # timeout uses fallback
    res = await run_with_timeout(slow(), timeout=0.01, fallback=lambda: "fallback")
    assert res == "fallback"


def test_list_available_models_no_keys(capfd, monkeypatch):
    # Ensure functions handle missing clients/keys gracefully
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    list_available_models.list_gemini_models()
    list_available_models.list_groq_models()
    captured = capfd.readouterr()
    assert "not installed or GOOGLE_API_KEY missing" in captured.out or "[Gemini]" in captured.out


def test_web_search_tool_no_clients(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    w = WebSearchTool()
    # with no clients, summarize_and_improve returns heuristic
    out = w.summarize_and_improve("# Title\n\nBody", [], style="S", goal="G")
    assert isinstance(out, str) and out.startswith("#")


def test_arxiv_scholar_no_arxiv():
    a = ArxivScholarTool()
    res = a.search("quantum", max_results=1)
    assert isinstance(res, list)


def test_main_build_agents(tmp_path, monkeypatch):
    # ensure build_agents returns expected keys and doesn't error with minimal repo
    # ensure optional external clients are disabled for deterministic behavior
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    repo_dir = tmp_path / "r"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# X")
    agents = main_mod.build_agents(str(repo_dir))
    assert isinstance(agents, dict)
    for key in ["repo_analyzer", "metadata_recommender", "content_improver", "reviewer_critic", "fact_checker"]:
        assert key in agents
