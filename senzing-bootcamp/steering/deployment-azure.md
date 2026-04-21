---
inclusion: manual
---

# Azure Deployment Reference

Use this section when `deployment_target` is "Azure".

## Prerequisites

Before packaging for Azure deployment, verify:

- Azure subscription with appropriate permissions (Contributor role or higher on the target resource group)
- Azure CLI (`az`) installed and authenticated — call `search_docs(query='Azure CLI setup', version='current')` for Senzing-specific guidance
- Resource group created for the Senzing deployment
- Azure Container Registry (ACR) provisioned for storing container images
- Familiarity with the chosen deployment method (ARM templates, Bicep, Terraform, or Azure Portal)

👉 "Do you have an Azure subscription and the Azure CLI installed? Have you already created a resource group for this deployment?" WAIT for response.

## Architecture Overview

Call `search_docs(query='Azure deployment architecture', version='current')` for current Senzing Azure patterns.

The typical Azure architecture includes:

- **Compute:** Azure Container Instances (ACI) for simple deployments, or Azure Kubernetes Service (AKS) for scalable production workloads
- **Database:** Azure Database for PostgreSQL — Flexible Server with encryption at rest and automated backups
- **Secrets:** Azure Key Vault for database credentials, API keys, and Senzing license — accessed via managed identity
- **Monitoring:** Azure Monitor and Log Analytics workspace for centralized logging, metrics, and alerting
- **Networking:** Virtual Network with subnets for compute and database tiers, Network Security Groups for access control

## Key Configuration Steps

**Step 3 (Package Code):** Create an `infra/` directory for infrastructure definitions. Use ARM templates, Bicep, or Terraform depending on the bootcamper's chosen deployment method. Call `generate_scaffold` for the application entry points.

**Step 5 (Containerization):** Build the container image and push to ACR. The `Dockerfile` is the same regardless of platform. Call `find_examples(query='container deployment')` for Senzing container patterns. Use `az acr build` for cloud-based image builds or `docker push` for local builds.

**Step 6 (Database):** Provision Azure Database for PostgreSQL — Flexible Server. Call `search_docs(query='PostgreSQL configuration', version='current')` for Senzing-specific database setup. Configure:

- Private endpoint or VNet integration for secure database access
- Managed identity on the compute resource for passwordless authentication (or store credentials in Key Vault)
- Automated backups and point-in-time restore

**Step 7 (CI/CD):** Use Azure DevOps Pipelines or GitHub Actions. Pipeline builds the container image, pushes to ACR, and deploys to ACI/AKS. Call `search_docs(query='Azure CI/CD deployment', version='current')` for current pipeline patterns.

**Step 10 (Scripts):** Create deployment scripts in `deployment/scripts/`:

- `deploy.sh` — runs `az container create` (ACI) or `helm upgrade` (AKS) for the target environment
- `rollback.sh` — reverts to previous container image tag or Helm release revision
- `health-check.sh` — verifies service health via Azure Monitor or direct HTTP probes
- `backup-db.sh` — triggers Azure PostgreSQL backup or exports data

## MCP Tool References

- `search_docs(query='Azure deployment', version='current')` — Senzing Azure guidance
- `search_docs(query='PostgreSQL configuration', version='current')` — database setup
- `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` — application code
- `find_examples(query='container deployment')` — containerization patterns
- `search_docs(query='Azure CI/CD deployment', version='current')` — pipeline patterns
