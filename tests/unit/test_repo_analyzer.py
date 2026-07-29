import pytest

from agents.repo_analyzer import RepoAnalyzerAgent, RepoAnalysis


class DummyParser:
    def __init__(self, payload):
        self._payload = payload

    def parse(self, repo_source: str):
        # ignore repo_source, return provided payload
        return self._payload


def test_repo_analyzer_basic(tmp_path):
    files = {
        "README.md": "# Title\n\nUsage: python main.py\n\nInstallation: pip install -r requirements.txt",
        "src/app.py": "print('hello')",
        "notebook.ipynb": "{}",
    }
    parsed = {"files": files,
              "README.md": files["README.md"], "title": "Sample"}
    parser = DummyParser(parsed)

    agent = RepoAnalyzerAgent(repo_source=str(tmp_path), repo_parser=parser)
    analysis = agent.run()

    assert isinstance(analysis, RepoAnalysis)
    assert analysis.readme.startswith("# Title")
    assert analysis.code_stats["file_count"] == len(files)
    # Ensure known sections are detected (Installation present)
    assert "installation" not in [m.lower() for m in analysis.missing_sections]


def test_repo_analyzer_missing_sections():
    files = {"README": "A project without sections"}
    parsed = {"files": files,
              "README.md": "A project without sections", "title": "T"}
    parser = DummyParser(parsed)
    agent = RepoAnalyzerAgent(repo_source="/tmp/x", repo_parser=parser)
    analysis = agent.run()
    # Installation should be missing
    assert "Installation" in analysis.missing_sections or any(
        "installation" in s.lower() for s in analysis.missing_sections)
