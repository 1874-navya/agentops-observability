def auth_headers():
    return {"X-API-Key": "test-key"}


def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingestion_requires_api_key(client):
    response = client.post("/api/v1/traces", json={"trace_id": "t1", "name": "agent"})
    assert response.status_code == 401


def test_ingest_then_read_trace(client):
    payload = {
        "trace_id": "trace-001",
        "name": "support-agent",
        "agent_name": "support-agent",
        "status": "ok",
        "duration_ms": 123.4,
        "input_tokens": 20,
        "output_tokens": 10,
        "spans": [
            {"span_id": "root", "name": "agent.run", "kind": "agent", "duration_ms": 123.4},
            {
                "span_id": "tool-1",
                "parent_span_id": "root",
                "name": "search",
                "kind": "tool",
                "duration_ms": 30,
            },
        ],
    }
    response = client.post("/api/v1/traces", json=payload, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["span_count"] == 2

    detail = client.get("/api/v1/traces/trace-001", headers=auth_headers())
    assert detail.status_code == 200
    assert detail.json()["total_tokens"] == 30
    assert len(detail.json()["spans"]) == 2


def test_batch_ingestion(client):
    response = client.post(
        "/api/v1/traces/batch",
        json={
            "traces": [
                {"trace_id": "a", "name": "agent-a"},
                {"trace_id": "b", "name": "agent-b"},
            ]
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_analytics_overview(client):
    client.post(
        "/api/v1/traces",
        json={
            "trace_id": "failed-run",
            "name": "agent",
            "status": "error",
            "duration_ms": 50,
            "total_tokens": 12,
        },
        headers=auth_headers(),
    )
    result = client.get("/api/v1/analytics/overview", headers=auth_headers())
    assert result.status_code == 200
    assert result.json()["total_traces"] == 1
    assert result.json()["failed_traces"] == 1
    assert result.json()["total_tokens"] == 12
