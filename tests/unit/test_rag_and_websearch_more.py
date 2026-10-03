import os
import types
import pytest

import tools.rag_retriever as rr_mod
from tools.rag_retriever import RAGRetriever
from tools.web_search import WebSearchTool


def test_rag_seeding_and_retrieve(monkeypatch, tmp_path):
    # Fake chromadb with PersistentClient and collection
    added = []

    class FakeCollection:
        def __init__(self):
            self._docs = []

        def count(self):
            return 0

        def add(self, ids, embeddings, documents):
            added.extend(documents)

        def query(self, query_embeddings, n_results):
            return {'documents': [['doc1', 'doc2'][:n_results]]}

    class FakePersistentClient:
        def __init__(self, path=None):
            self.path = path

        def get_or_create_collection(self, name):
            return FakeCollection()

    fake_chroma = types.SimpleNamespace(PersistentClient=FakePersistentClient)
    monkeypatch.setattr(rr_mod, 'chromadb', fake_chroma)

    # Fake genai client with embedding
    class FakeEmbedResp:
        def __init__(self):
            self.embedding = [0.1, 0.2]

    class FakeModels:
        def embed_content(self, model, contents):
            return FakeEmbedResp()

    class FakeGenAIClient:
        def __init__(self, api_key=None):
            self.models = FakeModels()

    monkeypatch.setenv('GOOGLE_API_KEY', 'x')
    monkeypatch.setattr(
        rr_mod, 'genai', types.SimpleNamespace(Client=FakeGenAIClient))

    # Instantiate retriever with existing path to force init
    db_dir = tmp_path / 'chroma_db'
    db_dir.mkdir()
    r = RAGRetriever(db_path=str(db_dir))
    # After init, seed should have been attempted and documents added
    assert isinstance(r.collection, FakeCollection)

    # Test retrieve uses fake client's embedding and returns flattened docs
    res = r.retrieve('query text', top_k=2)
    assert res == ['doc1', 'doc2'][:2]


def test_websearch_groq_primary(monkeypatch):
    tool = WebSearchTool(selected_model='m', provider='groq')

    class FakeMessage:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)

    class FakeCompletions:
        def create(self, model, messages):
            return types.SimpleNamespace(choices=[FakeChoice('Groq content')])

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroqClient:
        def __init__(self):
            self.chat = FakeChat()

    tool.groq_client = FakeGroqClient()
    tool.active_client = tool.groq_client

    out = tool.summarize_and_improve('# R', [], style='S', goal='G')
    assert 'Groq content' in out
