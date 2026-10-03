# main.py
"""
Entry point for the Publication Assistant multi-agent system.

Example usage:
    python main.py --repo-path ./some_repo
    python main.py --repo-path ./some_repo --enhanced  # Use enhanced collaborative mode
"""
from tools import RepoParser, KeywordExtractor, WebSearchTool, RAGRetriever, ArxivScholarTool
from tools import ContextEnrichmentTool, RepositoryGroundedGenerator
import argparse
from agents import (
    RepoAnalyzerAgent, MetadataRecommenderAgent, ContentImproverAgent, 
    ReviewerCriticAgent, FactCheckerAgent,
    DeepRepositoryAnalyzerAgent, IntelligentContentImproverAgent,
    ComprehensiveFactCheckerAgent, AdaptiveTechnicalWriter, SEOStrategyAgent
)
from orchestration import Orchestrator
import os
import sys
import logging
from dotenv import load_dotenv
from utils.logging import configure_logging
from utils.publication_builder import PublicationBuilder

# Set UTF-8 encoding for stdout
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


def build_agents(repo_source: str, enhanced: bool = False):
    """Build agent configuration based on mode."""
    repo_parser = RepoParser()
    
    if enhanced:
        # Enhanced collaborative agents
        repo_analyzer = DeepRepositoryAnalyzerAgent(
            repo_source=repo_source, repo_parser=repo_parser)
        
        keyword_extractor = KeywordExtractor()
        metadata_recommender = MetadataRecommenderAgent(
            keyword_extractor=keyword_extractor)
        
        web_search = WebSearchTool()
        rag_retriever = RAGRetriever()
        content_improver = IntelligentContentImproverAgent(
            web_search=web_search, rag=rag_retriever)
        
        reviewer = ReviewerCriticAgent()
        scholar = ArxivScholarTool()
        fact_checker = ComprehensiveFactCheckerAgent(scholar_tool=scholar)
        
        adaptive_writer = AdaptiveTechnicalWriter()
        seo_agent = SEOStrategyAgent()
        
        context_enricher = ContextEnrichmentTool()
        repo_grounded_generator = RepositoryGroundedGenerator()
        
        agents = {
            "deep_repo_analyzer": repo_analyzer,
            "repo_analyzer": repo_analyzer,  # Fallback
            "metadata_recommender": metadata_recommender,
            "intelligent_content_improver": content_improver,
            "content_improver": content_improver,  # Fallback
            "reviewer_critic": reviewer,
            "comprehensive_fact_checker": fact_checker,
            "fact_checker": fact_checker,  # Fallback
            "adaptive_technical_writer": adaptive_writer,
            "seo_strategy_agent": seo_agent,
        }
    else:
        # Original agents
        repo_analyzer = RepoAnalyzerAgent(
            repo_source=repo_source, repo_parser=repo_parser)
        keyword_extractor = KeywordExtractor()
        metadata_recommender = MetadataRecommenderAgent(
            keyword_extractor=keyword_extractor)
        web_search = WebSearchTool()
        rag_retriever = RAGRetriever()
        content_improver = ContentImproverAgent(
            web_search=web_search, rag=rag_retriever)
        reviewer = ReviewerCriticAgent()
        scholar = ArxivScholarTool()
        fact_checker = FactCheckerAgent(scholar_tool=scholar)
        
        agents = {
            "repo_analyzer": repo_analyzer,
            "metadata_recommender": metadata_recommender,
            "content_improver": content_improver,
            "reviewer_critic": reviewer,
            "fact_checker": fact_checker
        }
    
    return agents


def main():
    parser = argparse.ArgumentParser("Publication Assistant")
    parser.add_argument("--repo-path", required=True,
                        help="Path to repository directory or zip file")
    parser.add_argument("--enhanced", action="store_true",
                        help="Use enhanced collaborative mode with elite agents")
    parser.add_argument("--style", default="Technical Blog",
                        help="Writing style (Technical Blog, Research Paper, Documentation, etc.)")
    parser.add_argument("--goal", default="",
                        help="Specific goal for documentation generation")
    args = parser.parse_args()
    
    repo_path = args.repo_path
    agents = build_agents(repo_path, enhanced=args.enhanced)
    
    # Initialize orchestrator with collaborative mode if enhanced
    orchestrator = Orchestrator(use_collaborative=args.enhanced)
    
    result = orchestrator.run_pipeline(
        agents=agents, 
        repo_source=repo_path,
        style=args.style,
        goal=args.goal
    )
    
    # Print a comprehensive report
    print("=== Publication Assistant Report ===")
    print(f"Mode: {'Enhanced Collaborative' if args.enhanced else 'Standard'}")
    print(f"Style: {args.style}")
    print(f"Goal: {args.goal or 'General documentation'}")
    print()
    
    if "metadata" in result and result["metadata"]:
        if hasattr(result["metadata"], "title_suggestions"):
            try:
                print("Suggested titles:", result["metadata"].title_suggestions)
            except UnicodeEncodeError:
                print("Suggested titles: [Contains special characters]")
        else:
            print("Suggested titles: N/A")
        
        if hasattr(result["metadata"], "tags"):
            try:
                print("Suggested tags:", ", ".join(result["metadata"].tags[:20]))
            except UnicodeEncodeError:
                print("Suggested tags: [Contains special characters]")
        else:
            print("Suggested tags: N/A")
    
    if "review" in result and result["review"]:
        print("Review score:", result["review"].score if hasattr(result["review"], "score") else "N/A")
    
    if "analysis" in result and result["analysis"]:
        print("Missing README sections:", result["analysis"].missing_sections if hasattr(result["analysis"], "missing_sections") else "N/A")
        
        # Enhanced analysis details
        if hasattr(result["analysis"], "architecture"):
            print("Architecture style:", result["analysis"].architecture.architectural_style)
            print("Design patterns:", ", ".join(result["analysis"].architecture.design_patterns[:5]))
    
    if "fact_check" in result and result["fact_check"]:
        print("Fact-check results:")
        print("  - Claims found:", len(result["fact_check"].claims_found) if hasattr(result["fact_check"], "claims_found") else 0)
        print("  - Verified:", len(result["fact_check"].verified) if hasattr(result["fact_check"], "verified") else 0)
        print("  - Flagged:", len(result["fact_check"].flagged) if hasattr(result["fact_check"], "flagged") else 0)
    
    # Enhanced metrics
    if "collaborative_metrics" in result:
        print("\n=== Collaborative Metrics ===")
        for key, value in result["collaborative_metrics"].items():
            print(f"  {key}: {value}")
    
    if "quality_gates" in result:
        print("\n=== Quality Gates ===")
        for gate, passed in result["quality_gates"].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {gate}: {status}")
    
    print("\n=== Publication-Ready README Preview ===")
    print(result.get("publication_readme", "")[:4000])
    
    # SEO strategy if available
    if "seo_strategy" in result and result["seo_strategy"]:
        print("\n=== SEO Strategy ===")
        print("Discoverability score:", result["seo_strategy"].discoverability_score)
        print("Optimization priorities:", result["seo_strategy"].optimization_priority[:3])


if __name__ == "__main__":  # pragma: no cover
    main()
