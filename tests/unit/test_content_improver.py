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
