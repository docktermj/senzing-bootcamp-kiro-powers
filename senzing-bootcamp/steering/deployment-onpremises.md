---
inclusion: manual
---

# On-Premises Deployment Reference

Use this section when `deployment_target` is "on-premises" or "local Docker".

## Prerequisites

Before packaging for on-premises deployment, verify:

- PostgreSQL database server available (or SQLite for evaluation only — not recommended for production)
- Docker and Docker Compose installed on the target host(s)
- Network connectivity between application hosts and database server
- Sufficient hardware resources — call `search_docs(query='hardware sizing requirements', version='current')` for current Senzing sizing guidance
- Senzing SDK installed on target hosts — call `sdk_guide(topic='install', platform='linux', language='<chosen_language>', version='current')` for installation steps

👉 "Do you have Docker, Docker Compose, and PostgreSQL all installed and running on your target deployment host(s)?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

WAIT for response.

## Architecture Overview

Call `search_docs(query='on-premises deployment architecture', version='current')` and `find_examples(query='Docker Compose deployment')` for current patterns.

The typical on-premises architecture uses Docker Compose to orchestrate multiple services:

- **Senzing loader service** — processes input data files and loads records
- **Senzing query service** — handles entity resolution queries and API requests
- **PostgreSQL** — stores the Senzing entity repository (can be containerized or external)
- **Optional API gateway** — reverse proxy for the query service (nginx, Traefik)

**Alternative:** For environments where Docker is not available, use direct host installation with systemd services. Call `sdk_guide(topic='install', platform='linux', language='<chosen_language>', version='current')` for bare-metal setup.

## Key Configuration Steps

**Step 3 (Package Code):** Create a `docker-compose.yml` at project root defining all services. Use `generate_scaffold` for the application entry points. No `infra/` directory needed — Docker Compose is the infrastructure definition.

**Step 5 (Containerization):** The `Dockerfile` and `docker-compose.yml` are the primary deployment artifacts. Call `find_examples(query='Dockerfile')` for Senzing container patterns.

**Step 6 (Database):** Install PostgreSQL on the target host or use a containerized PostgreSQL in Docker Compose. Call `search_docs(query='PostgreSQL configuration', version='current')` for Senzing-specific database setup. Store connection strings in `.env` files per environment.

**Step 7 (CI/CD):** Use GitHub Actions, GitLab CI, or Jenkins. Pipeline pushes container images to a private registry (Docker Hub, Harbor, or a self-hosted registry) and deploys via `docker-compose pull && docker-compose up -d` on the target host.

**Step 10 (Scripts):** Create deployment scripts in `deployment/scripts/`:

- `deploy.sh` — pulls latest images and restarts services via Docker Compose
- `rollback.sh` — reverts to previous image tags
- `health-check.sh` — verifies all services are healthy
- `backup-db.sh` — runs `pg_dump` for database backup

## MCP Tool References

- `sdk_guide(topic='install', platform='linux', language='<chosen_language>', version='current')` — SDK installation
- `search_docs(query='PostgreSQL configuration', version='current')` — database setup
- `search_docs(query='on-premises deployment', version='current')` — deployment patterns
- `find_examples(query='Docker Compose deployment')` — Docker Compose examples
- `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` — application code
- `search_docs(query='hardware sizing requirements', version='current')` — hardware guidance
