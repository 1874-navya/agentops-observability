# API reference

All versioned AgentOps ingestion and query endpoints require the `X-API-Key` header.

- `GET /health` — liveness check (no authentication)
- `GET /ready` — database readiness
- `POST /api/v1/traces` — ingest one AgentOps JSON trace; repeated trace IDs update the existing trace
- `POST /api/v1/traces/batch` — ingest 1–100 JSON traces in one transaction
- `GET /api/v1/traces?limit=50` — recent traces, limit 1–500
- `GET /api/v1/traces/{trace_id}` — one trace and its spans; 404 if absent
- `GET /api/v1/analytics/overview` — aggregate trace, failure, token, and latency metrics
- `POST /v1/traces` — OTLP/HTTP binary Protobuf trace export

## OTLP receiver

The OTLP endpoint accepts `application/x-protobuf` `ExportTraceServiceRequest` bodies, optionally gzip-encoded. It returns a Protobuf `ExportTraceServiceResponse` on success. The endpoint currently supports the traces signal over HTTP, not OTLP gRPC, metrics, or logs.

The receiver groups spans by trace ID, preserves span and parent IDs, maps standard GenAI model/provider/token attributes, and stores the accepted trace batch in a single database transaction. It filters common sensitive attribute keys and does not persist exception messages or stack traces.
