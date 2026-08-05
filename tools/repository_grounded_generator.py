# tools/repository_grounded_generator.py
"""
Repository Grounded Generator for evidence-based content generation.
Ensures all generated content is strictly grounded in repository evidence.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RepositoryEvidence:
    """Evidence extracted from repository for content grounding."""
    file_evidence: Dict[str, str]  # File paths to relevant content
    code_examples: Dict[str, str]  # Descriptions to actual code examples
    configuration_values: Dict[str, Any]  # Config keys to actual values
    api_endpoints: List[Dict[str, str]]  # API endpoints with details
    import_statements: List[str]  # Actual imports found
    class_definitions: List[str]  # Actual class names
    function_signatures: List[str]  # Actual function signatures
    documentation_snippets: List[str]  # Actual docstrings/comments


@dataclass
class GroundedClaim:
    """A claim grounded in repository evidence."""
    claim: str
    evidence_sources: List[str]  # Files/lines supporting the claim
    confidence: float  # 0.0 to 1.0
    evidence_type: str  # 'code', 'config', 'documentation', 'inference'


@dataclass
class ValidationResult:
    """Result of content validation against repository."""
    is_valid: bool
    grounded_claims: List[GroundedClaim]
    ungrounded_claims: List[str]
    missing_evidence: List[str]
    confidence_score: float
    validation_details: Dict[str, Any]


class RepositoryGroundedGenerator:
    """
    Generate content strictly grounded in repository evidence.
    Prevents hallucinations by ensuring all claims are supported
    by actual repository content.
    """

    def __init__(self):
        self.evidence_cache = {}

    def extract_evidence(self, files: Dict[str, str], repo_analysis: Any) -> RepositoryEvidence:
        """Extract comprehensive evidence from repository."""
        logger.info("RepositoryGroundedGenerator: extracting evidence from repository")
        
        evidence = RepositoryEvidence(
            file_evidence={},
            code_examples={},
            configuration_values={},
            api_endpoints=[],
            import_statements=[],
            class_definitions=[],
            function_signatures=[],
            documentation_snippets=[],
        )
        
        # Extract code examples by file type
        for filepath, content in files.items():
            if filepath.endswith('.py'):
                self._extract_python_evidence(filepath, content, evidence)
            elif filepath.endswith('.json') or filepath.endswith('.yaml') or filepath.endswith('.yml'):
                self._extract_config_evidence(filepath, content, evidence)
            elif 'readme' in filepath.lower():
                self._extract_documentation_evidence(content, evidence)
        
        # Extract API endpoints if available
        if hasattr(repo_analysis, 'api_endpoints'):
            evidence.api_endpoints = [
                {"endpoint": endpoint, "source": "code_analysis"}
                for endpoint in repo_analysis.api_endpoints
            ]
        
        logger.info("RepositoryGroundedGenerator: extracted %d code examples, %d configurations", 
                   len(evidence.code_examples), len(evidence.configuration_values))
        
        return evidence

    def _extract_python_evidence(self, filepath: str, content: str, evidence: RepositoryEvidence):
        """Extract evidence from Python files."""
        # Store file content for reference
        evidence.file_evidence[filepath] = content
        
        # Extract imports
        imports = re.findall(r'^import\s+([^\n]+)|^from\s+([^\s]+)\s+import', content, re.MULTILINE)
        for import_match in imports:
            import_stmt = import_match[0] if import_match[0] else import_match[1]
            if import_stmt and import_stmt not in evidence.import_statements:
                evidence.import_statements.append(import_stmt)
        
        # Extract class definitions
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        evidence.class_definitions.extend(classes)
        
        # Extract function signatures
        functions = re.findall(r'^def\s+(\w+)\s*\([^)]*\)', content, re.MULTILINE)
        evidence.function_signatures.extend(functions)
        
        # Extract docstrings and comments
        docstrings = re.findall(r'"""([^"]+)"""', content, re.DOTALL)
        evidence.documentation_snippets.extend(docstrings)
        
        # Extract code examples (main blocks, if __name__ guards)
        main_blocks = re.findall(r'if __name__\s*==\s*["\']__main__["\']:\s*(.+?)(?=\n\n|\Z)', content, re.DOTALL)
        for i, block in enumerate(main_blocks):
            evidence.code_examples[f"main_block_{i}_{filepath}"] = block.strip()

    def _extract_config_evidence(self, filepath: str, content: str, evidence: RepositoryEvidence):
        """Extract evidence from configuration files."""
        evidence.file_evidence[filepath] = content
        
        # Extract key-value pairs from simple configs
        if filepath.endswith('.json'):
            try:
                import json
                config = json.loads(content)
                if isinstance(config, dict):
                    for key, value in config.items():
                        evidence.configuration_values[f"{filepath}:{key}"] = value
            except:
                pass
        elif filepath.endswith(('.yaml', '.yml')):
            try:
                import yaml
                config = yaml.safe_load(content)
                if isinstance(config, dict):
                    for key, value in config.items():
                        evidence.configuration_values[f"{filepath}:{key}"] = value
            except:
                pass

    def _extract_documentation_evidence(self, content: str, evidence: RepositoryEvidence):
        """Extract evidence from documentation files."""
        # Extract code blocks from markdown
        code_blocks = re.findall(r'```(\w+)?\n(.+?)```', content, re.DOTALL)
        for lang, code in code_blocks:
            evidence.code_examples[f"documentation_{lang}"] = code.strip()
        
        # Extract configuration examples
        config_examples = re.findall(r'```[bB]ash\n(.+?)```', content, re.DOTALL)
        for i, example in enumerate(config_examples):
            evidence.code_examples[f"config_example_{i}"] = example.strip()

    def generate_claim(self, claim_type: str, evidence: RepositoryEvidence, context: str = "") -> GroundedClaim:
        """Generate a claim grounded in repository evidence."""
        
        if claim_type == "has_fastapi":
            if any('fastapi' in imp.lower() for imp in evidence.import_statements):
                return GroundedClaim(
                    claim="The project uses FastAPI as its web framework",
                    evidence_sources=[imp for imp in evidence.import_statements if 'fastapi' in imp.lower()],
                    confidence=0.95,
                    evidence_type="code"
                )
        
        elif claim_type == "has_database":
            db_imports = [imp for imp in evidence.import_statements 
                         if any(db in imp.lower() for db in ['sqlalchemy', 'psycopg', 'pymongo', 'redis'])]
            if db_imports:
                return GroundedClaim(
                    claim=f"The project uses database integration: {', '.join(db_imports)}",
                    evidence_sources=db_imports,
                    confidence=0.90,
                    evidence_type="code"
                )
        
        elif claim_type == "has_authentication":
            auth_imports = [imp for imp in evidence.import_statements 
                           if any(auth in imp.lower() for auth in ['jwt', 'oauth', 'auth', 'security'])]
            if auth_imports:
                return GroundedClaim(
                    claim="The project implements authentication mechanisms",
                    evidence_sources=auth_imports,
                    confidence=0.85,
                    evidence_type="code"
                )
        
        elif claim_type == "has_testing":
            test_imports = [imp for imp in evidence.import_statements 
                          if any(test in imp.lower() for test in ['pytest', 'unittest', 'test'])]
            if test_imports:
                return GroundedClaim(
                    claim="The project includes testing infrastructure",
                    evidence_sources=test_imports,
                    confidence=0.90,
                    evidence_type="code"
                )
        
        elif claim_type == "has_async":
            if any('async' in func.lower() for func in evidence.function_signatures):
                async_funcs = [func for func in evidence.function_signatures if 'async' in func.lower()]
                return GroundedClaim(
                    claim=f"The project uses async patterns with {len(async_funcs)} async functions",
                    evidence_sources=async_funcs[:5],
                    confidence=0.95,
                    evidence_type="code"
                )
        
        # Default: low confidence inference claim
        return GroundedClaim(
            claim=f"Based on analysis, the project appears to include {claim_type}",
            evidence_sources=[],
            confidence=0.30,
            evidence_type="inference"
        )

    def validate_content(self, content: str, evidence: RepositoryEvidence) -> ValidationResult:
        """Validate content against repository evidence."""
        logger.info("RepositoryGroundedGenerator: validating content against repository evidence")
        
        grounded_claims = []
        ungrounded_claims = []
        missing_evidence = []
        
        # Extract claims from content
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Check if sentence makes a factual claim
            if self._is_factual_claim(sentence):
                validation = self._validate_claim(sentence, evidence)
                if validation.is_grounded:
                    grounded_claims.append(validation)
                else:
                    ungrounded_claims.append(sentence)
                    if validation.missing_evidence:
                        missing_evidence.extend(validation.missing_evidence)
        
        # Calculate overall confidence
        total_claims = len(grounded_claims) + len(ungrounded_claims)
        confidence_score = sum(claim.confidence for claim in grounded_claims) / max(total_claims, 1) if total_claims > 0 else 0.0
        
        is_valid = confidence_score >= 0.7 and len(ungrounded_claims) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            grounded_claims=grounded_claims,
            ungrounded_claims=ungrounded_claims,
            missing_evidence=missing_evidence,
            confidence_score=confidence_score,
            validation_details={
                "total_claims": total_claims,
                "grounded_count": len(grounded_claims),
                "ungrounded_count": len(ungrounded_claims),
                "evidence_sources": len(evidence.file_evidence),
            }
        )

    def _is_factual_claim(self, sentence: str) -> bool:
        """Determine if a sentence makes a factual claim."""
        factual_indicators = [
            'uses', 'implements', 'provides', 'supports', 'includes',
            'features', 'offers', 'enables', 'allows', 'integrates',
            'built with', 'powered by', 'based on', 'leverages'
        ]
        return any(indicator in sentence.lower() for indicator in factual_indicators)

    def _validate_claim(self, claim: str, evidence: RepositoryEvidence) -> GroundedClaim:
        """Validate a single claim against evidence."""
        claim_lower = claim.lower()
        
        # Check against imports
        for imp in evidence.import_statements:
            if imp.lower() in claim_lower:
                return GroundedClaim(
                    claim=claim,
                    evidence_sources=[f"Import: {imp}"],
                    confidence=0.85,
                    evidence_type="code"
                )
        
        # Check against class definitions
        for cls in evidence.class_definitions:
            if cls.lower() in claim_lower:
                return GroundedClaim(
                    claim=claim,
                    evidence_sources=[f"Class definition: {cls}"],
                    confidence=0.80,
                    evidence_type="code"
                )
        
        # Check against function signatures
        for func in evidence.function_signatures:
            if func.lower() in claim_lower:
                return GroundedClaim(
                    claim=claim,
                    evidence_sources=[f"Function: {func}"],
                    confidence=0.75,
                    evidence_type="code"
                )
        
        # Check against configuration
        for config_key, config_value in evidence.configuration_values.items():
            if str(config_key).lower() in claim_lower:
                return GroundedClaim(
                    claim=claim,
                    evidence_sources=[f"Configuration: {config_key}"],
                    confidence=0.70,
                    evidence_type="config"
                )
        
        # Check against API endpoints
        for endpoint in evidence.api_endpoints:
            if endpoint.get('endpoint', '').lower() in claim_lower:
                return GroundedClaim(
                    claim=claim,
                    evidence_sources=[f"API endpoint: {endpoint['endpoint']}"],
                    confidence=0.85,
                    evidence_type="code"
                )
        
        # Claim not grounded
        return GroundedClaim(
            claim=claim,
            evidence_sources=[],
            confidence=0.0,
            evidence_type="none"
        )

    def generate_repository_specific_content(self, section: str, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate repository-specific content for a section."""
        
        if section == "installation":
            return self._generate_installation_section(evidence, context)
        elif section == "usage":
            return self._generate_usage_section(evidence, context)
        elif section == "configuration":
            return self._generate_configuration_section(evidence, context)
        elif section == "api":
            return self._generate_api_section(evidence, context)
        elif section == "architecture":
            return self._generate_architecture_section(evidence, context)
        else:
            return self._generate_generic_section(section, evidence, context)

    def _generate_installation_section(self, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate installation section based on actual dependencies."""
        lines = ["## Installation", ""]
        
        # Check for requirements.txt
        if any('requirements.txt' in file for file in evidence.file_evidence.keys()):
            lines.append("Install the required dependencies:")
            lines.append("```bash")
            lines.append("pip install -r requirements.txt")
            lines.append("```")
            lines.append("")
        
        # Check for setup.py or pyproject.toml
        if any('setup.py' in file or 'pyproject.toml' in file for file in evidence.file_evidence.keys()):
            lines.append("Alternatively, install in development mode:")
            lines.append("```bash")
            lines.append("pip install -e .")
            lines.append("```")
            lines.append("")
        
        # Mention specific dependencies if found
        if evidence.import_statements:
            core_deps = set()
            for imp in evidence.import_statements:
                if imp in ['fastapi', 'django', 'flask', 'langchain', 'torch']:
                    core_deps.add(imp.capitalize())
            
            if core_deps:
                lines.append(f"Core dependencies include: {', '.join(sorted(core_deps))}")
                lines.append("")
        
        return "\n".join(lines)

    def _generate_usage_section(self, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate usage section based on actual code examples."""
        lines = ["## Usage", ""]
        
        # Check for main blocks
        main_examples = [key for key in evidence.code_examples.keys() if 'main_block' in key]
        if main_examples:
            lines.append("Run the application:")
            lines.append("```bash")
            # Extract the actual command if available
            example_code = evidence.code_examples[main_examples[0]]
            commands = re.findall(r'(python\s+[\w\.]+|python\s+-m\s+\w+)', example_code)
            if commands:
                lines.append(commands[0])
            else:
                lines.append("python main.py")
            lines.append("```")
            lines.append("")
        
        # Check for API endpoints
        if evidence.api_endpoints:
            lines.append("### API Endpoints")
            lines.append("")
            lines.append("The following API endpoints are available:")
            lines.append("")
            for endpoint in evidence.api_endpoints[:5]:
                lines.append(f"- `{endpoint['endpoint']}`")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_configuration_section(self, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate configuration section based on actual config files."""
        lines = ["## Configuration", ""]
        
        if evidence.configuration_values:
            lines.append("The application can be configured through the following settings:")
            lines.append("")
            
            # Group by file
            config_by_file = {}
            for key, value in evidence.configuration_values.items():
                file = key.split(':')[0]
                config_by_file.setdefault(file, []).append((key, value))
            
            for file, configs in config_by_file.items():
                lines.append(f"### {file}")
                lines.append("")
                for key, value in configs[:10]:  # Limit to 10 per file
                    key_name = key.split(':')[-1]
                    lines.append(f"- `{key_name}`: {value}")
                lines.append("")
        
        # Check for environment variables
        env_files = [file for file in evidence.file_evidence.keys() if '.env' in file.lower()]
        if env_files:
            lines.append("### Environment Variables")
            lines.append("")
            lines.append("Create a `.env` file with the following variables:")
            lines.append("```bash")
            # Extract common env patterns
            for file in env_files:
                content = evidence.file_evidence[file]
                env_vars = re.findall(r'([A-Z_]+)=', content)
                for var in env_vars[:10]:
                    lines.append(f"{var}=your_value_here")
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_api_section(self, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate API section based on actual endpoints."""
        if not evidence.api_endpoints:
            return ""
        
        lines = ["## API Reference", ""]
        lines.append("The application provides the following API endpoints:")
        lines.append("")
        
        for endpoint in evidence.api_endpoints:
            lines.append(f"### {endpoint['endpoint']}")
            lines.append("")
            lines.append(f"**Source:** Code analysis")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_architecture_section(self, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate architecture section based on code structure."""
        lines = ["## Architecture", ""]
        
        # Analyze module structure
        modules = set()
        for file_path in evidence.file_evidence.keys():
            parts = Path(file_path).parts
            if len(parts) > 1:
                modules.add(parts[0])
        
        if modules:
            lines.append("The project is organized into the following modules:")
            lines.append("")
            for module in sorted(modules):
                lines.append(f"- `{module}/`")
            lines.append("")
        
        # Mention key classes
        if evidence.class_definitions:
            lines.append("### Key Components")
            lines.append("")
            lines.append("The following classes represent the core components:")
            lines.append("")
            for cls in evidence.class_definitions[:10]:
                lines.append(f"- `{cls}`")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_generic_section(self, section: str, evidence: RepositoryEvidence, context: Dict[str, Any]) -> str:
        """Generate a generic section when specific generation isn't available."""
        return f"## {section.capitalize()}\n\nContent for this section should be based on the specific repository structure and implementation details."


__all__ = [
    "RepositoryGroundedGenerator",
    "RepositoryEvidence",
    "GroundedClaim",
    "ValidationResult",
]