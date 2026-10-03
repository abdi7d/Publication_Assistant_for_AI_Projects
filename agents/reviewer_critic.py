# agents/reviewer_critic.py
from dataclasses import dataclass
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class Review:
    score: float
    issues: List[str]
    strengths: List[str]
    recommendations: List[str]


class ReviewerCriticAgent:
    """
    Performs heuristic-based review of the README and repo content.
    """

    def __init__(self) -> None:
        pass

    def run(self, readme: str, code_stats: Dict[str, Any]) -> Review:
        logger.info("ReviewerCriticAgent: reviewing repository artifacts")
        issues: List[str] = []
        strengths: List[str] = []
        recommendations: List[str] = []

        lowered = readme.lower()
        headings = [match.group(1).strip().lower()
                    for match in re.finditer(r"^#+\s+(.+)$", readme, re.M)]
        heading_set = set(headings)

        if not any(keyword in heading_set for keyword in ["installation", "getting started", "quick start", "setup"]):
            issues.append("Missing 'Installation' section.")
            recommendations.append(
                "Add installation instructions with copy-paste commands.")

        if not any(keyword in heading_set for keyword in ["usage", "how to use", "quick start", "run"]):
            issues.append("Missing 'Usage' guidance.")
            recommendations.append(
                "Add a concise usage example for new users.")

        if not any(keyword in heading_set for keyword in ["license", "licensing"]):
            issues.append("Missing 'License' or licensing section.")
            recommendations.append(
                "Add a license summary and attribution section.")

        if not any(keyword in heading_set for keyword in ["contributing", "contribute", "community"]):
            issues.append("Missing 'Contributing' guidance.")
            recommendations.append(
                "Add contribution guidelines and issue/PR expectations.")

        if not any(keyword in heading_set for keyword in ["architecture", "design", "system overview"]):
            issues.append("Missing architecture or system overview.")
            recommendations.append(
                "Add an architecture summary or diagram for maintainers.")

        if len(readme.strip()) < 300:
            issues.append(
                "README is still quite brief; expand it with overview, setup, and examples.")
            recommendations.append(
                "Add a clearer project overview and contribution guidance.")

        if code_stats.get("total_lines", 0) < 20:
            issues.append(
                "Repository appears small; include examples and test instructions.")
            recommendations.append(
                "Add an example workflow or screenshot to improve onboarding.")

        if heading_set:
            strengths.append("README has an organized heading structure.")
            if any(keyword in heading_set for keyword in ["installation", "setup"]):
                strengths.append("Installation guidance is present.")
            if any(keyword in heading_set for keyword in ["usage", "how to use"]):
                strengths.append("Usage or quick start guidance is present.")
            if any(keyword in heading_set for keyword in ["license", "licensing"]):
                strengths.append("License information is included.")
            if any(keyword in heading_set for keyword in ["architecture", "design"]):
                strengths.append("Architecture or design context is present.")
        else:
            strengths.append(
                "Repository content is available for documentation synthesis.")

        if code_stats.get("entrypoints"):
            strengths.append("Repository includes runnable entrypoint(s).")

        score = max(0.0, 10.0 - len(issues) * 1.2)
        return Review(score=score, issues=issues, strengths=strengths, recommendations=recommendations)
