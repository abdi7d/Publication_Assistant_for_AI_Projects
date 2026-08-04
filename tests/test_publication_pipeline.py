import os
from types import SimpleNamespace

from app import clean_generated_content
from orchestration.graph import Orchestrator
from utils.publication_builder import PublicationBuilder


def test_clean_generated_content_preserves_mermaid_fences():
    content = "## Demo\n\n```mermaid\nflowchart TD\nA --> B\n```\n\n**Bold**"

    cleaned = clean_generated_content(content)

    assert "```mermaid" in cleaned
    assert "flowchart TD" in cleaned
    assert "**Bold**" in cleaned


def test_clean_generated_content_preserves_structured_markdown():
    content = "## Overview\n\n> Note\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n\n### Details"

    cleaned = clean_generated_content(content)

    assert "## Overview" in cleaned
    assert "> Note" in cleaned
    assert "| A | B |" in cleaned
    assert "### Details" in cleaned


def test_publication_builder_generates_rich_markdown():
    builder = PublicationBuilder()
    repo_analysis = SimpleNamespace(
        files={"README.md": "# Demo Project\n\nA sample AI project.",
               "requirements.txt": "fastapi\ngradio\nlanggraph"},
        readme="# Demo Project\n\nA sample AI project.",
        summary="A sample AI project.",
        code_stats={"file_count": 5, "languages": {
            "py": 3}, "total_lines": 120},
        missing_sections=["Installation", "Usage"],
    )
    metadata = SimpleNamespace(
        title_suggestions=["Demo Project"],
        tags=["ai", "agents", "fastapi"],
        short_description="A sample AI project for publication workflows.",
    )

    readme = builder.build_readme(
        repo_analysis=repo_analysis,
        metadata=metadata,
        repo_source="/tmp/demo-repo",
        style="Technical Blog",
        goal="Generate polished docs",
    )

    assert "## Table of Contents" in readme
    assert "## Features" in readme
    assert "## Architecture" in readme
    assert "```mermaid" in readme
    assert "<details>" in readme
    assert "## Installation" in readme


def test_publication_builder_includes_publication_package_sections():
    builder = PublicationBuilder()
    repo_analysis = SimpleNamespace(
        files={
            "README.md": "# Demo Repo\n\nThis is a demo repository.",
            "app.py": '@app.get("/health")\n\ndef health():\n    return {"status": "ok"}\n',
            "Dockerfile": "FROM python:3.11-slim\n",
            "requirements.txt": "fastapi\nlanggraph\n",
        },
        readme="# Demo Repo\n\nThis is a demo repository.",
        summary="Demo repository",
        code_stats={"file_count": 4, "languages": {
            "py": 2}, "total_lines": 80},
        missing_sections=["Installation"],
    )
    metadata = SimpleNamespace(
        title_suggestions=["Demo Repo"],
        tags=["demo", "python"],
        short_description="A demo repository.",
    )

    readme = builder.build_readme(
        repo_analysis=repo_analysis,
        metadata=metadata,
        repo_source="/tmp/demo-repo",
        style="Technical Blog",
        goal="Generate polished docs",
    )

    assert "## Executive Summary" in readme
    assert "## Publication Score" in readme
    assert "## SEO Optimization" in readme
    assert "## Visual Enhancement Suggestions" in readme
    assert "## Publication Readiness Report" in readme


def test_publication_builder_uses_repository_evidence():
    builder = PublicationBuilder()
    repo_analysis = SimpleNamespace(
        files={
            "README.md": "# Demo Repo\n\nThis is a demo repository.",
            "app.py": '@app.get("/health")\n\ndef health():\n    return {"status": "ok"}\n',
            "Dockerfile": "FROM python:3.11-slim\n",
            "requirements.txt": "fastapi\nlanggraph\n",
        },
        readme="# Demo Repo\n\nThis is a demo repository.",
        summary="Demo repository",
        code_stats={"file_count": 4, "languages": {
            "py": 2}, "total_lines": 80},
        missing_sections=["Installation"],
    )
    metadata = SimpleNamespace(
        title_suggestions=["Demo Repo"],
        tags=["demo", "python"],
        short_description="A demo repository.",
    )

    readme = builder.build_readme(
        repo_analysis=repo_analysis,
        metadata=metadata,
        repo_source="/tmp/demo-repo",
        style="Technical Blog",
        goal="Generate polished docs",
    )

    assert "/health" in readme
    assert "Docker" in readme
    assert "FastAPI" in readme


def test_orchestrator_returns_publication_readme_with_stub_agents(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Demo Repo\n\nThis is a demo repository.", encoding="utf-8")
    (repo_root / "requirements.txt").write_text("fastapi\nlanggraph\n", encoding="utf-8")

    class StubRepoAnalyzer:
        def run(self):
            return SimpleNamespace(
                files={"README.md": "# Demo Repo\n\nThis is a demo repository."},
                readme="# Demo Repo\n\nThis is a demo repository.",
                summary="Demo repository",
                code_stats={"file_count": 2, "languages": {
                    "py": 1}, "total_lines": 40},
                missing_sections=["Installation"],
            )

    class StubMetadata:
        def run(self, readme_text, code_files):
            return SimpleNamespace(
                title_suggestions=["Demo Repo"],
                tags=["demo", "python"],
                short_description="A demo repository.",
            )

    class StubContent:
        def run(self, readme, metadata, style="Technical Blog", goal=""):
            return SimpleNamespace(improved_readme=readme, suggested_images={})

    class StubReview:
        def run(self, readme, code_stats):
            return SimpleNamespace(score=9.0, issues=[], strengths=["Good"], recommendations=[])

    class StubFactCheck:
        def run(self, readme):
            return SimpleNamespace(claims_found=[], verified=[], flagged=[])

    orchestrator = Orchestrator()
    agents = {
        "repo_analyzer": StubRepoAnalyzer(),
        "metadata_recommender": StubMetadata(),
        "content_improver": StubContent(),
        "reviewer_critic": StubReview(),
        "fact_checker": StubFactCheck(),
    }

    result = orchestrator.run_pipeline(agents, str(repo_root))

    assert "publication_readme" in result
    assert "## Features" in result["publication_readme"]
    assert "```mermaid" in result["publication_readme"]
