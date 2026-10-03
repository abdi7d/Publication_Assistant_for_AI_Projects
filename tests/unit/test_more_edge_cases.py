import types
import os
import pytest

from tools.keyword_extractor import KeywordExtractor
import tools.list_available_models as lam
from tools.arxiv_scholar import ArxivScholarTool
import tools.rag_retriever as rr_mod


def test_keyword_extractor_llm(monkeypatch):
    class FakeModels:
        def generate_content(self, model, contents):
            return types.SimpleNamespace(text='alpha, beta, gamma')

    class FakeClient:
        def __init__(self, api_key=None):
            self.models = FakeModels()

    monkeypatch.setenv('GOOGLE_API_KEY', 'tok')
    monkeypatch.setattr('tools.keyword_extractor.genai',
                        types.SimpleNamespace(Client=FakeClient))

    ke = KeywordExtractor(top_k=5)
    kws = ke.extract('Some README about alpha and beta')
    assert 'alpha' in kws


def test_list_gemini_models_error(monkeypatch, capsys):
    class BadClient:
        def __init__(self, api_key=None):
            pass

        class models:
            @staticmethod
            def list():
                raise RuntimeError('api error')

    monkeypatch.setenv('GOOGLE_API_KEY', 't')
    monkeypatch.setattr(lam, 'genai', types.SimpleNamespace(Client=BadClient))
    lam.list_gemini_models()
    out = capsys.readouterr().out
    assert 'Error listing models' in out or 'Error' in out


def test_arxiv_client_exception(monkeypatch):
    # Simulate arxiv present but client.results raising
    fake_client = types.SimpleNamespace()

    def broken_results(search):
        raise RuntimeError('boom')
    fake_client.results = lambda search: broken_results(search)
    monkeypatch.setattr('tools.arxiv_scholar._HAS_ARXIV', True)
    monkeypatch.setattr('tools.arxiv_scholar.arxiv', types.SimpleNamespace(
        Client=lambda: fake_client, Search=lambda **k: object(), SortCriterion=types.SimpleNamespace(Relevance=1)))
    at = ArxivScholarTool()
    at.client = fake_client
    res = at.search('q')
    assert res == []


def test_rag_retrieve_missing_api_key(monkeypatch):
    # Ensure chromadb client present but no GOOGLE_API_KEY
    class FakeCollection:
        def query(self, **k):
            return {'documents': [['a']]}

    class FakeClient:
        def __init__(self, path=None):
            pass

        def get_or_create_collection(self, name):
            return FakeCollection()

    monkeypatch.setattr(rr_mod, 'chromadb', types.SimpleNamespace(
        PersistentClient=FakeClient))
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    r = rr_mod.RAGRetriever(db_path='.')
    # collection may be set but retrieve should return [] due to missing API key
    res = r.retrieve('text')
    assert res == []
