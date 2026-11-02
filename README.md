# AgentOps Observability

An open-source observability platform for agentic AI applications. Ingest traces, inspect agent and tool spans, measure latency and token usage, and explore failures through a REST API and dashboard.

## Architecture

```text
Agent applications
  ├─ AgentOps instrumentation helpers
  ├─ OpenTelemetry SDK + OTLP exporter
  └─ MLflow tracing adapter (optional)
          |
          v
    FastAPI ingestion API
          |
          v
 PostgreSQL traces + spans
      ├── Analytics API
      └── Streamlit dashboard
```

The core API is vendor-neutral. OpenTelemetry and MLflow are optional integrations; a Databricks workspace is not required for local operation.

## Quick start

```bash
cp .env.example .env
# Edit .env and set a long random AGENTOPS_API_KEY
docker compose up --build
```

- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- Dashboard: http://localhost:8501

The API container runs the Alembic migrations before starting FastAPI.

## Ingest a trace

```bash
curl -X POST http://localhost:8000/api/v1/traces \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: replace-this-with-a-long-random-secret' \
  -d '{
    "trace_id": "demo-trace-001",
    "name": "customer-support-agent",
    "agent_name": "support-agent",
    "status": "ok",
    "duration_ms": 420.5,
    "input_tokens": 120,
    "output_tokens": 60,
    "spans": [
      {"span_id": "agent-root", "name": "agent.run", "kind": "agent", "duration_ms": 420.5},
      {"span_id": "tool-search", "parent_span_id": "agent-root", "name": "search_knowledge_base", "kind": "tool", "duration_ms": 85.2}
    ]
  }'
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,dashboard,otel,mlflow]'
cp .env.example .env
alembic upgrade head
uvicorn agentops.api.main:app --reload
pytest
ruff check .
```

## Optional instrumentation

```python
from agentops.instrumentation.spans import agent_span, tool_span, llm_span

with agent_span("planner", agent_name="support"):
    with tool_span("knowledge_search", tool_name="search"):
        ...
    with llm_span("my-model", provider="my-provider", input_tokens=120, output_tokens=60):
        ...
```

Configure OTLP export with `configure_otel(service_name="my-agent", traces_endpoint="http://localhost:4318/v1/traces")` from `agentops.integrations.opentelemetry`. MLflow spans are available through `mlflow_span` from `agentops.integrations.mlflow`.

## Current scope

- [x] FastAPI single and batch trace ingestion
- [x] Trace and span query APIs
- [x] PostgreSQL models and Alembic initial migration
- [x] Transactional batch ingestion and trace upserts
- [x] Token and latency overview analytics
- [x] OpenTelemetry instrumentation helpers and OTLP exporter setup
- [x] MLflow tracing span adapter
- [x] Streamlit trace dashboard
- [x] Docker Compose and GitHub Actions CI
- [x] Unit and API integration tests
- [ ] OTLP receiver/collector pipeline into AgentOps persistence
- [ ] advanced filtering, cost attribution, retention, and alerting
- [ ] production auth scopes, quotas, and performance benchmarks

## Security

Never commit `.env` or send secrets, raw prompts, completions, or sensitive customer data in trace attributes. The Compose setup is for local development; harden authentication, TLS, rate limits, secret management, backups, and retention before public production deployment.

## License

MIT.
