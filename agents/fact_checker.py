# agents/fact_checker.py
from dataclasses import dataclass
from typing import List
import logging
import re

from tools.arxiv_scholar import ArxivScholarTool

logger = logging.getLogger(__name__)


@dataclass
class FactCheckResult:
    claims_found: List[str]
    verified: List[str]
    flagged: List[str]


class FactCheckerAgent:
    """
    Extracts plausible technical claims from README content and verifies them when a scholar tool is available.
    """

    def __init__(self, scholar_tool: ArxivScholarTool):
        self.scholar = scholar_tool

    def run(self, readme_text: str) -> FactCheckResult:
        logger.info("FactCheckerAgent: extracting claims")
        claims = self._extract_claims(readme_text)
        verified: List[str] = []
        flagged: List[str] = []

        for claim in claims[:3]:
            logger.info("Verifying claim: %s", claim[:80])
            if self.scholar is None:
                flagged.append(
                    f"{claim} (Verification unavailable - no scholar tool configured)")
                continue
            try:
                hits = self.scholar.search(claim, max_results=1)
            except Exception:
                flagged.append(
                    f"{claim} (Verification failed due to an external error)")
                continue
            if hits:
                verified.append(f"{claim} (Found paper: {hits[0]['title']})")
            else:
                flagged.append(f"{claim} (No direct match found)")

        return FactCheckResult(claims_found=claims, verified=verified, flagged=flagged)

    def _extract_claims(self, readme_text: str) -> List[str]:
        if not readme_text:
            return []
        sentences = re.split(r"(?<=[.!?])\s+", readme_text)
        claims = []
        patterns = [
            r"\b(novel|state-of-the-art|outperforms|significant|proposed|benchmark|advanced|research|groundbreaking|innovative|powerful)\b",
            r"\b(this project|this system|it can|powered by|built on|designed for|provides|supports|enables)\b",
        ]
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) <= 30:
                continue
            lowered = cleaned.lower()
            if any(re.search(pattern, lowered) for pattern in patterns):
                claims.append(cleaned)
        # Keep unique claims while preserving order
        unique_claims = []
        seen = set()
        for claim in claims:
            if claim not in seen:
                seen.add(claim)
                unique_claims.append(claim)
        return unique_claims
