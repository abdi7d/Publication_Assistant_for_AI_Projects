# tools/rag_retriever.py
import logging
import os
import uuid
from typing import List

try:
    import chromadb
except Exception:
    chromadb = None
try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = None
        self.collection = None
        self.embed_model = "models/gemini-embedding-001"

        if chromadb is None:
            logger.warning(
                "chromadb not installed. RAG functionality disabled.")
            return

        try:
            if db_path and not os.path.exists(db_path):
                logger.warning(
                    "RAG DB path %s does not exist; skipping chromadb init", db_path)
                return
        except Exception:
            pass

        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                "project_suggestions")
            if self.collection.count() == 0:
                self.seed_knowledge_base()
        except BaseException as exc:
            logger.error("Failed to initialize RAG system: %s", exc)
            self.client = None
            self.collection = None

    @staticmethod
    def _ensure_list_floats(obj) -> list | None:
        """Recursively unwrap common SDK embedding containers into a plain list of floats."""
        try:
            # direct list/tuple of numbers
            if isinstance(obj, (list, tuple)):
                # If the list contains SDK wrapper objects, try to unwrap first element
                if obj and not all(isinstance(x, (int, float)) for x in obj):
                    # try unwrap each element
                    for item in obj:
                        candidate = RAGRetriever._ensure_list_floats(item)
                        if candidate:
                            return candidate
                    return None
                return [float(x) for x in obj]

            # If obj is a mapping-like returned in .data
            from collections.abc import Mapping
            if isinstance(obj, Mapping):
                # common key names
                for key in ("embedding", "values", "embeddings"):
                    if key in obj:
                        return RAGRetriever._ensure_list_floats(obj[key])

            # Common SDK attributes
            if hasattr(obj, "values"):
                vals = getattr(obj, "values")
                return RAGRetriever._ensure_list_floats(vals)

            if hasattr(obj, "embedding"):
                val = getattr(obj, "embedding")
                return RAGRetriever._ensure_list_floats(val)

            if hasattr(obj, "embeddings"):
                embs = getattr(obj, "embeddings")
                return RAGRetriever._ensure_list_floats(embs)

        except Exception:
            return None
        return None

    def seed_knowledge_base(self):
        sample_docs = [
            "Add clear installation instructions with 'pip install -r requirements.txt'.",
            "Include usage examples with code snippets in the README.",
            "Suggest adding diagrams for architecture visualization (Mermaid or images).",
            "Recommend adding a License file (MIT, Apache 2.0).",
            "Include a Contributing guide (CONTRIBUTING.md).",
            "Add badges for build status, license, and python version.",
            "Structure the project with clearly defined folders: agents, tools, utils.",
            "Add unit tests using pytest in a 'tests/' directory.",
            "Provide a 'Quick Start' section for immediate gratification.",
            "List all dependencies clearly in requirements.txt or pyproject.toml.",
        ]

        if self.collection is None:
            return
        if genai is None or not os.getenv("GOOGLE_API_KEY"):
            logger.warning("RAG seed skipped: missing genai or API key.")
            return

        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

            for doc in sample_docs:
                resp = client.models.embed_content(
                    model=self.embed_model, contents=doc)
                embedding = RAGRetriever._ensure_list_floats(resp)
                if not embedding:
                    logger.warning(
                        "RAG seed: could not extract embedding for sample doc; skipping.")
                    continue
                # chroma expects a list of floats (or list-of-lists); pass plain list
                self.collection.add(ids=[str(uuid.uuid4())], embeddings=[
                                    embedding], documents=[doc])
            logger.info("Seeded RAG knowledge base with %d items.",
                        len(sample_docs))
        except Exception as exc:
            logger.error("Error seeding RAG: %s", exc)

    def retrieve(self, text: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant suggestions based on the input text."""
        if not text or self.collection is None:
            return []
        if genai is None or not os.getenv("GOOGLE_API_KEY"):
            return []

        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

            resp = client.models.embed_content(
                model=self.embed_model, contents=text[:1000])
            query_embedding = RAGRetriever._ensure_list_floats(resp)
            if query_embedding is None:
                logger.error(
                    "RAG retrieval error: could not extract query embedding from response: %s", type(resp))
                return []

            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=top_k)
            if results and results.get("documents"):
                return [doc for sublist in results["documents"] for doc in sublist]
            return []
        except Exception as exc:
            logger.error("RAG retrieval error: %s", exc)
            return []
