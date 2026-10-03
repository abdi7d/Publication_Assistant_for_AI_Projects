from agents.content_improver import ContentImproverAgent


def test_content_improver_basic(mock_web_search, mock_rag):
    agent = ContentImproverAgent(web_search=mock_web_search, rag=mock_rag)
    readme = "# Title\n\nA brief description of the project."
    metadata = {"tags": ["ai"]}
    out = agent.run(readme=readme, metadata=metadata,
                    style="Technical Blog", goal="Improve clarity")

    assert hasattr(out, "improved_readme")
    assert "Improved content" in out.improved_readme
    assert isinstance(out.suggested_images, dict)


def test_content_improver_falls_back_when_llm_errors(mock_rag):
    class FailingWebSearch:
        def search_similar_repos(self, query, top_k=3):
            return []

        def summarize_and_improve(self, readme, examples, style="Technical Blog", goal=""):
            return "Error: AI generated an empty response."

    agent = ContentImproverAgent(web_search=FailingWebSearch(), rag=mock_rag)
    out = agent.run(readme="# Title\n\nA short project description.", metadata={
                    "tags": ["python"]})

    assert "Error:" not in out.improved_readme
    assert "Installation" in out.improved_readme or "Usage" in out.improved_readme
