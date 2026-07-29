# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the **Publication Assistant for AI Projects** to production environments, including containerization, configuration, monitoring, and operational best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Running the Application](#running-the-application)
6. [Health Checks and Monitoring](#health-checks-and-monitoring)
7. [Scaling Considerations](#scaling-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Python**: 3.11 or newer
- **Docker**: 20.10+ (for containerized deployment)
- **System Requirements**:
  - Minimum: 2GB RAM, 2 CPU cores
  - Recommended: 4GB RAM, 4 CPU cores
  - Disk: 5GB free space (for uploads and vector DB)
- **Internet Access**: Required for GitHub repo parsing, web search, and LLM APIs

### Required API Keys

Obtain these API keys before deployment:

- **Google API Key**: For Gemini LLM access ([Google AI Studio](https://aistudio.google.com))
- **Groq API Key**: For fast LLM inference ([Groq Console](https://console.groq.com))
- **Tavily API Key**: For web search functionality ([Tavily API](https://tavily.com))
- **GitHub Token** (optional): For higher rate limits on private repos

---

## Local Development Setup

### 1. Clone and Navigate

```bash
cd "c:\Users\HP\Desktop\AI\Agentic AI\Module three\Publication Assistant for AI Projects"
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create .env File

```bash
copy .env.example .env  # Windows
# or
cp .env.example .env  # macOS/Linux
```

Edit `.env` with your API keys:

```env
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GITHUB_TOKEN=your_github_token_here  # optional

# Application Settings
LOG_LEVEL=INFO
MAX_UPLOAD_BYTES=52428800  # 50MB default
MAX_PROMPT_LENGTH=100000

# Server Configuration
HOST=127.0.0.1
PORT=8000
```

### 5. Run Locally

**Gradio UI (Interactive):**

```bash
python app.py --serve-ui
```

Access at `http://127.0.0.1:8000`

**CLI Mode:**

```bash
python main.py --repo-path ./path/to/repo
```

**FastAPI API Mode:**

```bash
python app.py --serve-api --host 0.0.0.0 --port 8000
```

---

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t publication-assistant:latest .
```

### 2. Create .env.docker File

```env
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LOG_LEVEL=INFO
```

### 3. Run Container

**Development (with port exposure):**

```bash
docker run -it \
  --env-file .env.docker \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/chroma_db:/app/chroma_db \
  publication-assistant:latest \
  python app.py --serve-ui --host 0.0.0.0 --port 8000
```

**Production (with resource limits):**

```bash
docker run -d \
  --name publication-assistant \
  --env-file .env.docker \
  -p 8000:8000 \
  -v uploads_volume:/app/uploads \
  -v chroma_volume:/app/chroma_db \
  -m 2g \
  --cpus 2 \
  --restart unless-stopped \
  publication-assistant:latest \
  python app.py --serve-api --host 0.0.0.0 --port 8000
```

### 4. Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  publication-assistant:
    build: .
    container_name: publication-assistant
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - LOG_LEVEL=INFO
      - HOST=0.0.0.0
      - PORT=8000
    volumes:
      - uploads_volume:/app/uploads
      - chroma_volume:/app/chroma_db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "1"
          memory: 1G

volumes:
  uploads_volume:
  chroma_volume:
```

Run with:

```bash
docker-compose up -d
```

---

## Environment Configuration

### Essential Variables

| Variable            | Default  | Description                                     |
| ------------------- | -------- | ----------------------------------------------- |
| `GOOGLE_API_KEY`    | Required | Google Gemini API key                           |
| `GROQ_API_KEY`      | Required | Groq fast LLM API key                           |
| `TAVILY_API_KEY`    | Required | Web search API key                              |
| `LOG_LEVEL`         | INFO     | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `MAX_UPLOAD_BYTES`  | 52428800 | Max file upload size (50MB default)             |
| `MAX_PROMPT_LENGTH` | 100000   | Max prompt input length in bytes                |
| `HOST`              | 0.0.0.0  | Server bind address                             |
| `PORT`              | 8000     | Server port                                     |

### Optional Variables

| Variable           | Default     | Description                              |
| ------------------ | ----------- | ---------------------------------------- |
| `GITHUB_TOKEN`     | None        | GitHub API token for higher rate limits  |
| `DEBUG_MODE`       | false       | Enable debug logging and detailed errors |
| `ENABLE_TELEMETRY` | true        | Enable metrics and monitoring            |
| `CHROMA_DB_PATH`   | ./chroma_db | Vector store storage location            |
| `UPLOADS_DIR`      | ./uploads   | Upload storage location                  |

---

## Running the Application

### Mode 1: Gradio UI (Interactive)

Best for interactive testing and user exploration.

```bash
python app.py --serve-ui [--host 0.0.0.0] [--port 8000]
```

**Features:**

- Web-based UI at `http://localhost:8000`
- File upload support
- Real-time result display
- History tracking

### Mode 2: FastAPI API (Backend)

Best for programmatic integration and CI/CD pipelines.

```bash
python app.py --serve-ui [--host 0.0.0.0] [--port 8000]
```

**Endpoints:**

- `POST /generate` - Submit repository for analysis
- `GET /health` - Health check
- `GET /results/<task_id>` - Retrieve results by ID
- `GET /history` - Get user submission history

### Mode 3: CLI (Batch Processing)

Best for one-off analysis or automated scripts.

```bash
python main.py --repo-path /path/to/repository [--style "Technical Blog"]
```

---

## Health Checks and Monitoring

### 1. Manual Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2026-07-06T10:30:00Z",
  "version": "1.0.0"
}
```

### 2. Container Health Check

Docker automatically checks container health every 30s (see docker-compose.yml).

View health status:

```bash
docker ps
# or
docker inspect publication-assistant | jq '.State.Health'
```

### 3. Monitoring Endpoints

- **Metrics** (Prometheus format): `GET /metrics`
- **Logs** (JSON): Check container logs with `docker logs -f publication-assistant`
- **Performance**: Use `docker stats` to monitor CPU, memory, I/O

### 4. Logs

**Local Development:**

```bash
# All logs
tail -f logs/app.log
```

**Docker:**

```bash
docker logs -f publication-assistant
docker logs --tail 100 publication-assistant
```

---

## Scaling Considerations

### Single Instance

For light to moderate load (< 10 concurrent users):

- Use configuration from Docker Deployment section
- Monitor CPU and memory; adjust resource limits as needed

### Multi-Instance (Load Balanced)

For production with multiple concurrent users:

**Option 1: Docker Swarm**

```bash
docker swarm init
docker service create \
  --name publication-assistant \
  --replicas 3 \
  --publish 8000:8000 \
  --env GOOGLE_API_KEY=$GOOGLE_API_KEY \
  publication-assistant:latest
```

**Option 2: Kubernetes**

Use `kubectl` to deploy multiple replicas with automatic load balancing and scaling.

### Stateless Design

The application is designed to be horizontally scalable:

- No session state stored in memory
- Uploads and results stored in persistent volumes
- Agents are instantiated fresh for each request
- Rate limiting applied per endpoint (not per instance)

### Caching Strategy

- **Vector DB (ChromaDB)**: Local SQLite; replicate across instances if needed
- **Upload Cache**: Shared volume across instances
- **Results Cache**: JSON files with TTL-based cleanup

---

## Troubleshooting

### 1. "API Key Not Found" Error

**Symptom:** LLM agents fail with authentication errors

**Solution:**

```bash
# Verify .env file exists and contains API keys
cat .env
# Ensure keys are valid
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent
```

### 2. Memory Issues

**Symptom:** Container crashes with OOMKilled

**Solution:**

```bash
# Increase memory limit
docker update --memory 4g publication-assistant

# Or in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 4G
```

### 3. Timeout on Large Repositories

**Symptom:** Pipeline fails after 300s

**Solution:**

- Reduce repository size or complexity
- Increase timeout in `resilience/timeout/timeout_manager.py`
- Use CLI mode for batch processing instead of UI

### 4. Port Already in Use

**Symptom:** `Address already in use: ('0.0.0.0', 8000)`

**Solution:**

```bash
# Find process using port 8000
netstat -tulpn | grep 8000  # Linux
lsof -i :8000  # macOS

# Use different port
python app.py --serve-ui --port 8001
```

### 5. ChromaDB Lock Error

**Symptom:** `SQLite database is locked`

**Solution:**

```bash
# Restart the container to release locks
docker restart publication-assistant

# Or clear old lock files
rm -f chroma_db/*.db-shm chroma_db/*.db-wal
```

---

## Performance Tuning

### 1. Agent Parallelization

Current implementation runs agents sequentially. For faster processing:

- Use LangGraph's async execution if available
- Increase `PYTHONUNBUFFERED=1` for streaming logs

### 2. Vector DB Optimization

```python
# In tools/rag_retriever.py, add indexing:
rag.vectorstore.add_index()  # After initial population
```

### 3. Rate Limiting

Configure rate limits to prevent abuse:

```python
# security/middleware/rate_limit_middleware.py
RATE_LIMITS = {
    "generate": "10 per hour",
    "health": "unlimited",
    "history": "100 per hour"
}
```

---

## Backup and Recovery

### 1. Backup Volumes

```bash
docker run --rm -v uploads_volume:/data \
  -v backup_location:/backup \
  alpine tar czf /backup/uploads_$(date +%s).tar.gz -C /data .
```

### 2. Restore Volumes

```bash
docker run --rm -v uploads_volume:/data \
  -v backup_location:/backup \
  alpine tar xzf /backup/uploads_latest.tar.gz -C /data
```

---

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use secrets management** (Docker Secrets, Kubernetes Secrets)
3. **Enable HTTPS** when deploying to public internet (use reverse proxy like Nginx)
4. **Restrict file upload types** (already enforced in `security/validators/file_validators.py`)
5. **Run container as non-root**: `USER appuser` in Dockerfile
6. **Regular security updates**: `pip install --upgrade pip setuptools wheel`

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [Gradio Deployment](https://gradio.app/deployment/)
- [Production Best Practices](./OPERATIONS.md)
