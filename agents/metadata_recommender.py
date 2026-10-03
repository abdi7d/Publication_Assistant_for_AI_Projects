# agents/metadata_recommender.py
from dataclasses import dataclass
from typing import List, Dict
import logging
import os
import re

from tools.keyword_extractor import KeywordExtractor

try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


@dataclass
class MetadataRecommendation:
    title_suggestions: List[str]
    tags: List[str]
    short_description: str


class MetadataRecommenderAgent:
    """
    Suggest metadata (title, tags, short description) for the repository based on README and code.
    """

    def __init__(self, keyword_extractor: KeywordExtractor):
        self.keyword_extractor = keyword_extractor
        self.model = None
        api_key = os.getenv("GOOGLE_API_KEY")
        if genai is not None and api_key:
            try:
                self.model = genai.Client(api_key=api_key)
            except Exception:
                self.model = None

    def run(self, readme_text: str, code_files: dict) -> MetadataRecommendation:
        logger.info("MetadataRecommenderAgent: extracting keywords")
        keywords = self.keyword_extractor.extract(readme_text)
        repo_terms = self._extract_repo_terms(readme_text, code_files)
        combined = self._merge_keywords(keywords, repo_terms)

        title_suggestions = self._make_titles(readme_text, combined)
        short_desc = self._generate_description(readme_text, combined)

        rec = MetadataRecommendation(
            title_suggestions=title_suggestions,
            tags=combined[:12],
            short_description=short_desc,
        )
        return rec

    def _extract_repo_terms(self, readme_text: str, code_files: dict) -> List[str]:
        terms = []
        if code_files:
            for filename in code_files.keys():
                base = os.path.basename(filename).split(
                    ".")[0].replace("-", " ").replace("_", " ").strip()
                if len(base) > 2:
                    terms.append(base)
            for content in code_files.values():
                if not isinstance(content, str):
                    continue
                for match in re.findall(r"\b(?:fastapi|flask|django|streamlit|gradio|uvicorn|pydantic|langgraph|langchain|openai|chromadb|numpy|pandas|pytest|requests|asyncio|jinja|redis|docker)\b", content.lower()):
                    terms.append(match)

        for match in re.findall(r"\b(?:python|ai|ml|llm|rag|model|agent|assistant|workflow|pipeline|api|cli|server|web|fastapi|docker)\b", readme_text.lower()):
            terms.append(match)

        return [term for term in terms if len(term) > 2]

    def _merge_keywords(self, keywords: List[str], repo_terms: List[str]) -> List[str]:
        combined = []
        for item in [*keywords, *repo_terms]:
            value = str(item).strip().lower()
            if not value:
                continue
            value = re.sub(r"[^a-z0-9]+", " ", value).strip()
            if not value:
                continue
            if value not in combined:
                combined.append(value)
        return combined[:12]

    def _extract_heading_title(self, readme: str) -> str:
        match = re.search(r"^#\s+(.+)$", readme, re.M)
        return match.group(1).strip() if match else "Project"

    def _make_titles(self, readme: str, keywords: List[str]) -> List[str]:
        theme = " ".join(keywords[:3]).title(
        ) if keywords else self._extract_heading_title(readme)
        if not self.model or not keywords:
            return [
                f"🚀 {theme} Assistant",
                f"✨ {theme} Suite",
                f"{theme} Workflow",
            ]

        prompt = f"""
        Generate 3 catchy, professional, and emoji-enhanced titles for an AI/Software project based on these keywords and snippet.
        Keywords: {", ".join(keywords[:5])}
        Snippet: {readme[:500]}

        Return a comma-separated list. Each title should ideally include a relevant emoji.
        """
        try:
            response = self.model.models.generate_content(
                model="gemini-flash-latest", contents=prompt)
            titles = [t.strip() for t in response.text.split(",") if t.strip()]
            return titles if titles else [
                f"🚀 {theme} Assistant",
                f"✨ {theme} Suite",
                f"{theme} Workflow",
            ]
        except Exception:
            return [
                f"🚀 {theme} Assistant",
                f"✨ {theme} Suite",
                f"{theme} Workflow",
            ]

    def _generate_description(self, readme: str, keywords: List[str]) -> str:
        if not self.model:
            if keywords:
                return f"A polished software project centered on {', '.join(keywords[:3])}."
            first_line = next((line.strip()
                              for line in readme.splitlines() if line.strip()), "")
            if first_line:
                return first_line if len(first_line) < 200 else first_line[:197] + "..."
            return "A polished software project for modern AI workflows."

        prompt = f"""
        Write a one-sentence, high-impact, and emoji-rich description (max 200 chars) for this project.
        Keywords: {", ".join(keywords[:5])}
        Readme start: {readme[:500]}
        Use at least one relevant emoji in the description.
        """
        try:
            response = self.model.models.generate_content(
                model="gemini-flash-latest", contents=prompt)
            desc = response.text.replace("\n", " ").strip()
            return desc if len(desc) < 250 else desc[:247] + "..."
        except Exception:
            return "A polished software project centered on " + ", ".join(keywords[:3])
