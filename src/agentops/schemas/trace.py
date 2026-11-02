from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SpanIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    span_id: str = Field(min_length=1, max_length=64)
    parent_span_id: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    kind: Literal["agent", "tool", "llm", "retrieval", "chain", "custom"] = "custom"
    status: Literal["unset", "ok", "error"] = "unset"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    model: str | None = Field(default=None, max_length=128)
    provider: str | None = Field(default=None, max_length=128)
    error_type: str | None = Field(default=None, max_length=255)
    error_message: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class TraceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    agent_name: str | None = Field(default=None, max_length=255)
    status: Literal["unset", "ok", "error"] = "unset"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    spans: list[SpanIn] = Field(default_factory=list, max_length=2000)

    @model_validator(mode="after")
    def validate_span_ids(self):
        ids = [span.span_id for span in self.spans]
        if len(ids) != len(set(ids)):
            raise ValueError("span_id values must be unique within a trace")
        known = set(ids)
        for span in self.spans:
            if span.parent_span_id == span.span_id:
                raise ValueError("a span cannot be its own parent")
            if span.parent_span_id and span.parent_span_id not in known:
                raise ValueError(f"unknown parent_span_id: {span.parent_span_id}")
        return self


class TraceBatchIn(BaseModel):
    traces: list[TraceIn] = Field(min_length=1, max_length=100)


class SpanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    span_id: str
    parent_span_id: str | None
    name: str
    kind: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: float | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str | None
    provider: str | None
    error_type: str | None
    error_message: str | None
    attributes: dict[str, Any]


class TraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    agent_name: str | None
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: float | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    metadata_json: dict[str, Any]
    spans: list[SpanOut]


class IngestResult(BaseModel):
    trace_id: str
    span_count: int
    created: bool
