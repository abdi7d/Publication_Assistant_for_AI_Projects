# agents/repo_analyzer.py
from dataclasses import dataclass
from typing import Dict, Any, List
import logging
import os
import re

from tools.repo_parser import RepoParser

logger = logging.getLogger(__name__)


@dataclass
class RepoAnalysis:
    files: Dict[str, str]
    readme: str
    summary: str
    code_stats: Dict[str, Any]
    missing_sections: List[str]


class RepoAnalyzerAgent:
    """
    Agent that analyzes a repository structure (README, code, notebooks).
    Responsibilities:
      - Parse repo files
      - Extract README content, list files
      - Produce richer code metrics and project signals
      - Detect missing documentation sections
    """

    def __init__(self, repo_source: str, repo_parser: RepoParser):
        self.repo_source = repo_source
        self.parser = repo_parser

    def run(self) -> RepoAnalysis:
        logger.info("RepoAnalyzerAgent: parsing repository %s",
                    self.repo_source)
        parsed = self.parser.parse(self.repo_source)
        files = parsed.get("files", {})
        readme = parsed.get("README.md") or parsed.get("README") or ""
        code_stats = self._compute_code_stats(files)
        missing = self._detect_missing_sections(readme)
        summary = self._build_summary(readme, parsed, code_stats)

        analysis = RepoAnalysis(
            files=files,
            readme=readme,
            summary=summary,
            code_stats=code_stats,
            missing_sections=missing,
        )
        logger.debug("RepoAnalyzerAgent: analysis completed")
        return analysis

    def _compute_code_stats(self, files: Dict[str, str]) -> Dict[str, Any]:
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
