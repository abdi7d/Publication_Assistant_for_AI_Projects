# agents/__init__.py
from .repo_analyzer import RepoAnalyzerAgent, RepoAnalysis
from .metadata_recommender import MetadataRecommenderAgent
from .content_improver import ContentImproverAgent, ContentImprovement
from .reviewer_critic import ReviewerCriticAgent
from .fact_checker import FactCheckerAgent, FactCheckResult

# Enhanced agents
from .deep_repo_analyzer import DeepRepositoryAnalyzerAgent, DeepRepositoryAnalysis
from .intelligent_content_improver import IntelligentContentImproverAgent
from .comprehensive_fact_checker import ComprehensiveFactCheckerAgent
from .adaptive_technical_writer import AdaptiveTechnicalWriter, AudienceProfile, WritingStyle
from .seo_strategy_agent import SEOStrategyAgent, SEOStrategy

__all__ = [
    # Original agents
    "RepoAnalyzerAgent",
    "RepoAnalysis",
    "MetadataRecommenderAgent",
    "ContentImproverAgent",
    "ContentImprovement",
    "ReviewerCriticAgent",
    "FactCheckerAgent",
    "FactCheckResult",
    # Enhanced agents
    "DeepRepositoryAnalyzerAgent",
    "DeepRepositoryAnalysis",
    "IntelligentContentImproverAgent",
    "ComprehensiveFactCheckerAgent",
    "AdaptiveTechnicalWriter",
    "AudienceProfile",
    "WritingStyle",
    "SEOStrategyAgent",
    "SEOStrategy",
]