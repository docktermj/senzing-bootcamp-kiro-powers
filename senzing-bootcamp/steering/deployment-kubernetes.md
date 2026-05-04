---
inclusion: manual
---

# Kubernetes/Container Deployment Reference

Use this section when `deployment_target` is "Kubernetes", "K8s", or when the bootcamper wants a provider-agnostic container orchestration approach. This applies to any Kubernetes cluster — EKS, AKS, GKE, on-premises (kubeadm, Rancher), or local (minikube, kind).

## Prerequisites

Before packaging for Kubernetes deployment, verify:

- Kubernetes cluster access with `kubectl` configured and authenticated
- Helm v3 installed for chart-based deployments
- Container registry accessible from the cluster (Docker Hub, ECR, ACR, Artifact Registry, Harbor, or any private registry)
- Namespace created for Senzing workloads (e.g., `kubectl create namespace senzing`)
- Call `search_docs(query='Kubernetes deployment', version='current')` for current Senzing Kubernetes guidance

👉 "What Kubernetes cluster are you targeting — a managed service (EKS, AKS, GKE), an on-premises cluster, or a local cluster (minikube, kind)? And do you have Helm v3 installed?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

WAIT for response.

## Architecture Overview

Call `search_docs(query='Kubernetes deployment architecture', version='current')` and `find_examples(query='Kubernetes Helm')` for current Senzing Kubernetes patterns.

The typical Kubernetes architecture includes:

- **Loader:** Kubernetes Job or Deployment for batch data loading — runs to completion, then scales to zero
- **Query service:** Deployment with multiple replicas behind a Service, exposed via Ingress or LoadBalancer
- **Database:** External managed PostgreSQL (recommended) or a PostgreSQL StatefulSet with PersistentVolumeClaims for self-managed clusters
- **Configuration:** ConfigMap for Senzing engine configuration, Secret for database credentials and license
- **Networking:** Service for internal communication, Ingress for external API access, NetworkPolicy for pod-to-pod restrictions

## Key Configuration Steps

**Step 3 (Package Code):** Create a `helm/` directory for the Helm chart. Structure:

- `helm/senzing/Chart.yaml` — chart metadata
- `helm/senzing/values.yaml` — default configuration values
- `helm/senzing/templates/` — Kubernetes resource templates (Deployment, Service, ConfigMap, Secret, Job)

Call `generate_scaffold` for the application entry points. Call `find_examples(query='Kubernetes Helm')` for Helm chart patterns.

**Step 5 (Containerization):** Build the container image and push to the cluster-accessible registry. The `Dockerfile` is the same regardless of platform. Call `find_examples(query='Dockerfile')` for Senzing container patterns. Tag images with the git commit SHA or semantic version for traceability.

**Step 6 (Database):** Use an external managed PostgreSQL service (Cloud SQL, RDS, Azure Database) or deploy PostgreSQL as a StatefulSet within the cluster. Call `search_docs(query='PostgreSQL configuration', version='current')` for Senzing-specific database setup. Configure:

- PersistentVolumeClaim for database storage (if self-managed)
- Kubernetes Secret for database connection string
- Init container or Job to run database schema setup before the first deployment

**Step 7 (CI/CD):** Use GitHub Actions, GitLab CI, or any CI system that can run `helm upgrade`. Pipeline builds the container image, pushes to the registry, and deploys via `helm upgrade --install senzing helm/senzing/ -f values-<env>.yaml`. Call `search_docs(query='Kubernetes CI/CD deployment', version='current')` for current patterns.

**Step 10 (Scripts):** Create deployment scripts in `deployment/scripts/`:

- `deploy.sh` — runs `helm upgrade --install` with the appropriate values file for the target environment
- `rollback.sh` — runs `helm rollback senzing <revision>` to revert to a previous release
- `health-check.sh` — verifies pod health via `kubectl get pods` and readiness probe status
- `backup-db.sh` — runs `pg_dump` via a Kubernetes Job or connects to the managed database for backup

Create Helm values files per environment:

- `helm/senzing/values-dev.yaml` — development settings (1 replica, debug logging, relaxed resource limits)
- `helm/senzing/values-staging.yaml` — staging settings (2 replicas, info logging, production-like limits)
- `helm/senzing/values-prod.yaml` — production settings (3+ replicas, warn logging, strict resource limits, HPA enabled)

**Scaling:** Configure Horizontal Pod Autoscaler (HPA) for the query service based on CPU/memory utilization. Set Pod Disruption Budgets (PDB) to maintain availability during rolling upgrades. Call `search_docs(query='scaling', version='current')` for Senzing-specific scaling guidance.

**Health checks:** Define liveness and readiness probes on all Senzing containers:

- Liveness probe: HTTP GET `/health` or TCP socket check — restarts unhealthy pods
- Readiness probe: HTTP GET `/ready` — removes unready pods from Service endpoints

## MCP Tool References

- `search_docs(query='Kubernetes deployment', version='current')` — Senzing Kubernetes guidance
- `search_docs(query='container deployment', version='current')` — container best practices
- `find_examples(query='Kubernetes Helm')` — Helm chart patterns
- `find_examples(query='Dockerfile')` — Dockerfile patterns
- `search_docs(query='PostgreSQL configuration', version='current')` — database setup
- `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` — application code
- `search_docs(query='scaling', version='current')` — scaling guidance
