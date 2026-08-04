# tools/web_search.py
import os
import logging
from typing import List, Dict, Any

from resilience.circuit_breaker import circuit_breaker

TavilySearchResults = None

try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class WebSearchTool:
    def __init__(self, selected_model: str = None, provider: str = None):
        self.search = None
        tavily_key = os.getenv("TAVILY_API_KEY")
        tavily_impl = None
        if tavily_key:
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults as _Tav
                tavily_impl = _Tav
            except Exception:
                tavily_impl = None

        if tavily_impl is not None and tavily_key:
            try:
                self.search = tavily_impl(max_results=5)
                logger.info("WebSearchTool: Tavily search tool initialized.")
            except Exception as exc:
                logger.error(
                    "WebSearchTool: Tavily initialization failed: %s", exc)
                self.search = None
        else:
            logger.debug(
                "WebSearchTool: Tavily tool NOT initialized. Key present: %s", bool(tavily_key))

        self.model = None
        self.selected_model = selected_model or "gemini-1.5-flash"
        self.provider = provider or "google"
        self.gemini_client = None
        self.groq_client = None
        self.active_client = None

        google_api_key = os.getenv("GOOGLE_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        if genai is not None and google_api_key:
            try:
                self.gemini_client = genai.Client(api_key=google_api_key)
                logger.info(
                    "WebSearchTool: Gemini client successfully initialized.")
            except Exception as exc:
                logger.error(
                    "WebSearchTool: Gemini client initialization failed: %s", exc)
                self.gemini_client = None
        try:
            from groq import Groq
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info(
                    "WebSearchTool: Groq client successfully initialized.")
        except Exception as exc:
            logger.warning(
                "WebSearchTool: Groq client initialization failed: %s", exc)
            self.groq_client = None

        if self.provider == "google":
            self.active_client = self.gemini_client or self.groq_client
        elif self.provider == "groq":
            self.active_client = self.groq_client or self.gemini_client
        else:
            self.active_client = self.gemini_client or self.groq_client

    @circuit_breaker(failure_threshold=3, recovery_timeout=30.0)
    def search_similar_repos(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar repositories or articles using Tavily."""
        logger.info("Searching web with Tavily for: %s", query)
        try:
            if self.search is None:
                logger.warning(
                    "Tavily search tool unavailable; returning empty results.")
                return []

            results = self.search.invoke(query)
            if isinstance(results, str):
                logger.warning(
                    "Tavily returned a string instead of a list: %s", results[:100])
                return []
            if not isinstance(results, list):
                logger.warning(
                    "Tavily returned unexpected type: %s", type(results))
                return []

            clean_results = []
            for res in results[:top_k]:
                if not isinstance(res, dict):
                    continue
                clean_results.append({
                    "title": res.get("title", "No Title"),
                    "link": res.get("url", ""),
                    "snippet": res.get("content", "")
                })
            return clean_results
        except Exception as exc:
            logger.error("Tavily search error: %s", exc)
            return []

    def summarize_and_improve(self, readme: str, examples: List[Dict], style: str = "Technical Blog", goal: str = "") -> str:
        """Use the configured LLM to suggest README improvements, with a fallback to a safe heuristic."""
        logger.info("summarize_and_improve: Style=%s, Goal=%s", style, goal)

        example_text = ""
        if examples:
            example_text = "\n\n".join(
                [f"Example ({e['title']}): {e['snippet']}" for e in examples if isinstance(e, dict)])

        prompt = f"""
    You are the final Synthesis Agent for a publication-quality documentation pipeline.

    Your task is to transform the supplied repository context into a polished, publication-ready GitHub README that feels professional, trustworthy, and developer-friendly.

    Core objectives:
    - Preserve the project's most meaningful technical details while removing noise.
    - Emphasize clarity, discoverability, and public-facing quality.
    - Structure the README with a strong title, concise overview, installation guidance, usage examples, architecture highlights, and validation steps.
    - Present the work as a credible software project, not as a generic template.
    - Keep the output strictly valid Markdown and suitable for direct publication on GitHub.

    WRITING STYLE
    Style: {style}
    User Goal: {goal if goal else 'Improve the repository for discoverability, professionalism, and public presentation.'}

    REPOSITORY README
    {readme[:4000]}

    SIMILAR SUCCESSFUL PROJECTS
    {example_text}

    Return ONLY the improved README.md. Do NOT include "Suggested Tags" or badge sections at the top. Use installation and usage headings, short examples, and keep the output strictly valid Markdown.
    """

        try:
            client = self.active_client
            model = self.selected_model
            if client is None:
                logger.warning(
                    "No LLM client available in summarize_and_improve; returning heuristic improvement.")
                lines = readme.splitlines()
                title = lines[0] if lines else "Project"
                return f"# {title}\n\nImproved summary: This project implements a clear, well-structured workflow with installation and usage guidance."

            if self.provider == "google" and hasattr(client, "models"):
                # Retry generation a few times for transient rate limits
                import time
                max_attempts = 3
                backoff = 1.0
                for attempt in range(max_attempts):
                    try:
                        response = client.models.generate_content(
                            model=model, contents=prompt)
                        if not response or not getattr(response, "text", None):
                            logger.error("Gemini returned empty response")
                            return "Error: AI generated an empty response."
                        return response.text
                    except Exception as exc:
                        logger.warning(
                            "Gemini attempt %s failed: %s", attempt + 1, exc)
                        if attempt < max_attempts - 1:
                            time.sleep(backoff)
                            backoff *= 2
                            continue
                        logger.error(
                            "Gemini call failed, trying Groq if available: %s", exc)
                        if self.groq_client:
                            try:
                                groq_model = "llama-3.1-8b-instant"
                                groq_response = self.groq_client.chat.completions.create(
                                    model=groq_model, messages=[{"role": "user", "content": prompt}])
                                return groq_response.choices[0].message.content
                            except Exception as exc2:
                                logger.error(
                                    "Groq fallback also failed: %s", exc2)
                                return f"Error generating improvement suggestions: {str(exc2)}"
                        return f"Error generating improvement suggestions: {str(exc)}"

            if self.provider == "groq" and hasattr(client, "chat"):
                try:
                    groq_response = client.chat.completions.create(
                        model=model, messages=[{"role": "user", "content": prompt}])
                    return groq_response.choices[0].message.content
                except Exception as exc:
                    logger.error(
                        "Groq call failed, trying Gemini if available: %s", exc)
                    if self.gemini_client:
                        try:
                            gemini_model = "gemini-1.5-flash-latest"
                            response = self.gemini_client.models.generate_content(
                                model=gemini_model, contents=prompt)
                            if not response or not response.text:
                                logger.error("Gemini returned empty response")
                                return "Error: AI generated an empty response."
                            return response.text
                        except Exception as exc2:
                            logger.error(
                                "Gemini fallback also failed: %s", exc2)
                            return f"Error generating improvement suggestions: {str(exc2)}"
                    return f"Error generating improvement suggestions: {str(exc)}"

            logger.error("No valid LLM provider or client found.")
            return "Error: No valid LLM provider or client found."
        except Exception as exc:
            logger.exception("LLM generation crash: %s", exc)
            return f"Error generating improvement suggestions: {str(exc)}"
