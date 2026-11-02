FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE alembic.ini ./
COPY src ./src
COPY migrations ./migrations
COPY dashboard ./dashboard
RUN pip install --no-cache-dir ".[dashboard]"
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=3s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn agentops.api.main:app --host 0.0.0.0 --port 8000"]
