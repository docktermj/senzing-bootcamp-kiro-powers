---
inclusion: manual
---

# GCP Deployment Reference

Use this section when `deployment_target` is "Google Cloud" or "GCP".

## Prerequisites

Before packaging for GCP deployment, verify:

- GCP project with billing enabled
- gcloud CLI installed and authenticated (`gcloud auth login`, `gcloud config set project <project_id>`)
- Artifact Registry repository created for storing container images (preferred over Container Registry)
- IAM service account with appropriate roles for compute, database, and secrets access
- Call `search_docs(query='GCP deployment', version='current')` for current Senzing GCP guidance

👉 "Do you have a GCP project with the gcloud CLI installed and an Artifact Registry repository created for container images?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

WAIT for response.

## Architecture Overview

Call `search_docs(query='GCP deployment architecture', version='current')` for current Senzing GCP patterns.

The typical GCP architecture includes:

- **Compute:** Cloud Run for serverless container execution (simpler, auto-scaling), or Google Kubernetes Engine (GKE) for full Kubernetes control
- **Database:** Cloud SQL for PostgreSQL with automated backups, high availability, and private IP access
- **Secrets:** Secret Manager for database credentials, API keys, and Senzing license — accessed via workload identity (GKE) or service account (Cloud Run)
- **Monitoring:** Cloud Monitoring for metrics and alerting, Cloud Logging for centralized log aggregation
- **Networking:** VPC with private services access for Cloud SQL, Cloud NAT for outbound traffic from private subnets

## Key Configuration Steps

**Step 3 (Package Code):** Create an `infra/` directory for Terraform configurations or Deployment Manager templates. Call `generate_scaffold` for the application entry points. Use Terraform modules for reusable infrastructure components.

**Step 5 (Containerization):** Build the container image and push to Artifact Registry. Call `find_examples(query='container deployment')` for Senzing container patterns. Use Cloud Build for CI-driven image builds or `docker push` for local builds.

**Step 6 (Database):** Provision Cloud SQL for PostgreSQL. Call `search_docs(query='PostgreSQL configuration', version='current')` for Senzing-specific database setup. Configure:

- Private IP for secure database access within the VPC
- Workload identity (GKE) or service account credentials (Cloud Run) for authentication
- Automated backups and point-in-time recovery

**Step 7 (CI/CD):** Use Cloud Build or GitHub Actions. Pipeline builds the container image, pushes to Artifact Registry, and deploys to Cloud Run (`gcloud run deploy`) or GKE (`helm upgrade`). Call `search_docs(query='GCP CI/CD deployment', version='current')` for current pipeline patterns.

**Step 10 (Scripts):** Create deployment scripts in `deployment/scripts/`:

- `deploy.sh` — runs `gcloud run deploy` (Cloud Run) or `helm upgrade` (GKE) for the target environment
- `rollback.sh` — reverts to previous Cloud Run revision or Helm release revision
- `health-check.sh` — verifies service health via Cloud Monitoring or direct HTTP probes
- `backup-db.sh` — triggers Cloud SQL backup or exports data to Cloud Storage

## MCP Tool References

- `search_docs(query='GCP deployment', version='current')` — Senzing GCP guidance
- `search_docs(query='PostgreSQL configuration', version='current')` — database setup
- `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` — application code
- `find_examples(query='container deployment')` — containerization patterns
- `search_docs(query='GCP CI/CD deployment', version='current')` — pipeline patterns
