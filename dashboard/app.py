import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="AgentOps", page_icon="🔎", layout="wide")
st.title("AgentOps Observability")
st.caption("Operational visibility into agent runs, tool calls, token consumption, and latency.")

api_url = os.getenv("AGENTOPS_API_URL", "http://localhost:8000").rstrip("/")
api_key = os.getenv("AGENTOPS_API_KEY", "local-development-only")
headers = {"X-API-Key": api_key}

try:
    overview_response = requests.get(
        f"{api_url}/api/v1/analytics/overview", headers=headers, timeout=5
    )
    overview_response.raise_for_status()
    metrics = overview_response.json()

    columns = st.columns(4)
    columns[0].metric("Traces", metrics["total_traces"])
    columns[1].metric("Failed traces", metrics["failed_traces"])
    columns[2].metric("Tokens", f'{metrics["total_tokens"]:,}')
    columns[3].metric("Average latency", f'{metrics["average_latency_ms"]:.1f} ms')

    response = requests.get(f"{api_url}/api/v1/traces", headers=headers, timeout=10)
    response.raise_for_status()
    traces = response.json()

    st.subheader("Recent traces")
    if traces:
        frame = pd.DataFrame(
            [
                {
                    "Trace ID": item["id"],
                    "Agent": item["agent_name"] or item["name"],
                    "Status": item["status"],
                    "Latency (ms)": item["duration_ms"],
                    "Tokens": item["total_tokens"],
                    "Started": item["started_at"],
                }
                for item in traces
            ]
        )
        st.dataframe(frame, use_container_width=True, hide_index=True)
        selected = st.selectbox("Inspect trace", [item["id"] for item in traces])
        detail = requests.get(
            f"{api_url}/api/v1/traces/{selected}", headers=headers, timeout=10
        )
        detail.raise_for_status()
        st.json(detail.json())
    else:
        st.info("No traces yet. Submit a trace to the ingestion API to populate this dashboard.")
except requests.RequestException as exc:
    st.error(f"AgentOps API unavailable: {exc}")
