# agents/seo_strategy_agent.py
"""
SEO Strategy Agent for comprehensive SEO optimization.
Generates SEO metadata, optimizes for discoverability, and handles multi-audience content strategy.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class SEOMetadata:
    """Comprehensive SEO metadata for repository."""
    primary_keywords: List[str]
    secondary_keywords: List[str]
    long_tail_keywords: List[str]
    search_intents: List[str]
    title_variations: List[str]
    description_variations: List[str]
    meta_description: str
    open_graph_tags: Dict[str, str]
    twitter_card_tags: Dict[str, str]


@dataclass
class GitHubOptimization:
    """GitHub-specific optimization recommendations."""
    optimal_topics: List[str]
    repository_description: str
    readme_structure: List[str]
    social_sharing_tags: List[str]
    contribution_guidelines: str
    badge_recommendations: List[str]


@dataclass
class AudienceAdaptation:
    """Content adapted for different audiences."""
    executive_summary: str
    technical_deep_dive: str
    quick_start_guide: str
    tutorial_content: str
    research_summary: str


@dataclass
class SEOStrategy:
    """Comprehensive SEO strategy for repository."""
    seo_metadata: SEOMetadata
    github_optimization: GitHubOptimization
    audience_adaptations: Dict[str, AudienceAdaptation]
    discoverability_score: float
    optimization_priority: List[str]
    implementation_plan: List[str]


class SEOStrategyAgent:
    """
    Comprehensive SEO optimization for repositories.
    Generates metadata, optimizes for discoverability, and creates
    multi-audience content strategies.
    """

    def __init__(self):
        self.keyword_cache = {}
        self.search_intent_cache = {}

    def generate_comprehensive_strategy(self, repo_analysis: Any, metadata: Any, 
                                       context: Dict[str, Any]) -> SEOStrategy:
        """Generate comprehensive SEO strategy for repository."""
        logger.info("SEOStrategyAgent: generating comprehensive SEO strategy")
        
        # Generate SEO metadata
        seo_metadata = self._generate_seo_metadata(repo_analysis, metadata, context)
        
        # Generate GitHub optimization
        github_optimization = self._generate_github_optimization(repo_analysis, metadata, context)
        
        # Generate audience adaptations
        audience_adaptations = self._generate_audience_adaptations(repo_analysis, metadata, context)
        
        # Calculate discoverability score
        discoverability_score = self._calculate_discoverability_score(
            seo_metadata, github_optimization, repo_analysis
        )
        
        # Determine optimization priorities
        optimization_priority = self._determine_optimization_priority(
            seo_metadata, github_optimization, discoverability_score
        )
        
        # Create implementation plan
        implementation_plan = self._create_implementation_plan(optimization_priority)
        
        return SEOStrategy(
            seo_metadata=seo_metadata,
            github_optimization=github_optimization,
            audience_adaptations=audience_adaptations,
            discoverability_score=discoverability_score,
            optimization_priority=optimization_priority,
            implementation_plan=implementation_plan,
        )

    def _generate_seo_metadata(self, repo_analysis: Any, metadata: Any, 
                             context: Dict[str, Any]) -> SEOMetadata:
        """Generate comprehensive SEO metadata."""
        
        # Extract keywords from repository
        primary_keywords = self._extract_primary_keywords(repo_analysis, metadata)
        secondary_keywords = self._extract_secondary_keywords(repo_analysis, metadata)
        long_tail_keywords = self._generate_long_tail_keywords(repo_analysis, metadata)
        
        # Determine search intents
        search_intents = self._determine_search_intents(repo_analysis, metadata)
        
        # Generate title variations
        title_variations = self._generate_title_variations(metadata, primary_keywords)
        
        # Generate description variations
        description_variations = self._generate_description_variations(
            metadata, primary_keywords, secondary_keywords
        )
        
        # Generate meta description
        meta_description = self._generate_meta_description(metadata, primary_keywords)
        
        # Generate Open Graph tags
        open_graph_tags = self._generate_open_graph_tags(metadata, primary_keywords)
        
        # Generate Twitter Card tags
        twitter_card_tags = self._generate_twitter_card_tags(metadata, primary_keywords)
        
        return SEOMetadata(
            primary_keywords=primary_keywords,
            secondary_keywords=secondary_keywords,
            long_tail_keywords=long_tail_keywords,
            search_intents=search_intents,
            title_variations=title_variations,
            description_variations=description_variations,
            meta_description=meta_description,
            open_graph_tags=open_graph_tags,
            twitter_card_tags=twitter_card_tags,
        )

    def _extract_primary_keywords(self, repo_analysis: Any, metadata: Any) -> List[str]:
        """Extract primary keywords from repository and metadata."""
        keywords = set()
        
        # From metadata tags
        if hasattr(metadata, 'tags'):
            keywords.update(metadata.tags[:10])
        
        # From repository technology stack
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            for category, technologies in stack.items():
                keywords.update(technologies)
        
        # From project type
        if hasattr(repo_analysis, 'code_stats'):
            project_type = repo_analysis.code_stats.get('project_type', '')
            keywords.add(project_type)
        
        # From architecture
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            keywords.add(arch.architectural_style)
            keywords.update(arch.design_patterns[:5])
        
        return list(keywords)[:15]  # Limit to top 15

    def _extract_secondary_keywords(self, repo_analysis: Any, metadata: Any) -> List[str]:
        """Extract secondary keywords for broader discoverability."""
        keywords = set()
        
        # Related technologies
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            if 'ai_ml' in stack:
                keywords.update(['machine learning', 'artificial intelligence', 'deep learning'])
            if 'web_frameworks' in stack:
                keywords.update(['web development', 'api', 'backend'])
            if 'databases' in stack:
                keywords.update(['database', 'data storage', 'persistence'])
        
        # General software terms
        keywords.update(['open source', 'software development', 'programming', 'code'])
        
        # Framework-specific terms
        if hasattr(repo_analysis, 'code_stats'):
            primary_lang = repo_analysis.code_stats.get('primary_language', '')
            if primary_lang == 'py':
                keywords.update(['python', 'python3', 'python programming'])
        
        return list(keywords)[:20]

    def _generate_long_tail_keywords(self, repo_analysis: Any, metadata: Any) -> List[str]:
        """Generate long-tail keywords for specific search queries."""
        long_tail = []
        
        primary_keywords = self._extract_primary_keywords(repo_analysis, metadata)
        
        # Combine primary keywords with action verbs
        actions = ['how to', 'tutorial', 'guide', 'example', 'implementation', 'best practices']
        
        for keyword in primary_keywords[:5]:
            for action in actions:
                long_tail.append(f"{action} {keyword}")
        
        # Combine with use cases
        use_cases = ['for beginners', 'for production', 'for research', 'for development']
        
        for keyword in primary_keywords[:3]:
            for use_case in use_cases:
                long_tail.append(f"{keyword} {use_case}")
        
        return long_tail[:25]

    def _determine_search_intents(self, repo_analysis: Any, metadata: Any) -> List[str]:
        """Determine the search intents the repository should target."""
        intents = []
        
        # Informational intent (learning, tutorials)
        if hasattr(repo_analysis, 'code_quality'):
            if repo_analysis.code_quality.documentation_completeness > 50:
                intents.append('informational')
        
        # Navigational intent (finding specific project)
        intents.append('navigational')
        
        # Transactional intent (using/downloading)
        intents.append('transactional')
        
        # Commercial investigation (comparing alternatives)
        if hasattr(repo_analysis, 'architecture'):
            if repo_analysis.architecture.architectural_style != 'monolithic':
                intents.append('commercial_investigation')
        
        return intents

    def _generate_title_variations(self, metadata: Any, primary_keywords: List[str]) -> List[str]:
        """Generate title variations for A/B testing."""
        variations = []
        
        base_title = metadata.title_suggestions[0] if hasattr(metadata, 'title_suggestions') and metadata.title_suggestions else "Project"
        
        # Variation 1: Focus on primary benefit
        variations.append(f"{base_title} - {primary_keywords[0] if primary_keywords else 'Modern Solution'}")
        
        # Variation 2: Include secondary keyword
        if len(primary_keywords) > 1:
            variations.append(f"{base_title} | {primary_keywords[1]} Framework")
        
        # Variation 3: Action-oriented
        variations.append(f"Build with {base_title} - {primary_keywords[0] if primary_keywords else 'Efficient Development'}")
        
        # Variation 4: Descriptive
        variations.append(f"{base_title}: A {primary_keywords[0] if primary_keywords else 'Powerful'} Tool for Developers")
        
        return variations[:5]

    def _generate_description_variations(self, metadata: Any, primary_keywords: List[str],
                                       secondary_keywords: List[str]) -> List[str]:
        """Generate description variations for different platforms."""
        variations = []
        
        base_desc = metadata.short_description if hasattr(metadata, 'short_description') else "A software project"
        
        # Variation 1: Feature-focused
        variations.append(f"{base_desc} featuring {', '.join(primary_keywords[:3])}")
        
        # Variation 2: Benefit-focused
        variations.append(f"Build {', '.join(secondary_keywords[:3])} with {base_desc}")
        
        # Variation 3: Technical
        variations.append(f"A {primary_keywords[0] if primary_keywords else 'modern'} solution for {secondary_keywords[0] if secondary_keywords else 'developers'}")
        
        # Variation 4: Concise
        variations.append(f"{base_desc} - {primary_keywords[0] if primary_keywords else 'open source'} project")
        
        return variations[:4]

    def _generate_meta_description(self, metadata: Any, primary_keywords: List[str]) -> str:
        """Generate optimized meta description."""
        base_desc = metadata.short_description if hasattr(metadata, 'short_description') else "A software project"
        
        # Include primary keywords naturally
        if primary_keywords:
            keywords_str = ', '.join(primary_keywords[:3])
            meta_desc = f"{base_desc}. Built with {keywords_str}. Open source, production-ready solution."
        else:
            meta_desc = f"{base_desc}. Production-ready open source software project."
        
        # Keep under 160 characters for SEO
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."
        
        return meta_desc

    def _generate_open_graph_tags(self, metadata: Any, primary_keywords: List[str]) -> Dict[str, str]:
        """Generate Open Graph tags for social sharing."""
        base_title = metadata.title_suggestions[0] if hasattr(metadata, 'title_suggestions') and metadata.title_suggestions else "Project"
        base_desc = metadata.short_description if hasattr(metadata, 'short_description') else "A software project"
        
        return {
            "og:title": base_title,
            "og:description": base_desc,
            "og:type": "website",
            "og:keywords": ', '.join(primary_keywords[:5]),
            "og:site_name": base_title,
        }

    def _generate_twitter_card_tags(self, metadata: Any, primary_keywords: List[str]) -> Dict[str, str]:
        """Generate Twitter Card tags for social sharing."""
        base_title = metadata.title_suggestions[0] if hasattr(metadata, 'title_suggestions') and metadata.title_suggestions else "Project"
        base_desc = metadata.short_description if hasattr(metadata, 'short_description') else "A software project"
        
        return {
            "twitter:card": "summary_large_image",
            "twitter:title": base_title,
            "twitter:description": base_desc,
            "twitter:keywords": ', '.join(primary_keywords[:5]),
        }

    def _generate_github_optimization(self, repo_analysis: Any, metadata: Any,
                                   context: Dict[str, Any]) -> GitHubOptimization:
        """Generate GitHub-specific optimization recommendations."""
        
        # Generate optimal topics (up to 20)
        optimal_topics = self._generate_optimal_topics(repo_analysis, metadata)
        
        # Generate repository description
        repository_description = self._generate_repository_description(metadata, repo_analysis)
        
        # Generate README structure
        readme_structure = self._generate_readme_structure(repo_analysis)
        
        # Generate social sharing tags
        social_sharing_tags = self._generate_social_sharing_tags(metadata)
        
        # Generate contribution guidelines
        contribution_guidelines = self._generate_contribution_guidelines(repo_analysis)
        
        # Generate badge recommendations
        badge_recommendations = self._generate_badge_recommendations(repo_analysis)
        
        return GitHubOptimization(
            optimal_topics=optimal_topics,
            repository_description=repository_description,
            readme_structure=readme_structure,
            social_sharing_tags=social_sharing_tags,
            contribution_guidelines=contribution_guidelines,
            badge_recommendations=badge_recommendations,
        )

    def _generate_optimal_topics(self, repo_analysis: Any, metadata: Any) -> List[str]:
        """Generate optimal GitHub topics (up to 20)."""
        topics = set()
        
        # From primary keywords
        primary_keywords = self._extract_primary_keywords(repo_analysis, metadata)
        topics.update([kw.lower().replace(' ', '-') for kw in primary_keywords[:10]])
        
        # From technology stack
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            for category, technologies in stack.items():
                for tech in technologies:
                    topics.add(tech.lower().replace(' ', '-'))
        
        # Add general topics
        topics.update(['open-source', 'software-development', 'python'])
        
        # Add domain-specific topics
        if hasattr(repo_analysis, 'code_stats'):
            project_type = repo_analysis.code_stats.get('project_type', '').lower()
            if 'ai' in project_type or 'ml' in project_type:
                topics.update(['machine-learning', 'artificial-intelligence', 'deep-learning'])
            if 'api' in project_type or 'web' in project_type:
                topics.update(['api', 'web-development', 'rest-api'])
        
        return list(topics)[:20]

    def _generate_repository_description(self, metadata: Any, repo_analysis: Any) -> str:
        """Generate optimized repository description."""
        base_desc = metadata.short_description if hasattr(metadata, 'short_description') else "A software project"
        
        # Add key features
        features = []
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            # Handle both old and new architecture formats
            if hasattr(arch, 'api_endpoints') and arch.api_endpoints:
                features.append("REST API")
            if hasattr(arch, 'architectural_style') and arch.architectural_style != "monolithic":
                features.append(f"{arch.architectural_style} architecture")
        
        if features:
            description = f"{base_desc}. Features: {', '.join(features)}."
        else:
            description = base_desc
        
        # Keep under 280 characters for GitHub
        if len(description) > 280:
            description = description[:277] + "..."
        
        return description

    def _generate_readme_structure(self, repo_analysis: Any) -> List[str]:
        """Generate optimal README structure."""
        structure = [
            "Project Title and Badge",
            "Short Description",
            "Table of Contents",
            "Features",
            "Installation",
            "Quick Start",
            "Usage",
            "Configuration",
            "API Reference",
            "Architecture",
            "Contributing",
            "License",
        ]
        
        # Add repository-specific sections
        if hasattr(repo_analysis, 'architecture'):
            if repo_analysis.architecture.api_endpoints:
                structure.insert(structure.index("Architecture"), "API Documentation")
        
        if hasattr(repo_analysis, 'code_quality'):
            if repo_analysis.code_quality.test_coverage_estimate > 0:
                structure.insert(structure.index("Contributing"), "Testing")
        
        return structure

    def _generate_social_sharing_tags(self, metadata: Any) -> List[str]:
        """Generate social sharing hashtags."""
        tags = []
        
        if hasattr(metadata, 'tags'):
            tags.extend([f"#{tag.replace(' ', '')}" for tag in metadata.tags[:5]])
        
        # Add general tags
        tags.extend(['#opensource', '#dev', '#coding'])
        
        return tags

    def _generate_contribution_guidelines(self, repo_analysis: Any) -> str:
        """Generate contribution guidelines."""
        guidelines = "## Contributing\n\n"
        
        if hasattr(repo_analysis, 'code_quality'):
            quality = repo_analysis.code_quality
            if quality.test_coverage_estimate > 0:
                guidelines += "We welcome contributions! Please ensure all tests pass and maintain test coverage.\n\n"
            else:
                guidelines += "We welcome contributions! Please add tests for new features.\n\n"
        else:
            guidelines += "We welcome contributions! Please follow our code style and add tests.\n\n"
        
        guidelines += "1. Fork the repository\n"
        guidelines += "2. Create a feature branch\n"
        guidelines += "3. Make your changes\n"
        guidelines += "4. Submit a pull request\n\n"
        
        return guidelines

    def _generate_badge_recommendations(self, repo_analysis: Any) -> List[str]:
        """Generate badge recommendations."""
        badges = []
        
        # Standard badges
        badges.append("[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)")
        
        # Language badge
        if hasattr(repo_analysis, 'code_stats'):
            primary_lang = repo_analysis.code_stats.get('primary_language', 'Python')
            badges.append(f"[![Language: {primary_lang}](https://img.shields.io/badge/Language-{primary_lang}-blue.svg)]()")
        
        # Framework badges
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            if 'frameworks' in stack and stack['frameworks']:
                for framework in stack['frameworks'][:2]:
                    badges.append(f"[![Framework: {framework}](https://img.shields.io/badge/Framework-{framework}-orange.svg)]()")
        
        return badges

    def _generate_audience_adaptations(self, repo_analysis: Any, metadata: Any,
                                    context: Dict[str, Any]) -> Dict[str, AudienceAdaptation]:
        """Generate content adaptations for different audiences."""
        
        adaptations = {}
        
        # Executive summary for decision makers
        adaptations['executive'] = AudienceAdaptation(
            executive_summary=self._generate_executive_summary(metadata, repo_analysis),
            technical_deep_dive="",
            quick_start_guide="",
            tutorial_content="",
            research_summary="",
        )
        
        # Technical deep dive for engineers
        adaptations['technical'] = AudienceAdaptation(
            executive_summary="",
            technical_deep_dive=self._generate_technical_deep_dive(repo_analysis),
            quick_start_guide="",
            tutorial_content="",
            research_summary="",
        )
        
        # Quick start for developers
        adaptations['developer'] = AudienceAdaptation(
            executive_summary="",
            technical_deep_dive="",
            quick_start_guide=self._generate_quick_start_guide(repo_analysis),
            tutorial_content="",
            research_summary="",
        )
        
        # Tutorial for learners
        adaptations['learner'] = AudienceAdaptation(
            executive_summary="",
            technical_deep_dive="",
            quick_start_guide="",
            tutorial_content=self._generate_tutorial_content(repo_analysis),
            research_summary="",
        )
        
        # Research summary for academics
        adaptations['research'] = AudienceAdaptation(
            executive_summary="",
            technical_deep_dive="",
            quick_start_guide="",
            tutorial_content="",
            research_summary=self._generate_research_summary(repo_analysis),
        )
        
        return adaptations

    def _generate_executive_summary(self, metadata: Any, repo_analysis: Any) -> str:
        """Generate executive summary for decision makers."""
        base_desc = metadata.short_description if hasattr(metadata, 'short_description') else "A software project"
        
        summary = f"## Executive Summary\n\n"
        summary += f"{base_desc} This project provides a production-ready solution "
        summary += f"with modern architecture and comprehensive features. "
        
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            if stack['frameworks']:
                summary += f"Built with {', '.join(stack['frameworks'][:2])}, "
        
        summary += "it offers scalability, security, and maintainability for enterprise applications."
        
        return summary

    def _generate_technical_deep_dive(self, repo_analysis: Any) -> str:
        """Generate technical deep dive for engineers."""
        deep_dive = "## Technical Deep Dive\n\n"
        
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            deep_dive += f"### Architecture\n\n"
            deep_dive += f"The system follows a {arch.architectural_style} architecture pattern. "
            deep_dive += f"Key design patterns include: {', '.join(arch.design_patterns[:5])}.\n\n"
        
        if hasattr(repo_analysis, 'code_quality'):
            quality = repo_analysis.code_quality
            deep_dive += f"### Code Quality\n\n"
            deep_dive += f"Maintainability index: {quality.maintainability_index:.1f}/100\n"
            deep_dive += f"Test coverage: {quality.test_coverage_estimate:.1f}%\n"
            deep_dive += f"Documentation completeness: {quality.documentation_completeness:.1f}%\n\n"
        
        return deep_dive

    def _generate_quick_start_guide(self, repo_analysis: Any) -> str:
        """Generate quick start guide for developers."""
        guide = "## Quick Start Guide\n\n"
        guide += "Get up and running in minutes:\n\n"
        guide += "### Installation\n\n"
        guide += "```bash\n"
        guide += "pip install -r requirements.txt\n"
        guide += "```\n\n"
        guide += "### Configuration\n\n"
        guide += "Copy `.env.example` to `.env` and configure your settings.\n\n"
        guide += "### Run\n\n"
        guide += "```bash\n"
        guide += "python main.py\n"
        guide += "```\n\n"
        
        return guide

    def _generate_tutorial_content(self, repo_analysis: Any) -> str:
        """Generate tutorial content for learners."""
        tutorial = "## Tutorial\n\n"
        tutorial += "Learn how to use this project step by step:\n\n"
        tutorial += "### Step 1: Understanding the Basics\n\n"
        tutorial += "This project is designed to be accessible to developers of all levels. "
        tutorial += "Start by reviewing the architecture overview.\n\n"
        tutorial += "### Step 2: Your First Implementation\n\n"
        tutorial += "Follow the quick start guide to get the system running locally.\n\n"
        tutorial += "### Step 3: Advanced Features\n\n"
        tutorial += "Explore the API documentation and configuration options for advanced usage.\n\n"
        
        return tutorial

    def _generate_research_summary(self, repo_analysis: Any) -> str:
        """Generate research summary for academics."""
        summary = "## Research Summary\n\n"
        
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            summary += f"### Methodology\n\n"
            summary += f"This project implements a {arch.architectural_style} approach "
            summary += f"utilizing {', '.join(arch.design_patterns[:3])} design patterns.\n\n"
        
        summary += "### Key Contributions\n\n"
        summary += "- Modular architecture for extensibility\n"
        summary += "- Production-ready implementation\n"
        summary += "- Comprehensive testing framework\n"
        summary += "- Performance optimization strategies\n\n"
        
        return summary

    def _calculate_discoverability_score(self, seo_metadata: SEOMetadata,
                                      github_optimization: GitHubOptimization,
                                      repo_analysis: Any) -> float:
        """Calculate overall discoverability score."""
        score = 0.0
        
        # SEO metadata quality (40%)
        keyword_count = len(seo_metadata.primary_keywords) + len(seo_metadata.secondary_keywords)
        score += min(keyword_count / 30, 1.0) * 0.4
        
        # GitHub optimization (30%)
        topic_count = len(github_optimization.optimal_topics)
        score += min(topic_count / 20, 1.0) * 0.3
        
        # Content quality (30%)
        if hasattr(repo_analysis, 'code_quality'):
            quality = repo_analysis.code_quality
            documentation_score = quality.documentation_completeness / 100
            score += documentation_score * 0.3
        
        return round(score, 2)

    def _determine_optimization_priority(self, seo_metadata: SEOMetadata,
                                      github_optimization: GitHubOptimization,
                                      discoverability_score: float) -> List[str]:
        """Determine optimization priorities based on current state."""
        priorities = []
        
        if discoverability_score < 0.5:
            priorities.append("HIGH: Add comprehensive GitHub topics")
            priorities.append("HIGH: Optimize repository description")
            priorities.append("HIGH: Improve keyword coverage")
        elif discoverability_score < 0.7:
            priorities.append("MEDIUM: Expand secondary keywords")
            priorities.append("MEDIUM: Add Open Graph tags")
            priorities.append("MEDIUM: Create audience-specific content")
        else:
            priorities.append("LOW: A/B test title variations")
            priorities.append("LOW: Refine long-tail keywords")
            priorities.append("LOW: Monitor search performance")
        
        return priorities

    def _create_implementation_plan(self, priorities: List[str]) -> List[str]:
        """Create implementation plan based on priorities."""
        plan = []
        
        # Extract priority levels
        high_priority = [p for p in priorities if p.startswith("HIGH")]
        medium_priority = [p for p in priorities if p.startswith("MEDIUM")]
        low_priority = [p for p in priorities if p.startswith("LOW")]
        
        if high_priority:
            plan.append("Phase 1 (Immediate): " + ", ".join(high_priority))
        if medium_priority:
            plan.append("Phase 2 (Short-term): " + ", ".join(medium_priority))
        if low_priority:
            plan.append("Phase 3 (Long-term): " + ", ".join(low_priority))
        
        return plan


__all__ = [
    "SEOStrategyAgent",
    "SEOStrategy",
    "SEOMetadata",
    "GitHubOptimization",
    "AudienceAdaptation",
]