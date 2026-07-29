import os
import sys
import types
import pytest

from tools.web_search import WebSearchTool
import tools.list_available_models as lam


def test_tavily_search_string_response(monkeypatch):
    # Create a fake langchain_community.tools.tavily_search module
    mod_name = 'langchain_community.tools.tavily_search'
    fake_mod = types.ModuleType(mod_name)

    class Tavily:
        def __init__(self, max_results=5):
            pass

        def invoke(self, q):
            return 'just a string'

    fake_mod.TavilySearchResults = Tavily
    sys.modules[mod_name] = fake_mod

    monkeypatch.setenv('TAVILY_API_KEY', 'token')
    tool = WebSearchTool()
    # Force the search to use our fake
    tool.search = Tavily()
    res = tool.search_similar_repos('q')
    assert res == []


def test_tavily_search_list_of_non_dicts(monkeypatch):
    mod_name = 'langchain_community.tools.tavily_search'
    fake_mod = types.ModuleType(mod_name)

    class Tavily2:
        def __init__(self, max_results=5):
            pass

        def invoke(self, q):
            return ['a', 'b', 123]

    fake_mod.TavilySearchResults = Tavily2
    sys.modules[mod_name] = fake_mod

    monkeypatch.setenv('TAVILY_API_KEY', 'token')
    tool = WebSearchTool()
    tool.search = Tavily2()
    res = tool.search_similar_repos('q')
    assert res == []


def test_list_groq_models_print(monkeypatch, capsys):
    class FakeModel:
        def __init__(self, id):
            self.id = id

    class FakeGroqClient:
        def __init__(self, api_key=None):
            pass

        class models:
            @staticmethod
            def list():
                return [FakeModel('g1'), FakeModel('g2')]

    monkeypatch.setenv('GROQ_API_KEY', 'token')
    monkeypatch.setattr(lam, 'Groq', FakeGroqClient)
    lam.list_groq_models()
    out = capsys.readouterr().out
    assert 'Available models' in out or 'g1' in out
