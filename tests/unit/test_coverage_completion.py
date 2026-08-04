import asyncio
import builtins
import importlib
import os
import sys
import types
import zipfile
from pathlib import Path

import pytest

from agents.content_improver import ContentImproverAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from agents.repo_analyzer import RepoAnalyzerAgent
from orchestration.graph import Orchestrator
from resilience.retry import backoff as rb
from resilience.retry.retry_manager import RetryManager
from resilience.timeout.timeout_manager import TimeoutManager, run_with_timeout
from security.configs import config_loader
from security.validators.file_validators import validate_mime_type, validate_upload
from security.validators import input_validators as iv
from tools.arxiv_scholar import ArxivScholarTool
from tools.keyword_extractor import KeywordExtractor
from tools.list_available_models import list_gemini_models, list_groq_models
from tools.rag_retriever import RAGRetriever
from tools.repo_parser import RepoParser
from tools.web_search import WebSearchTool


def test_content_improver_covers_fallback_and_summary_paths():
    class SearchStub:
        def search_similar_repos(self, readme, top_k=3):
            raise RuntimeError("boom")

        def summarize_and_improve(self, readme, examples, style="Technical Blog", goal=""):
            raise RuntimeError("boom")

    class RagStub:
        def retrieve(self, readme):
            raise RuntimeError("boom")

    agent = ContentImproverAgent(web_search=SearchStub(), rag=RagStub())
    result = agent.run("# Example Project\n\nA short description.", {"tags": ["ai", "nlp"]})
    assert "Installation" in result.improved_readme
    assert result.suggested_images["architecture_diagram"]
    assert agent._extract_title("# Heading\n\nBody") == "Heading"
    assert agent._extract_summary("## Overview\n\n## Details") == ""
    assert agent._looks_like_error("Error: empty response") is True


def test_metadata_recommender_covers_fallback_paths(monkeypatch):
    import agents.metadata_recommender as mod

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "google" or name.startswith("google."):
            raise ImportError("simulated")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(mod)

    agent = mod.MetadataRecommenderAgent(keyword_extractor=type("K", (), {"extract": lambda self, text: ["ai", "rag"]})())
    agent.model = None
    rec = agent.run("# Demo\n\nProject about AI and workflows.", {"app.py": "import fastapi", "requirements.txt": "fastapi pytest"})
    assert rec.tags
    assert rec.short_description

    agent.model = type("M", (), {"models": type("Models", (), {"generate_content": lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))})()})()
    titles = agent._make_titles("# Demo", ["ai", "workflow"])
    assert titles[0].startswith("🚀")
    desc = agent._generate_description("# Demo", ["ai", "workflow"])
    assert desc


def test_repo_analyzer_covers_code_stats_and_missing_sections():
    class FakeParser:
        def parse(self, repo_source):
            return {
                "files": {
                    "app.py": "import fastapi\n\nif __name__ == '__main__':\n    print('hi')\n",
                    "requirements.txt": "fastapi\npytest\n",
                    "README.md": "# Demo\n\n## Installation\n\nInstall it.\n\n## Usage\n\nRun it.\n\n## License\n\nMIT\n\n## Contributing\n\nOpen a PR.\n\n## Examples\n\nExamples here.\n\n## Architecture\n\nSimple architecture.\n",
                },
                "README.md": "# Demo\n\n## Installation\n\nInstall it.\n",
                "title": "Demo",
            }

    agent = RepoAnalyzerAgent("dummy", FakeParser())
    analysis = agent.run()
    assert analysis.code_stats["dependencies"] == ["fastapi", "pytest"]
    assert analysis.code_stats["entrypoints"] == ["app.py"]
    assert analysis.code_stats["project_type"] == "Python FastAPI service"
    assert "Usage" in analysis.missing_sections
    assert "Project type" in analysis.summary


def test_orchestrator_covers_execute_and_graph_failure(monkeypatch):
    class FakeGraph:
        def __init__(self, *args, **kwargs):
            self.compiled = None

        def add_node(self, *args, **kwargs):
            return None

        def set_entry_point(self, *args, **kwargs):
            return None

        def add_edge(self, *args, **kwargs):
            return None

        def compile(self):
            class Compiled:
                def invoke(self, inputs):
                    raise RuntimeError("boom")

            self.compiled = Compiled()
            return self.compiled

    monkeypatch.setattr("orchestration.graph.StateGraph", FakeGraph)
    orchestrator = Orchestrator()
    assert orchestrator.execute("dummy", agents=None) == {}

    class StubRepoAnalyzer:
        def run(self):
            return types.SimpleNamespace(readme="# Demo", files={}, code_stats={})

    monkeypatch.setattr(orchestrator.publication_builder, "build_readme", lambda *args, **kwargs: "fallback")
    result = orchestrator.run_pipeline({"repo_analyzer": StubRepoAnalyzer()}, "dummy")
    assert result["publication_readme"] == "fallback"


def test_backoff_helpers_cover_jitter_and_factory():
    assert rb.exponential_backoff(3, base=1.0, multiplier=2.0, max_delay=10.0, jitter=True) >= 0
    assert rb.calculate_jitter(0.0) == 0.0
    factory = rb.jittered_exponential_backoff(base=1.0, multiplier=2.0, max_delay=5.0, jitter=0.1)
    assert factory(1) >= 0
    assert rb.capped_backoff(10, cap=2.0, base=2.0, multiplier=2.0) == 2.0


def test_retry_manager_and_timeout_manager_cover_extra_paths(monkeypatch):
    import resilience.retry.retry_manager as rm

    class WarningLogger:
        def warning(self, *args, **kwargs):
            raise RuntimeError("boom")

        def info(self, *args, **kwargs):
            return None

        def error(self, *args, **kwargs):
            return None

    monkeypatch.setattr(rm, "logger", WarningLogger())
    monkeypatch.setattr(rm.time, "sleep", lambda *_args, **_kwargs: None)

    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("boom")
        return "ok"

    manager = RetryManager(max_retries=1, backoff_base=0.0)
    assert manager.execute(flaky) == "ok"

    @rm.retry_async(max_attempts=2, base_delay=0.0, factor=2.0, max_delay=0.0)
    async def flaky_async():
        if attempts["count"] < 2:
            attempts["count"] += 1
            raise ValueError("boom")
        return "done"

    assert asyncio.run(flaky_async()) == "done"

    async def slow_coro():
        await asyncio.sleep(0.01)
        return 1

    assert asyncio.run(run_with_timeout(slow_coro(), timeout=0.001, fallback=lambda: 99)) == 99
    manager_timeout = TimeoutManager(timeout_seconds=0)
    assert manager_timeout.execute(lambda: "ok") == "ok"


def test_security_settings_and_validators_cover_extra_branches(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    config_loader._settings = None
    settings = config_loader.get_settings()
    assert settings.APP_ENV == "production"
    assert settings.DEBUG is False

    assert validate_mime_type(b"x", "archive.bin") == (True, "ok")
    assert validate_upload(b"x", "file.bin", "application/json") == (False, "extension_not_allowed")
    assert validate_mime_type(b"x", "file.txt") == (True, "ok")

    assert iv.validate_prompt("   ")[0] is False
    assert iv.validate_prompt("bad\x00value")[0] is False
    long_prompt = "x" * 6000
    assert iv.validate_prompt(long_prompt)[0] is False


def test_arxiv_keyword_list_and_repo_parser_cover_fallbacks(monkeypatch, tmp_path):
    import importlib
    import tools.arxiv_scholar as arxiv_mod
    import tools.keyword_extractor as keyword_mod

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "arxiv" or name.startswith("arxiv"):
            raise ImportError("simulated")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(arxiv_mod)
    assert arxiv_mod.ArxivScholarTool().search("Hello <b>world</b>") == []

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(keyword_mod)
    extractor = keyword_mod.KeywordExtractor(top_k=3)
    keywords = extractor.extract("Python AI project with FastAPI and LangChain")
    assert keywords

    monkeypatch.setattr(keyword_mod, "genai", None)
    extractor = keyword_mod.KeywordExtractor(top_k=3)
    assert extractor.extract("Python FastAPI project")

    list_gemini_models()
    list_groq_models()

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# Demo\n\nInstall now.\n", encoding="utf-8")
    (repo_dir / "app.py").write_text("print('hi')\n", encoding="utf-8")

    parser = RepoParser()
    parsed = parser.parse(str(repo_dir))
    assert parsed["README.md"].startswith("# Demo")
    assert parsed["title"] == "Demo"

    zip_path = tmp_path / "repo.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("README.md", "# Zip Repo")
    parsed_zip = parser.parse(str(zip_path))
    assert parsed_zip["README.md"] == "# Zip Repo"

    assert parser.parse("") == {"files": {}, "README.md": ""}

    assert parser.parse("invalid-repo-name") == {"files": {}, "README.md": ""}


def test_rag_retriever_and_web_search_cover_multiple_paths(monkeypatch):
    import tools.rag_retriever as rag_mod

    monkeypatch.setattr(rag_mod, "chromadb", None)
    retriever = rag_mod.RAGRetriever(db_path="./missing")
    assert retriever.retrieve("hello") == []

    class FakeCollection:
        def __init__(self):
            self.docs = []

        def count(self):
            return 0

        def add(self, ids, embeddings, documents):
            self.docs.extend(documents)

        def query(self, query_embeddings, n_results=3):
            return {"documents": [["doc-a"]]}

    class FakeClient:
        def __init__(self, path=None):
            self.collection = FakeCollection()

        def get_or_create_collection(self, name):
            return self.collection

    class FakeGenaiResponse:
        def __init__(self, values):
            self.values = values

    class FakeGenaiClient:
        def __init__(self, api_key=None):
            self.api_key = api_key

        class Models:
            def embed_content(self, model, contents):
                return FakeGenaiResponse([0.1, 0.2])

        models = Models()

    monkeypatch.setattr(rag_mod, "chromadb", types.SimpleNamespace(PersistentClient=FakeClient))
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    monkeypatch.setattr(rag_mod, "genai", types.SimpleNamespace(Client=FakeGenaiClient))
    retriever = rag_mod.RAGRetriever(db_path=".")
    assert retriever.retrieve("hello") == ["doc-a"]

    tool = WebSearchTool(selected_model="gemini-1.5-flash", provider="google")
    tool.gemini_client = None
    tool.groq_client = None
    tool.active_client = None
    assert "Improved summary" in tool.summarize_and_improve("# Title\n\nBody", [], style="s", goal="g")

    class EmptyResponse:
        text = None

    class GeminiClient:
        class Models:
            def generate_content(self, model, contents):
                return EmptyResponse()

        models = Models()

    tool = WebSearchTool(selected_model="x", provider="google")
    tool.gemini_client = GeminiClient()
    tool.groq_client = None
    tool.active_client = tool.gemini_client
    assert "empty response" in tool.summarize_and_improve("# Title", [], style="s", goal="g").lower()

    class GroqClient:
        class Chat:
            class Completions:
                def create(self, model, messages):
                    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="groq output"))])

            completions = Completions()

        chat = Chat()

    tool = WebSearchTool(selected_model="x", provider="groq")
    tool.gemini_client = None
    tool.groq_client = GroqClient()
    tool.active_client = tool.groq_client
    assert "groq output" in tool.summarize_and_improve("# Title", [], style="s", goal="g")

    class SearchStub:
        def invoke(self, query):
            return "not-a-list"

    tool = WebSearchTool(selected_model="x", provider="google")
    tool.search = SearchStub()
    assert tool.search_similar_repos("query") == []

    class SearchResultsStub:
        def invoke(self, query):
            return [{"title": "t", "url": "u", "content": "c"}]

    tool.search = SearchResultsStub()
    assert tool.search_similar_repos("query", top_k=1)[0]["title"] == "t"
