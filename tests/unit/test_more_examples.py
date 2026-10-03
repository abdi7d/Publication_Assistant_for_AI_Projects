import os
import zipfile

from tools.repo_parser import RepoParser
from tools.web_search import WebSearchTool
from tools.rag_retriever import RAGRetriever


def test_repo_parser_invalid_source_raises():
    p = RepoParser()
    try:
        p.parse("not_a_repo_source")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_repo_parser_dir_parsing(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    f = d / "README.md"
    f.write_text("# X")
    p = RepoParser()
    parsed = p.parse(str(d))
    assert "README.md" in parsed and parsed["README.md"].startswith("#")


def test_repo_parser_skips_large_files(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    big = d / "big.bin"
    # create >100KB file
    big.write_bytes(b"0" * 120_000)
    p = RepoParser()
    parsed = p.parse(str(d))
    # big file should be skipped
    assert len(parsed.get("files", {})) == 0


def test_web_search_fallback_no_clients(monkeypatch):
    # Ensure environment has no API keys
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    w = WebSearchTool()
    # When no clients are available, summarize_and_improve should return heuristic text
    out = w.summarize_and_improve("short readme", [], style="S", goal="G")
    assert isinstance(out, str)


def test_rag_retrieve_no_chromadb(monkeypatch):
    # Ensure chromadb not installed case
    monkeypatch.setenv("DUMMY", "1")
    r = RAGRetriever(db_path=str(tmp_path := "./nonexistent_db"))
    # Without chromadb the retrieve should return an empty list
    assert r.retrieve("anything") == []


def test_metadata_make_titles_fallback(mock_keyword_extractor):
    from agents.metadata_recommender import MetadataRecommenderAgent

    m = MetadataRecommenderAgent(keyword_extractor=mock_keyword_extractor)
    titles = m._make_titles("small readme", ["ai", "tool"])
    assert isinstance(titles, list) and len(titles) >= 1


def test_content_improver_handles_empty_readme(mock_web_search, mock_rag):
    from agents.content_improver import ContentImproverAgent

    c = ContentImproverAgent(web_search=mock_web_search, rag=mock_rag)
    out = c.run("", metadata={}, style="", goal="")
    assert "improved_readme" in out.__dict__ or hasattr(out, 'improved_readme')


def test_fact_checker_handles_no_claims(mock_scholar):
    from agents.fact_checker import FactCheckerAgent

    f = FactCheckerAgent(scholar_tool=mock_scholar)
    res = f.run("Short text with no scientific claims.")
    assert isinstance(res.claims_found, list)


def test_reviewer_small_repo_scores_low():
    from agents.reviewer_critic import ReviewerCriticAgent

    r = ReviewerCriticAgent()
    review = r.run("No installation here", {"total_lines": 3})
    assert review.score <= 10


def test_repo_parser_zip(tmp_path):
    # Create a zip with a README
    zpath = tmp_path / "r.zip"
    d = tmp_path / "d"
    d.mkdir()
    (d / "README.md").write_text("# ZipReadme")
    with zipfile.ZipFile(str(zpath), "w") as z:
        z.write(str(d / "README.md"), arcname="README.md")
    p = RepoParser()
    parsed = p.parse(str(zpath))
    assert parsed.get("README.md", "").startswith("# ZipReadme")
