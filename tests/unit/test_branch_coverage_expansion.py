import asyncio
import builtins
import importlib
import os
import sys
import types
import zipfile
from pathlib import Path

import pytest

from agents.fact_checker import FactCheckerAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from agents.repo_analyzer import RepoAnalyzerAgent
from orchestration.graph import Orchestrator
from resilience.retry import backoff as rb
from resilience.retry.retry_manager import RetryManager
from resilience.timeout.timeout_manager import TimeoutManager, run_with_timeout
from security.validators import file_validators as fv
from tools.arxiv_scholar import ArxivScholarTool
from tools.keyword_extractor import KeywordExtractor
from tools.list_available_models import list_gemini_models, list_groq_models
from tools.rag_retriever import RAGRetriever
from tools.repo_parser import RepoParser
from tools.web_search import WebSearchTool
from utils.publication_builder import PublicationBuilder


def test_fact_checker_and_metadata_branches(monkeypatch):
    class FakeScholar:
        def search(self, query, max_results=1):
            if query == "empty":
                return []
            return [{"title": "Paper"}]

    agent = FactCheckerAgent(scholar_tool=None)
    res = agent.run("This project is groundbreaking and provides advanced features.")
    assert res.flagged

    agent = FactCheckerAgent(scholar_tool=FakeScholar())
    assert agent.run("This project is groundbreaking and provides advanced features.").verified
    assert agent.run("This project is empty and no match exists.").verified

    import agents.metadata_recommender as metadata_mod

    class FakeKeywordExtractor:
        def extract(self, text):
            return ["ai", "rag"]

    monkeypatch.setattr(metadata_mod, "genai", None)
    metadata_agent = MetadataRecommenderAgent(FakeKeywordExtractor())
    metadata_agent.model = None
    rec = metadata_agent.run(
        "# Demo\n\nPython AI assistant with FastAPI.",
        {"app.py": "import fastapi", "requirements.txt": "fastapi pytest"},
    )
    assert rec.tags
    assert rec.short_description

    class BadModel:
        class Models:
            def generate_content(self, *args, **kwargs):
                raise RuntimeError("boom")

        models = Models()

    metadata_agent.model = BadModel()
    assert metadata_agent._make_titles("# Demo", ["ai", "workflow"])[0].startswith("🚀")
    assert metadata_agent._generate_description("# Demo", ["ai", "workflow"])


def test_repo_analyzer_and_orchestrator_branches(monkeypatch):
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

    analyzer = RepoAnalyzerAgent("dummy", FakeParser())
    analysis = analyzer.run()
    assert analysis.code_stats["dependencies"] == ["fastapi", "pytest"]
    assert analysis.code_stats["entrypoints"] == ["app.py"]
    assert analysis.code_stats["project_type"] == "Python FastAPI service"
    assert "Usage" in analysis.missing_sections
    assert "Project type" in analysis.summary

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
                    return {"repo_analysis": None, "metadata": None}

            self.compiled = Compiled()
            return self.compiled

    monkeypatch.setattr("orchestration.graph.StateGraph", FakeGraph)
    orchestrator = Orchestrator()
    assert orchestrator.execute("repo", agents=None) == {}

    class StubRepoAnalyzer:
        def run(self):
            return types.SimpleNamespace(readme="# Demo", files={}, code_stats={})

    monkeypatch.setattr(orchestrator.publication_builder, "build_readme", lambda *args, **kwargs: "fallback")
    result = orchestrator.run_pipeline({"repo_analyzer": StubRepoAnalyzer()}, "repo")
    assert result["publication_readme"] == "fallback"


def test_resilience_security_and_tool_branches(monkeypatch):
    import resilience.retry.retry_manager as rm
    import tools.arxiv_scholar as arxiv_mod
    import tools.keyword_extractor as keyword_mod
    import tools.rag_retriever as rag_mod

    assert rb.exponential_backoff(3, base=1.0, multiplier=2.0, max_delay=10.0, jitter=True) >= 0
    assert rb.calculate_jitter(0.0) == 0.0
    factory = rb.jittered_exponential_backoff(base=1.0, multiplier=2.0, max_delay=5.0, jitter=0.1)
    assert factory(1) >= 0
    assert rb.capped_backoff(10, cap=2.0, base=2.0, multiplier=2.0) == 2.0

    class WarningLogger:
        def warning(self, *args, **kwargs):
            raise RuntimeError("boom")

        def info(self, *args, **kwargs):
            return None

        def error(self, *args, **kwargs):
            return None

    monkeypatch.setattr(rm, "logger", WarningLogger())
    monkeypatch.setattr(rm.time, "sleep", lambda *_a, **_kw: None)

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
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("boom")
        return "done"

    assert asyncio.run(flaky_async()) == "done"

    async def slow_coro():
        await asyncio.sleep(0.01)
        return 1

    assert asyncio.run(run_with_timeout(slow_coro(), timeout=0.001, fallback=lambda: 99)) == 99
    assert TimeoutManager(timeout_seconds=0).execute(lambda: "ok") == "ok"

    assert fv.sanitize_filename("bad/../name.txt") == "name.txt"
    assert fv.validate_extension("file.txt") == (True, "ok")
    assert fv.validate_upload_size(b"x" * 10) == (True, "ok")
    assert fv.validate_upload(b"x", "file.bin", "application/json") == (False, "extension_not_allowed")

    monkeypatch.setattr(arxiv_mod, "_HAS_ARXIV", True)
    monkeypatch.setattr(arxiv_mod, "arxiv", types.SimpleNamespace(SortCriterion=types.SimpleNamespace(Relevance="relevance"), Search=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))))
    tool = ArxivScholarTool()
    tool.client = object()
    assert tool.search("Hello <b>world</b>") == []

    class FakeResult:
        title = "Paper"
        summary = "Summary"
        entry_id = "id"
        pdf_url = "https://example.com"
        published = "2024-01-01"

    class FakeClient:
        def results(self, search):
            yield FakeResult()

    monkeypatch.setattr(arxiv_mod, "arxiv", types.SimpleNamespace(SortCriterion=types.SimpleNamespace(Relevance="relevance"), Search=lambda **kwargs: object()))
    tool = ArxivScholarTool()
    tool.client = FakeClient()
    assert tool.search("state of the art", max_results=1)[0]["title"] == "Paper"

    monkeypatch.setattr(keyword_mod, "genai", None)
    extractor = KeywordExtractor(top_k=3)
    assert extractor.extract("") == []
    assert extractor.extract("Python AI project with FastAPI and LangChain")

    class FakeGenaiClient:
        class Models:
            def generate_content(self, *args, **kwargs):
                return types.SimpleNamespace(text="ai, rag")

        models = Models()

    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    monkeypatch.setattr(keyword_mod, "genai", types.SimpleNamespace(Client=lambda api_key: FakeGenaiClient()))
    extractor = KeywordExtractor(top_k=3)
    assert extractor.extract("Python FastAPI project") == ["ai", "rag"]

    monkeypatch.setattr(rag_mod, "chromadb", None)
    assert RAGRetriever(db_path="./missing").retrieve("hello") == []

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

    class FakeGenaiClientForRag:
        def __init__(self, api_key=None):
            self.api_key = api_key

        class Models:
            def embed_content(self, model, contents):
                return FakeGenaiResponse([0.1, 0.2])

        models = Models()

    monkeypatch.setattr(rag_mod, "chromadb", types.SimpleNamespace(PersistentClient=FakeClient))
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    monkeypatch.setattr(rag_mod, "genai", types.SimpleNamespace(Client=FakeGenaiClientForRag))
    retriever = RAGRetriever(db_path=".")
    assert retriever.retrieve("hello") == ["doc-a"]


def test_repo_parser_and_web_search_and_publication_builder(monkeypatch, tmp_path):
    import tools.web_search as web_mod

    parser = RepoParser()
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# Demo\n\nInstall now.\n", encoding="utf-8")
    (repo_dir / "app.py").write_text("print('hi')\n", encoding="utf-8")
    parsed = parser.parse(str(repo_dir))
    assert parsed["README.md"].startswith("# Demo")
    assert parsed["title"] == "Demo"

    zip_path = tmp_path / "repo.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("README.md", "# Zip Repo")
    assert parser.parse(str(zip_path))["README.md"] == "# Zip Repo"

    assert parser.parse("") == {"files": {}, "README.md": ""}
    assert parser.parse("invalid-repo-name") == {"files": {}, "README.md": ""}

    monkeypatch.setattr(web_mod, "genai", None)
    monkeypatch.setenv("TAVILY_API_KEY", "")
    tool = WebSearchTool(selected_model="m", provider="google")
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

    builder = PublicationBuilder()
    md = builder.build_readme(
        repo_analysis=types.SimpleNamespace(
            readme="# Demo\n\nInstall now.",
            files={
                "app.py": "import fastapi\n",
                "requirements.txt": "fastapi\npytest\n",
                "Dockerfile": "FROM python:3.11\n",
                "assets/architecture.png": "image",
                ".github/workflows/ci.yml": "name: ci\n",
            },
            code_stats={"total_lines": 42, "file_count": 4},
            missing_sections=["Usage", "Architecture"],
        ),
        metadata=types.SimpleNamespace(title_suggestions=["Demo"], tags=["ai", "docs"], short_description="Short description"),
        repo_source="demo-repo",
    )
    assert "# Demo" in md
    assert "## Table of Contents" in md
    assert "```mermaid" in md
    assert "## Installation" in md

    raw = "## Summary\n\n[TOC]\n\n```flowchart\nA-->B\n```\n\n![demo](assets/demo.png)"
    processed = builder._post_process_markdown(raw)
    assert "```mermaid" in processed
    assert "<figure>" in processed
    assert builder._render_tree({})
    assert builder._infer_tech_stack({"app.py": "import fastapi"})
    assert builder._infer_repo_evidence({"app.py": "@app.get('/health')\n", "Dockerfile": "docker"})["endpoints"]
    assert builder._infer_cli_flags({"cli.py": "parser.add_argument('--repo-path')\n"}) == ["--repo-path"]
    assert builder._infer_env_vars({"main.py": "GOOGLE_API_KEY=abc\n"}) == ["GOOGLE_API_KEY"]
    assert builder._detect_images({"assets/architecture.png": "img"}) == ["assets/architecture.png"]
    assert builder._repo_stats({"total_lines": 10, "file_count": 2}, {}) == {"Version": "0.1.0", "Files": "2", "Lines": "10", "Updated": "2026"}
    assert builder._first(["a"], "b") == "a"
    assert builder._first_list([], ["x"]) == ["x"]


def test_exhaustive_coverage_paths(monkeypatch):
    import agents.metadata_recommender as metadata_mod
    import agents.reviewer_critic as reviewer_mod
    import orchestration.graph as graph_mod
    import resilience.retry.backoff as backoff_mod
    import resilience.retry.retry_manager as retry_mod
    import resilience.timeout.timeout_manager as timeout_mod
    import security.configs.config_loader as config_mod
    import security.validators.file_validators as file_validators_mod
    import security.validators.input_validators as input_validators_mod
    import tools.arxiv_scholar as arxiv_mod
    import tools.keyword_extractor as keyword_mod
    import tools.list_available_models as list_models_mod
    import tools.rag_retriever as rag_mod
    import tools.web_search as web_mod

    class FakeKeywordExtractor:
        def extract(self, text):
            return ["ai", "", "rag"]

    metadata_agent = MetadataRecommenderAgent(FakeKeywordExtractor())
    metadata_agent.model = types.SimpleNamespace(
        models=types.SimpleNamespace(
            generate_content=lambda *args, **kwargs: types.SimpleNamespace(text="One, Two, Three")
        )
    )
    metadata_result = metadata_agent.run(
        "# Demo\n\nPython AI assistant with FastAPI.",
        {"app.py": "import fastapi", "notes": 7, "empty.txt": ""},
    )
    assert metadata_result.title_suggestions[0]
    metadata_agent.model = types.SimpleNamespace(
        models=types.SimpleNamespace(
            generate_content=lambda *args, **kwargs: types.SimpleNamespace(text="x" * 300)
        )
    )
    assert metadata_agent._generate_description("# Demo", ["ai", "workflow"]).endswith("...")

    reviewer_agent = reviewer_mod.ReviewerCriticAgent()
    review = reviewer_agent.run("# Installation\n\n## Usage\n\n## License\n\n## Contributing\n\n## Architecture\n", {"total_lines": 40, "entrypoints": ["main.py"]})
    assert review.score >= 0
    review_empty = reviewer_agent.run("short", {"total_lines": 5, "entrypoints": []})
    assert review_empty.issues

    class FailingGraph:
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
                last_result = {"repo_analysis": None}

                def invoke(self, inputs):
                    raise RuntimeError("boom")

            self.compiled = Compiled()
            return self.compiled

    monkeypatch.setattr(graph_mod, "StateGraph", FailingGraph)
    orchestrator = Orchestrator()
    result = orchestrator.run_pipeline({"repo_analyzer": object()}, "repo")
    assert result["publication_readme"].startswith("#")

    assert backoff_mod.exponential_backoff(0, base=1.0, jitter=True) == 1.0
    assert backoff_mod.calculate_jitter(-1.0) == 0.0
    assert backoff_mod.capped_exponential_backoff_factory(base=1.0, multiplier=2.0, max_delay=4.0)(1) == 1.0
    assert asyncio.run(backoff_mod.sleep_backoff(1, base=0.0, factor=2.0, max_delay=0.0)) is None
    monkeypatch.setattr(backoff_mod.time, "sleep", lambda *_args, **_kwargs: None)
    backoff_mod.sync_backoff_sleep(2, base=0.0, factor=2.0, max_delay=0.0)

    class FailingLogger:
        def warning(self, *args, **kwargs):
            raise RuntimeError("boom")

        def info(self, *args, **kwargs):
            raise RuntimeError("boom")

        def error(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(retry_mod, "logger", FailingLogger())
    with pytest.raises(ValueError):
        RetryManager(max_retries=1, backoff_base=0.0).execute(lambda: (_ for _ in ()).throw(ValueError("boom")))

    @retry_mod.retry_async(max_attempts=2, base_delay=0.0, factor=2.0, max_delay=0.0)
    async def always_fails():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        asyncio.run(always_fails())

    async def delayed_coro():
        await asyncio.sleep(0.01)
        return 2

    with pytest.raises(RuntimeError):
        asyncio.run(timeout_mod.run_with_timeout(delayed_coro(), timeout=0.001, fallback=lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
    assert asyncio.run(timeout_mod.TimeoutManager(timeout_seconds=None).run(delayed_coro(), timeout=0)) == 2

    assert config_mod._env_list("MISSING", ["a", "b"]) == ["a", "b"]
    assert file_validators_mod.validate_mime_type(b"x", "file.pdf") == (True, "ok")
    assert file_validators_mod.validate_upload(b"x", "file.pdf", "application/zip") == (False, "mime_type_not_allowed")
    assert input_validators_mod.validate_prompt("   ")[0] is False

    real_import = builtins.__import__

    def import_fail(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {"google", "google.genai", "chromadb"}:
            raise ImportError(name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_fail)
    sys.modules.pop("tools.keyword_extractor", None)
    sys.modules.pop("tools.rag_retriever", None)
    sys.modules.pop("tools.web_search", None)
    keyword_imported = importlib.import_module("tools.keyword_extractor")
    rag_imported = importlib.import_module("tools.rag_retriever")
    web_imported = importlib.import_module("tools.web_search")
    assert keyword_imported.KeywordExtractor().extract("ai python") == ["python", "ai"]
    assert rag_imported.RAGRetriever(db_path="./missing").retrieve("hello") == []
    assert web_imported.WebSearchTool(selected_model="m", provider="google").summarize_and_improve("# Title", [], style="s", goal="g")

    monkeypatch.setattr(arxiv_mod, "_HAS_ARXIV", True)
    monkeypatch.setattr(arxiv_mod, "arxiv", types.SimpleNamespace(SortCriterion=types.SimpleNamespace(Relevance="relevance"), Search=lambda **kwargs: object()))
    tool = ArxivScholarTool()
    tool.client = types.SimpleNamespace(results=lambda search: (_ for _ in ()).throw(RuntimeError("boom")))
    assert tool.search("hello") == []

    monkeypatch.setattr(keyword_mod, "genai", types.SimpleNamespace(Client=lambda api_key: (_ for _ in ()).throw(RuntimeError("boom"))))
    extractor = KeywordExtractor(top_k=3)
    assert extractor.extract("Python AI project")

    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    monkeypatch.setattr(list_models_mod, "genai", types.SimpleNamespace(Client=lambda api_key: types.SimpleNamespace(models=types.SimpleNamespace(list=lambda: [types.SimpleNamespace(name="gemini-test")]))))
    monkeypatch.setattr(list_models_mod, "Groq", lambda api_key: types.SimpleNamespace(models=types.SimpleNamespace(list=lambda: [types.SimpleNamespace(id="groq-test")])) )
    list_gemini_models()
    list_groq_models()

    class WebSearchClient:
        class Models:
            def generate_content(self, *args, **kwargs):
                return types.SimpleNamespace(text=None)

        models = Models()

    class GroqFallbackClient:
        class Chat:
            class Completions:
                def create(self, model, messages):
                    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="groq output"))])

            completions = Completions()

        chat = Chat()

    tool = WebSearchTool(selected_model="x", provider="google")
    tool.gemini_client = WebSearchClient()
    tool.groq_client = GroqFallbackClient()
    tool.active_client = tool.gemini_client
    assert "empty response" in tool.summarize_and_improve("# Title", [], style="s", goal="g").lower()

    tool = WebSearchTool(selected_model="x", provider="groq")
    tool.gemini_client = None
    tool.groq_client = GroqFallbackClient()
    tool.active_client = tool.groq_client
    assert "groq output" in tool.summarize_and_improve("# Title", [], style="s", goal="g")

    class SearchStringStub:
        def invoke(self, query):
            return "not-a-list"

    tool = WebSearchTool(selected_model="x", provider="google")
    tool.search = SearchStringStub()
    assert tool.search_similar_repos("query") == []

    class SearchListStub:
        def invoke(self, query):
            return [{"title": "t", "url": "u", "content": "c"}]

    tool.search = SearchListStub()
    assert tool.search_similar_repos("query")[0]["title"] == "t"

    builder = PublicationBuilder()
    assert builder._header("Title", "Desc", ["x"], {"Files": "1"})
    assert builder._hero_section("Desc", "Technical Blog", "Goal", {"endpoints": ["/health"], "deployment": ["Dockerfile"], "workflows": [".github/workflows/ci.yml"]})
    assert builder._demo_section(["assets/demo.png"])
    assert builder._table_of_contents()
    assert builder._slugify_id("Hello World") == "hello-world"
    assert builder._post_process_markdown("## Summary\n\n[TOC]\n\n```flowchart\nA-->B\n```\n\n![demo](assets/demo.png)")
    assert builder._features_section(["ai"], ["Usage"])
    assert builder._executive_summary_section("Desc", {"endpoints": ["/health"]}, ["Usage"])
    assert builder._publication_score_section()
    assert builder._improved_project_names_section("Demo", ["ai"])
    assert builder._better_repository_description_section("Demo", "Desc", ["ai"])
    assert builder._seo_optimization_section(["ai"])
    assert builder._readme_rewrite_section("Demo", "Desc", ["ai"], {"endpoints": ["/health"]}, ["--repo-path"], ["GOOGLE_API_KEY"])
    assert builder._mermaid_diagrams_section()
    assert builder._repository_tree_section("repository/\n├── README.md")
    assert builder._visual_enhancement_suggestions_section(["assets/demo.png"])
    assert builder._image_recommendations_section("Demo")
    assert builder._architecture_explanation_section()
    assert builder._agent_collaboration_section()
    assert builder._tool_usage_section()
    assert builder._readme_review_section(["Usage"])
    assert builder._github_best_practices_section()
    assert builder._technical_writing_improvements_section()
    assert builder._publication_readiness_report_section()
    assert builder._architecture_section()
    assert builder._project_structure_section("repo/")
    assert builder._tech_stack_section([("Python", "Core")])
    assert builder._installation_section()
    assert builder._configuration_section(["GOOGLE_API_KEY"])
    assert builder._usage_section(["--serve-ui", "--host", "--port"])
    assert builder._api_section(["/health"])
    assert builder._workflow_section()
    assert builder._tool_section()
    assert builder._rag_section()
    assert builder._langgraph_section()
    assert builder._security_section()
    assert builder._performance_section()
    assert builder._testing_section({"total_lines": 3})
    assert builder._deployment_section()
    assert builder._monitoring_section()
    assert builder._cicd_section()
    assert builder._roadmap_section()
    assert builder._contributing_section()
    assert builder._faq_section("# Demo")
    assert builder._troubleshooting_section(["Usage"])
    assert builder._license_section()
    assert builder._citation_section()
    assert builder._acknowledgements_section()
