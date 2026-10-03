import importlib


def test_generate_full_article_end_to_end(monkeypatch, tmp_path):
    # Import app and monkeypatch heavy tools to deterministic mocks
    import app
    importlib.reload(app)

    # Monkeypatch RepoParser.parse to return a simple repo
    class P:
        def parse(self, src):
            return {"files": {"README.md": "# X\n\nA sample."}, "README.md": "# X\n\nA sample."}

    monkeypatch.setattr(app, "RepoParser", P)

    class W:
        def __init__(self, *a, **k):
            pass

        def search_similar_repos(self, *_a, **_k):
            return [{"title": "Example", "snippet": "s"}]

        def summarize_and_improve(self, readme, examples, style="", goal=""):
            return "# Title\n\nImproved body."

    monkeypatch.setattr(app, "WebSearchTool", W)

    class R:
        def __init__(self, *a, **k):
            pass

        def retrieve(self, text):
            return ["Add Usage"]

    monkeypatch.setattr(app, "RAGRetriever", R)

    # Run the generation function
    title, sub, tags, body = app.generate_full_article(
        "/tmp/x", style="Technical Blog", length="Medium", model="heuristic", goal="", project_desc="desc", provider=None)

    assert isinstance(title, str) and title.startswith("#")
    assert "Improved body" in body or "No improvements generated." in body
