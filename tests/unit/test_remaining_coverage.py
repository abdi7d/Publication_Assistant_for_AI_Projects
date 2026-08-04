from agents.content_improver import ContentImproverAgent
from agents.fact_checker import FactCheckerAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from orchestration.graph import Orchestrator
from utils.publication_builder import PublicationBuilder
from tools.web_search import WebSearchTool
from tools.rag_retriever import RAGRetriever


def test_content_improver_handles_web_search_none_and_rag_none():
    agent = ContentImproverAgent(web_search=None, rag=None)
    result = agent.run("# Demo\n\nA simple project.", metadata={"tags": ["ai"]})
    assert "Installation" in result.improved_readme
    assert result.suggested_images["architecture_diagram"]


def test_content_improver_extracts_title_and_summary_from_readme():
    agent = ContentImproverAgent(web_search=None, rag=None)
    result = agent.run("# Custom Project\n\nAn overview paragraph.", metadata={"tags": []})
    assert "Custom Project" in result.improved_readme


def test_fact_checker_handles_scholar_exception():
    class ExplodingScholar:
        def search(self, query, max_results=1):
            raise RuntimeError("boom")

    agent = FactCheckerAgent(scholar_tool=ExplodingScholar())
    result = agent.run("This project proposes a novel and advanced approach.")
    assert result.flagged


def test_metadata_recommender_uses_fallback_when_model_generation_fails(monkeypatch):
    class FakeModel:
        def __init__(self):
            self.models = type("Models", (), {"generate_content": lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))})()

    class FakeGenai:
        @staticmethod
        def Client(*args, **kwargs):
            return FakeModel()

    import agents.metadata_recommender as mod
    monkeypatch.setattr(mod, "genai", FakeGenai)
    agent = MetadataRecommenderAgent(keyword_extractor=type("K", (), {"extract": lambda self, text: ["ai"]})())
    rec = agent.run("A project about AI", {"app.py": "import fastapi"})
    assert rec.title_suggestions
    assert rec.short_description


def test_orchestrator_builds_publication_readme_with_stubbed_agents(monkeypatch):
    class StubRepoAnalysis:
        readme = "# Demo"
        files = {"app.py": "print('hi')"}
        code_stats = {"python": 1}

    class StubAgent:
        def run(self, *args, **kwargs):
            return None

    class StubMetadata:
        title_suggestions = ["Demo"]
        tags = ["ai"]
        short_description = "Short"

    class StubContent:
        improved_readme = "# Demo\n\nA polished README"
        suggested_images = {}

    class StubReview:
        score = 5.0
        issues = []
        strengths = []
        recommendations = []

    class StubFactCheck:
        claims_found = []
        verified = []
        flagged = []

    class FakeGraph:
        def __init__(self, *args, **kwargs):
            pass

        def add_node(self, *args, **kwargs):
            return None

        def set_entry_point(self, *args, **kwargs):
            return None

        def add_edge(self, *args, **kwargs):
            return None

        def compile(self):
            class Compiled:
                def invoke(self, inputs):
                    return {
                        "repo_analysis": StubRepoAnalysis(),
                        "metadata": StubMetadata(),
                        "content_improvement": StubContent(),
                        "review": StubReview(),
                        "fact_check": StubFactCheck(),
                    }
            return Compiled()

    monkeypatch.setattr("orchestration.graph.StateGraph", FakeGraph)
    orchestrator = Orchestrator()
    result = orchestrator.run_pipeline(
        {
            "repo_analyzer": type("A", (), {"run": lambda self: StubRepoAnalysis()})(),
            "metadata_recommender": type("B", (), {"run": lambda self, *args, **kwargs: StubMetadata()})(),
            "content_improver": type("C", (), {"run": lambda self, *args, **kwargs: StubContent()})(),
            "reviewer_critic": type("D", (), {"run": lambda self, *args, **kwargs: StubReview()})(),
            "fact_checker": type("E", (), {"run": lambda self, *args, **kwargs: StubFactCheck()})(),
        },
        "https://example.com/repo",
    )
    assert "publication_readme" in result


def test_publication_builder_post_process_handles_plain_graph_and_heading_ids():
    builder = PublicationBuilder()
    md = "## Table of Contents\n\n[TOC]\n\n```graph\nflow\n```"
    processed = builder._post_process_markdown(md)
    assert "```mermaid" in processed
    assert "#" in processed
