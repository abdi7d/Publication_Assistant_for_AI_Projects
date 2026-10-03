# agents/intelligent_content_improver.py
"""
Intelligent Content Improver Agent with chain-of-thought reasoning.
Repository-aware content generation with adaptive complexity and context understanding.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import logging
import re
from tools.web_search import WebSearchTool
from tools.rag_retriever import RAGRetriever
from tools.repository_grounded_generator import RepositoryGroundedGenerator, RepositoryEvidence

logger = logging.getLogger(__name__)


@dataclass
class ContentPlan:
    """Plan for content generation based on repository analysis."""
    target_audience: str
    technical_depth: str
    section_structure: List[str]
    key_topics: List[str]
    content_strategy: str
    complexity_level: str


@dataclass
class ReasoningChain:
    """Chain of thought reasoning for content generation."""
    analysis_steps: List[str]
    decisions: List[str]
    evidence_used: List[str]
    confidence_scores: Dict[str, float]
    reasoning_summary: str


@dataclass
class ContentImprovement:
    """Improved content with reasoning metadata."""
    improved_readme: str
    suggested_images: Dict[str, str]
    content_plan: ContentPlan
    reasoning_chain: ReasoningChain
    repository_references: List[str]
    confidence_score: float


class IntelligentContentImproverAgent:
    """
    Repository-aware content generation with reasoning.
    Uses chain-of-thought to determine appropriate content strategy
    and generates repository-specific documentation.
    """

    def __init__(self, web_search: Optional[WebSearchTool] = None, rag: Optional[RAGRetriever] = None):
        self.web_search = web_search
        self.rag = rag
        self.repo_grounded_generator = RepositoryGroundedGenerator()

    def run(self, readme: str, metadata: Any, repo_analysis: Any, 
            style: str = "Technical Blog", goal: str = "") -> ContentImprovement:
        """Generate improved content with reasoning."""
        logger.info("IntelligentContentImproverAgent: generating content with reasoning (Style: %s, Goal: %s)", style, goal)
        
        # Step 1: Analyze repository context
        repo_context = self._analyze_repository_context(repo_analysis)
        
        # Step 2: Generate content plan through reasoning
        content_plan = self._generate_content_plan(repo_context, style, goal, metadata)
        
        # Step 3: Build reasoning chain
        reasoning_chain = self._build_reasoning_chain(repo_context, content_plan, readme)
        
        # Step 4: Extract repository evidence
        repo_evidence = self.repo_grounded_generator.extract_evidence(
            repo_analysis.files if hasattr(repo_analysis, 'files') else {}, 
            repo_analysis
        )
        
        # Step 5: Generate content using plan and evidence
        improved_content = self._generate_intelligent_content(
            readme, content_plan, repo_evidence, repo_context, reasoning_chain
        )
        
        # Step 6: Gather external examples if available
        external_examples = []
        if self.web_search:
            try:
                external_examples = self.web_search.search_similar_repos(readme, top_k=3) or []
            except Exception:
                external_examples = []
        
        # Step 7: Gather RAG hints if available
        rag_hints = []
        if self.rag:
            try:
                rag_hints = self.rag.retrieve(readme) or []
            except Exception:
                rag_hints = []
        
        # Enhance content with external insights
        if external_examples or rag_hints:
            improved_content = self._enhance_with_external_insights(
                improved_content, external_examples, rag_hints
            )
        
        # Generate image suggestions
        image_suggestions = self._generate_image_suggestions(repo_context, content_plan)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            reasoning_chain, repo_evidence, improved_content
        )
        
        # Extract repository references
        repo_references = self._extract_repository_references(improved_content, repo_evidence)
        
        return ContentImprovement(
            improved_readme=improved_content,
            suggested_images=image_suggestions,
            content_plan=content_plan,
            reasoning_chain=reasoning_chain,
            repository_references=repo_references,
            confidence_score=confidence_score,
        )

    def _analyze_repository_context(self, repo_analysis: Any) -> Dict[str, Any]:
        """Analyze repository to understand context and characteristics."""
        context = {
            "complexity": "medium",
            "maturity": "growing",
            "domain": "software",
            "has_tests": False,
            "has_ci_cd": False,
            "has_documentation": False,
            "primary_language": "Python",
            "architecture": "monolithic",
            "api_present": False,
            "database_present": False,
        }
        
        # Analyze from repo_analysis if available
        if hasattr(repo_analysis, 'code_stats'):
            stats = repo_analysis.code_stats
            context["primary_language"] = stats.get("primary_language", "Python")
            context["file_count"] = stats.get("file_count", 0)
            
            # Determine complexity based on file count and structure
            if stats.get("file_count", 0) > 50:
                context["complexity"] = "high"
            elif stats.get("file_count", 0) > 20:
                context["complexity"] = "medium"
            else:
                context["complexity"] = "low"
        
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            context["architecture"] = arch.architectural_style
            context["design_patterns"] = arch.design_patterns
            context["api_present"] = len(arch.api_endpoints) > 0 if hasattr(arch, 'api_endpoints') else False
        
        if hasattr(repo_analysis, 'code_quality'):
            quality = repo_analysis.code_quality
            context["has_tests"] = quality.test_coverage_estimate > 0
            context["documentation_completeness"] = quality.documentation_completeness
        
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            context["frameworks"] = stack.get("frameworks", [])
            context["databases"] = stack.get("databases", [])
            context["database_present"] = len(stack.get("databases", [])) > 0
        
        if hasattr(repo_analysis, 'deployment_indicators'):
            context["has_ci_cd"] = len(repo_analysis.deployment_indicators) > 0
        
        return context

    def _generate_content_plan(self, repo_context: Dict[str, Any], style: str, 
                             goal: str, metadata: Any) -> ContentPlan:
        """Generate content plan through reasoning about repository and goals."""
        
        # Determine target audience based on repository characteristics
        if repo_context["complexity"] == "high":
            target_audience = "experienced developers"
            technical_depth = "advanced"
        elif repo_context["complexity"] == "medium":
            target_audience = "intermediate developers"
            technical_depth = "intermediate"
        else:
            target_audience = "beginner developers"
            technical_depth = "beginner"
        
        # Adjust based on style
        if style == "Research Paper":
            target_audience = "researchers and academics"
            technical_depth = "advanced"
        elif style == "Tutorial":
            target_audience = "learners and beginners"
            technical_depth = "beginner"
        elif style == "Marketing":
            target_audience = "technical decision makers"
            technical_depth = "intermediate"
        
        # Determine section structure based on repository type
        section_structure = self._determine_section_structure(repo_context, style)
        
        # Extract key topics from repository
        key_topics = self._extract_key_topics(repo_context, metadata)
        
        # Determine content strategy
        content_strategy = self._determine_content_strategy(repo_context, goal, style)
        
        return ContentPlan(
            target_audience=target_audience,
            technical_depth=technical_depth,
            section_structure=section_structure,
            key_topics=key_topics,
            content_strategy=content_strategy,
            complexity_level=repo_context["complexity"],
        )

    def _determine_section_structure(self, repo_context: Dict[str, Any], style: str) -> List[str]:
        """Determine appropriate sections based on repository and style."""
        base_sections = [
            "Overview",
            "Features",
            "Installation",
            "Usage",
        ]
        
        # Add repository-specific sections
        if repo_context.get("api_present"):
            base_sections.append("API Reference")
        
        if repo_context.get("database_present"):
            base_sections.append("Database Schema")
        
        if repo_context.get("architecture") != "monolithic":
            base_sections.append("Architecture")
        
        if repo_context.get("has_tests"):
            base_sections.append("Testing")
        
        if repo_context.get("has_ci_cd"):
            base_sections.append("Deployment")
        
        # Add style-specific sections
        if style == "Research Paper":
            base_sections.extend(["Methodology", "Experiments", "Results"])
        elif style == "Documentation":
            base_sections.extend(["Configuration", "Troubleshooting", "Contributing"])
        elif style == "Technical Blog":
            base_sections.extend(["How it Works", "Use Cases", "Performance"])
        
        return base_sections

    def _extract_key_topics(self, repo_context: Dict[str, Any], metadata: Any) -> List[str]:
        """Extract key topics from repository context and metadata."""
        topics = []
        
        # From repository context
        if "frameworks" in repo_context:
            topics.extend(repo_context["frameworks"])
        
        if "databases" in repo_context:
            topics.extend(repo_context["databases"])
        
        # From metadata
        if hasattr(metadata, 'tags'):
            topics.extend(metadata.tags[:5])
        
        # From architecture
        if "design_patterns" in repo_context:
            topics.extend(repo_context["design_patterns"][:3])
        
        return list(set(topics))

    def _determine_content_strategy(self, repo_context: Dict[str, Any], goal: str, style: str) -> str:
        """Determine overall content strategy."""
        strategies = []
        
        if repo_context["complexity"] == "high":
            strategies.append("comprehensive")
        else:
            strategies.append("concise")
        
        if repo_context.get("has_tests"):
            strategies.append("quality-focused")
        
        if goal:
            strategies.append(f"goal-oriented: {goal}")
        
        if style == "Tutorial":
            strategies.append("learning-focused")
        elif style == "Research Paper":
            strategies.append("academic")
        
        return ", ".join(strategies)

    def _build_reasoning_chain(self, repo_context: Dict[str, Any], content_plan: ContentPlan, 
                            original_readme: str) -> ReasoningChain:
        """Build chain of thought reasoning for content generation."""
        analysis_steps = []
        decisions = []
        evidence_used = []
        confidence_scores = {}
        
        # Step 1: Analyze original README
        analysis_steps.append(f"Original README length: {len(original_readme)} characters")
        if len(original_readme) > 2000:
            analysis_steps.append("Original README is comprehensive - will enhance rather than replace")
            decisions.append("Enhancement strategy: improve existing content")
            confidence_scores["enhancement_strategy"] = 0.85
        else:
            analysis_steps.append("Original README is brief - will expand significantly")
            decisions.append("Enhancement strategy: comprehensive expansion")
            confidence_scores["enhancement_strategy"] = 0.90
        
        # Step 2: Analyze repository complexity
        analysis_steps.append(f"Repository complexity: {repo_context['complexity']}")
        if repo_context["complexity"] == "high":
            decisions.append("Include advanced technical details and architecture explanations")
            evidence_used.append("File count and structure indicate high complexity")
            confidence_scores["technical_depth"] = 0.80
        else:
            decisions.append("Focus on clear, accessible explanations")
            evidence_used.append("Simpler repository structure detected")
            confidence_scores["technical_depth"] = 0.85
        
        # Step 3: Determine audience approach
        analysis_steps.append(f"Target audience: {content_plan.target_audience}")
        decisions.append(f"Tailor content for {content_plan.target_audience}")
        evidence_used.append(f"Repository complexity and style indicate {content_plan.target_audience} audience")
        confidence_scores["audience_targeting"] = 0.75
        
        # Step 4: Section structure reasoning
        analysis_steps.append(f"Selected {len(content_plan.section_structure)} sections")
        decisions.append(f"Section structure: {', '.join(content_plan.section_structure[:5])}")
        evidence_used.append("Repository capabilities drive section selection")
        confidence_scores["section_structure"] = 0.80
        
        reasoning_summary = (
            f"Based on repository analysis (complexity: {repo_context['complexity']}, "
            f"architecture: {repo_context.get('architecture', 'unknown')}), "
            f"generating content for {content_plan.target_audience} with {content_plan.technical_depth} "
            f"technical depth using {content_plan.content_strategy} strategy."
        )
        
        return ReasoningChain(
            analysis_steps=analysis_steps,
            decisions=decisions,
            evidence_used=evidence_used,
            confidence_scores=confidence_scores,
            reasoning_summary=reasoning_summary,
        )

    def _generate_intelligent_content(self, original_readme: str, content_plan: ContentPlan,
                                     repo_evidence: RepositoryEvidence, repo_context: Dict[str, Any],
                                     reasoning_chain: ReasoningChain) -> str:
        """Generate intelligent content based on plan and evidence."""
        
        # Start with original content if it exists
        if original_readme:
            content = original_readme
        else:
            content = ""
        
        # Enhance each section according to plan
        for section in content_plan.section_structure:
            section_content = self._generate_section_content(
                section, repo_evidence, repo_context, content_plan
            )
            
            # Add section if not present or enhance existing
            section_header = f"## {section}"
            if section_header not in content:
                content += f"\n\n{section_header}\n\n{section_content}"
            else:
                # Enhance existing section
                content = self._enhance_existing_section(content, section, section_content)
        
        # Add repository-specific enhancements
        content = self._add_repository_specific_content(content, repo_evidence, repo_context)
        
        return content

    def _generate_section_content(self, section: str, repo_evidence: RepositoryEvidence,
                                 repo_context: Dict[str, Any], content_plan: ContentPlan) -> str:
        """Generate content for a specific section."""
        
        # Use repository grounded generator for factual sections
        grounded_content = self.repo_grounded_generator.generate_repository_specific_content(
            section, repo_evidence, repo_context
        )
        
        if grounded_content and not grounded_content.startswith("## Generic"):
            return grounded_content
        
        # Generate intelligent fallback content
        if section == "Overview":
            return self._generate_overview_section(repo_context, content_plan)
        elif section == "Features":
            return self._generate_features_section(repo_context, repo_evidence)
        elif section == "Architecture":
            return self._generate_architecture_section(repo_context, repo_evidence)
        else:
            return self._generate_generic_section(section, repo_context, content_plan)

    def _generate_overview_section(self, repo_context: Dict[str, Any], content_plan: ContentPlan) -> str:
        """Generate overview section based on repository context."""
        lines = ["## Overview", ""]
        
        # Describe the project based on context
        if repo_context.get("frameworks"):
            lines.append(f"This project is built using {', '.join(repo_context['frameworks'])}.")
            lines.append("")
        
        if repo_context["architecture"] != "monolithic":
            lines.append(f"The system follows a {repo_context['architecture']} architecture pattern.")
            lines.append("")
        
        # Describe target audience
        lines.append(f"Designed for {content_plan.target_audience}, this project provides "
                    f"{content_plan.technical_depth} level functionality.")
        lines.append("")
        
        return "\n".join(lines)

    def _generate_features_section(self, repo_context: Dict[str, Any], repo_evidence: RepositoryEvidence) -> str:
        """Generate features section based on repository evidence."""
        lines = ["## Features", ""]
        
        # Extract features from repository evidence
        if repo_evidence.class_definitions:
            lines.append("### Core Components")
            lines.append("")
            for cls in repo_evidence.class_definitions[:5]:
                lines.append(f"- **{cls}**: Core functionality component")
            lines.append("")
        
        if repo_evidence.api_endpoints:
            lines.append("### API Capabilities")
            lines.append("")
            lines.append(f"- {len(repo_evidence.api_endpoints)} REST API endpoints")
            lines.append("- Structured request/response handling")
            lines.append("")
        
        if repo_context.get("has_tests"):
            lines.append("### Quality Assurance")
            lines.append("")
            lines.append("- Comprehensive test coverage")
            lines.append("- Automated testing pipeline")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_architecture_section(self, repo_context: Dict[str, Any], repo_evidence: RepositoryEvidence) -> str:
        """Generate architecture section based on repository evidence."""
        lines = ["## Architecture", ""]
        
        lines.append(f"The project follows a {repo_context['architecture']} architecture pattern.")
        lines.append("")
        
        if repo_evidence.class_definitions:
            lines.append("### Component Structure")
            lines.append("")
            lines.append("The system is composed of the following key components:")
            lines.append("")
            for cls in repo_evidence.class_definitions[:8]:
                lines.append(f"- `{cls}`")
            lines.append("")
        
        if repo_context.get("design_patterns"):
            lines.append("### Design Patterns")
            lines.append("")
            for pattern in repo_context["design_patterns"]:
                lines.append(f"- {pattern}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_generic_section(self, section: str, repo_context: Dict[str, Any], 
                                content_plan: ContentPlan) -> str:
        """Generate generic section content."""
        return f"## {section}\n\nThis section contains details about {section.lower()} " \
               f"tailored for {content_plan.target_audience}."

    def _enhance_existing_section(self, content: str, section: str, new_content: str) -> str:
        """Enhance existing section with new content."""
        section_pattern = f"## {section}"
        if section_pattern in content:
            # Find the section and append new content
            parts = content.split(section_pattern)
            if len(parts) > 1:
                # Insert new content after section header
                enhanced = parts[0] + section_pattern + "\n\n" + new_content + "\n\n" + parts[1]
                return enhanced
        return content

    def _add_repository_specific_content(self, content: str, repo_evidence: RepositoryEvidence,
                                       repo_context: Dict[str, Any]) -> str:
        """Add repository-specific enhancements."""
        
        # Add code examples if available
        if repo_evidence.code_examples:
            content += "\n\n## Code Examples\n\n"
            for desc, code in list(repo_evidence.code_examples.items())[:3]:
                content += f"### {desc}\n\n```python\n{code}\n```\n\n"
        
        # Add configuration details
        if repo_evidence.configuration_values:
            content += "\n\n## Configuration Details\n\n"
            for key, value in list(repo_evidence.configuration_values.items())[:5]:
                content += f"- `{key}`: {value}\n"
        
        return content

    def _enhance_with_external_insights(self, content: str, external_examples: List[str],
                                      rag_hints: List[str]) -> str:
        """Enhance content with external insights from web search and RAG."""
        
        if rag_hints:
            content += "\n\n## Best Practices\n\n"
            for hint in rag_hints[:5]:
                content += f"- {hint}\n"
        
        if external_examples:
            content += "\n\n## Similar Projects\n\n"
            for example in external_examples[:3]:
                content += f"- {example}\n"
        
        return content

    def _generate_image_suggestions(self, repo_context: Dict[str, Any], 
                                  content_plan: ContentPlan) -> Dict[str, str]:
        """Generate image suggestions based on repository characteristics."""
        suggestions = {}
        
        if repo_context["architecture"] != "monolithic":
            suggestions["architecture_diagram"] = "System architecture diagram showing component interactions"
        
        if repo_context.get("api_present"):
            suggestions["api_flow_diagram"] = "API request/response flow diagram"
        
        suggestions["screenshot"] = "Application interface screenshot"
        suggestions["logo"] = "Project logo or branding"
        
        return suggestions

    def _calculate_confidence_score(self, reasoning_chain: ReasoningChain,
                                   repo_evidence: RepositoryEvidence, content: str) -> float:
        """Calculate overall confidence score for generated content."""
        
        # Base confidence from reasoning chain
        reasoning_confidence = sum(reasoning_chain.confidence_scores.values()) / max(len(reasoning_chain.confidence_scores), 1)
        
        # Evidence confidence
        evidence_confidence = min(len(repo_evidence.file_evidence) / 10, 1.0)
        
        # Content length confidence
        content_confidence = min(len(content) / 5000, 1.0)
        
        # Weighted average
        overall_confidence = (reasoning_confidence * 0.4 + evidence_confidence * 0.4 + content_confidence * 0.2)
        
        return round(overall_confidence, 2)

    def _extract_repository_references(self, content: str, repo_evidence: RepositoryEvidence) -> List[str]:
        """Extract repository references from generated content."""
        references = []
        
        # Find references to classes, functions, files
        for cls in repo_evidence.class_definitions:
            if cls in content:
                references.append(f"Class: {cls}")
        
        for func in repo_evidence.function_signatures:
            if func in content:
                references.append(f"Function: {func}")
        
        for file_path in repo_evidence.file_evidence.keys():
            if file_path in content:
                references.append(f"File: {file_path}")
        
        return references[:20]  # Limit to top 20


__all__ = [
    "IntelligentContentImproverAgent",
    "ContentImprovement",
    "ContentPlan",
    "ReasoningChain",
]