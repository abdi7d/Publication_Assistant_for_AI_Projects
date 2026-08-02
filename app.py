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
from security.validators.validators import sanitize_text
from security.validators.file_validators import validate_upload
import gradio as gr
import logging
import os
import tempfile
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
load_dotenv()

# --- Core Component Imports ---


# --- Setup ---
# Empty line here to maintain spacing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Projects persistence file
PROJECTS_FILE = Path("projects.json")
HISTORY_FILE = Path("history.json")
SAVED_FILE = Path("saved.json")
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


def load_projects():
    if not PROJECTS_FILE.exists():
        return {}
    try:
        with PROJECTS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_project(project_id: str, repo_url: str, metadata: dict = None):
    projects = load_projects()
    projects[project_id] = {"repo_url": repo_url, "metadata": metadata or {}}
    with PROJECTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)
    return list(projects.keys())


def validate_submission(repo_url: str, goal: str = "", project_desc: str = "") -> tuple[bool, str]:
    """Validate repository and prompt inputs before running the agent pipeline."""
    repo_url = sanitize_text(repo_url or "")
    goal = sanitize_text(goal or "")
    project_desc = sanitize_text(project_desc or "")

    if not repo_url:
        return False, "Repository URL is required."

    if len(repo_url) > 2000:
        return False, "Repository URL is too long."

    if any(token in repo_url.lower() for token in ["<script", "javascript:", "data:"]):
        return False, "Repository URL contains unsupported characters."

    combined_input = "\n".join([repo_url, goal, project_desc])
    ok, error = validate_prompt(combined_input)
    if not ok:
        return False, error or "Input contains invalid or unsafe content."

    return True, ""


def slugify(text: str) -> str:
    text = text or "project"
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        return "project"
    return text


def delete_project(project_id: str):
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
    """Remove markdown decoration and tag-like noise from generated content."""
    if not text:
        return ""

    cleaned = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    cleaned = re.sub(r"\[[^\]]+\]\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"(?m)^#{1,6}\s+", "", cleaned)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"(?m)^[-*]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\d+\.\s+", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

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


def generate_full_article(repo_url, style, length, model, goal, project_desc, provider=None):
    """The main generation pipeline triggered by the 'Generate' button."""
    ok, msg = validate_submission(repo_url, goal, project_desc)
    if not ok:
        return "Error", "Error", "", msg

    try:
        # Instantiate Tools & Agents
        parser, kw, rag = RepoParser(), KeywordExtractor(), RAGRetriever()
        web = WebSearchTool(selected_model=model, provider=provider)
        scholar = ArxivScholarTool()
        agents = {
            "repo_analyzer": RepoAnalyzerAgent(repo_url, parser),
            "metadata_recommender": MetadataRecommenderAgent(kw),
            "content_improver": ContentImproverAgent(web, rag),
            "reviewer_critic": ReviewerCriticAgent(),
            "fact_checker": FactCheckerAgent(scholar),
        }

        # Run Pipeline
        orch = Orchestrator()
        result = orch.run_pipeline(agents, repo_url, style=style, goal=goal)

        analysis = result.get("analysis")
        metadata = result.get("metadata")
        content_impr = result.get("content_improvement")

        # Formatting Output
        title = getattr(metadata, 'title_suggestions', ["Untitled Project"])[0]
        subtitle = getattr(metadata, 'short_description',
                           project_desc or "Analysis Result")
        tags = getattr(metadata, 'tags', ["AI", "Research"])

        # Render tags as HTML pill badges (only once, at the top)
        tags_html = render_tags_as_html(tags)

        # Build structured body: only one title, add 'Project Tags' subtitle above tags, and ensure tags are not repeated in the body
        # Compose output: title, 'Project Tags' subtitle, tags, then cleaned body
        out_title = f"# {title}"
        out_tags = '<div style="margin-top: 10px; margin-bottom: 2px; font-weight: bold; font-size: 18px;">Project Tags</div>' + tags_html
        improved_readme = getattr(
            content_impr, 'improved_readme', "No improvements generated.")

        cleaned_body = clean_generated_content(improved_readme)
        lines = cleaned_body.splitlines()
        cleaned_lines = []
        skip = True
        for line in lines:
            if skip and not line.strip():
                continue
            if skip and (re.match(r'^\s*Project Tags', line, re.IGNORECASE) or re.match(r'^\s*Tags', line, re.IGNORECASE)):
                continue
            if skip and (re.match(r'^\s*#{1,3} ', line) or re.match(r'^\s*<div', line) or re.match(r'^\s*<span', line)):
                continue
            if skip and line.strip() and not (re.match(r'^\s*#{1,3} ', line) or re.match(r'^\s*Project Tags', line, re.IGNORECASE) or re.match(r'^\s*Tags', line, re.IGNORECASE) or re.match(r'^\s*<div', line) or re.match(r'^\s*<span', line)):
                skip = False
            if not skip:
                cleaned_lines.append(line)
        body = '\n'.join(cleaned_lines).lstrip(
            '\n') or "No improvements generated."
        body = clean_generated_content(body)

        # Only return one title, then tags, then body (no subtitle)
        return out_title, "", out_tags, body

    except Exception as e:
        logger.exception("Generation failed")
        return "Error", "Error", "", f"Pipeline failed: {str(e)}"


# --- FastAPI app setup ---

app = FastAPI(title="Publication Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


class ValidateRequest(BaseModel):
    repo_url: str


class GenerateRequest(BaseModel):
    repo_url: str
    style: str = "Technical Blog"
    length: str = "Medium"
    model: str = "gemini-1.5-flash-latest"
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

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "publication-assistant"}

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

    @app.post("/api/generate")
    async def api_generate(request: GenerateRequest):
        final_url = request.repo_url
        model_map = {
            "Gemini 3.6 Flash (Google)": ("google", "gemini-3.6-flash"),
            "Gemini 3.5 Flash (Google)": ("google", "gemini-3.5-flash"),
            "Gemini 3.5 Flash-Lite (Google)": ("google", "gemini-3.5-flash-lite"),
            "Llama 4 Scout (Groq)": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),
            "Llama 4 Maverick (Groq)": ("groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
            "Heuristic Fallback (No LLM)": ("none", "heuristic")
        }
        provider, model_id = model_map.get(
            request.model, ("google", "gemini-1.5-flash-latest"))

        title, sub, tags, body = generate_full_article(
            final_url, request.style, request.length, model_id,
            request.goal, request.project_desc, provider)

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
            "projects": list(load_projects().keys())
        }

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
        data = await request.json()
        key = data.get('key')
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

    if Path("ui").exists():
        app.mount("/static", StaticFiles(directory="ui"), name="static")


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
    model_map = {
        "Gemini 3.6 Flash (Google)": ("google", "gemini-3.6-flash"),
        "Gemini 3.5 Flash (Google)": ("google", "gemini-3.5-flash"),
        "Gemini 3.5 Flash-Lite (Google)": ("google", "gemini-3.5-flash-lite"),
        "Llama 4 Scout (Groq)": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),
        "Llama 4 Maverick (Groq)": ("groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
        "Heuristic Fallback (No LLM)": ("none", "heuristic")
    }
    provider, model_id = model_map.get(model, ("google", "gemini-3.6-flash"))

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


def create_gradio_demo():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:

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
                            "🚀 Generate Article", variant="primary")

                        with gr.Column(visible=False) as output_container:
                            gr.Markdown("---")
                            out_title = gr.Markdown()
                            out_sub = gr.Markdown()
                            out_tags = gr.HTML()  # Changed to HTML for pill badges
                            out_body = gr.Markdown()

        # --- Event Handling ---
        validate_btn.click(on_validate, inputs=[
                           repo_url_input, proj_mode, existing_proj_dropdown], outputs=[val_msg, tree_viewer])

        generate_btn.click(
            on_generate,
            inputs=[repo_url_input, style_input, length_input, model_input,
                    goal_input, desc_input, proj_mode, existing_proj_dropdown],
            outputs=[output_container, out_title, out_sub,
                     out_tags, out_body, existing_proj_dropdown]
        )

        proj_mode.change(on_mode_change, inputs=[proj_mode], outputs=[
                         existing_proj_dropdown, repo_url_input, val_msg])

        existing_proj_dropdown.change(on_existing_select, inputs=[
                                      existing_proj_dropdown], outputs=[repo_url_input, val_msg])

        delete_btn.click(on_delete, inputs=[existing_proj_dropdown], outputs=[
                         existing_proj_dropdown, repo_url_input, val_msg])

    return demo


# --- Launch ---
if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--serve-ui", action="store_true",
                        help="Serve the static UI from ui/ and expose API endpoints")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host for the web server")
    parser.add_argument("--port", type=int, default=8000,
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
        demo.launch()
