from agents.reviewer_critic import ReviewerCriticAgent


def test_reviewer_detects_missing_installation():
    agent = ReviewerCriticAgent()
    readme = "# Sample\n\nNo installation provided here."
    code_stats = {"total_lines": 5}
    review = agent.run(readme, code_stats)

    assert review.score <= 10.0
    assert any("Missing" in i or "installation" in i.lower()
               for i in review.issues)
