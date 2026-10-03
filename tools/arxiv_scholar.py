# tools/arxiv_scholar.py
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    import arxiv  # type: ignore
    _HAS_ARXIV = True
except Exception:
    arxiv = None  # type: ignore
    _HAS_ARXIV = False
    logger.warning(
        "Optional dependency 'arxiv' not installed. ArxivScholarTool will return empty results.")


class ArxivScholarTool:
    def __init__(self, rate_limit: float = 0.3):
        self.rate_limit = rate_limit
        self.client = None
        if _HAS_ARXIV:
            try:
                self.client = arxiv.Client()
            except Exception:
                self.client = None
                logger.exception(
                    "Failed to initialize arxiv.Client; arXiv lookups disabled.")

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search arXiv for papers related to the query."""
        if not query or not _HAS_ARXIV or self.client is None:
            return []
        # Sanitize and shorten query to avoid sending large or markup-laden strings to arXiv

        def _sanitize(q: str) -> str:
            import re
            # Remove HTML tags
            q = re.sub(r"<[^>]+>", " ", q)
            # Remove Markdown links/images and inline code
            q = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", q)
            q = re.sub(r"\[[^\]]+\]\([^)]*\)", " ", q)
            q = re.sub(r"`[^`]*`", " ", q)
            # Remove non-alphanumeric characters (keep spaces)
            q = re.sub(r"[^0-9A-Za-z\s]", " ", q)
            # Collapse whitespace and truncate
            q = re.sub(r"\s+", " ", q).strip()
            return q[:300]

        safe_query = _sanitize(query)
        if not safe_query:
            return []

        try:
            search = arxiv.Search(
                query=safe_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = []
            for result in self.client.results(search):
                results.append({
                    "title": result.title,
                    "summary": result.summary.replace("\n", " "),
                    "id": result.entry_id,
                    "pdf_url": result.pdf_url,
                    "published": str(result.published),
                })
            return results
        except Exception as exc:
            logger.exception("Arxiv query error: %s", exc)
            return []

    def search_arxiv(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        return self.search(query, max_results=max_results)
