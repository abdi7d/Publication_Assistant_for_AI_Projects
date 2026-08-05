from uuid import uuid4
import time
import threading
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, File, UploadFile, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware
from typing import Dict
import concurrent.futures

from security.configs.config_loader import settings as app_settings
from security.logging.logging_config import configure_logging
from security.middleware.auth_middleware import AuthMiddleware, require_auth, optional_auth
from security.middleware.rate_limit_middleware import RateLimitMiddleware
from security.middleware.request_size_middleware import RequestSizeMiddleware
from security.middleware.security_headers_middleware import SecurityHeadersMiddleware

from tools.arxiv_scholar import ArxivScholarTool
from tools.rag_retriever import RAGRetriever
from tools.keyword_extractor import KeywordExtractor
from tools.web_search import WebSearchTool
from tools.repo_parser import RepoParser
from agents.fact_checker import FactCheckerAgent
from agents.reviewer_critic import ReviewerCriticAgent
from agents.content_improver import ContentImproverAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from agents.repo_analyzer import RepoAnalyzerAgent
from orchestration.graph import Orchestrator
from security.validators.input_validators import validate_prompt
from utils.publication_builder import PublicationBuilder
from security.validators.validators import sanitize_text
from security.validators.file_validators import validate_upload
from security.validators.repo_validators import validate_comprehensive_submission
from utils.error_handler import setup_error_handlers
import gradio as gr
import logging
import os
import tempfile
import json
import re
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
UI_DIR = PROJECT_ROOT / "ui"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Global tool cache to avoid repeated expensive initializations.
GLOBAL_RAG_RETRIEVER: RAGRetriever | None = None
GLOBAL_ARXIV_SCHOLAR_TOOL: ArxivScholarTool | None = None
GLOBAL_WEB_SEARCH_TOOLS: Dict[str, WebSearchTool] = {}
GLOBAL_REPO_PARSER: RepoParser | None = None
GLOBAL_KEYWORD_EXTRACTOR: KeywordExtractor | None = None
load_dotenv()

# Simple in-memory job manager to track generation jobs and progress.


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def create_job(self, meta: dict) -> str:
        job_id = str(uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "meta": meta,
                "state": "IDLE",
                "steps": [],
                "start_ts": None,
                "end_ts": None,
                "result": None,
                "error": None,
                "cancel_event": threading.Event(),
            }
        return job_id

    def start(self, job_id: str, steps: list[str]):
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return
            j["start_ts"] = time.time()
            j["state"] = "RUNNING"
            j["steps"] = [{"name": s, "status": "PENDING"} for s in steps]

    def update_step(self, job_id: str, step_name: str, status: str, detail: str | None = None):
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return
            for step in j["steps"]:
                if step["name"] == step_name:
                    step["status"] = status
                    step["detail"] = detail
                elif step["status"] == "IN_PROGRESS" and status in ("COMPLETE", "FAILED", "CANCELLED"):
                    # if a later step completes, ensure previous in-progress is marked complete
                    step["status"] = "COMPLETE"

    def set_state(self, job_id: str, state: str):
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return
            j["state"] = state
            if state in ("SUCCESS", "ERROR", "CANCELLED"):
                j["end_ts"] = time.time()

    def set_result(self, job_id: str, result: dict):
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return
            j["result"] = result

    def set_error(self, job_id: str, error: str):
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return
            j["error"] = error
            j["state"] = "ERROR"
            j["end_ts"] = time.time()

    def cancel(self, job_id: str):
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return False
            j["cancel_event"].set()
            j["state"] = "CANCELLED"
            j["end_ts"] = time.time()
            return True

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return None
            # return a shallow copy to avoid races
            return dict(j)


GLOBAL_JOB_MANAGER = JobManager()
GLOBAL_GRADIO_ACTIVE = False

# --- Core Component Imports ---


# --- Setup ---
# Empty line here to maintain spacing
configure_logging()
logger = logging.getLogger(__name__)

# Projects persistence file
PROJECTS_FILE = Path("projects.json")
HISTORY_FILE = Path("history.json")
SAVED_FILE = Path("saved.json")
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# File locking for safe concurrent access (cross-platform)
import threading

_file_locks: Dict[str, threading.Lock] = {}
_file_locks_lock = threading.Lock()

def get_file_lock(file_path: Path) -> threading.Lock:
    """Get or create a lock for a specific file."""
    path_str = str(file_path)
    with _file_locks_lock:
        if path_str not in _file_locks:
            _file_locks[path_str] = threading.Lock()
        return _file_locks[path_str]


def load_projects():
    lock = get_file_lock(PROJECTS_FILE)
    with lock:
        if not PROJECTS_FILE.exists():
            return {}
        try:
            with PROJECTS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def save_project(project_id: str, repo_url: str, metadata: dict = None):
    lock = get_file_lock(PROJECTS_FILE)
    with lock:
        projects = load_projects()
        projects[project_id] = {"repo_url": repo_url, "metadata": metadata or {}}
        with PROJECTS_FILE.open("w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2)
    return list(projects.keys())


def validate_submission(repo_url: str, goal: str = "", project_desc: str = "") -> tuple[bool, str]:
    """Validate repository and prompt inputs before running the agent pipeline."""
    # Use comprehensive validation
    return validate_comprehensive_submission(repo_url, goal, project_desc)


def slugify(text: str) -> str:
    text = text or "project"
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        return "project"
    return text


def _run_generation_with_timeout(timeout_seconds: int, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(generate_full_article, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds), None
        except concurrent.futures.TimeoutError:
            future.cancel()
            return None, f"Generation timed out after {timeout_seconds} seconds."
        except Exception as exc:
            return None, str(exc)


def delete_project(project_id: str):
    lock = get_file_lock(PROJECTS_FILE)
    with lock:
        projects = load_projects()
        if project_id in projects:
            projects.pop(project_id)
            with PROJECTS_FILE.open("w", encoding="utf-8") as f:
                json.dump(projects, f, indent=2)
    return list(projects.keys())


def render_tags_as_html(tags: list) -> str:
    """Renders a list of tags as interactive-looking HTML pill badges."""
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
    html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">'
    for i, tag in enumerate(tags[:10]):
        color = colors[i % len(colors)]
        html += f'<span style="background-color: {color}22; color: {color}; border: 1px solid {color}44; border-radius: 16px; padding: 4px 12px; font-size: 14px; font-weight: 500; font-family: sans-serif;">{tag}</span>'
    html += '</div>'
    return html


def clean_generated_content(text: str) -> str:
    """Preserve rich Markdown structure while keeping Mermaid blocks intact."""
    if not text:
        return ""

    mermaid_blocks: list[str] = []

    def _protect_mermaid(match: re.Match[str]) -> str:
        block = match.group(0)
        token = f"MERMAID_BLOCK_{len(mermaid_blocks)}"
        mermaid_blocks.append(block)
        return token

    protected = re.sub(
        r"```(?:mermaid|[a-zA-Z0-9_-]+)[\s\S]*?```", _protect_mermaid, text)

    cleaned = protected.replace("\r\n", "\n")
    # Remove image markdown entirely
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", cleaned)

    # Remove top-level H1 headings
    cleaned = re.sub(r"^#\s.*$\n?", "", cleaned, flags=re.M)

    # Convert link markdown [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)

    # Preserve bold-only lines while stripping inline emphasis noise.
    standalone_bolds: list[str] = []

    def _protect_standalone_bold(match: re.Match[str]) -> str:
        token = f"__STANDALONE_BOLD_{len(standalone_bolds)}__"
        standalone_bolds.append(match.group(0))
        return token

    cleaned = re.sub(
        r"^(?:\*\*|__)([^\n*]+?)(?:\*\*|__)\s*$",
        _protect_standalone_bold,
        cleaned,
        flags=re.M,
    )
    cleaned = re.sub(r"(?<!\*)\*\*([^\n*]+?)\*\*(?!\*)", r"\1", cleaned)
    cleaned = re.sub(r"(?<!_)__([^\n_]+?)__(?!_)", r"\1", cleaned)

    for index, block in enumerate(standalone_bolds):
        cleaned = cleaned.replace(f"__STANDALONE_BOLD_{index}__", block)

    # Remove simple HTML tags but keep their inner text
    cleaned = re.sub(r"<(/?)[^>]+>", "", cleaned)

    # Remove list markers at line starts (retain the content)
    cleaned = re.sub(r"^[\s]*[-*+]\s+", "", cleaned, flags=re.M)

    # Collapse excessive newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    for index, block in enumerate(mermaid_blocks):
        cleaned = cleaned.replace(f"MERMAID_BLOCK_{index}", block)

    return cleaned

# --- Logic Functions ---


def validate_repo_logic(repo_url):
    """Handles the repo validation for the UI button."""
    if not repo_url:
        return "⚠️ Please enter a repository URL.", ""

    parser = RepoParser()
    try:
        result = parser.parse(repo_url)
        files = list(result.get("files", {}).keys())[:20]
        tree = "\n".join([f"📄 {f}" for f in files])
        return "✅ Repository validated successfully.", tree
    except Exception as e:
        logger.warning("Validation failed, trying fallback: %s", e)
        try:
            temp_dir = tempfile.mkdtemp(prefix="fallback_")
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write(
                    "# Fallback Project\nRemote clone failed, showing local structure.")
            result = parser.parse(temp_dir)
            files = list(result.get("files", {}).keys())
            tree = "\n".join([f"📄 {f}" for f in files])
            return f"ℹ️ Remote clone failed. Using offline sample fallback.", tree
        except:
            return f"❌ Validation Error: {str(e)}", ""


def generate_full_article(repo_url, style, length, model, goal, project_desc, provider=None,
                          job_id: str | None = None, progress_callback=None, cancel_event: threading.Event | None = None):
    """The main generation pipeline triggered by the 'Generate' button.

    Optional args:
      job_id: associate this run with a JobManager job id
      progress_callback: callable(job_id, step_name, status, detail)
      cancel_event: threading.Event used to allow cancellation
    """
    # VALIDATING
    if progress_callback:
        try:
            progress_callback(job_id, "VALIDATING",
                              "IN_PROGRESS", "Validating inputs")
        except Exception:
            pass

    ok, msg = validate_submission(repo_url, goal, project_desc)
    if not ok:
        if progress_callback:
            try:
                progress_callback(job_id, "VALIDATING", "FAILED", msg)
                progress_callback(job_id, None, "ERROR", msg)
            except Exception:
                pass
        return "Error", "Error", "", msg

    try:
        # Instantiate tools once and reuse them across requests to improve UI responsiveness.
        global GLOBAL_REPO_PARSER, GLOBAL_KEYWORD_EXTRACTOR, GLOBAL_RAG_RETRIEVER
        global GLOBAL_WEB_SEARCH_TOOLS, GLOBAL_ARXIV_SCHOLAR_TOOL

        if GLOBAL_REPO_PARSER is None:
            GLOBAL_REPO_PARSER = RepoParser()
        if GLOBAL_KEYWORD_EXTRACTOR is None:
            GLOBAL_KEYWORD_EXTRACTOR = KeywordExtractor()
        if GLOBAL_RAG_RETRIEVER is None:
            GLOBAL_RAG_RETRIEVER = RAGRetriever()
        if GLOBAL_ARXIV_SCHOLAR_TOOL is None:
            GLOBAL_ARXIV_SCHOLAR_TOOL = ArxivScholarTool()

        search_key = f"{provider}:{model}"
        if search_key not in GLOBAL_WEB_SEARCH_TOOLS:
            GLOBAL_WEB_SEARCH_TOOLS[search_key] = WebSearchTool(
                selected_model=model, provider=provider)
        web = GLOBAL_WEB_SEARCH_TOOLS[search_key]
        parser = GLOBAL_REPO_PARSER
        kw = GLOBAL_KEYWORD_EXTRACTOR
        rag = GLOBAL_RAG_RETRIEVER
        scholar = GLOBAL_ARXIV_SCHOLAR_TOOL
        agents = {
            "repo_analyzer": RepoAnalyzerAgent(repo_url, parser),
            "metadata_recommender": MetadataRecommenderAgent(kw),
            "content_improver": ContentImproverAgent(web, rag),
            "reviewer_critic": ReviewerCriticAgent(),
            "fact_checker": FactCheckerAgent(scholar),
        }

        # Define job steps
        steps = [
            "VALIDATING",
            "ANALYZING",
            "UNDERSTANDING",
            "GENERATING",
            "WRITING",
            "CREATING_DIAGRAMS",
            "REVIEWING",
            "FINALIZING",
        ]

        if job_id and progress_callback:
            try:
                progress_callback(job_id, None, "STARTED", "Starting pipeline")
            except Exception:
                pass

        # Run Pipeline
        if progress_callback:
            try:
                progress_callback(job_id, "ANALYZING",
                                  "IN_PROGRESS", "Parsing repository")
            except Exception:
                pass

        if cancel_event and cancel_event.is_set():
            if progress_callback:
                progress_callback(job_id, None, "CANCELLED",
                                  "Cancelled before run")
            raise Exception("Cancelled")

        orch = Orchestrator()
        result = orch.run_pipeline(agents, repo_url, style=style, goal=goal)

        if progress_callback:
            try:
                progress_callback(job_id, "ANALYZING",
                                  "COMPLETE", "Repository parsed")
                progress_callback(job_id, "UNDERSTANDING",
                                  "IN_PROGRESS", "Understanding project")
            except Exception:
                pass

        if cancel_event and cancel_event.is_set():
            if progress_callback:
                progress_callback(job_id, None, "CANCELLED",
                                  "User requested cancellation")
            raise Exception("Cancelled")

        analysis = result.get("analysis")
        metadata = result.get("metadata")
        content_impr = result.get("content_improvement")

        title = getattr(metadata, 'title_suggestions', ["Untitled Project"])[0]
        subtitle = getattr(metadata, 'short_description',
                           project_desc or "Analysis Result")
        tags = getattr(metadata, 'tags', ["AI", "Research"])

        tags_html = render_tags_as_html(tags)
        out_title = f"# {title}"
        out_tags = '<div style="margin-top: 10px; margin-bottom: 2px; font-weight: bold; font-size: 18px;">Project Tags</div>' + tags_html

        # Prefer improved README from the ContentImprover agent when available.
        publication_readme = None
        if content_impr and getattr(content_impr, 'improved_readme', None):
            publication_readme = getattr(content_impr, 'improved_readme')
        else:
            publication_readme = result.get("publication_readme")
            if not publication_readme:
                builder = PublicationBuilder()
                publication_readme = builder.build_readme(
                    repo_analysis=analysis,
                    metadata=metadata,
                    repo_source=repo_url,
                    style=style,
                    goal=goal,
                )

        if progress_callback:
            try:
                progress_callback(job_id, "GENERATING",
                                  "COMPLETE", "AI agents completed")
                progress_callback(job_id, "WRITING",
                                  "IN_PROGRESS", "Composing content")
            except Exception:
                pass

        # Clean and normalize the produced markdown for UI consumption.
        body = clean_generated_content(
            publication_readme or "No improvements generated.")

        if progress_callback:
            try:
                progress_callback(job_id, "WRITING",
                                  "COMPLETE", "Content written")
                progress_callback(job_id, "CREATING_DIAGRAMS",
                                  "IN_PROGRESS", "Creating diagrams")
                progress_callback(job_id, "CREATING_DIAGRAMS",
                                  "COMPLETE", "Diagrams ready")
                progress_callback(job_id, "REVIEWING",
                                  "IN_PROGRESS", "Reviewing content")
                progress_callback(job_id, "REVIEWING",
                                  "COMPLETE", "Review complete")
                progress_callback(job_id, "FINALIZING",
                                  "IN_PROGRESS", "Finalizing package")
                progress_callback(job_id, "FINALIZING",
                                  "COMPLETE", "Packaging complete")
                progress_callback(job_id, None, "SUCCESS",
                                  "Generation completed")
            except Exception:
                pass

        return out_title, "", out_tags, body

    except Exception as e:
        logger.exception("Generation failed")
        if progress_callback:
            try:
                progress_callback(job_id, None, "ERROR", str(e))
            except Exception:
                pass
        return "Error", "Error", "", f"Pipeline failed: {str(e)}"


# --- FastAPI app setup ---

app = FastAPI(
    title=app_settings.APP_NAME,
    version="1.1.0",
    description="Production-grade publication assistant for AI projects.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=app_settings.ALLOWED_HOSTS if app_settings.ALLOWED_HOSTS != ["*"] else ["localhost", "127.0.0.1", "testserver"]
)

# Secure CORS configuration - only allow specific origins in production
cors_origins = app_settings.CORS_ORIGINS if app_settings.CORS_ORIGINS != ["*"] else ["http://localhost:7860", "http://127.0.0.1:7860", "http://localhost:8000", "http://127.0.0.1:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],  # Restrict headers
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add request size validation middleware
app.add_middleware(RequestSizeMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Setup error handlers
setup_error_handlers(app)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    correlation_id = request.headers.get("x-correlation-id") or request_id
    
    # Attach to request state for use in endpoints
    request.state.request_id = request_id
    request.state.correlation_id = correlation_id
    
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={
                         "request_id": request_id, "correlation_id": correlation_id, "service": app_settings.APP_NAME})
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["x-request-id"] = request_id
    response.headers["x-correlation-id"] = correlation_id
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
            "service": app_settings.APP_NAME,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 3),
        },
    )
    return response


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("unexpected_error", extra={"request_id": request.headers.get(
        "x-request-id") or str(uuid4()), "service": app_settings.APP_NAME})
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error",
                 "message": "An unexpected server error occurred."},
    )


def _load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


DEFAULT_MODEL_NAME = "Gemini 1.5 Flash Latest (Google)"

MODEL_MAP = {
    "Gemini 3.6 Flash (Google)": ("google", "gemini-3.6-flash"),
    "Gemini 3.5 Flash (Google)": ("google", "gemini-3.5-flash"),
    "Gemini 3.5 Flash-Lite (Google)": ("google", "gemini-3.5-flash-lite"),
    "Gemini 1.5 Flash Latest (Google)": ("google", "gemini-1.5-flash-latest"),
    "Gemini 1.0 Pro (Google)": ("google", "gemini-1.0-pro"),
    "Llama 4 Scout (Groq)": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),
    "Llama 4 Maverick (Groq)": ("groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
    "Groq Llama-3.1-8B-Instant (Groq)": ("groq", "meta-llama/llama-3.1-8b-instant"),
    "Groq Mixtral-8x7B-32768 (Groq)": ("groq", "meta-llama/mixtral-8x7b-32768"),
    "Heuristic Fallback (No LLM)": ("none", "heuristic"),
}


class ValidateRequest(BaseModel):
    repo_url: str


class GenerateRequest(BaseModel):
    repo_url: str
    style: str = "Technical Blog"
    length: str = "Medium"
    model: str = DEFAULT_MODEL_NAME
    goal: str = ""
    project_desc: str = ""
    project_id: Optional[str] = None


class ProjectRequest(BaseModel):
    project_id: str
    repo_url: str
    metadata: dict = {}


class HistoryEntryRequest(BaseModel):
    entry: dict


class SavedItemRequest(BaseModel):
    item: dict


class SettingsRequest(BaseModel):
    data: dict


def register_fastapi_routes(app: FastAPI):
    @app.get("/")
    async def index():
        return FileResponse(path="ui/index.html", media_type="text/html")

    @app.get("/index.html")
    async def page_index_html():
        return FileResponse(path="ui/index.html", media_type="text/html")
    
    @app.get("/web-ui")
    async def web_ui_redirect():
        return FileResponse(path="ui/index.html", media_type="text/html")
    
    @app.get("/gradio")
    async def gradio_redirect():
        # This will trigger the Gradio interface
        return FileResponse(path="ui/gradio-placeholder.html", media_type="text/html")
    
    # Serve UI static files
    @app.get("/ui/{file_path:path}")
    async def serve_ui_files(file_path: str):
        ui_path = Path("ui") / file_path
        if ui_path.exists() and ui_path.is_file():
            return FileResponse(path=str(ui_path))
        raise HTTPException(status_code=404, detail="File not found")
    
    # Serve UI files directly (for --serve-ui mode)
    app.mount("/static", StaticFiles(directory="ui"), name="static")

    @app.get("/health")
    async def health_check():
        """Comprehensive health check with dependency verification."""
        health_status = {
            "status": "healthy",
            "service": app_settings.APP_NAME,
            "environment": app_settings.APP_ENV,
            "version": "1.1.0",
            "checks": {}
        }
        
        # Check critical dependencies
        try:
            import langgraph
            health_status["checks"]["langgraph"] = "ok"
        except ImportError:
            health_status["checks"]["langgraph"] = "missing"
            health_status["status"] = "degraded"
        
        try:
            import chromadb
            health_status["checks"]["chromadb"] = "ok"
        except ImportError:
            health_status["checks"]["chromadb"] = "missing"
            health_status["status"] = "degraded"
        
        try:
            import google.genai
            health_status["checks"]["google_genai"] = "ok"
        except ImportError:
            health_status["checks"]["google_genai"] = "missing"
            health_status["status"] = "degraded"
        
        # Check critical directories
        health_status["checks"]["uploads_dir"] = "ok" if UPLOADS_DIR.exists() else "missing"
        health_status["checks"]["logs_dir"] = "ok" if Path(app_settings.LOG_DIR).exists() else "missing"
        
        # Check environment variables
        health_status["checks"]["google_api_key"] = "configured" if os.getenv("GOOGLE_API_KEY") else "missing"
        health_status["checks"]["groq_api_key"] = "configured" if os.getenv("GROQ_API_KEY") else "missing"
        
        # Overall status
        if health_status["status"] == "degraded":
            return JSONResponse(content=health_status, status_code=503)
        
        return health_status

    @app.get("/ready")
    async def readiness_check():
        return {"status": "ready", "service": app_settings.APP_NAME}

    @app.get("/live")
    async def liveness_check():
        return {"status": "alive", "service": app_settings.APP_NAME}

    @app.get("/analytics.html")
    async def page_analytics():
        return FileResponse(path="ui/analytics.html", media_type="text/html")

    @app.get("/results.html")
    async def page_results():
        return FileResponse(path="ui/results.html", media_type="text/html")

    @app.get("/projects.html")
    async def page_projects():
        return FileResponse(path="ui/projects.html", media_type="text/html")

    @app.get("/saved.html")
    async def page_saved():
        return FileResponse(path="ui/saved.html", media_type="text/html")

    @app.get("/help.html")
    async def page_help():
        return FileResponse(path="ui/help.html", media_type="text/html")

    @app.get("/history.html")
    async def page_history():
        return FileResponse(path="ui/history.html", media_type="text/html")

    @app.get("/generate.html")
    async def page_generate():
        return FileResponse(path="ui/generate.html", media_type="text/html")

    @app.get("/settings.html")
    async def page_settings():
        return FileResponse(path="ui/settings.html", media_type="text/html")

    @app.post("/api/validate")
    async def api_validate(request: ValidateRequest):
        repo_url = request.repo_url
        msg, tree = validate_repo_logic(repo_url)
        return {"message": msg, "tree": tree}

    @app.post("/api/upload")
    async def api_upload(files: list[UploadFile] = File(...)):
        saved_items = []
        for upload in files:
            content = await upload.read()
            ok, message = validate_upload(
                content, upload.filename, upload.content_type)
            if not ok:
                return JSONResponse(status_code=400, content={"error": message})
            filename = os.path.basename(upload.filename)
            target = UPLOADS_DIR / filename
            with target.open("wb") as f:
                f.write(content)
            saved_items.append(
                {"filename": filename, "content_type": upload.content_type})
        return {"saved": saved_items}

    @app.post("/api/generate")
    async def api_generate(request: GenerateRequest):
        import time
        start_ts = time.time()
        final_url = request.repo_url
        provider, model_id = MODEL_MAP.get(
            request.model, MODEL_MAP[DEFAULT_MODEL_NAME])

        timeout_seconds = 90
        result, error = _run_generation_with_timeout(
            timeout_seconds,
            final_url,
            request.style,
            request.length,
            model_id,
            request.goal,
            request.project_desc,
            provider,
        )

        if error:
            logger.warning("/api/generate timed out or failed: %s", error)
            return {
                "title": "Error",
                "subtitle": "",
                "tags": [],
                "body": f"Generation failed: {error}",
                "projects": list(load_projects().keys()),
                "status": "error",
                "generation_time_seconds": round(time.time() - start_ts, 3),
                "error": error,
            }

        title, sub, tags, body = result
        generation_time = round(time.time() - start_ts, 3)
        is_error = (
            title == "Error"
            or sub == "Error"
            or isinstance(body, str) and (
                body.startswith("Generation failed")
                or body.startswith("Pipeline failed")
                or body.startswith("Error")
            )
        )

        if request.project_id:
            try:
                save_project(request.project_id,
                             final_url, {"title": title})
            except Exception:
                logger.exception("Failed to save project")

        return {
            "title": title,
            "subtitle": sub,
            "tags": tags,
            "body": body,
            "projects": list(load_projects().keys()),
            "status": "error" if is_error else "done",
            "generation_time_seconds": generation_time,
        }

    @app.post("/api/generate_async")
    async def api_generate_async(request: GenerateRequest):
        """Start an asynchronous generation job and return a job_id for polling."""
        final_url = request.repo_url
        provider, model_id = MODEL_MAP.get(
            request.model, MODEL_MAP[DEFAULT_MODEL_NAME])

        job_meta = {"repo_url": final_url,
                    "model": model_id, "style": request.style}
        job_id = GLOBAL_JOB_MANAGER.create_job(job_meta)

        steps = [
            "VALIDATING",
            "ANALYZING",
            "UNDERSTANDING",
            "GENERATING",
            "WRITING",
            "CREATING_DIAGRAMS",
            "REVIEWING",
            "FINALIZING",
        ]
        GLOBAL_JOB_MANAGER.start(job_id, steps)

        def progress_cb(jid, step, status, detail=None):
            # normalize
            if step:
                GLOBAL_JOB_MANAGER.update_step(jid, step, status, detail)
            else:
                # top-level state updates
                if status == "STARTED":
                    GLOBAL_JOB_MANAGER.set_state(jid, "RUNNING")
                elif status == "SUCCESS":
                    GLOBAL_JOB_MANAGER.set_state(jid, "SUCCESS")
                elif status == "ERROR":
                    GLOBAL_JOB_MANAGER.set_state(jid, "ERROR")
                    GLOBAL_JOB_MANAGER.set_error(jid, detail or "error")
                elif status == "CANCELLED":
                    GLOBAL_JOB_MANAGER.set_state(jid, "CANCELLED")

        def runner():
            start_ts = time.time()
            try:
                out_title, out_sub, out_tags, out_body = generate_full_article(
                    final_url, request.style, request.length, model_id, request.goal, request.project_desc,
                    provider, job_id, progress_callback=progress_cb, cancel_event=GLOBAL_JOB_MANAGER.get(job_id)["cancel_event"])

                gen_time = round(time.time() - start_ts, 3)
                result = {
                    "title": out_title,
                    "subtitle": out_sub,
                    "tags": out_tags,
                    "body": out_body,
                    "generation_time_seconds": gen_time,
                }
                GLOBAL_JOB_MANAGER.set_result(job_id, result)
                GLOBAL_JOB_MANAGER.set_state(job_id, "SUCCESS")
            except Exception as exc:
                GLOBAL_JOB_MANAGER.set_error(job_id, str(exc))

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        return {"job_id": job_id}

    @app.get("/api/generate_status")
    async def api_generate_status(job_id: str):
        j = GLOBAL_JOB_MANAGER.get(job_id)
        if not j:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        # compute progress percent
        total = len(j.get("steps") or [])
        done = sum(1 for s in (j.get("steps") or []) if s.get(
            "status") in ("COMPLETE", "COMPLETE", "FAILED"))
        percent = int(
            (done / total) * 100) if total else (100 if j.get("state") == "SUCCESS" else 0)
        resp = {
            "id": j.get("id"),
            "state": j.get("state"),
            "steps": j.get("steps"),
            "start_ts": j.get("start_ts"),
            "end_ts": j.get("end_ts"),
            "percent": percent,
            "error": j.get("error"),
        }
        return resp

    @app.post("/api/generate_cancel")
    async def api_generate_cancel(req: Request):
        data = await req.json()
        job_id = data.get("job_id")
        if not job_id:
            return JSONResponse(status_code=400, content={"error": "missing job_id"})
        ok = GLOBAL_JOB_MANAGER.cancel(job_id)
        return {"ok": bool(ok)}

    @app.get("/api/generate_result")
    async def api_generate_result(job_id: str):
        j = GLOBAL_JOB_MANAGER.get(job_id)
        if not j:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        if j.get("result"):
            return j.get("result")
        return JSONResponse(status_code=202, content={"status": j.get("state")})

    @app.get("/api/projects")
    async def api_projects_get():
        return load_projects()

    @app.post("/api/projects")
    async def api_projects_post(request: ProjectRequest):
        save_project(request.project_id,
                     request.repo_url, request.metadata)
        return {"ok": True, "projects": list(load_projects().keys())}

    @app.delete("/api/projects")
    async def api_projects_delete(request: ProjectRequest):
        delete_project(request.project_id)
        return {"ok": True, "projects": list(load_projects().keys())}

    @app.get("/api/history")
    async def api_history_get():
        return _load_json(HISTORY_FILE)

    @app.post("/api/history")
    async def api_history_post(entry: HistoryEntryRequest):
        hist = _load_json(HISTORY_FILE)
        if entry.entry:
            hist.setdefault('entries', []).insert(0, entry.entry)
            _save_json(HISTORY_FILE, hist)
        return hist

    @app.get("/api/saved")
    async def api_saved_get():
        return _load_json(SAVED_FILE)

    @app.post("/api/saved")
    async def api_saved_post(item: SavedItemRequest):
        saved = _load_json(SAVED_FILE)
        if item.item:
            saved.setdefault('items', []).insert(0, item.item)
            _save_json(SAVED_FILE, saved)
        return saved

    @app.delete("/api/saved")
    async def api_saved_delete(request: Request):
        data = {}
        try:
            data = await request.json()
        except Exception:
            data = {}
        key = data.get('key') or request.query_params.get('key')
        if not key:
            return {"error": "missing key"}
        saved = _load_json(SAVED_FILE)
        items = saved.get('items', [])
        saved['items'] = [i for i in items if i.get('id') != key]
        _save_json(SAVED_FILE, saved)
        return saved

    @app.get("/api/analytics")
    async def api_analytics():
        projects = load_projects()
        hist = _load_json(HISTORY_FILE)
        entries = hist.get('entries', []) if isinstance(hist, dict) else []
        generation_count = len(entries)
        unique_repos = len({e.get('repo')
                           for e in entries if e.get('repo')})
        last_run = entries[0].get('timestamp') if entries else None
        return {
            "projects_count": len(projects),
            "generation_count": generation_count,
            "unique_repos": unique_repos,
            "last_run": last_run
        }

    @app.get("/api/settings")
    async def api_settings_get():
        return _load_json(Path('.settings.json'))

    @app.post("/api/settings")
    async def api_settings_post(settings: SettingsRequest):
        _save_json(Path('.settings.json'), settings.data)
        return {"ok": True, "settings": settings.data}

    @app.get("/api/help")
    async def api_help():
        return {
            "docs_url": "https://github.com/abdi7d/ready-tensor-publication-explorer-rag-chatbot",
            "contact": "abdid.yadata@gmail.com"
        }

    @app.get("/api/about")
    async def api_about():
        return {
            "name": "Publication Assistant for AI Projects",
            "version": "1.1.0",
            "description": "Production-grade publication assistant for AI projects using intelligent multi-agent collaboration.",
            "features": [
                "Repository Analysis",
                "Metadata Generation", 
                "Content Improvement",
                "Fact Checking",
                "Multi-Agent Orchestration"
            ]
        }

    if UI_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")
    if ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


register_fastapi_routes(app)

# --- Gradio UI (CSS removed; using a soft theme and simple Markdown for styling) ---


def on_validate(url, mode, existing_sel):
    if mode == "Use Existing Project" and existing_sel:
        projects = load_projects()
        proj = projects.get(existing_sel)
        if proj:
            url = proj.get("repo_url", url)
    msg, tree = validate_repo_logic(url)
    return gr.update(value=msg, visible=True), tree


def on_generate(url, style, length, model, goal, desc, mode, existing_sel, new_id=None):
    provider, model_id = MODEL_MAP.get(model, MODEL_MAP[DEFAULT_MODEL_NAME])

    projects = load_projects()
    final_url = url
    project_id_to_save = None
    if mode == "Use Existing Project" and existing_sel:
        proj = projects.get(existing_sel)
        if not proj:
            for k, v in projects.items():
                if k.lower() == (existing_sel or "").lower():
                    proj = v
                    existing_sel = k
                    break
        if not proj:
            for k, v in projects.items():
                if existing_sel and existing_sel.lower() in k.lower():
                    proj = v
                    existing_sel = k
                    break
        if proj:
            final_url = proj.get("repo_url", url)
            project_id_to_save = existing_sel
    else:
        project_id_to_save = slugify(final_url) or "project"

    title, sub, tags, body = generate_full_article(
        final_url, style, length, model_id, goal, desc, provider)

    if mode != "Use Existing Project" and project_id_to_save:
        try:
            save_project(project_id_to_save, final_url, {"title": title})
        except Exception:
            logger.exception("Failed to save project")

    updated_choices = list(load_projects().keys())
    return (
        gr.update(visible=True),
        title,
        sub,
        tags,
        body,
        gr.update(choices=updated_choices, value=project_id_to_save or "",
                  visible=len(updated_choices) > 0),
    )


def on_generate_stream(url, style, length, model, goal, desc, mode, existing_sel):
    """Generator-based Gradio handler that streams progress updates while
    the synchronous pipeline runs in a background thread.
    Outputs: (output_container_visible, title, subtitle, tags_html, body, existing_proj_dropdown, progress_md)
    """
    projects = load_projects()
    provider, model_id = MODEL_MAP.get(model, MODEL_MAP[DEFAULT_MODEL_NAME])

    final_url = url
    project_id_to_save = None
    if mode == "Use Existing Project" and existing_sel:
        proj = projects.get(existing_sel)
        if proj:
            final_url = proj.get("repo_url", url)
            project_id_to_save = existing_sel
    else:
        project_id_to_save = slugify(final_url) or "project"

    progress_lines = []
    result = {}

    def progress_cb(job_id, step, status, detail=None):
        # append a human-friendly progress line
        label = (step or "STATE").replace("_", " ")
        line = f"{label}: {status} {('- ' + str(detail)) if detail else ''}"
        progress_lines.append(line)

    def runner():
        try:
            title, sub, tags_html, body = generate_full_article(
                final_url, style, length, model_id, goal, desc, provider,
                job_id=None, progress_callback=progress_cb)
            result['title'] = title
            result['subtitle'] = sub
            result['tags'] = tags_html
            result['body'] = body
        except Exception as e:
            result['error'] = str(e)

    t = threading.Thread(target=runner, daemon=True)
    t.start()

    # initial yield: show container and an empty progress box
    yield gr.update(visible=True), "", "", "", "", gr.update(choices=list(load_projects().keys()), value=project_id_to_save or "", visible=True), "Starting..."

    # stream while running
    while t.is_alive() or progress_lines:
        if progress_lines:
            out = "<br/>".join(progress_lines)
            progress_lines.clear()
            yield gr.update(visible=True), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(choices=list(load_projects().keys()), value=project_id_to_save or "", visible=True), out
        else:
            # yield a heartbeat so the frontend stays responsive
            yield gr.update(visible=True), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(choices=list(load_projects().keys()), value=project_id_to_save or "", visible=True), "Working..."
        time.sleep(0.6)

    # final result
    if result.get('error'):
        final_progress = f"Error: {result.get('error')}"
        yield gr.update(visible=True), "Error", "", "", final_progress, gr.update(choices=list(load_projects().keys()), value=project_id_to_save or "", visible=True), final_progress
    else:
        yield gr.update(visible=True), result.get('title', ''), result.get('subtitle', ''), result.get('tags', ''), result.get('body', ''), gr.update(choices=list(load_projects().keys()), value=project_id_to_save or "", visible=True), "Completed"


def on_mode_change(mode):
    projects = load_projects()
    has_existing = len(projects) > 0
    if mode == "Use Existing Project":
        return (
            gr.update(visible=has_existing, value=""),
            gr.update(value="", interactive=False),
            gr.update(
                value="Using existing project. Select one from dropdown.", visible=True),
        )
    return (
        gr.update(visible=False, value=""),
        gr.update(interactive=True, value=""),
        gr.update(value="", visible=False),
    )


def on_existing_select(selected):
    if not selected:
        return gr.update(value=""), gr.update(value="No project selected.", visible=True)
    projects = load_projects()
    proj = projects.get(selected)
    if not proj:
        for k, v in projects.items():
            if k.lower() == selected.lower() or (selected.lower() in k.lower()):
                proj = v
                selected = k
                break
    repo = proj.get("repo_url", "") if proj else ""
    return gr.update(value=repo, interactive=False), gr.update(value=f"Using existing project: {selected}", visible=True)


def on_delete(selected):
    if not selected:
        return gr.update(visible=False, choices=list(load_projects().keys())), gr.update(value=""), gr.update(value="No project selected.")
    updated = delete_project(selected)
    return (
        gr.update(choices=updated, value="", visible=len(updated) > 0),
        gr.update(value=""),
        gr.update(value=f"Deleted project '{selected}'."),
    )


def create_gradio_demo():  # pragma: no cover
    with gr.Blocks() as demo:

        with gr.Row():
            # --- LEFT SIDEBAR (Config Area) ---
            with gr.Column(scale=1):
                gr.Markdown("## ⚙️ Configuration")

                gr.Markdown("### 📖 Writing Style")
                style_input = gr.Dropdown(
                    ["Technical Blog", "Academic Showcase",
                        "Executive Summary", "User Guide"],
                    value="Technical Blog", label="Choose preferred style"
                )

                gr.Markdown("### 📏 Publication Length")
                length_input = gr.Radio(
                    ["Short", "Medium", "Long"], value="Medium", label="Target length")

                gr.Markdown("### 🤖 AI Model")
                model_input = gr.Dropdown(
                    [
                        "Gemini 3.6 Flash (Google)",
                        "Gemini 3.5 Flash (Google)",
                        "Gemini 3.5 Flash-Lite (Google)",
                        "Llama 4 Scout (Groq)",
                        "Llama 4 Maverick (Groq)",
                        "Heuristic Fallback (No LLM)"
                    ],
                    value="Gemini 3.6 Flash (Google)", label="Choose LLM"
                )

            # --- RIGHT MAIN PANEL ---
            with gr.Column(scale=4):
                # Header using Markdown (relies on theme for colors)
                gr.Markdown("""
    # 📝 Publication Assistant for AI Projects
    *Transform your GitHub repository into a polished article or README.*
    """)

                # Project Selection Row
                projects = load_projects()
                existing_choices = list(projects.keys())
                show_existing = len(existing_choices) > 0

                with gr.Row():
                    with gr.Column(scale=2):
                        proj_mode = gr.Dropdown(
                            ["Create New Project", "Use Existing Project"],
                            value="Create New Project",
                            label="📂 Project Mode"
                        )

                # Existing project selector (hidden unless mode set to use existing)
                existing_proj_dropdown = gr.Dropdown(
                    choices=existing_choices,
                    value="",
                    visible=show_existing,
                    label="Select Existing Project",
                    allow_custom_value=True,
                )
                delete_btn = gr.Button(
                    "Delete Project", variant="danger", visible=show_existing)

                with gr.Tabs() as tabs:

                    # Tab 1: Project Setup
                    with gr.TabItem("🔧 Project Setup"):
                        gr.Markdown("#### 📁 Repository URL")
                        with gr.Row():
                            repo_url_input = gr.Textbox(
                                placeholder="https://github.com/user/repo", scale=4, container=False)
                            validate_btn = gr.Button(
                                "🔍 Validate", scale=1, variant="secondary")

                        val_msg = gr.Markdown(visible=False)
                        tree_viewer = gr.Code(
                            label="Repo Structure", language="markdown", lines=6)

                        gr.Markdown("#### 📋 Project Description (Optional)")
                        desc_input = gr.Textbox(
                            lines=3, placeholder="Describe the core purpose of your project...", show_label=False)

                        gr.Markdown("#### 📄 Supplemental Documents")
                        gr.File(label="Upload PDFs or Docs for context",
                                file_count="multiple")

                    # Tab 2: Generation
                    with gr.TabItem("🚀 Generation"):
                        gr.Markdown("#### 🎯 Generation Goal")
                        goal_input = gr.Textbox(
                            # placeholder="e.g. Focus on the architecture and the 'Fake Information Replacement' module.",
                            placeholder="e.g. Write an article about this project and make sure to mention the fake information replacement module.",
                            lines=3, show_label=False
                        )

                        generate_btn = gr.Button(
                            "🚀 Generate", variant="primary")

                        with gr.Column(visible=False) as output_container:
                            gr.Markdown("---")
                            out_title = gr.Markdown()
                            out_sub = gr.Markdown()
                            out_tags = gr.HTML()  # Changed to HTML for pill badges
                            out_body = gr.Markdown()
                            progress_md = gr.Markdown(visible=True)

        # --- Event Handling ---
        validate_btn.click(on_validate, inputs=[
                           repo_url_input, proj_mode, existing_proj_dropdown], outputs=[val_msg, tree_viewer])

        generate_btn.click(
            on_generate_stream,
            inputs=[repo_url_input, style_input, length_input, model_input,
                    goal_input, desc_input, proj_mode, existing_proj_dropdown],
            outputs=[output_container, out_title, out_sub,
                     out_tags, out_body, existing_proj_dropdown, progress_md]
        )

        proj_mode.change(on_mode_change, inputs=[proj_mode], outputs=[
                         existing_proj_dropdown, repo_url_input, val_msg])

        existing_proj_dropdown.change(on_existing_select, inputs=[
                                      existing_proj_dropdown], outputs=[repo_url_input, val_msg])

        delete_btn.click(on_delete, inputs=[existing_proj_dropdown], outputs=[
                         existing_proj_dropdown, repo_url_input, val_msg])

    return demo


def _activate_gradio_mode():
    global GLOBAL_GRADIO_ACTIVE
    GLOBAL_GRADIO_ACTIVE = True


# --- Launch ---
if __name__ == "__main__":  # pragma: no cover
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--serve-ui", action="store_true",
                        help="Serve the static UI from ui/ and expose API endpoints")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host for the web server")
    parser.add_argument("--port", type=int, default=8001,
                        help="Port for the web server")
    args = parser.parse_args()

    if args.serve_ui:
        logger.info("Registered FastAPI routes:")
        for route in app.routes:
            logger.info(f"  {route.path} -> {route.name}")
        logger.info("Starting UI server at http://%s:%s", args.host, args.port)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        demo = create_gradio_demo()
        # Activate demo mode so on_generate uses async job flow
        _activate_gradio_mode()
        # Launch without theme parameter (compatibility fix)
        demo.launch()
