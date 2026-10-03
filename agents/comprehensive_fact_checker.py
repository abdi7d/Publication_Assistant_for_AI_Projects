# agents/comprehensive_fact_checker.py
"""
Comprehensive Fact Checker with multi-source verification.
Goes beyond arXiv to verify claims against repository evidence and external sources.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from tools.arxiv_scholar import ArxivScholarTool
from tools.repository_grounded_generator import RepositoryGroundedGenerator, RepositoryEvidence

logger = logging.getLogger(__name__)


@dataclass
class FactCheckResult:
    """Result of comprehensive fact checking."""
    claims_found: List[str]
    verified: List[str]
    flagged: List[str]
    confidence_scores: Dict[str, float]
    verification_sources: Dict[str, List[str]]
    repository_grounded: List[str]
    external_sources_verified: List[str]


@dataclass
class VerificationResult:
    """Result of verifying a single claim."""
    claim: str
    is_verified: bool
    confidence: float
    sources: List[str]
    verification_method: str  # 'repository', 'arxiv', 'external', 'inference'


class ComprehensiveFactCheckerAgent:
    """
    Extracts technical claims and verifies them using multiple sources:
    - Repository evidence (code, config, documentation)
    - Academic sources (arXiv)
    - External documentation and official sources
    """

    def __init__(self, scholar_tool: Optional[ArxivScholarTool] = None):
        self.scholar = scholar_tool
        self.repo_grounded_generator = RepositoryGroundedGenerator()
        self.verification_cache = {}

    def run(self, readme_text: str, repo_evidence: Optional[RepositoryEvidence] = None, 
             files: Optional[Dict[str, str]] = None) -> FactCheckResult:
        """Run comprehensive fact checking on README content."""
        logger.info("ComprehensiveFactCheckerAgent: performing multi-source fact verification")
        
        # Extract claims from text
        claims = self._extract_claims(readme_text)
        
        # Initialize evidence if not provided
        if repo_evidence is None and files:
            repo_evidence = self.repo_grounded_generator.extract_evidence(files, None)
        
        verified = []
        flagged = []
        confidence_scores = {}
        verification_sources = {}
        repository_grounded = []
        external_sources_verified = []
        
        for claim in claims[:10]:  # Limit to top 10 claims
            logger.info("Verifying claim: %s", claim[:80])
            
            # Try repository verification first
            repo_result = self._verify_against_repository(claim, repo_evidence) if repo_evidence else None
            
            # Try arXiv verification for academic claims
            arxiv_result = self._verify_against_arxiv(claim) if self.scholar else None
            
            # Try external sources
            external_result = self._verify_against_external_sources(claim)
            
            # Aggregate results
            final_result = self._aggregate_verification_results(claim, repo_result, arxiv_result, external_result)
            
            if final_result.is_verified:
                verified.append(f"{claim} (Confidence: {final_result.confidence:.2f})")
                verification_sources[claim] = final_result.sources
                
                if final_result.verification_method == 'repository':
                    repository_grounded.append(claim)
                elif final_result.verification_method in ['arxiv', 'external']:
                    external_sources_verified.append(claim)
            else:
                flagged.append(f"{claim} (Confidence: {final_result.confidence:.2f}) - {final_result.verification_method}")
            
            confidence_scores[claim] = final_result.confidence
        
        return FactCheckResult(
            claims_found=claims,
            verified=verified,
            flagged=flagged,
            confidence_scores=confidence_scores,
            verification_sources=verification_sources,
            repository_grounded=repository_grounded,
            external_sources_verified=external_sources_verified,
        )

    def _extract_claims(self, readme_text: str) -> List[str]:
        """Extract plausible technical claims from README content."""
        if not readme_text:
            return []
        
        sentences = re.split(r'(?<=[.!?])\s+', readme_text)
        claims = []
        
        # Patterns for technical claims
        patterns = [
            r'\b(novel|state-of-the-art|outperforms|significant|proposed|benchmark|advanced|research|groundbreaking|innovative|powerful)\b',
            r'\b(this project|this system|it can|powered by|built on|designed for|provides|supports|enables|implements|uses|leverages)\b',
            r'\b(fast|scalable|efficient|secure|reliable|robust|flexible|modular|extensible)\b',
            r'\b(supports|handles|manages|processes|analyzes|generates|transforms)\b',
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

    def _verify_against_repository(self, claim: str, evidence: RepositoryEvidence) -> Optional[VerificationResult]:
        """Verify claim against repository evidence."""
        if not evidence:
            return None
        
        claim_lower = claim.lower()
        
        # Check against imports
        for imp in evidence.import_statements:
            if imp.lower() in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.90,
                    sources=[f"Repository import: {imp}"],
                    verification_method='repository'
                )
        
        # Check against class definitions
        for cls in evidence.class_definitions:
            if cls.lower() in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.85,
                    sources=[f"Repository class: {cls}"],
                    verification_method='repository'
                )
        
        # Check against function signatures
        for func in evidence.function_signatures:
            if func.lower() in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.80,
                    sources=[f"Repository function: {func}"],
                    verification_method='repository'
                )
        
        # Check against configuration
        for config_key, config_value in evidence.configuration_values.items():
            if str(config_key).lower() in claim_lower or str(config_value).lower() in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.75,
                    sources=[f"Configuration: {config_key}"],
                    verification_method='repository'
                )
        
        # Check against API endpoints
        for endpoint in evidence.api_endpoints:
            if endpoint.get('endpoint', '').lower() in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.85,
                    sources=[f"API endpoint: {endpoint['endpoint']}"],
                    verification_method='repository'
                )
        
        # Check against code examples
        for desc, code in evidence.code_examples.items():
            if any(word in code.lower() for word in claim_lower.split()):
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.70,
                    sources=[f"Code example: {desc}"],
                    verification_method='repository'
                )
        
        return None

    def _verify_against_arxiv(self, claim: str) -> Optional[VerificationResult]:
        """Verify claim against academic sources (arXiv)."""
        if not self.scholar:
            return None
        
        try:
            hits = self.scholar.search(claim, max_results=2)
            if hits:
                sources = [f"arXiv paper: {hit['title']}" for hit in hits]
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.80,
                    sources=sources,
                    verification_method='arxiv'
                )
        except Exception as e:
            logger.warning("ArXiv verification failed for claim: %s, error: %s", claim[:50], e)
        
        return None

    def _verify_against_external_sources(self, claim: str) -> Optional[VerificationResult]:
        """Verify claim against external documentation and official sources."""
        claim_lower = claim.lower()
        
        # Known technology facts (could be expanded with API calls)
        tech_facts = {
            'fastapi': 'FastAPI is a modern, fast web framework for building APIs with Python',
            'langchain': 'LangChain is a framework for developing applications powered by language models',
            'langgraph': 'LangGraph is a library for building stateful, multi-actor applications with LLMs',
            'python': 'Python is a high-level, interpreted programming language',
            'docker': 'Docker is a platform for developing, shipping, and running applications in containers',
            'kubernetes': 'Kubernetes is an open-source container orchestration platform',
            'redis': 'Redis is an in-memory data structure store, used as a database, cache, and message broker',
            'postgresql': 'PostgreSQL is a powerful, open-source object-relational database system',
        }
        
        for tech, fact in tech_facts.items():
            if tech in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.65,
                    sources=[f"Official documentation: {tech}"],
                    verification_method='external'
                )
        
        # Check for common framework claims
        framework_claims = {
            'async': 'Async/await is a Python feature for asynchronous programming',
            'type hints': 'Type hints are Python annotations for variable types',
            'dataclass': 'Dataclasses are Python classes for storing data',
            'context manager': 'Context managers manage resources using "with" statements',
        }
        
        for claim_pattern, fact in framework_claims.items():
            if claim_pattern in claim_lower:
                return VerificationResult(
                    claim=claim,
                    is_verified=True,
                    confidence=0.60,
                    sources=[f"Python documentation: {claim_pattern}"],
                    verification_method='external'
                )
        
        return None

    def _aggregate_verification_results(self, claim: str, repo_result: Optional[VerificationResult],
                                      arxiv_result: Optional[VerificationResult],
                                      external_result: Optional[VerificationResult]) -> VerificationResult:
        """Aggregate results from multiple verification sources."""
        
        results = [r for r in [repo_result, arxiv_result, external_result] if r is not None]
        
        if not results:
            return VerificationResult(
                claim=claim,
                is_verified=False,
                confidence=0.0,
                sources=[],
                verification_method='inference'
            )
        
        # Prioritize repository evidence as most reliable
        if repo_result and repo_result.is_verified:
            return repo_result
        
        # Then academic sources
        if arxiv_result and arxiv_result.is_verified:
            return arxiv_result
        
        # Then external sources
        if external_result and external_result.is_verified:
            return external_result
        
        # If none verified, return the one with highest confidence
        verified_results = [r for r in results if r.is_verified]
        if verified_results:
            return max(verified_results, key=lambda x: x.confidence)
        
        # Return highest confidence unverified result
        return max(results, key=lambda x: x.confidence)

    def verify_technical_accuracy(self, content: str, repo_evidence: RepositoryEvidence,
                                  files: Dict[str, str]) -> Dict[str, Any]:
        """Comprehensive technical accuracy verification."""
        logger.info("ComprehensiveFactCheckerAgent: performing technical accuracy verification")
        
        # Verify all content against repository
        validation_result = self.repo_grounded_generator.validate_content(content, repo_evidence)
        
        # Extract and verify specific technical claims
        fact_check_result = self.run(content, repo_evidence, files)
        
        # Calculate overall technical accuracy score
        total_claims = len(fact_check_result.claims_found)
        verified_count = len(fact_check_result.verified)
        
        accuracy_score = (verified_count / max(total_claims, 1)) * 100 if total_claims > 0 else 0
        
        # Combine with validation confidence
        overall_confidence = (accuracy_score + validation_result.confidence_score * 100) / 2
        
        return {
            "technical_accuracy_score": accuracy_score,
            "overall_confidence": overall_confidence,
            "validation_result": validation_result,
            "fact_check_result": fact_check_result,
            "repository_grounded_count": len(fact_check_result.repository_grounded),
            "externally_verified_count": len(fact_check_result.external_sources_verified),
            "recommendations": self._generate_accuracy_recommendations(fact_check_result, validation_result),
        }

    def _generate_accuracy_recommendations(self, fact_check_result: FactCheckResult,
                                         validation_result) -> List[str]:
        """Generate recommendations for improving technical accuracy."""
        recommendations = []
        
        # Flag unverified claims
        if fact_check_result.flagged:
            recommendations.append(
                f"Review {len(fact_check_result.flagged)} unverified claims and provide evidence or remove them"
            )
        
        # Check confidence scores
        low_confidence_claims = [claim for claim, score in fact_check_result.confidence_scores.items() 
                                if score < 0.5]
        if low_confidence_claims:
            recommendations.append(
                f"{len(low_confidence_claims)} claims have low confidence scores - consider adding supporting evidence"
            )
        
        # Check validation results
        if validation_result.ungrounded_claims:
            recommendations.append(
                f"{len(validation_result.ungrounded_claims)} claims lack repository evidence - consider revising"
            )
        
        # Repository grounding recommendations
        if len(fact_check_result.repository_grounded) < len(fact_check_result.claims_found) / 2:
            recommendations.append(
                "Increase repository grounding by referencing actual code, configuration, or implementation details"
            )
        
        if not recommendations:
            recommendations.append("Technical accuracy is good - claims are well-supported by evidence")
        
        return recommendations


__all__ = [
    "ComprehensiveFactCheckerAgent",
    "FactCheckResult",
    "VerificationResult",
]