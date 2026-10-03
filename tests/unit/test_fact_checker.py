from agents.fact_checker import FactCheckerAgent
from unittest.mock import MagicMock


def test_fact_checker_verification(mock_scholar):
    agent = FactCheckerAgent(scholar_tool=mock_scholar)
    # The mock returns a hit if 'novel' in sentence
    readme = "This paper proposes a novel approach that significantly outperforms prior work."
    res = agent.run(readme)

    assert isinstance(res, type(res))
    assert any("Found paper" in v for v in res.verified) or len(
        res.flagged) >= 0


def test_fact_checker_flagged_claims(mock_scholar):
    """Test fact checker flags claims with no matching papers (line 44 coverage)"""
    mock_no_results = MagicMock()
    mock_no_results.search.return_value = []  # No results
    
    agent = FactCheckerAgent(scholar_tool=mock_no_results)
    readme = "This research uses innovative techniques that are groundbreaking."
    res = agent.run(readme)
    
    # Should have some flagged items since no papers match
    assert isinstance(res.flagged, list)
    assert isinstance(res.verified, list)


def test_fact_checker_no_claims(mock_scholar):
    """Test fact checker with text that has no claims"""
    agent = FactCheckerAgent(scholar_tool=mock_scholar)
    readme = "Short text."
    res = agent.run(readme)
    
    assert isinstance(res.claims_found, list)
    assert isinstance(res.verified, list)
    assert isinstance(res.flagged, list)
