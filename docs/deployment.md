# Local deployment

1. Copy .env.example to .env.
2. Set a unique random AGENTOPS_API_KEY.
3. Start services with docker compose up --build -d.
4. Check /health and /ready.
5. Open the API at port 8000 and dashboard at port 8501.

Compose uses a persistent named PostgreSQL volume. It is intended for local development, not as a hardened public deployment. Production deployments should use managed PostgreSQL, TLS, a secret manager, backups, monitoring, rate limits, and a non-root container user. Restrict CORS origins.
