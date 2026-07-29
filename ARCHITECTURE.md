# Architecture & Design Documentation

## System Overview

The **Publication Assistant for AI Projects** is a production-grade multi-agent system that analyzes GitHub repositories and generates high-quality publication improvements. This document describes the system architecture, design decisions, and component interactions.

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                   │
│   ┌─────────────────────┐      ┌──────────────────────┐     │
│   │    Gradio UI        │      │  FastAPI REST    │     │
│   │  (Interactive)      │      │  (Programmatic)      │     │
│   └──────────┬──────────┘      └──────────┬───────────┘     │
└──────────────┼─────────────────────────────┼────────────────┘
               │                             │
┌──────────────┼─────────────────────────────┼────────────────┐
│              ▼                             ▼                 │
│         ┌─────────────────────────────────────┐              │
│         │   Application Logic (app.py)        │              │
│         │  • Input validation & sanitization  │              │
│         │  • Upload handling                  │              │
│         │  • Results formatting               │              │
│         │  • Persistence (JSON)               │              │
│         └────────────────┬────────────────────┘              │
│                          │                                   │
│         ┌────────────────▼────────────────────┐              │
│         │      Orchestration Layer            │              │
│         │    (LangGraph StateGraph)           │              │
│         │  • Pipeline coordination            │              │
│         │  • State management                 │              │
│         │  • Error handling & fallbacks       │              │
│         └────────────────┬────────────────────┘              │
│                          │                                   │
│  ┌───────────────────────┼────────────────────────┐          │
│  ▼                       ▼                        ▼           │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  ┌───┐ │
│ │  Agent   │  │  Agent   │  │  Agent   │  │ Agent │  │... │ │
│ │ 1: Repo  │  │ 2: Meta  │  │ 3:       │  │ 4:    │  │    │ │
│ │ Analyzer │  │ Rec.     │  │ Content  │  │ Review│  │    │ │
│ │          │  │          │  │ Improver │  │ Critic│  │    │ │
│ └──┬───────┘  └─────┬────┘  └────┬─────┘  └───┬───┘  └──┬─┘ │
│    │                │            │            │         │    │
│    └────────────────┼────────────┼────────────┼─────────┘    │
│                     │            │            │               │
│  ┌──────────────────┼────────────┼────────────┼────────────┐  │
│  ▼                  ▼            ▼            ▼            ▼  │
│ ┌────────┐  ┌────────────┐  ┌────────┐  ┌─────────┐  ┌──────┤
│ │RepoParser     │KeywordExtractor    │WebSearch   │RAGRetriever   │
│ │               │                     │           │              │
│ └────────────────┴─────────────────────┴───────────┴──────────────┘
│                                       │                          │
│                                       ▼                          │
│                        ┌────────────────────────┐               │
│                        │ Resilience Layer       │               │
│                        │ • Retry/Backoff        │               │
│                        │ • Timeouts             │               │
│                        │ • Circuit Breakers     │               │
│                        │ • Concurrency Control  │               │
│                        └────────────────────────┘               │
│                                       │                          │
│                                       ▼                          │
│                        ┌────────────────────────┐               │
│                        │ Security Layer         │               │
│                        │ • Input Validation     │               │
│                        │ • File Validation      │               │
│                        │ • Prompt Guard         │               │
│                        │ • Sanitization         │               │
│                        └────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │    External Services & Storage    │
        │  • LLM Providers (Google, Groq)  │
        │  • Web Search (Tavily)           │
        │  • Vector DB (ChromaDB)          │
        │  • GitHub (Repository Access)    │
        │  • ArXiv (Citation Verification)  │
        └───────────────────────────────────┘
```

---

## Component Descriptions

### 1. User Interface Layer

#### Gradio UI (`app.py` - Gradio mode)

**Purpose:** Interactive web interface for manual analysis

**Features:**

- File upload support (repositories as ZIP)
- Real-time result streaming
- Project history tracking
- Settings management
- Clean, responsive design

**Technology:** Gradio 4.0+

**Endpoints:**

- Upload repo/URL
- Configure analysis style
- View results with suggestions
- Save/export results

#### FastAPI API (`app.py` - API mode)

**Purpose:** RESTful API for programmatic integration

**Endpoints:**

- `POST /generate` - Submit repository
- `GET /health` - Health check
- `GET /results/<id>` - Retrieve results
- `GET /history` - View submission history
- `POST /validate` - Validate repository

---

### 2. Application Logic

**File:** `app.py`

**Responsibilities:**

1. **Input Validation** - Sanitize and validate all user inputs
2. **File Handling** - Manage uploads, ZIP extraction, cleanup
3. **Project Persistence** - Store/retrieve projects in `projects.json`
4. **Result Formatting** - Structure outputs for UI/API
5. **Error Handling** - User-friendly error messages

**Key Functions:**

- `validate_submission()` - Pre-flight validation
- `process_repository()` - Main pipeline orchestration
- `format_results()` - Structure agent outputs

---

### 3. Orchestration Layer

**File:** `orchestration/graph.py`

**Technology:** LangGraph StateGraph

**Pipeline:**

```
Repo Analysis
    ↓
Metadata Recommendation
    ↓
Content Improvement (RAG + Web Search)
    ↓
Review & Critique
    ↓
Fact Checking
    ↓
Final Report
```

**State Structure:**

```python
{
    "repo_source": str,          # GitHub URL or local path
    "repo_analysis": RepoAnalysis,
    "metadata": Metadata,
    "content_improvement": ContentImprovement,
    "review": Review,
    "fact_check": FactCheck
}
```

**Error Handling:**

- Each node has try/except with graceful fallbacks
- If agent fails, stub output generated to prevent pipeline breakage
- All failures logged with context

---

### 4. Agent Layer

Five specialized agents work together to analyze and improve repositories:

#### 4.1 RepoAnalyzerAgent

**Responsibility:** Parse repository structure and extract metadata

**Tools:**

- `RepoParser` - Read local, ZIP, or remote repos

**Output:**

```python
{
    "readme": str,
    "files": List[str],
    "code_stats": Dict,
    "structure": str,
    "missing_sections": List[str]
}
```

#### 4.2 MetadataRecommenderAgent

**Responsibility:** Generate title, tags, and short descriptions

**Tools:**

- `KeywordExtractor` - Extract technical keywords

**Output:**

```python
{
    "title_suggestions": List[str],
    "tags": List[str],
    "short_description": str
}
```

#### 4.3 ContentImproverAgent

**Responsibility:** Rewrite and improve README content

**Tools:**

- `WebSearchTool` - Find similar repositories
- `RAGRetriever` - Get documentation best practices

**Output:**

```python
{
    "improved_readme": str,
    "suggested_images": Dict[str, str]
}
```

#### 4.4 ReviewerCriticAgent

**Responsibility:** Score documentation quality and identify gaps

**Output:**

```python
{
    "score": float,  # 1-10
    "issues": List[str],
    "strengths": List[str],
    "recommendations": List[str]
}
```

#### 4.5 FactCheckerAgent

**Responsibility:** Verify technical claims using academic sources

**Tools:**

- `ArxivScholarTool` - Search academic papers

**Output:**

```python
{
    "claims_found": List[str],
    "verified": List[str],
    "flagged": List[str]
}
```

---

### 5. Tool Layer

#### 5.1 RepoParser

**Purpose:** Read repositories from various sources

**Supported Sources:**

- Local file system
- ZIP archives
- GitHub URLs (via API)
- Gitee URLs

**Output:** Repository structure + README + file list

#### 5.2 KeywordExtractor

**Purpose:** Extract technical keywords from code/docs

**Implementation:** Google Gemini API or fallback heuristics

**Output:** List of ranked keywords

#### 5.3 WebSearchTool

**Purpose:** Find similar repositories for inspiration

**Provider:** Tavily Search API

**Output:** List of GitHub repos with descriptions

#### 5.4 RAGRetriever

**Purpose:** Retrieve best-practice documentation hints

**Storage:** ChromaDB (SQLite-based vector store)

**Architecture:**

1. Pre-load best-practice examples into vector store
2. Embed user README using sentence transformers
3. Retrieve top-5 similar examples
4. Pass to LLM for synthesis

#### 5.5 ArxivScholarTool

**Purpose:** Verify technical claims against academic literature

**Provider:** arXiv.org API

**Output:** Matching papers for fact verification

---

### 6. Resilience Layer

**Location:** `resilience/`

#### 6.1 Retry Manager

**Purpose:** Implement exponential backoff with jitter

**Configuration:**

- Max attempts: configurable per use case
- Base delay: 0.1s default
- Exponential factor: 2.0
- Max delay: 10s

```python
@retry_async(max_attempts=3, base_delay=0.1, factor=2.0)
async def call_llm(...):
    pass
```

#### 6.2 Timeout Manager

**Purpose:** Enforce time limits on operations

**Configuration:**

- Agent timeout: 60s per agent
- Overall pipeline: 300s
- Web search: 10s

#### 6.3 Circuit Breaker

**Purpose:** Prevent cascading failures

**States:**

- CLOSED: Normal operation
- OPEN: Fail fast after threshold exceeded
- HALF_OPEN: Attempt recovery

#### 6.4 Concurrency Manager

**Purpose:** Control parallel execution

**Implementation:** asyncio semaphores and locks

---

### 7. Security Layer

**Location:** `security/`

#### 7.1 Input Validators

**Purpose:** Sanitize and validate prompts

**Checks:**

- Not empty
- No control characters
- Within size limits (100KB default)

#### 7.2 File Validators

**Purpose:** Secure file uploads

**Checks:**

- Allowed extensions: pdf, txt, md, docx, png, jpg, jpeg
- Size limit: 50MB default
- MIME type validation
- Filename sanitization

#### 7.3 Prompt Guard

**Purpose:** Detect and prevent prompt injection attacks

**Techniques:**

- Pattern matching for common injection payloads
- Isolation of user input from system prompts
- Token count validation

#### 7.4 Sanitizers

**Purpose:** Clean output before display

**Implementation:**

- HTML escaping
- Markdown safe rendering
- URL validation

---

### 8. Data Flow

#### Request Flow

```
1. User submits repository URL
    ↓
2. Input validation (security layer)
    ↓
3. File upload/extraction (if ZIP)
    ↓
4. Orchestrator instantiates agents
    ↓
5. Pipeline execution:
   a. RepoAnalyzerAgent → RepoAnalysis
   b. MetadataRecommenderAgent → Metadata
   c. ContentImproverAgent → ImprovedReadme
   d. ReviewerCriticAgent → QualityScore
   e. FactCheckerAgent → FactCheck
    ↓
6. Format results
    ↓
7. Return to user (UI or API)
    ↓
8. Persist to projects.json
```

#### State Passing

Each agent receives the current state and adds its output:

```python
state = {...}
state["repo_analysis"] = repo_analyzer.run()
state["metadata"] = metadata_recommender.run(state["repo_analysis"])
state["content_improvement"] = content_improver.run(
    state["repo_analysis"],
    state["metadata"]
)
# ... etc
```

---

## Design Patterns

### 1. Graceful Degradation

If any agent fails, a stub output is generated to prevent pipeline breakage:

```python
try:
    result = agent.run()
except Exception as e:
    logger.exception("Agent failed", exc_info=e)
    result = StubOutput()  # Valid but minimal
return {**state, "agent_output": result}
```

### 2. Tool Isolation

Tools are optional and independently resilient:

```python
try:
    search_results = web_search.search(query)
except Exception:
    logger.warning("Web search unavailable, continuing")
    search_results = []  # Fallback to no external results
```

### 3. State Machine

LangGraph provides deterministic execution order:

```python
workflow.add_edge("node_a", "node_b")  # node_b only runs after node_a completes
workflow.add_edge("node_b", END)       # Final node
```

### 4. Dependency Injection

Agents receive tools via constructor:

```python
repo_analyzer = RepoAnalyzerAgent(
    repo_source=repo_url,
    repo_parser=RepoParser()
)
```

---

## Deployment Topologies

### Single Instance (Development/Small Load)

```
User → FastAPI/Gradio → Agent Pipeline → External APIs
  (all in one container)
```

### Multi-Instance (Production)

```
User
  ↓
Load Balancer (Nginx)
  ↓
┌─────────────────────────────────────┐
│ Container 1: FastAPI/Agents Pipeline  │
│ Container 2: FastAPI/Agents Pipeline  │
│ Container 3: FastAPI/Agents Pipeline  │
└──────────────┬──────────────────────┘
               ↓
        Shared Volumes:
        • /uploads (NFS)
        • /chroma_db (Persistent)
               ↓
        External Services:
        • Google Gemini
        • Groq
        • Tavily Search
        • ArXiv
```

---

## Configuration Management

### Environment Variables

See `.env.example` for all configuration options.

**Critical Variables:**

- API Keys (GOOGLE_API_KEY, GROQ_API_KEY, TAVILY_API_KEY)
- Storage paths (UPLOADS_DIR, CHROMA_DB_PATH)
- Limits (MAX_UPLOAD_BYTES, MAX_PROMPT_LENGTH)

### Config Loader

**File:** `security/configs/config_loader.py`

Loads and validates configuration at startup:

```python
settings = load_settings()  # Reads .env
assert settings.GOOGLE_API_KEY  # Fails if missing
```

---

## Monitoring & Observability

### Metrics

- Request latency (per endpoint)
- Error rates (by agent)
- Retry attempts
- Vector DB size
- Token usage

### Logging

- Structured JSON logs
- Correlation IDs per request
- Audit trail for submissions

### Health Checks

- Liveness: `/health`
- Readiness: `/health?detailed=true`
- Full diagnostics: Integration tests

---

## Scalability Considerations

### Current Bottlenecks

1. **Vector DB**: Single SQLite file; OK for < 100k documents
2. **LLM Rate Limits**: Groove and Google have quotas
3. **Serialization**: Large repos take time to parse

### Future Improvements

1. **Distributed Vector DB**: Use Milvus for 1M+ embeddings
2. **LLM Caching**: Cache frequent queries
3. **Repository Caching**: Pre-parse popular repos
4. **Async Pipeline**: Parallelize independent agents

---

## Security & Compliance

### Input Security

- All user input validated and sanitized
- Prompt injection detection
- File upload restrictions
- Rate limiting

### Output Security

- HTML escaping
- Markdown sanitization
- No secrets in output

### Data Security

- Uploads stored in isolated directory
- Temporary files cleaned up
- No sensitive data logged

---

## Testing Strategy

### Unit Tests

- Agent logic
- Tool implementations
- Security validators
- Utility functions

### Integration Tests

- Orchestration pipeline
- Agent communication
- Failure recovery

### E2E Tests

- Full workflow (repo → results)
- API endpoints
- UI interactions

### Performance Tests

- Concurrency under load
- Stress test (max repo size)
- Rate limiting

---

## Future Enhancements

1. **Multi-Model Support**: LLaMA, Mistral in addition to Google/Groq
2. **Caching Layer**: Redis for frequently accessed repos
3. **Async Agents**: Parallel execution where possible
4. **Advanced RAG**: Hybrid search (dense + sparse)
5. **Custom Agents**: User-defined agent plugins
6. **Benchmarking**: Automated evaluation against baselines

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Gradio Deployment Guide](https://gradio.app/deployment/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Resilience Patterns](./resilience/RESILIENCE.md)
- [Security Guidelines](./security/architecture.md)
