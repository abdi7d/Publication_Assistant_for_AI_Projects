import app


def test_validate_repo_logic_empty():
    msg, tree = app.validate_repo_logic("")
    assert "Please enter a repository URL" in msg or msg.startswith("⚠️")


def test_generate_full_article_missing_repo():
    title, sub, tags, body = app.generate_full_article(
        "", style="S", length="M", model="heuristic", goal="", project_desc="")
    assert title == "Error" or body.startswith(
        "Pipeline failed") or "Please provide a URL" in body


def test_validate_repo_logic_fallback(monkeypatch, tmp_path):
    # Force RepoParser.parse to raise to trigger fallback branch in validate_repo_logic
    class P:
        def parse(self, src):
            raise RuntimeError("clone failed")

    monkeypatch.setattr(app, "RepoParser", P)
    msg, tree = app.validate_repo_logic("http://example.com/nonexistent")
    assert msg and isinstance(tree, str)


def test_generate_full_article_with_saved_project(monkeypatch, tmp_path):
    # Monkeypatch tools to be deterministic similar to earlier E2E
    class P:
        def parse(self, src):
            return {"files": {"README.md": "# X\n\nA sample."}, "README.md": "# X\n\nA sample."}

    monkeypatch.setattr(app, "RepoParser", P)

    class W:
        def __init__(self, *a, **k):
            pass

        def search_similar_repos(self, *_a, **_k):
            return []

        def summarize_and_improve(self, readme, examples, style="", goal=""):
            return "# Title\n\nImproved body."

    monkeypatch.setattr(app, "WebSearchTool", W)
    title, sub, tags, body = app.generate_full_article(
        "/tmp/x", style="Technical Blog", length="Medium", model="heuristic", goal="", project_desc="desc")
    assert isinstance(title, str)
