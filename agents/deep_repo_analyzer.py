# agents/deep_repo_analyzer.py
"""
Deep Repository Analyzer Agent with architectural analysis capabilities.
Provides comprehensive repository understanding beyond basic file counting.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set
import logging
import re
import ast
import os
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureAnalysis:
    """Architectural patterns and design decisions detected in repository."""
    design_patterns: List[str]
    architectural_style: str
    module_dependencies: Dict[str, List[str]]
    data_flow_patterns: List[str]
    architectural_decisions: List[str]
    component_hierarchy: Dict[str, List[str]]
    communication_patterns: List[str]
    api_endpoints: List[str]  # Added API endpoints to architecture analysis


@dataclass
class CodeQualityMetrics:
    """Code quality and maintainability metrics."""
    complexity_scores: Dict[str, float]
    code_smells: List[str]
    test_coverage_estimate: float
    documentation_completeness: float
    code_duplication: float
    naming_convention_score: float
    maintainability_index: float


@dataclass
class PatternLibrary:
    """Implementation patterns and best practices extracted from repository."""
    recurring_patterns: List[str]
    best_practices: List[str]
    framework_patterns: List[str]
    utility_functions: List[str]
    error_handling_patterns: List[str]
    configuration_patterns: List[str]


@dataclass
class DeepRepositoryAnalysis:
    """Comprehensive deep repository analysis."""
    files: Dict[str, str]
    readme: str
    summary: str
    code_stats: Dict[str, Any]
    missing_sections: List[str]
    architecture: ArchitectureAnalysis
    code_quality: CodeQualityMetrics
    patterns: PatternLibrary
    technology_stack: Dict[str, List[str]]
    api_endpoints: List[str]
    data_models: List[str]
    configuration_files: List[str]
    deployment_indicators: List[str]


class DeepRepositoryAnalyzerAgent:
    """
    Advanced repository understanding with architectural analysis.
    Goes beyond basic file counting to understand design patterns,
    code quality, and implementation characteristics.
    """

    def __init__(self, repo_source: str, repo_parser):
        self.repo_source = repo_source
        self.parser = repo_parser

    def run(self) -> DeepRepositoryAnalysis:
        """Run comprehensive deep repository analysis."""
        logger.info("DeepRepositoryAnalyzerAgent: performing deep analysis of %s", self.repo_source)
        
        parsed = self.parser.parse(self.repo_source)
        files = parsed.get("files", {})
        readme = parsed.get("README.md") or parsed.get("README") or ""
        
        # Basic analysis (from original agent)
        code_stats = self._compute_code_stats(files)
        missing = self._detect_missing_sections(readme)
        summary = self._build_summary(readme, parsed, code_stats)
        
        # Deep analysis (new capabilities)
        architecture = self._analyze_architecture(files)
        code_quality = self._analyze_code_quality(files)
        patterns = self._extract_patterns(files)
        tech_stack = self._analyze_technology_stack(files)
        api_endpoints = self._extract_api_endpoints(files)
        data_models = self._extract_data_models(files)
        config_files = self._identify_configuration_files(files)
        deployment_indicators = self._detect_deployment_indicators(files)
        
        analysis = DeepRepositoryAnalysis(
            files=files,
            readme=readme,
            summary=summary,
            code_stats=code_stats,
            missing_sections=missing,
            architecture=architecture,
            code_quality=code_quality,
            patterns=patterns,
            technology_stack=tech_stack,
            api_endpoints=api_endpoints,
            data_models=data_models,
            configuration_files=config_files,
            deployment_indicators=deployment_indicators,
        )
        
        logger.debug("DeepRepositoryAnalyzerAgent: deep analysis completed")
        return analysis

    def _analyze_architecture(self, files: Dict[str, str]) -> ArchitectureAnalysis:
        """Analyze architectural patterns and design decisions."""
        design_patterns = []
        architectural_style = "Monolithic"
        module_dependencies = defaultdict(list)
        data_flow_patterns = []
        architectural_decisions = []
        component_hierarchy = defaultdict(list)
        communication_patterns = []
        
        # Analyze directory structure for architectural hints
        dirs = set()
        for filepath in files.keys():
            parts = Path(filepath).parts
            if len(parts) > 1:
                dirs.add(parts[0])
        
        # Detect architectural style
        if "microservices" in dirs or "services" in dirs:
            architectural_style = "Microservices"
        elif "api" in dirs and "frontend" in dirs:
            architectural_style = "Client-Server"
        elif "agents" in dirs and "orchestration" in dirs:
            architectural_style = "Multi-Agent System"
        elif "layers" in dirs or any(x in dirs for x in ["controllers", "services", "repositories"]):
            architectural_style = "Layered Architecture"
        
        # Detect design patterns from code structure
        for filepath, content in files.items():
            if not filepath.endswith('.py'):
                continue
                
            # Singleton pattern detection
            if re.search(r'class\s+\w+.*:\s*_instance\s*=\s*None', content):
                design_patterns.append("Singleton")
            
            # Factory pattern detection
            if re.search(r'def\s+(create|make|build)\w*\s*\(', content):
                design_patterns.append("Factory")
            
            # Observer pattern detection
            if re.search(r'(subscribe|notify|observer|listener)', content, re.IGNORECASE):
                design_patterns.append("Observer")
            
            # Strategy pattern detection
            if re.search(r'(strategy|algorithm.*interface)', content, re.IGNORECASE):
                design_patterns.append("Strategy")
        
        # Analyze imports for module dependencies
        for filepath, content in files.items():
            if not filepath.endswith('.py'):
                continue
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name.split('.')[0]
                            if module_name in dirs:
                                module_dependencies[filepath].append(module_name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.split('.')[0]
                            if module_name in dirs:
                                module_dependencies[filepath].append(module_name)
            except:
                pass
        
        # Detect data flow patterns
        if any("pipeline" in f.lower() for f in files.keys()):
            data_flow_patterns.append("Pipeline")
        if any("stream" in f.lower() for f in files.keys()):
            data_flow_patterns.append("Stream Processing")
        if any("event" in f.lower() for f in files.keys()):
            data_flow_patterns.append("Event-Driven")
        
        # Extract architectural decisions from comments and documentation
        for content in files.values():
            decisions = re.findall(r'#\s*(TODO|FIXME|NOTE|HACK):\s*(.+)', content, re.IGNORECASE)
            architectural_decisions.extend([d[1] for d in decisions])
        
        # Build component hierarchy from directory structure
        for filepath in files.keys():
            parts = Path(filepath).parts
            if len(parts) > 1:
                parent = parts[0]
                child = "/".join(parts[1:])
                component_hierarchy[parent].append(child)
        
        # Detect communication patterns
        if any("api" in f.lower() or "rest" in f.lower() for f in files.keys()):
            communication_patterns.append("REST API")
        if any("graphql" in f.lower() for f in files.keys()):
            communication_patterns.append("GraphQL")
        if any("websocket" in f.lower() or "socket" in f.lower() for f in files.keys()):
            communication_patterns.append("WebSocket")
        if any("message" in f.lower() or "queue" in f.lower() for f in files.keys()):
            communication_patterns.append("Message Queue")
        
        # Extract API endpoints (if not already set in context)
        api_endpoints = []
        for filepath, content in files.items():
            if not filepath.endswith('.py'):
                continue
            
            # FastAPI endpoints
            fastapi_routes = re.findall(r'@.*\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']', content)
            for method, path in fastapi_routes:
                api_endpoints.append(f"{method.upper()} {path}")
            
            # Flask routes
            flask_routes = re.findall(r'@.*\.route\s*\(["\']([^"\']+)["\']', content)
            for path in flask_routes:
                api_endpoints.append(f"GET/POST {path}")
        
        return ArchitectureAnalysis(
            design_patterns=list(set(design_patterns)),
            architectural_style=architectural_style,
            module_dependencies=dict(module_dependencies),
            data_flow_patterns=data_flow_patterns,
            architectural_decisions=architectural_decisions[:10],  # Limit to top 10
            component_hierarchy=dict(component_hierarchy),
            communication_patterns=communication_patterns,
            api_endpoints=api_endpoints,
        )

    def _analyze_code_quality(self, files: Dict[str, str]) -> CodeQualityMetrics:
        """Analyze code quality metrics."""
        complexity_scores = {}
        code_smells = []
        py_files = {f: c for f, c in files.items() if f.endswith('.py')}
        
        total_complexity = 0
        file_count = len(py_files)
        
        for filepath, content in py_files.items():
            try:
                tree = ast.parse(content)
                complexity = self._calculate_cyclomatic_complexity(tree)
                complexity_scores[filepath] = complexity
                total_complexity += complexity
                
                # Detect code smells
                if complexity > 20:
                    code_smells.append(f"High complexity in {filepath}")
                
                # Long function detection
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if len(node.body) > 50:  # More than 50 lines
                            code_smells.append(f"Long function {node.name} in {filepath}")
                
            except:
                complexity_scores[filepath] = 0
        
        # Estimate test coverage
        test_files = [f for f in files.keys() if 'test' in f.lower()]
        test_coverage_estimate = min(len(test_files) / max(file_count, 1) * 100, 95) if file_count > 0 else 0
        
        # Documentation completeness
        documented_files = sum(1 for content in py_files.values() if '"""' in content or "'''" in content)
        documentation_completeness = documented_files / max(file_count, 1) * 100 if file_count > 0 else 0
        
        # Code duplication (simplified)
        code_lines = [line.strip() for content in py_files.values() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        line_counter = Counter(code_lines)
        duplicate_lines = sum(count for count in line_counter.values() if count > 1)
        code_duplication = duplicate_lines / max(len(code_lines), 1) * 100 if code_lines else 0
        
        # Naming convention score
        naming_violations = 0
        for filepath, content in py_files.items():
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                            naming_violations += 1
            except:
                pass
        total_functions = sum(len(re.findall(r'def\s+\w+', content)) for content in py_files.values())
        naming_convention_score = (1 - naming_violations / max(total_functions, 1)) * 100 if total_functions > 0 else 100
        
        # Maintainability index (simplified)
        avg_complexity = total_complexity / max(file_count, 1) if file_count > 0 else 0
        maintainability_index = max(0, 100 - avg_complexity - code_duplication/2 - naming_violations)
        
        return CodeQualityMetrics(
            complexity_scores=complexity_scores,
            code_smells=code_smells[:20],  # Limit to top 20
            test_coverage_estimate=test_coverage_estimate,
            documentation_completeness=documentation_completeness,
            code_duplication=code_duplication,
            naming_convention_score=naming_convention_score,
            maintainability_index=maintainability_index,
        )

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST."""
        complexity = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        return complexity

    def _extract_patterns(self, files: Dict[str, str]) -> PatternLibrary:
        """Extract implementation patterns and best practices."""
        recurring_patterns = []
        best_practices = []
        framework_patterns = []
        utility_functions = []
        error_handling_patterns = []
        configuration_patterns = []
        
        py_files = {f: c for f, c in files.items() if f.endswith('.py')}
        
        # Detect recurring patterns
        function_signatures = []
        for content in py_files.values():
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
            function_signatures.extend(functions)
        
        common_functions = [func for func, count in Counter(function_signatures).items() if count > 2]
        if common_functions:
            recurring_patterns.append(f"Common function patterns: {', '.join(common_functions[:5])}")
        
        # Detect best practices
        for content in py_files.values():
            if '__main__' in content:
                best_practices.append("Uses __main__ guard")
            if 'logging' in content:
                best_practices.append("Uses logging instead of print")
            if 'typing' in content:
                best_practices.append("Uses type hints")
            if 'try:' in content and 'except' in content:
                best_practices.append("Implements error handling")
        
        # Detect framework-specific patterns
        for filepath, content in py_files.items():
            if 'fastapi' in content.lower():
                framework_patterns.append("FastAPI dependency injection")
                if 'Depends' in content:
                    framework_patterns.append("FastAPI dependencies")
            if 'django' in content.lower():
                framework_patterns.append("Django models/views patterns")
            if 'langchain' in content.lower():
                framework_patterns.append("LangChain chain/prompt patterns")
        
        # Extract utility functions
        for filepath, content in py_files.items():
            if 'utils' in filepath.lower() or 'helper' in filepath.lower():
                functions = re.findall(r'def\s+(\w+)\s*\([^)]*\)', content)
                utility_functions.extend([f"{filepath}:{func}" for func in functions[:5]])
        
        # Detect error handling patterns
        for content in py_files.values():
            if 'raise ' in content:
                error_handling_patterns.append("Custom exceptions")
            if 'finally:' in content:
                error_handling_patterns.append("Cleanup with finally")
            if 'contextlib' in content or 'with ' in content:
                error_handling_patterns.append("Context managers")
        
        # Detect configuration patterns
        for filepath, content in files.items():
            if any(x in filepath.lower() for x in ['config', 'settings', 'env']):
                configuration_patterns.append(f"Configuration file: {filepath}")
            if 'os.environ' in content or 'getenv' in content:
                configuration_patterns.append("Environment variable usage")
        
        return PatternLibrary(
            recurring_patterns=list(set(recurring_patterns)),
            best_practices=list(set(best_practices)),
            framework_patterns=list(set(framework_patterns)),
            utility_functions=utility_functions[:10],
            error_handling_patterns=list(set(error_handling_patterns)),
            configuration_patterns=list(set(configuration_patterns)),
        )

    def _analyze_technology_stack(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """Analyze technology stack from dependencies and code."""
        stack = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "testing": [],
            "devops": [],
            "ai_ml": [],
        }
        
        # Analyze dependencies
        for filepath, content in files.items():
            if filepath.endswith('requirements.txt') or filepath.endswith('pyproject.toml'):
                if 'fastapi' in content.lower():
                    stack["frameworks"].append("FastAPI")
                if 'django' in content.lower():
                    stack["frameworks"].append("Django")
                if 'flask' in content.lower():
                    stack["frameworks"].append("Flask")
                if 'langchain' in content.lower():
                    stack["ai_ml"].append("LangChain")
                if 'langgraph' in content.lower():
                    stack["ai_ml"].append("LangGraph")
                if 'pytest' in content.lower():
                    stack["testing"].append("Pytest")
                if 'postgresql' in content.lower() or 'psycopg' in content.lower():
                    stack["databases"].append("PostgreSQL")
                if 'mongodb' in content.lower() or 'pymongo' in content.lower():
                    stack["databases"].append("MongoDB")
                if 'redis' in content.lower():
                    stack["databases"].append("Redis")
                if 'docker' in content.lower():
                    stack["devops"].append("Docker")
                if 'kubernetes' in content.lower() or 'k8s' in content.lower():
                    stack["devops"].append("Kubernetes")
        
        # Analyze code for additional insights
        py_content = "\n".join([c for f, c in files.items() if f.endswith('.py')])
        if 'import tensorflow' in py_content or 'import torch' in py_content:
            stack["ai_ml"].append("Deep Learning Framework")
        if 'sklearn' in py_content or 'pandas' in py_content:
            stack["ai_ml"].append("Data Science Stack")
        
        # Language detection from file extensions
        extensions = set(Path(f).suffix for f in files.keys())
        if '.py' in extensions:
            stack["languages"].append("Python")
        if '.js' in extensions or '.ts' in extensions:
            stack["languages"].append("JavaScript/TypeScript")
        if '.go' in extensions:
            stack["languages"].append("Go")
        if '.rs' in extensions:
            stack["languages"].append("Rust")
        
        return {k: list(set(v)) for k, v in stack.items()}

    def _extract_api_endpoints(self, files: Dict[str, str]) -> List[str]:
        """Extract API endpoints from code."""
        endpoints = []
        
        for filepath, content in files.items():
            if not filepath.endswith('.py'):
                continue
            
            # FastAPI endpoints
            fastapi_routes = re.findall(r'@.*\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']', content)
            for method, path in fastapi_routes:
                endpoints.append(f"{method.upper()} {path}")
            
            # Flask routes
            flask_routes = re.findall(r'@.*\.route\s*\(["\']([^"\']+)["\']', content)
            for path in flask_routes:
                endpoints.append(f"GET/POST {path}")
        
        return endpoints[:20]  # Limit to top 20

    def _extract_data_models(self, files: Dict[str, str]) -> List[str]:
        """Extract data models/schemas from code."""
        models = []
        
        for filepath, content in files.items():
            if not filepath.endswith('.py'):
                continue
            
            # Pydantic models
            pydantic_models = re.findall(r'class\s+(\w+)\s*\([^)]*BaseModel[^)]*\)', content)
            models.extend([f"Pydantic: {model}" for model in pydantic_models])
            
            # SQLAlchemy models
            sqlalchemy_models = re.findall(r'class\s+(\w+)\s*\([^)]*Base[^)]*\)', content)
            models.extend([f"SQLAlchemy: {model}" for model in sqlalchemy_models])
            
            # Dataclasses
            dataclass_models = re.findall(r'@dataclass\s+class\s+(\w+)', content)
            models.extend([f"Dataclass: {model}" for model in dataclass_models])
        
        return models[:15]  # Limit to top 15

    def _identify_configuration_files(self, files: Dict[str, str]) -> List[str]:
        """Identify configuration files."""
        config_patterns = ['config', 'settings', 'env', '.env', 'yaml', 'yml', 'toml', 'ini']
        return [f for f in files.keys() if any(pattern in f.lower() for pattern in config_patterns)]

    def _detect_deployment_indicators(self, files: Dict[str, str]) -> List[str]:
        """Detect deployment and DevOps indicators."""
        indicators = []
        
        for filepath in files.keys():
            if 'dockerfile' in filepath.lower():
                indicators.append("Docker support")
            if 'docker-compose' in filepath.lower():
                indicators.append("Docker Compose configuration")
            if 'kubernetes' in filepath.lower() or 'k8s' in filepath.lower():
                indicators.append("Kubernetes configuration")
            if '.github' in filepath or 'workflow' in filepath.lower():
                indicators.append("CI/CD workflows")
            if 'terraform' in filepath.lower():
                indicators.append("Terraform infrastructure")
            if 'helm' in filepath.lower():
                indicators.append("Helm charts")
        
        return list(set(indicators))

    def _compute_code_stats(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Compute basic code statistics (from original agent)."""
        languages: Dict[str, int] = {}
        total_lines = 0
        dependencies: List[str] = []
        entrypoints: List[str] = []

        for fname, content in files.items():
            total_lines += content.count("\n") + 1
            ext = os.path.splitext(fname)[1].lstrip(".") or "txt"
            languages[ext] = languages.get(ext, 0) + 1

            normalized_name = os.path.basename(fname).lower()
            if normalized_name in {"requirements.txt", "pyproject.toml", "setup.py", "package.json", "environment.yml"}:
                dependencies.extend(self._extract_dependencies(content))
            if normalized_name in {"app.py", "main.py", "server.py", "cli.py", "run.py", "manage.py"}:
                entrypoints.append(fname)
            if "if __name__ == '__main__'" in content or 'if __name__ == "__main__"' in content:
                entrypoints.append(fname)

        primary_language = max(languages.items(), key=lambda item: item[1])[
            0] if languages else "txt"
        return {
            "file_count": len(files),
            "languages": languages,
            "total_lines": total_lines,
            "primary_language": primary_language,
            "project_type": self._infer_project_type(files),
            "entrypoints": sorted(set(entrypoints)),
            "dependencies": sorted(set(dependencies)),
        }

    def _infer_project_type(self, files: Dict[str, str]) -> str:
        """Infer project type (from original agent)."""
        combined = "\n".join(files.values()).lower()
        if any(token in combined for token in ["fastapi", "uvicorn", "starlette", "pydantic"]):
            return "Python FastAPI service"
        if any(token in combined for token in ["flask", "django", "streamlit", "gradio"]):
            return "Python web application"
        if any(token in combined for token in ["langgraph", "langchain", "openai", "transformers"]):
            return "AI/LLM workflow project"
        if any(token in combined for token in ["jupyter", "notebook", "ipynb"]):
            return "Interactive notebook-based project"
        if any(token in combined for token in ["dockerfile", "docker", "compose"]):
            return "Containerized application"
        if any(token in combined for token in ["pytest", "unittest"]):
            return "Python software project"
        return "Software project"

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies (from original agent)."""
        deps = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("-", "[", "name=")):
                continue
            dep = re.split(r"[<>=!~\s]", line, maxsplit=1)[0]
            if dep and dep not in {"python"}:
                deps.append(dep)
        return deps

    def _build_summary(self, readme: str, parsed: Dict[str, Any], code_stats: Dict[str, Any]) -> str:
        """Build summary (from original agent)."""
        first_paragraph = ""
        for part in (p.strip() for p in readme.split("\n\n") if p.strip()):
            first_paragraph = part
            break
        if first_paragraph:
            summary = re.sub(r"\s+", " ", first_paragraph)
            if code_stats.get("project_type"):
                summary = f"{summary} | Project type: {code_stats['project_type']}"
            return summary
        return parsed.get("title", "Repository")

    def _detect_missing_sections(self, readme: str) -> List[str]:
        """Detect missing README sections (from original agent)."""
        required = ["Installation", "Usage", "License",
                    "Contributing", "Examples", "Architecture"]
        text = readme.lower()
        missing = []
        for section in required:
            key = section.lower()
            if key == "usage":
                patterns = ["usage", "how to use", "quick start", "run the"]
            elif key == "contributing":
                patterns = ["contributing", "contribute", "community"]
            elif key == "architecture":
                patterns = ["architecture", "design", "system overview"]
            else:
                patterns = [key]
            if not any(pattern in text for pattern in patterns):
                missing.append(section)
        return missing


__all__ = [
    "DeepRepositoryAnalyzerAgent",
    "DeepRepositoryAnalysis",
    "ArchitectureAnalysis",
    "CodeQualityMetrics",
    "PatternLibrary",
]