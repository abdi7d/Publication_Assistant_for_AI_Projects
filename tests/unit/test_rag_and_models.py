import os
import pytest

from tools.rag_retriever import RAGRetriever
import tools.list_available_models as lam


def test_rag_init_without_chromadb(monkeypatch):
    # Simulate chromadb missing by ensuring module-level chromadb is None
    monkeypatch.setattr('tools.rag_retriever.chromadb', None)
    r = RAGRetriever(db_path='./nonexistent_db_path_for_tests')
    assert r.client is None
    assert r.collection is None
    # retrieve should return empty list when collection None
    assert r.retrieve('some text') == []


def test_list_available_models_no_clients(capsys, monkeypatch):
    # Simulate genai and Groq missing
    monkeypatch.setattr('tools.list_available_models.genai', None)
    monkeypatch.setattr('tools.list_available_models.Groq', None)
    lam.list_gemini_models()
    lam.list_groq_models()
    captured = capsys.readouterr()
    assert 'google-genai not installed' in captured.out or 'GOOGLE_API_KEY' in captured.out
