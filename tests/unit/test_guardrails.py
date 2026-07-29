from app import validate_submission
from orchestration.graph import Orchestrator


def test_validate_submission_rejects_blank_repo():
    ok, message = validate_submission("   ", "Write about this project", "A demo repo")
    assert not ok
    assert "Repository URL" in message


def test_validate_submission_accepts_safe_inputs():
    ok, message = validate_submission(
        "https://github.com/example/project",
        "Write a concise summary",
        "A sample project for testing",
    )
    assert ok
    assert message == ""


def test_orchestrator_returns_fallbacks_when_stage_fails():
    class FailingAgent:
        def run(self, *args, **kwargs):
            raise RuntimeError("boom")

    class StubRepoAnalysis:
        readme = "# Demo"
        files = {}
        code_stats = {}

    agents = {
        "repo_analyzer": type("A", (), {"run": lambda self: StubRepoAnalysis()})(),
        "metadata_recommender": FailingAgent(),
        "content_improver": FailingAgent(),
        "reviewer_critic": FailingAgent(),
        "fact_checker": FailingAgent(),
    }

    result = Orchestrator().run_pipeline(agents, "https://example.com/repo")
    assert result["analysis"] is not None
    assert result["metadata"] is not None
    assert result["review"] is not None
    assert result["fact_check"] is not None
