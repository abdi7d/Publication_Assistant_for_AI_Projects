# tools/keyword_extractor.py
import logging
import os
import re
from typing import List

try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class KeywordExtractor:
    def __init__(self, top_k: int = 10):
        self.top_k = top_k
        self.model = None

        if genai is not None and os.getenv("GOOGLE_API_KEY"):
            try:
                self.model = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            except Exception as exc:
                logger.warning("Failed to initialize Gemini model: %s", exc)
                self.model = None

    def extract(self, text: str) -> List[str]:
        """Extracts high-quality keywords using Gemini LLM or a stronger heuristic fallback."""
        if not text:
            return []

        if self.model:
            prompt = f"""
            Extract the top {self.top_k} most relevant technical keywords, topics, and libraries from the following text.
            Return ONLY a comma-separated list of keywords. NO formatting, no bullets, no introduction.

            Text:
            {text[:3000]}
            """
            try:
                # Retry a few times in case of transient rate limits
                import time
                max_attempts = 3
                backoff = 1.0
                response = None
                for attempt in range(max_attempts):
                    try:
                        response = self.model.models.generate_content(
                            model="gemini-flash-latest", contents=prompt)
                        break
                    except Exception as exc:
                        logger.warning(
                            "KeywordExtractor LLM attempt %s failed: %s", attempt + 1, exc)
                        if attempt < max_attempts - 1:
                            time.sleep(backoff)
                            backoff *= 2
                        else:
                            raise
                keywords = [k.strip()
                            for k in response.text.split(",") if k.strip()]
                logger.debug(
                    "KeywordExtractor (LLM): extracted keywords: %s", keywords)
                return keywords[:self.top_k]
            except Exception as exc:
                logger.error("Keyword extraction (LLM) error: %s", exc)

        return self._heuristic_extract(text)

    def _heuristic_extract(self, text: str) -> List[str]:
        logger.info("KeywordExtractor: using heuristic fallback")
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "your", "have", "are", "can", "use",
                     "project", "repo", "repository", "readme", "based", "into", "about", "using", "build", "built"}

        freq = {}
        for word in words:
            if word not in stopwords:
                freq[word] = freq.get(word, 0) + 1

        candidates = []
        for word, count in sorted(freq.items(), key=lambda item: (-item[1], item[0])):
            candidates.append(word)

        domain_terms = ["python", "ai", "ml", "llm", "rag", "agent", "assistant", "workflow", "pipeline", "api",
                        "cli", "web", "docker", "fastapi", "langgraph", "langchain", "gradio", "streamlit", "pydantic", "pytest"]
        for term in domain_terms:
            if term in text.lower() and term not in candidates:
                candidates.append(term)

        return candidates[:self.top_k]
