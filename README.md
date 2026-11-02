# AgentOps Observability

An open-source observability platform for agentic AI applications. AgentOps ingests structured traces, persists runs and spans in PostgreSQL, exposes trace and analytics APIs, and provides a Streamlit dashboard.

## Architecture

```text
Agent applications
  └─ AgentOps instrumentation / OpenTelemetry / MLflow adapter
       └─ FastAPI ingestion API
            └─ PostgreSQL (traces, spans, metrics)
                 ├─ Analytics API
                 └─ Streamlit dashboard
```

Core ingestion is vendor-neutral. OpenTelemetry supplies distributed trace context and spans; MLflow is an optional adapter. The service does not require a Databricks workspace to run.

## Status

v0.1 foundation is being implemented incrementally. Initial scope: trace ingestion, PostgreSQL persistence, analytics, dashboard, Docker Compose, and CI. OpenTelemetry and MLflow runtime adapters follow in the next milestone.

## Planned quick start

Copy `.env.example` to `.env`, set a unique `AGENTOPS_API_KEY`, and run:

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs  
Dashboard: http://localhost:8501

See `docs/` for architecture, API, and deployment details.
