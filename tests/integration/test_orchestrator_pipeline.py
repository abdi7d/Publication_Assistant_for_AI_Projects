import importlib


def test_orchestrator_pipeline(fake_langgraph, mock_repo_parser, mock_keyword_extractor, mock_web_search, mock_rag, mock_scholar):
    # Import orchestrator after fake langgraph is injected
    import orchestration.graph as graph_mod

    importlib.reload(graph_mod)
    Orchestrator = graph_mod.Orchestrator

    # Build agents using lightweight mocks
    from agents.repo_analyzer import RepoAnalyzerAgent
    from agents.metadata_recommender import MetadataRecommenderAgent
    from agents.content_improver import ContentImproverAgent
    from agents.reviewer_critic import ReviewerCriticAgent
    from agents.fact_checker import FactCheckerAgent

    repo_parser = mock_repo_parser
    repo_analyzer = RepoAnalyzerAgent(
        repo_source="/tmp/x", repo_parser=repo_parser)
    metadata_recommender = MetadataRecommenderAgent(
        keyword_extractor=mock_keyword_extractor)
    content_improver = ContentImproverAgent(
        web_search=mock_web_search, rag=mock_rag)
    reviewer = ReviewerCriticAgent()
    fact_checker = FactCheckerAgent(scholar_tool=mock_scholar)

    agents = {
        "repo_analyzer": repo_analyzer,
        "metadata_recommender": metadata_recommender,
        "content_improver": content_improver,
        "reviewer_critic": reviewer,
        "fact_checker": fact_checker,
    }

    orch = Orchestrator()
    res = orch.run_pipeline(agents=agents, repo_source="/tmp/x")

    assert "analysis" in res and res["analysis"] is not None
    assert "metadata" in res
    assert "review" in res
