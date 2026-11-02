CREATE TABLE traces (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255),
    status VARCHAR(32) NOT NULL DEFAULT 'unset',
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_ms DOUBLE PRECISION,
    input_tokens INTEGER NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
    output_tokens INTEGER NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
    total_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ix_traces_started_at ON traces (started_at DESC);
CREATE INDEX ix_traces_status_started ON traces (status, started_at DESC);

CREATE TABLE spans (
    trace_id VARCHAR(64) NOT NULL REFERENCES traces(id) ON DELETE CASCADE,
    span_id VARCHAR(64) NOT NULL,
    parent_span_id VARCHAR(64),
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(32) NOT NULL DEFAULT 'custom',
    status VARCHAR(32) NOT NULL DEFAULT 'unset',
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_ms DOUBLE PRECISION,
    input_tokens INTEGER NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
    output_tokens INTEGER NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
    total_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    model VARCHAR(128),
    provider VARCHAR(128),
    error_type VARCHAR(255),
    error_message TEXT,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (trace_id, span_id)
);
CREATE INDEX ix_spans_trace_started ON spans (trace_id, started_at);
CREATE INDEX ix_spans_kind_status ON spans (kind, status);
