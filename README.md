# AgentOps Observability

An open-source observability platform for agentic AI applications. Ingest traces, inspect agent and tool spans, measure latency and token usage, and explore failures through a REST API and dashboard.

## Architecture

```text
Agent applications
  ├─ AgentOps instrumentation helpers
  ├─ OpenTelemetry SDK + OTLP/HTTP exporter
  └─ MLflow tracing adapter (optional)
          |
          v
   FastAPI OTLP + JSON ingestion
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
- OTLP traces: http://localhost:8000/v1/traces

The API container runs the Alembic migrations before starting FastAPI.

## Ingest a trace with JSON

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

## Export OpenTelemetry spans directly

Install the optional integration and configure the HTTP exporter to point at the AgentOps OTLP endpoint. Include the API key as an exporter header:

```python
import os

from agentops.integrations.opentelemetry import configure_otel
from agentops.instrumentation.spans import agent_span, llm_span, tool_span

provider = configure_otel(
    service_name="demo-agent",
    traces_endpoint="http://localhost:8000/v1/traces",
    headers={"X-API-Key": os.environ["AGENTOPS_API_KEY"]},
)

with agent_span("agent.run", agent_name="demo-agent"):
    with tool_span("knowledge.search", tool_name="search"):
        pass
    with llm_span("demo-model", provider="demo", input_tokens=40, output_tokens=12):
        pass

provider.force_flush()
provider.shutdown()
```

The OTLP HTTP receiver accepts binary Protobuf trace requests, supports gzip request encoding, enforces a 64 MiB request/decompressed-body limit, filters sensitive attribute keys, and persists each export transactionally. The receiver currently supports the OTLP traces signal over HTTP; it does not implement OTLP gRPC, metrics, or logs.

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

## MLflow

MLflow spans are available through `mlflow_span` from `agentops.integrations.mlflow`. It uses MLflow's fluent `start_span` API and remains an optional dependency.

## Current scope

- [x] FastAPI single and batch trace ingestion
- [x] Trace and span query APIs
- [x] PostgreSQL models and Alembic initial migration
- [x] Transactional batch ingestion and trace upserts
- [x] Token and latency overview analytics
- [x] Native OTLP/HTTP binary Protobuf trace receiver
- [x] OpenTelemetry instrumentation helpers and OTLP exporter setup
- [x] MLflow tracing span adapter
- [x] Streamlit trace dashboard
- [x] Docker Compose and GitHub Actions CI
- [x] Unit, API integration, and OTLP receiver tests
- [ ] OTLP gRPC, metrics, and logs
- [ ] advanced filtering, cost attribution, retention, and alerting
- [ ] production auth scopes, quotas, and performance benchmarks

## Security

Never commit `.env` or send secrets, raw prompts, completions, or sensitive customer data in trace attributes. The receiver filters common sensitive attribute-key patterns, but application owners remain responsible for data minimization. The Compose setup is for local development; harden authentication, TLS, rate limits, secret management, backups, and retention before public production deployment.

## License

MIT.
