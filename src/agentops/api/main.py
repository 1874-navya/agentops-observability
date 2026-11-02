from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentops import __version__
from agentops.api.routes import analytics, health, otlp, traces
from agentops.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title="AgentOps Observability API",
    version=__version__,
    description="Trace ingestion and analytics for agentic AI applications.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Content-Encoding", "X-API-Key"],
)
app.include_router(health.router)
app.include_router(traces.router)
app.include_router(analytics.router)
app.include_router(otlp.router)
