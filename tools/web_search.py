# tools/web_search.py
import os
import logging
from typing import List, Dict, Any

# Defer importing TavilySearchResults until runtime to avoid LangChain deprecation
# warnings at module import time when the optional dependency is not used in tests.
TavilySearchResults = None

try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class WebSearchTool:
    def __init__(self, selected_model: str = None, provider: str = None):
        # graceful fallbacks if dependencies missing
        self.search = None
        tavily_key = os.getenv("TAVILY_API_KEY")
        tavily_impl = None
        if tavily_key:
            try:
                # lazy import to avoid deprecation warnings when key absent
                from langchain_community.tools.tavily_search import TavilySearchResults as _Tav
                tavily_impl = _Tav
            except Exception:
                tavily_impl = None

        if tavily_impl is not None and tavily_key:
            try:
                self.search = tavily_impl(max_results=5)
                logger.info("WebSearchTool: Tavily search tool initialized.")
            except Exception as e:
                logger.error(
                    f"WebSearchTool: Tavily initialization failed: {e}")
                self.search = None
        else:
            logger.debug(
                f"WebSearchTool: Tavily tool NOT initialized. Key present: {bool(tavily_key)}")

        self.model = None
        self.selected_model = selected_model or "gemini-1.5-flash"
        self.provider = provider or "google"
        self.gemini_client = None
        self.groq_client = None
        self.active_client = None
        # Try to initialize both clients if possible
        google_api_key = os.getenv("GOOGLE_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        # Gemini (Google)
        if genai is not None and google_api_key:
            try:
                self.gemini_client = genai.Client(api_key=google_api_key)
                logger.info(
                    "WebSearchTool: Gemini client successfully initialized.")
            except Exception as e:
                logger.error(
                    f"WebSearchTool: Gemini client initialization failed: {e}")
                self.gemini_client = None
        # Groq (Llama)
        try:
            from groq import Groq
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info(
                    "WebSearchTool: Groq client successfully initialized.")
        except Exception as e:
            logger.warning(
                f"WebSearchTool: Groq client initialization failed: {e}")
            self.groq_client = None

        # Set active client based on provider, fallback if needed
        if self.provider == "google":
            self.active_client = self.gemini_client or self.groq_client
        elif self.provider == "groq":
            self.active_client = self.groq_client or self.gemini_client
        else:
            self.active_client = self.gemini_client or self.groq_client

    def search_similar_repos(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Searches for similar repositories or articles using Tavily.
        """
        logger.info(f"Searching web with Tavily for: {query}")
        try:
            if self.search is None:
                logger.warning(
                    "Tavily search tool unavailable; returning empty results.")
                return []

            # TavilySearchResults.run returns a list of dictionaries
            # We use invoke which is standard for LangChain tools
            results = self.search.invoke(query)

            # Ensure results is a list of dicts
            if isinstance(results, str):
                logger.warning(
                    f"Tavily returned a string instead of a list: {results[:100]}...")
                return []

            if not isinstance(results, list):
                logger.warning(
                    f"Tavily returned unexpected type: {type(results)}")
                return []

            # Standardize output
            clean_results = []
            for res in results[:top_k]:
                if not isinstance(res, dict):
                    continue
                clean_results.append({
                    "title": res.get("title", "No Title"),
                    "link": res.get("url", ""),  # Tavily uses 'url'
                    "snippet": res.get("content", "")  # Tavily uses 'content'
                })
            return clean_results
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    def summarize_and_improve(self, readme: str, examples: List[Dict], style: str = "Technical Blog", goal: str = "") -> str:
        """
        Uses Gemini to suggest improvements based on the current README, found examples, and user goal.
        """
        logger.info(f"summarize_and_improve: Style={style}, Goal={goal}")

        example_text = ""
        if examples:
            example_text = "\n\n".join(
                [f"Example ({e['title']}): {e['snippet']}" for e in examples if isinstance(e, dict)])

        prompt = f"""
You are the final Synthesis Agent of a production-grade AI-powered Publication Assistant for AI Projects.

Your responsibility is to combine the outputs of five collaborating expert agents into a single, polished, publication-ready GitHub README.

The collaborating agents are:

1. Repo Analyzer
   - Understands repository structure, source code, dependencies, architecture, and README.
   - Identifies strengths, missing documentation, and implementation details.

2. Metadata Recommender
   - Generates SEO-friendly project titles.
   - Recommends keywords, topics, categories, and discoverability improvements.

3. Content Improver
   - Rewrites content for clarity, professionalism, readability, and engagement.
   - Creates concise explanations and attractive project descriptions.

4. Reviewer / Critic
   - Detects missing documentation.
   - Improves organization and logical flow.
   - Ensures consistency and completeness.

5. Fact Checker
   - Ensures every technical statement is supported by the repository.
   - Never invents features, technologies, benchmarks, APIs, or results.
   - Removes unsupported claims.

--------------------------------------------------

WRITING STYLE

Style:
{style}

User Goal:
{goal if goal else "Improve the repository for discoverability, professionalism, and public presentation."}

--------------------------------------------------

REPOSITORY README

{readme[:4000]}

--------------------------------------------------

SIMILAR SUCCESSFUL PROJECTS

{example_text}

--------------------------------------------------

YOUR OBJECTIVES

Produce a GitHub README that is:

• Professional
• Beautiful
• Highly readable
• Portfolio-ready
• Recruiter-friendly
• Developer-friendly
• Open-source friendly
• SEO optimized
• Easy to scan
• Technically accurate
• Complete
• Visually engaging

The README should significantly improve:

✓ Discoverability
✓ Clarity
✓ Completeness
✓ Professionalism
✓ User onboarding
✓ GitHub presentation
✓ Documentation quality

--------------------------------------------------

IMPROVEMENTS TO MAKE

Improve or create when appropriate:

• Better project title
• Better subtitle
• Better project summary
• Better introduction
• Strong value proposition
• Better project overview
• Key Features
• Architecture explanation
• Project workflow
• Installation
• Quick Start
• Usage examples
• Configuration
• Project Structure
• Technology Stack
• Folder Structure
• API (if applicable)
• Examples
• Screenshots placeholders
• Diagrams (Mermaid)
• Contribution Guide
• Roadmap
• FAQ
• Troubleshooting
• License
• Acknowledgements

Add any important missing documentation.

Remove unnecessary repetition.

Improve formatting.

Improve readability.

Improve professionalism.

--------------------------------------------------

VISUAL REQUIREMENTS

Use Markdown professionally.

Use:

• Emojis for ALL major headings
• Tables where useful
• Checklists
• Callout blocks
• Quote blocks
• Code blocks
• Mermaid diagrams when appropriate
• Collapsible <details> sections for advanced information
• Horizontal separators
• Consistent heading hierarchy

Avoid walls of text.

Keep paragraphs short.

Use bullets whenever possible.

--------------------------------------------------

TECHNICAL REQUIREMENTS

Never invent features.

Never invent benchmarks.

Never invent APIs.

Never invent technologies.

Never invent performance numbers.

Never mention tools or frameworks that are not actually used.

If information is unavailable, improve the wording without fabricating details.

--------------------------------------------------

TECHNICAL ACCURACY

Never invent:
- features
- benchmarks
- datasets
- APIs
- models
- integrations
- metrics
- architecture

If something appears incomplete or uncertain:
- explicitly state that additional repository information would be needed.

--------------------------------------------------

VISUAL PRESENTATION

Produce a visually engaging README.

Use:
- emojis for headings
- markdown tables
- checklists
- blockquotes
- collapsible sections where useful
- code blocks
- callouts
- horizontal rules

When appropriate, generate Mermaid diagrams for:
- architecture
- workflow
- pipeline
- component interaction

Only generate diagrams when enough information exists.

--------------------------------------------------

EXAMPLES

If enough information exists, generate:
- installation example
- usage example
- CLI example
- API example
- expected output example

Otherwise omit them.

--------------------------------------------------

AUDIENCE ADAPTATION

Infer the primary audience.

Examples include:
- AI researchers
- ML engineers
- developers
- students
- contributors
- end users

Adjust tone and explanations accordingly.

--------------------------------------------------

SEO REQUIREMENTS

Naturally improve discoverability by incorporating relevant:

• AI
• Machine Learning
• LLM
• LangGraph
• LangChain
• Multi-Agent Systems
• RAG
• Python
• GitHub
• Open Source

Only include keywords that genuinely match the repository.

--------------------------------------------------

QUALITY CHECKLIST

Before producing the final README, internally verify:

✓ Technically accurate
✓ No hallucinations
✓ Well organized
✓ Easy to navigate
✓ Consistent formatting
✓ Attractive layout
✓ Professional tone
✓ Beginner friendly
✓ Experienced developer friendly
✓ Complete documentation
✓ No duplicate sections
✓ No unnecessary verbosity

--------------------------------------------------

STRICT RULES

1. Output ONLY valid Markdown.
2. Do NOT explain your reasoning.
3. Do NOT include analysis.
4. Do NOT mention the five agents.
5. Do NOT include "Suggested Tags" or badge sections at the top.
6. Do NOT fabricate missing information.
7. Make the README feel like it belongs to a top GitHub open-source project.
8. Optimize for GitHub rendering.
9. The output should be immediately usable as README.md.
10. Prioritize clarity, professionalism, discoverability, and maintainability.

Return ONLY the improved README.md.
"""

        try:
            # Use the correct client and model based on provider
            client = self.active_client
            model = self.selected_model
            if client is None:
                logger.warning(
                    "No LLM client available in summarize_and_improve; returning simple heuristic improvement.")
                lines = readme.splitlines()
                title = lines[0] if lines else "Project"
                return f"# {title}\n\nImproved summary: This project implements X. Add Installation and Usage sections."

            # Google Gemini
            if self.provider == "google" and hasattr(client, "models"):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    if not response or not response.text:
                        logger.error("Gemini returned empty response")
                        return "Error: AI generated an empty response."
                    return response.text
                except Exception as e:
                    logger.error(
                        f"Gemini call failed, trying Groq if available: {e}")
                    # Fallback to Groq if available
                    if self.groq_client:
                        try:
                            # Always use a valid Groq model for fallback
                            groq_model = "llama-3.1-8b-instant"
                            groq_response = self.groq_client.chat.completions.create(
                                model=groq_model,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            return groq_response.choices[0].message.content
                        except Exception as e2:
                            logger.error(f"Groq fallback also failed: {e2}")
                            return f"Error generating improvement suggestions: {str(e2)}"
                    return f"Error generating improvement suggestions: {str(e)}"

            # Groq (Llama)
            if self.provider == "groq" and hasattr(client, "chat"):
                try:
                    groq_response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return groq_response.choices[0].message.content
                except Exception as e:
                    logger.error(
                        f"Groq call failed, trying Gemini if available: {e}")
                    # Fallback to Gemini if available
                    if self.gemini_client:
                        try:
                            # Always use a valid Gemini model for fallback
                            gemini_model = "gemini-1.5-flash-latest"
                            response = self.gemini_client.models.generate_content(
                                model=gemini_model,
                                contents=prompt
                            )
                            if not response or not response.text:
                                logger.error("Gemini returned empty response")
                                return "Error: AI generated an empty response."
                            return response.text
                        except Exception as e2:
                            logger.error(f"Gemini fallback also failed: {e2}")
                            return f"Error generating improvement suggestions: {str(e2)}"
                    return f"Error generating improvement suggestions: {str(e)}"

            # If all else fails
            logger.error("No valid LLM provider or client found.")
            return "Error: No valid LLM provider or client found."
        except Exception as e:
            logger.exception(f"LLM generation crash: {e}")
            return f"Error generating improvement suggestions: {str(e)}"
