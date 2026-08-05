# agents/adaptive_technical_writer.py
"""
Adaptive Technical Writer for audience-specific content adaptation.
Professional technical writing with style adaptation based on audience analysis.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class AudienceProfile:
    """Profile of the target audience."""
    expertise_level: str  # 'beginner', 'intermediate', 'advanced', 'expert'
    primary_use_case: str  # 'learning', 'development', 'production', 'research'
    technical_background: str  # 'minimal', 'basic', 'intermediate', 'advanced'
    time_availability: str  # 'quick', 'moderate', 'thorough'
    content_preferences: List[str]


@dataclass
class WritingStyle:
    """Writing style characteristics."""
    tone: str  # 'formal', 'conversational', 'academic', 'technical'
    complexity: str  # 'simple', 'moderate', 'complex'
    verbosity: str  # 'concise', 'balanced', 'detailed'
    terminology_level: str  # 'minimal', 'moderate', 'extensive'


@dataclass
class AdaptedContent:
    """Content adapted for specific audience."""
    content: str
    audience_profile: AudienceProfile
    writing_style: WritingStyle
    adaptation_notes: List[str]
    reading_level: str
    estimated_reading_time: int


class AdaptiveTechnicalWriter:
    """
    Professional technical writing with audience adaptation.
    Adjusts content complexity, terminology, and explanation depth
    based on audience analysis.
    """

    def __init__(self):
        self.terminology_cache = {}
        self.reading_level_cache = {}

    def assess_audience(self, repo_analysis: Any, metadata: Any) -> AudienceProfile:
        """Analyze repository to determine target audience profile."""
        logger.info("AdaptiveTechnicalWriter: assessing audience profile")
        
        # Analyze code complexity for expertise level
        expertise_level = self._determine_expertise_level(repo_analysis)
        
        # Determine primary use case from repository structure
        primary_use_case = self._determine_use_case(repo_analysis)
        
        # Assess technical background requirements
        technical_background = self._assess_technical_background(repo_analysis)
        
        # Determine time availability based on documentation depth
        time_availability = self._determine_time_availability(repo_analysis)
        
        # Identify content preferences
        content_preferences = self._determine_content_preferences(repo_analysis, metadata)
        
        return AudienceProfile(
            expertise_level=expertise_level,
            primary_use_case=primary_use_case,
            technical_background=technical_background,
            time_availability=time_availability,
            content_preferences=content_preferences,
        )

    def _determine_expertise_level(self, repo_analysis: Any) -> str:
        """Determine required expertise level from repository."""
        if hasattr(repo_analysis, 'code_quality'):
            quality = repo_analysis.code_quality
            if quality.maintainability_index < 50:
                return "expert"
            elif quality.maintainability_index < 70:
                return "advanced"
            elif quality.maintainability_index < 85:
                return "intermediate"
            else:
                return "beginner"
        
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            if arch.architectural_style in ["Microservices", "Event-Driven"]:
                return "advanced"
            elif len(arch.design_patterns) > 3:
                return "intermediate"
        
        return "intermediate"

    def _determine_use_case(self, repo_analysis: Any) -> str:
        """Determine primary use case from repository characteristics."""
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            if "ai_ml" in stack and stack["ai_ml"]:
                return "research"
            if "frameworks" in stack and any(fw in stack["frameworks"] for fw in ["FastAPI", "Django"]):
                return "production"
        
        if hasattr(repo_analysis, 'code_stats'):
            stats = repo_analysis.code_stats
            if "test" in stats.get("project_type", "").lower():
                return "development"
        
        return "development"

    def _assess_technical_background(self, repo_analysis: Any) -> str:
        """Assess required technical background."""
        if hasattr(repo_analysis, 'technology_stack'):
            stack = repo_analysis.technology_stack
            tech_count = sum(len(v) for v in stack.values())
            
            if tech_count > 10:
                return "advanced"
            elif tech_count > 5:
                return "intermediate"
            elif tech_count > 2:
                return "basic"
        
        return "intermediate"

    def _determine_time_availability(self, repo_analysis: Any) -> str:
        """Determine appropriate time availability for documentation."""
        if hasattr(repo_analysis, 'code_stats'):
            stats = repo_analysis.code_stats
            if stats.get("file_count", 0) > 50:
                return "thorough"
            elif stats.get("file_count", 0) > 20:
                return "moderate"
        
        return "moderate"

    def _determine_content_preferences(self, repo_analysis: Any, metadata: Any) -> List[str]:
        """Determine audience content preferences."""
        preferences = []
        
        if hasattr(repo_analysis, 'code_quality'):
            quality = repo_analysis.code_quality
            if quality.test_coverage_estimate > 50:
                preferences.append("detailed_testing_info")
            if quality.documentation_completeness > 70:
                preferences.append("comprehensive_documentation")
        
        if hasattr(repo_analysis, 'architecture'):
            arch = repo_analysis.architecture
            if arch.architectural_style != "monolithic":
                preferences.append("architecture_explanations")
            if arch.api_endpoints:
                preferences.append("api_documentation")
        
        if hasattr(metadata, 'tags'):
            tags = metadata.tags if hasattr(metadata, 'tags') else []
            if "tutorial" in [tag.lower() for tag in tags]:
                preferences.append("step_by_step_guides")
            if "reference" in [tag.lower() for tag in tags]:
                preferences.append("quick_reference")
        
        if not preferences:
            preferences = ["clear_explanations", "practical_examples"]
        
        return preferences

    def determine_writing_style(self, audience_profile: AudienceProfile, style: str = "Technical Blog") -> WritingStyle:
        """Determine appropriate writing style based on audience and desired style."""
        
        # Base style on requested style
        if style == "Research Paper":
            tone = "academic"
            complexity = "complex"
            verbosity = "detailed"
            terminology_level = "extensive"
        elif style == "Tutorial":
            tone = "conversational"
            complexity = "simple"
            verbosity = "detailed"
            terminology_level = "minimal"
        elif style == "Documentation":
            tone = "technical"
            complexity = "moderate"
            verbosity = "balanced"
            terminology_level = "moderate"
        elif style == "Marketing":
            tone = "conversational"
            complexity = "simple"
            verbosity = "concise"
            terminology_level = "minimal"
        else:  # Technical Blog
            tone = "conversational"
            complexity = "moderate"
            verbosity = "balanced"
            terminology_level = "moderate"
        
        # Adjust based on audience expertise
        if audience_profile.expertise_level == "expert":
            complexity = "complex"
            terminology_level = "extensive"
            verbosity = "concise"
        elif audience_profile.expertise_level == "beginner":
            complexity = "simple"
            terminology_level = "minimal"
            verbosity = "detailed"
        
        return WritingStyle(
            tone=tone,
            complexity=complexity,
            verbosity=verbosity,
            terminology_level=terminology_level,
        )

    def generate_content(self, section: str, audience: AudienceProfile, 
                        writing_style: WritingStyle, context: Dict[str, Any]) -> str:
        """Generate content adapted for specific audience and style."""
        
        # Get base content for the section
        base_content = self._get_base_content(section, context)
        
        # Adapt content based on writing style
        adapted_content = self._adapt_content_style(base_content, writing_style)
        
        # Adjust complexity based on audience
        audience_adapted = self._adapt_for_audience(adapted_content, audience)
        
        # Add audience-specific elements
        final_content = self._add_audience_elements(audience_adapted, audience, section)
        
        return final_content

    def _get_base_content(self, section: str, context: Dict[str, Any]) -> str:
        """Get base content for a section."""
        # This would typically use repository-grounded generator
        # For now, return section-specific base content
        base_contents = {
            "Overview": "This project provides core functionality for the intended use case.",
            "Installation": "Install the required dependencies and configure the environment.",
            "Usage": "Use the application by following these steps.",
            "Architecture": "The system is designed with modularity and scalability in mind.",
            "API": "The API provides endpoints for various operations.",
        }
        
        return base_contents.get(section, f"This section describes {section.lower()}.")

    def _adapt_content_style(self, content: str, writing_style: WritingStyle) -> str:
        """Adapt content based on writing style."""
        
        # Adapt tone
        if writing_style.tone == "formal":
            content = self._make_formal(content)
        elif writing_style.tone == "conversational":
            content = self._make_conversational(content)
        elif writing_style.tone == "academic":
            content = self._make_academic(content)
        
        # Adapt complexity
        if writing_style.complexity == "simple":
            content = self._simplify_language(content)
        elif writing_style.complexity == "complex":
            content = self._add_technical_depth(content)
        
        # Adapt verbosity
        if writing_style.verbosity == "concise":
            content = self._make_concise(content)
        elif writing_style.verbosity == "detailed":
            content = self._add_detail(content)
        
        return content

    def _make_formal(self, content: str) -> str:
        """Make content more formal."""
        replacements = {
            "use": "utilize",
            "help": "assist",
            "show": "demonstrate",
            "need": "require",
            "can": "is capable of",
        }
        
        for informal, formal in replacements.items():
            content = re.sub(rf'\b{informal}\b', formal, content, flags=re.IGNORECASE)
        
        return content

    def _make_conversational(self, content: str) -> str:
        """Make content more conversational."""
        content = re.sub(r'\.', '. You\'ll find that', content, count=1)
        content = re.sub(r'\. This', '. This means that', content)
        
        return content

    def _make_academic(self, str_content: str) -> str:
        """Make content more academic."""
        # Add formal language and citations style
        str_content = re.sub(r'\bshows?\b', 'demonstrates', str_content, flags=re.IGNORECASE)
        str_content = re.sub(r'\buses?\b', 'employs', str_content, flags=re.IGNORECASE)
        
        return str_content

    def _simplify_language(self, content: str) -> str:
        """Simplify language for broader accessibility."""
        simplifications = {
            "utilize": "use",
            "demonstrate": "show",
            "facilitate": "help",
            "consequently": "so",
            "fundamentally": "basically",
        }
        
        for complex, simple in simplifications.items():
            content = re.sub(rf'\b{complex}\b', simple, content, flags=re.IGNORECASE)
        
        return content

    def _add_technical_depth(self, content: str) -> str:
        """Add technical depth for expert audiences."""
        # Add technical elaboration
        content += "\n\n**Technical Implementation:** "
        content += "This functionality is implemented using industry-standard patterns "
        content += "and optimized for performance and scalability."
        
        return content

    def _make_concise(self, content: str) -> str:
        """Make content more concise."""
        # Remove redundant words
        content = re.sub(r'\b(very|really|quite)\s+', '', content)
        content = re.sub(r'\s+', ' ', content)
        
        return content

    def _add_detail(self, content: str) -> str:
        """Add more detail to content."""
        content += "\n\n**Additional Details:** "
        content += "This aspect includes comprehensive error handling, "
        content += "logging, and configuration options for various use cases."
        
        return content

    def _adapt_for_audience(self, content: str, audience: AudienceProfile) -> str:
        """Adapt content specifically for the audience profile."""
        
        if audience.expertise_level == "beginner":
            content = self._add_explanations(content)
        elif audience.expertise_level == "expert":
            content = self._add_technical_specifications(content)
        
        if audience.primary_use_case == "learning":
            content = self._add_learning_aids(content)
        elif audience.primary_use_case == "production":
            content = self._add_production_considerations(content)
        
        return content

    def _add_explanations(self, content: str) -> str:
        """Add explanatory content for beginners."""
        content += "\n\n**Note:** If you're new to this technology, "
        content += "consider reviewing the fundamentals before proceeding."
        
        return content

    def _add_technical_specifications(self, content: str) -> str:
        """Add technical specifications for experts."""
        content += "\n\n**Technical Specifications:** "
        content += "Refer to the API documentation for detailed parameter specifications "
        content += "and performance characteristics."
        
        return content

    def _add_learning_aids(self, content: str) -> str:
        """Add learning aids for educational use cases."""
        content += "\n\n**Learning Resources:** "
        content += "Practice with the provided examples to build understanding."
        
        return content

    def _add_production_considerations(self, content: str) -> str:
        """Add production considerations for production use cases."""
        content += "\n\n**Production Considerations:** "
        content += "Ensure proper monitoring, logging, and error handling "
        content += "are configured for production deployment."
        
        return content

    def _add_audience_elements(self, content: str, audience: AudienceProfile, section: str) -> str:
        """Add audience-specific elements to content."""
        
        # Add quick start for time-constrained audiences
        if audience.time_availability == "quick" and section == "Usage":
            content = self._add_quick_start(content)
        
        # Add deep dive for thorough audiences
        if audience.time_availability == "thorough" and section == "Architecture":
            content = self._add_deep_dive(content)
        
        return content

    def _add_quick_start(self, content: str) -> str:
        """Add quick start section for time-constrained audiences."""
        quick_start = "\n\n### Quick Start\n\n"
        quick_start += "Get started immediately with these essential steps:\n\n"
        quick_start += "1. Install dependencies\n"
        quick_start += "2. Configure environment\n"
        quick_start += "3. Run the application\n\n"
        
        return quick_start + content

    def _add_deep_dive(self, content: str) -> str:
        """Add deep dive section for thorough audiences."""
        deep_dive = "\n\n### Deep Dive\n\n"
        deep_dive += "For comprehensive understanding, explore these aspects:\n\n"
        deep_dive += "- Internal component interactions\n"
        deep_dive += "- Performance characteristics\n"
        deep_dive += "- Extension points and customization\n\n"
        
        return content + deep_dive

    def calculate_reading_level(self, content: str) -> str:
        """Calculate the reading level of content."""
        # Simplified reading level calculation
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        if not sentences or not words:
            return "intermediate"
        
        avg_words_per_sentence = len(words) / len(sentences)
        
        if avg_words_per_sentence < 15:
            return "beginner"
        elif avg_words_per_sentence < 20:
            return "intermediate"
        else:
            return "advanced"

    def estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes."""
        words = len(content.split())
        # Average reading speed: 200 words per minute
        reading_time = max(1, words // 200)
        return reading_time

    def adapt_full_documentation(self, content: str, audience: AudienceProfile, 
                                writing_style: WritingStyle) -> AdaptedContent:
        """Adapt full documentation for audience."""
        logger.info("AdaptiveTechnicalWriter: adapting full documentation")
        
        # Split content into sections
        sections = self._split_into_sections(content)
        
        # Adapt each section
        adapted_sections = {}
        adaptation_notes = []
        
        for section_name, section_content in sections.items():
            adapted = self.generate_content(section_name, audience, writing_style, {})
            adapted_sections[section_name] = adapted
            
            # Track adaptations
            if len(adapted) > len(section_content) * 1.5:
                adaptation_notes.append(f"Expanded {section_name} for clarity")
            elif len(adapted) < len(section_content) * 0.7:
                adaptation_notes.append(f"Condensed {section_name} for conciseness")
        
        # Reassemble document
        adapted_content = "\n\n".join(adapted_sections.values())
        
        # Calculate metrics
        reading_level = self.calculate_reading_level(adapted_content)
        reading_time = self.estimate_reading_time(adapted_content)
        
        return AdaptedContent(
            content=adapted_content,
            audience_profile=audience,
            writing_style=writing_style,
            adaptation_notes=adaptation_notes,
            reading_level=reading_level,
            estimated_reading_time=reading_time,
        )

    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """Split content into sections based on headers."""
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('##'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.replace('##', '').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections


__all__ = [
    "AdaptiveTechnicalWriter",
    "AudienceProfile",
    "WritingStyle",
    "AdaptedContent",
]