# Architecture

## Data path

1. Agent applications create spans using AgentOps helpers or OpenTelemetry APIs.
2. OpenTelemetry applications export OTLP/HTTP binary Protobuf traces to `POST /v1/traces`; applications may also submit the AgentOps JSON trace schema to FastAPI.
3. The OTLP adapter groups spans by trace ID, maps resource/span attributes, validates the resulting model, and persists traces transactionally.
4. FastAPI query and analytics APIs read trace/span data from PostgreSQL.
5. Streamlit consumes the API; it does not connect directly to PostgreSQL.

## Responsibilities

- **Instrumentation:** creates agent, tool, and LLM spans with trace context.
- **OTLP receiver:** handles binary Protobuf trace export over HTTP, optional gzip, resource/span conversion, attribute filtering, and trace grouping.
- **JSON ingestion API:** validates AgentOps trace payloads and batch writes.
- **PostgreSQL:** stores trace summaries and spans with relational keys and query indexes.
- **Analytics service:** computes operational aggregates.
- **Dashboard:** visualizes data through the versioned API.
- **MLflow adapter:** provides a nested MLflow span context manager as an optional integration.

## Data model

A trace represents one logical agent execution. A span represents one operation (agent, tool, LLM, retrieval, chain, or custom). Span identifiers are unique within a trace, so PostgreSQL uses a composite `(trace_id, span_id)` primary key. Parent references may refer to spans outside the current export batch because distributed exporters can send partial trace trees.

## OTLP receiver behavior

The endpoint currently accepts OTLP/HTTP binary Protobuf trace requests. It supports gzip content encoding and enforces a 64 MiB limit on request and decompressed bodies. It returns the OTLP Protobuf success response. OTLP gRPC, metrics, logs, and JSON-Protobuf are not yet implemented.

The receiver extracts service name, agent/tool/LLM kind, model/provider, and GenAI token-usage attributes. For trace-level token totals it prefers LLM spans when available to avoid summing duplicate parent-span counters. Sensitive attribute key patterns and exception messages/stack traces are excluded from storage.

## Reliability and security

- SQLAlchemy connection pooling uses pre-ping.
- Trace IDs are idempotent: re-ingesting an ID replaces its span collection.
- JSON batch ingestion and OTLP export persistence use one database transaction.
- API keys are compared using constant-time comparison.
- Schemas reject unknown fields and bound batch/span sizes.
- Never send secrets, credentials, raw prompts, completions, or personal data in span attributes.
- Before production internet exposure, add TLS, rate limiting, secret rotation, retention policies, backups, and deployment-specific identity/authentication.
