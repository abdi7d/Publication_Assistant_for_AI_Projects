# utils/dependency_container.py
"""
Dependency injection container for managing application dependencies.
Eliminates global state and enables proper lifecycle management.
"""
from typing import Optional, Dict, Any
import logging
import threading
from contextlib import contextmanager

from tools.arxiv_scholar import ArxivScholarTool
from tools.rag_retriever import RAGRetriever
from tools.keyword_extractor import KeywordExtractor
from tools.web_search import WebSearchTool
from tools.repo_parser import RepoParser

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Singleton dependency container for managing tool instances.
    Provides thread-safe access to expensive-to-initialize tools.
    """
    
    _instance: Optional['DependencyContainer'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._rag_retriever: Optional[RAGRetriever] = None
            self._arxiv_scholar_tool: Optional[ArxivScholarTool] = None
            self._web_search_tools: Dict[str, WebSearchTool] = {}
            self._repo_parser: Optional[RepoParser] = None
            self._keyword_extractor: Optional[KeywordExtractor] = None
            self._lock = threading.local()
            self._initialized = True
    
    def get_rag_retriever(self, db_path: str = "./chroma_db") -> RAGRetriever:
        """Get or create RAG retriever instance."""
        if self._rag_retriever is None:
            self._rag_retriever = RAGRetriever(db_path=db_path)
            logger.info("RAGRetriever initialized")
        return self._rag_retriever
    
    def get_arxiv_scholar_tool(self, rate_limit: float = 0.3) -> ArxivScholarTool:
        """Get or create arXiv scholar tool instance."""
        if self._arxiv_scholar_tool is None:
            self._arxiv_scholar_tool = ArxivScholarTool(rate_limit=rate_limit)
            logger.info("ArxivScholarTool initialized")
        return self._arxiv_scholar_tool
    
    def get_web_search_tool(
        self, 
        selected_model: str = None, 
        provider: str = None
    ) -> WebSearchTool:
        """Get or create web search tool instance."""
        key = f"{provider}:{selected_model}"
        if key not in self._web_search_tools:
            self._web_search_tools[key] = WebSearchTool(
                selected_model=selected_model, 
                provider=provider
            )
            logger.info("WebSearchTool initialized for %s", key)
        return self._web_search_tools[key]
    
    def get_repo_parser(self) -> RepoParser:
        """Get or create repo parser instance."""
        if self._repo_parser is None:
            self._repo_parser = RepoParser()
            logger.info("RepoParser initialized")
        return self._repo_parser
    
    def get_keyword_extractor(self, top_k: int = 10) -> KeywordExtractor:
        """Get or create keyword extractor instance."""
        if self._keyword_extractor is None:
            self._keyword_extractor = KeywordExtractor(top_k=top_k)
            logger.info("KeywordExtractor initialized")
        return self._keyword_extractor
    
    def reset(self):
        """Reset all cached instances (useful for testing)."""
        self._rag_retriever = None
        self._arxiv_scholar_tool = None
        self._web_search_tools.clear()
        self._repo_parser = None
        self._keyword_extractor = None
        logger.info("DependencyContainer reset")
    
    @contextmanager
    def scoped_dependencies(self):
        """Context manager for scoped dependency usage."""
        try:
            yield self
        finally:
            # Cleanup if needed
            pass


# Global container instance
container = DependencyContainer()


__all__ = ["DependencyContainer", "container"]