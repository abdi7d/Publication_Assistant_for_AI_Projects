# Operations Guide

## Overview

This guide covers operational aspects of running the Publication Assistant in production, including monitoring, logging, alerting, maintenance, and incident response.

## Table of Contents

1. [Monitoring & Observability](#monitoring--observability)
2. [Logging Strategy](#logging-strategy)
3. [Alerting](#alerting)
4. [Maintenance](#maintenance)
5. [Performance Baselines](#performance-baselines)
6. [Incident Response](#incident-response)
7. [Capacity Planning](#capacity-planning)

---

## Monitoring & Observability

### Key Metrics to Track

| Metric                    | Target         | Alert Threshold |
| ------------------------- | -------------- | --------------- |
| **Request Latency** (p95) | < 60s          | > 120s          |
| **Error Rate**            | < 1%           | > 5%            |
| **Uptime**                | > 99.5%        | < 99%           |
| **CPU Usage**             | 50-70%         | > 85%           |
| **Memory Usage**          | 60-80%         | > 90%           |
| **Vector DB Size**        | Monitor growth | > 10GB          |
| **Retry Rate**            | < 5%           | > 20%           |
| **Agent Success Rate**    | > 95%          | < 90%           |

### Prometheus Metrics Endpoint

The application exposes metrics at `/metrics` in Prometheus format.

**Example scrape config (prometheus.yml):**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "publication-assistant"
    static_configs:
      - targets: ["localhost:8000"]
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Key Metrics:**

- `publication_assistant_requests_total` - Total requests by endpoint
- `publication_assistant_request_duration_seconds` - Request latency histogram
- `publication_assistant_errors_total` - Errors by type
- `publication_assistant_agent_success_rate` - Agent success rates
- `publication_assistant_retry_count` - Retry attempts per request
- `publication_assistant_vector_db_size_bytes` - ChromaDB size

### Health Check Strategy

#### Level 1: Basic Liveness

```bash
GET /health
```

Response: `{"status": "healthy"}`

**Frequency:** Every 5 seconds
**Timeout:** 3 seconds
**Success Threshold:** 2/3 checks

#### Level 2: Readiness

```bash
GET /health?detailed=true
```

Response:

```json
{
  "status": "ready",
  "components": {
    "api": "healthy",
    "llm": "healthy",
    "vector_db": "healthy",
    "web_search": "degraded"
  }
}
```

**Frequency:** Every 15 seconds
**Success Threshold:** All critical components healthy

#### Level 3: Deep Diagnostics

Periodically run full integration tests:

```bash
pytest tests/integration/ -v
```

---

## Logging Strategy

### Log Levels and Usage

| Level        | Usage                            | Example                                  |
| ------------ | -------------------------------- | ---------------------------------------- |
| **DEBUG**    | Development/troubleshooting only | "LLM response tokens: 1024"              |
| **INFO**     | Important state changes          | "Pipeline started for repo: org/project" |
| **WARNING**  | Recoverable issues               | "Retry attempt 2/3 for web search"       |
| **ERROR**    | Failures requiring intervention  | "Agent failed with ValueError"           |
| **CRITICAL** | System-level failures            | "Vector DB corrupted"                    |

### Log Output Formats

#### Structured JSON Logging

All logs should be JSON for machine parsing:

```json
{
  "timestamp": "2026-07-06T10:30:00.123Z",
  "level": "INFO",
  "logger": "orchestration.graph",
  "message": "Pipeline completed successfully",
  "pipeline_id": "req-12345",
  "duration_ms": 45000,
  "agents": {
    "repo_analyzer": "success",
    "metadata_recommender": "success",
    "content_improver": "success",
    "reviewer_critic": "success",
    "fact_checker": "success"
  }
}
```

#### Log Aggregation

**For Docker:**

```bash
# Forward logs to ELK stack or CloudWatch
docker run -d \
  --log-driver awslogs \
  --log-opt awslogs-group=/ecs/publication-assistant \
  publication-assistant:latest
```

**For Kubernetes:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: publication-assistant
spec:
  containers:
    - name: app
      image: publication-assistant:latest
      env:
        - name: LOG_LEVEL
          value: INFO
        - name: LOG_FORMAT
          value: json
```

### Log Retention

- **Development**: 7 days
- **Staging**: 30 days
- **Production**: 90 days
- **Archive**: Long-term storage (AWS S3, GCS)

### Debugging Logs

Enable debug mode for specific issues:

```bash
# Enable debug logging temporarily
LOG_LEVEL=DEBUG python app.py --serve-api

# Debug specific module
python -c "import logging; logging.getLogger('tools.web_search').setLevel(logging.DEBUG)"
```

---

## Alerting

### Alert Rules

**High Priority (Page on-call):**

```yaml
- alert: HighErrorRate
  expr: rate(publication_assistant_errors_total[5m]) > 0.05
  for: 5m

- alert: HighLatency
  expr: histogram_quantile(0.95, publication_assistant_request_duration_seconds) > 120
  for: 10m

- alert: VectorDBDown
  expr: up{job="publication-assistant"} == 0
  for: 1m
```

**Medium Priority (Page if persists):**

```yaml
- alert: HighMemoryUsage
  expr: container_memory_usage_bytes > 1.9e9
  for: 15m

- alert: HighRetryRate
  expr: rate(publication_assistant_retry_count[5m]) > 0.2
  for: 10m
```

**Low Priority (Ticket only):**

```yaml
- alert: ExcessiveVectorDBGrowth
  expr: rate(publication_assistant_vector_db_size_bytes[24h]) > 1e9
  for: 1h
```

### Notification Channels

- **Critical**: PagerDuty, SMS, Slack #critical-alerts
- **Warning**: Email, Slack #alerts
- **Info**: Slack #operations

---

## Maintenance

### Daily Tasks

- [ ] Review error logs for patterns
- [ ] Check disk space (uploads, chroma_db)
- [ ] Verify backup completions
- [ ] Monitor API key expiration status

### Weekly Tasks

- [ ] Review performance metrics and trends
- [ ] Clean up old uploads (>30 days)
- [ ] Test disaster recovery procedure (once monthly)
- [ ] Review security logs for suspicious activity

### Monthly Tasks

- [ ] Rotate API keys and secrets
- [ ] Update dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Optimize ChromaDB indexes
- [ ] Analyze usage patterns and capacity needs
- [ ] Review and prune test coverage gaps

### Quarterly Tasks

- [ ] Full security audit
- [ ] Performance benchmarking
- [ ] Disaster recovery drill
- [ ] Update documentation

### Backup and Recovery

**Backup Schedule:**

```bash
# Daily automated backups
0 2 * * * docker exec publication-assistant \
  tar czf /backup/chroma_$(date +%Y%m%d_%H%M%S).tar.gz /app/chroma_db
```

**Recovery Procedure:**

1. Stop the container: `docker stop publication-assistant`
2. Restore from backup: `tar xzf backup/chroma_*.tar.gz -C ./`
3. Start container: `docker start publication-assistant`
4. Verify health: `curl http://localhost:8000/health`

---

## Performance Baselines

### Expected Performance Metrics

**Repository Analysis Pipeline:**

| Stage                   | Expected Duration | Notes                      |
| ----------------------- | ----------------- | -------------------------- |
| Repo Parsing            | 2-5s              | Local repos faster         |
| Metadata Recommendation | 3-8s              | LLM inference time         |
| Content Improvement     | 10-30s            | Includes web search        |
| Review & Critique       | 5-15s             | Quick scoring              |
| Fact Checking           | 5-20s             | ArXiv lookups              |
| **Total**               | **30-80s**        | Depends on repo complexity |

### Resource Consumption

**Per Request:**

| Resource | Typical   | Peak                   |
| -------- | --------- | ---------------------- |
| CPU      | 1-2 cores | 3-4 cores (during RAG) |
| Memory   | 256MB     | 512MB                  |
| Network  | 1-5MB     | 10-20MB (web search)   |
| Disk I/O | 10-50MB/s | 100MB/s (RAG)          |

**System Total:**

| Resource | 1 User    | 5 Users  | 10 Users |
| -------- | --------- | -------- | -------- |
| CPU      | 0.5 cores | 2 cores  | 4 cores  |
| Memory   | 1GB       | 2GB      | 3GB      |
| Network  | 100 Kbps  | 500 Kbps | 1 Mbps   |

### Load Test Results

```bash
# Run load test
pytest tests/performance/test_concurrency_and_stress.py -v

# Expected results:
# - 5 concurrent users: 100% success rate
# - 10 concurrent users: 98% success rate
# - 20 concurrent users: 90% success rate
```

---

## Incident Response

### Incident Severity Levels

| Level  | Description                          | Response Time       |
| ------ | ------------------------------------ | ------------------- |
| **P1** | Service completely down              | Immediate (< 5 min) |
| **P2** | Severe degradation (>50% error rate) | < 15 min            |
| **P3** | Minor issues (< 5% error rate)       | < 1 hour            |
| **P4** | Cosmetic/non-critical                | Next business day   |

### Response Procedures

#### P1: Service Down

1. **Immediate:** Check container status

   ```bash
   docker ps -a
   docker logs publication-assistant --tail 50
   ```

2. **Diagnosis:** Check health endpoint

   ```bash
   curl -v http://localhost:8000/health
   ```

3. **Recovery:** Restart container

   ```bash
   docker restart publication-assistant
   docker exec publication-assistant curl http://localhost:8000/health
   ```

4. **If restart fails:** Redeploy from image
   ```bash
   docker stop publication-assistant
   docker run -d --name publication-assistant ...
   ```

#### P2: High Error Rate

1. **Analyze:** Check logs for error patterns

   ```bash
   docker logs publication-assistant | grep ERROR | tail -20
   ```

2. **Identify:** Common causes
   - API key invalid/expired
   - Vector DB corrupted
   - Out of memory
   - Network timeout

3. **Mitigate:** Apply fix based on root cause

   ```bash
   # If API key: update environment and restart
   docker restart publication-assistant

   # If memory: increase limits
   docker update --memory 4g publication-assistant

   # If DB: clear and rebuild
   docker exec publication-assistant rm -rf /app/chroma_db
   ```

#### P3: Minor Issues

1. Review error logs
2. Check metrics for anomalies
3. Apply targeted fix
4. Monitor for recurrence

### Escalation Path

```
Issue Detected
    ↓
Initial Response (on-call engineer)
    ↓
    ├─ Resolved? → Document & Close
    └─ Unresolved after 15 min
        ↓
        Escalate to Senior Engineer
        ↓
        ├─ Resolved? → Document & Close
        └─ Escalate to Architecture Team
```

---

## Capacity Planning

### Growth Projections

**Year 1 Targets:**

| Metric           | Q1  | Q2   | Q3   | Q4    |
| ---------------- | --- | ---- | ---- | ----- |
| Concurrent Users | 5   | 10   | 20   | 50    |
| Requests/day     | 500 | 2000 | 5000 | 15000 |
| Storage (GB)     | 2   | 5    | 10   | 20    |

### Infrastructure Scaling

**Current Setup (1-10 concurrent users):**

- 1 container instance
- 2 CPU cores, 2GB RAM
- Single disk volume

**Future (10-50 concurrent users):**

- 3 container instances (load balanced)
- 4 CPU cores per instance, 4GB RAM each
- Shared persistent storage (NFS or cloud storage)

**Enterprise (50+ concurrent users):**

- Kubernetes cluster (5+ replicas)
- Auto-scaling based on CPU/memory
- Distributed vector DB (e.g., Milvus)
- Multi-region deployment

---

## Contact & Resources

- **On-Call Escalation**: [PagerDuty Link]
- **Incident Channel**: #incidents on Slack
- **Documentation**: [Project Wiki]
- **Runbooks**: [Runbooks Repository]
