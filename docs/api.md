# API reference

All versioned endpoints require the X-API-Key header.

- GET /health — liveness check (no authentication)
- GET /ready — database readiness
- POST /api/v1/traces — ingest one trace; repeated trace IDs update the existing trace
- POST /api/v1/traces/batch — ingest 1–100 traces in one transaction
- GET /api/v1/traces?limit=50 — recent traces, limit 1–500
- GET /api/v1/traces/{trace_id} — one trace and its spans; 404 if absent
- GET /api/v1/analytics/overview — aggregate trace, failure, token, and latency metrics

OpenAPI UI: /docs
