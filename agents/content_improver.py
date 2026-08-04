# agents/content_improver.py
from dataclasses import dataclass
from typing import Dict, Any
import logging
import re

from tools.web_search import WebSearchTool
from tools.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)


@dataclass
class ContentImprovement:
    improved_readme: str
    suggested_images: Dict[str, str]


class ContentImproverAgent:
    """
    Produces a polished README draft using web-search examples and RAG hints, with a deterministic fallback.
    """

    def __init__(self, web_search: WebSearchTool, rag: RAGRetriever):
        self.web_search = web_search
        self.rag = rag

    def run(self, readme: str, metadata: Dict[str, Any], style: str = "Technical Blog", goal: str = "") -> ContentImprovement:
        logger.info(
            "ContentImproverAgent: generating improved content (Style: %s, Goal: %s)", style, goal)

        examples = []
        rag_hints = []
        if self.web_search is not None:
            try:
                examples = self.web_search.search_similar_repos(
                    readme, top_k=3) or []
            except Exception:
                examples = []

        if self.rag is not None:
            try:
                rag_hints = self.rag.retrieve(readme) or []
            except Exception:
                rag_hints = []

        context_readme = readme + \
            "\n\n<!-- BEST PRACTICES SUGGESTIONS -->\n" + "\n".join(rag_hints)
        improved = self._try_generate(context_readme, examples, style, goal)
        if self._looks_like_error(improved):
            improved = self._build_fallback_readme(readme, metadata, rag_hints)

        suggestions = {
            "architecture_diagram": "Diagram showing data flow and primary system components.",
            "demo_screenshot": "CLI or UI usage example with clear sample output."
        }

        return ContentImprovement(improved_readme=improved, suggested_images=suggestions)

    def _try_generate(self, readme: str, examples: list, style: str, goal: str) -> str:
        if self.web_search is None:
            return ""
        try:
            improved = self.web_search.summarize_and_improve(
                readme, examples, style=style, goal=goal)
            return improved or ""
        except Exception:
            return ""

    def _looks_like_error(self, text: str) -> bool:
        if not text:
            return True
        lowered = text.lower()
        return any(marker in lowered for marker in ["error:", "empty response", "no valid", "not available"])

    def _build_fallback_readme(self, readme: str, metadata: Dict[str, Any], rag_hints: list) -> str:
        title = self._extract_title(readme) or "Project"
        summary = metadata.get(
            "short_description") or self._extract_summary(readme)
        tags = metadata.get("tags", []) if isinstance(metadata, dict) else []
        features = [f"Built around {tag}" for tag in tags[:4]] if tags else [
            "Well-structured implementation", "Clear onboarding path"]

        sections = [
            f"# {title}",
            "",
            f"{summary}" if summary else "A polished, publication-ready software project with clear structure and documentation.",
            "",
            "## ✨ What this project delivers",
            *[f"- {feature}" for feature in features],
            "- Guided setup and execution",
            "- Repeatable examples for developers",
            "- Clean, modern project layout",
            "",
            "## 🚀 Installation",
            "Install dependencies and run the application in one step.",
            "",
            "```bash",
            "pip install -r requirements.txt",
            "```",
            "",
            "## 🧪 Usage",
            "Run the application and verify behavior with one command.",
            "",
            "```bash",
            "python main.py",
            "```",
            "",
            "## 🛠️ Recommended Repository Structure",
            "",
            "- `agents/` — orchestration and workflow logic",
            "- `tools/` — integrations, retrieval, and helper services",
            "- `utils/` — shared utilities and support functions",
            "- `ui/` — presentation layer and user interaction",
            "",
            "## 🧭 Architecture Overview",
            "",
            "The repository is designed for iterative AI workflows that separate analysis, metadata generation, content refinement, and review into reusable components.",
            "",
            "## 📌 Why this matters",
            "",
            "This template makes it easy for contributors to onboard quickly, understand the project purpose, and iterate on documentation with confidence.",
        ]
        if rag_hints:
            sections.extend(["", "## 💡 Recommended Improvements",
                            *[f"- {hint}" for hint in rag_hints[:4]]])
        return "\n".join(sections)

    def _extract_title(self, readme: str) -> str:
        match = re.search(r"^#\s+(.+)$", readme, re.M)
        return match.group(1).strip() if match else "Project"

    def _extract_summary(self, readme: str) -> str:
        paragraphs = [p.strip()
                      for p in re.split(r"\n\s*\n", readme) if p.strip()]
        for paragraph in paragraphs:
            cleaned = re.sub(r"^#\s+", "", paragraph)
            if cleaned and not cleaned.startswith("##"):
                return cleaned
        return ""
