# Architecture

1. Agent applications create operation spans using AgentOps helpers or OpenTelemetry APIs.
2. Applications export spans to an OTLP endpoint or submit the vendor-neutral AgentOps schema to FastAPI.
3. FastAPI validates and authenticates payloads and persists trace/span rows in PostgreSQL.
4. Analytics endpoints aggregate run health, token volume, and latency.
5. Streamlit consumes the API; it does not connect directly to PostgreSQL.

A trace represents one logical agent execution. A span represents one operation (agent, tool, LLM, retrieval, chain, or custom). Span identifiers are unique within a trace, so PostgreSQL uses a composite (trace_id, span_id) primary key. Parent references must resolve within the submitted trace.

Batch ingestion is transactional. Trace IDs are idempotent: re-ingesting an ID replaces its span collection. API keys are compared using constant-time comparison. Schemas reject unknown fields and bound batch/span sizes.

Before public production exposure, add TLS, rate limits, secret rotation, retention policies, backups, and deployment-specific identity. Never send secrets, prompts, completions, or personal data in span attributes.
