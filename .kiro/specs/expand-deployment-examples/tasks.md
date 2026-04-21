# Tasks: Expand Module 12 Deployment Examples

## Task 1: Enhance Step 1 Platform Selection with Branching

- [x] 1.1 Update Step 1 to add an explicit agent instruction to load the corresponding platform reference section after the bootcamper selects their deployment target
- [x] 1.2 Add a `search_docs` call with the selected platform name to retrieve current Senzing deployment guidance for that platform
- [x] 1.3 Add brief "If <platform>:" pointers in Steps 3, 5, 6, 7, and 10 that reference the corresponding platform appendix section for non-AWS platforms

## Task 2: Add On-Premises Deployment Reference Section

- [x] 2.1 Add an "On-Premises Deployment Reference" section after the main workflow with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
- [x] 2.2 Include prerequisites: PostgreSQL database, Docker and Docker Compose, network configuration, hardware sizing via `search_docs`
- [x] 2.3 Include architecture overview: Docker Compose multi-service setup, direct host installation alternative, database connectivity
- [x] 2.4 Include configuration steps: environment-specific config files, database connection strings, log aggregation, backup procedures
- [x] 2.5 Include MCP tool references: `sdk_guide` for installation, `search_docs` for PostgreSQL, `find_examples` for Docker Compose patterns, `generate_scaffold` for code structure

## Task 3: Add Azure Deployment Reference Section

- [x] 3.1 Add an "Azure Deployment Reference" section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
- [x] 3.2 Include prerequisites: Azure subscription, Azure CLI, resource group, Azure Container Registry
- [x] 3.3 Include architecture overview: ACI or AKS for compute, Azure Database for PostgreSQL, Key Vault for secrets, Azure Monitor
- [x] 3.4 Include configuration steps: ARM/Bicep/Terraform definitions, managed identity, container image build and push, environment-specific parameter files
- [x] 3.5 Include MCP tool references: `search_docs` for Azure guidance, `generate_scaffold` for code, `find_examples` for container patterns

## Task 4: Add GCP Deployment Reference Section

- [x] 4.1 Add a "GCP Deployment Reference" section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
- [x] 4.2 Include prerequisites: GCP project, gcloud CLI, Artifact Registry, IAM service account
- [x] 4.3 Include architecture overview: Cloud Run or GKE for compute, Cloud SQL for PostgreSQL, Secret Manager, Cloud Monitoring
- [x] 4.4 Include configuration steps: Terraform or Deployment Manager definitions, workload identity, container image build and push, environment-specific variable files
- [x] 4.5 Include MCP tool references: `search_docs` for GCP guidance, `generate_scaffold` for code, `find_examples` for container patterns

## Task 5: Add Kubernetes/Container Deployment Reference Section

- [x] 5.1 Add a "Kubernetes/Container Deployment Reference" section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
- [x] 5.2 Include prerequisites: cluster access, kubectl and Helm v3, container registry, namespace creation
- [x] 5.3 Include architecture overview: Helm chart structure, Deployment/StatefulSet patterns, persistent volume claims, Service and Ingress
- [x] 5.4 Include configuration steps: Helm values files per environment, HPA, liveness/readiness probes, pod disruption budgets
- [x] 5.5 Include MCP tool references: `search_docs` for K8s guidance, `find_examples` for Helm patterns, `generate_scaffold` for code

## Task 6: Validate Final File Structure

- [x] 6.1 Verify the file retains YAML front matter with `inclusion: manual`, the user reference link, Before/After framing, Prerequisites, Phase 1/Phase 2 structure, and all existing step numbers
- [x] 6.2 Verify all existing AWS CDK "If AWS:" blocks in Steps 3, 5, 6, 7, and 10 are preserved unchanged
- [x] 6.3 Verify all four platform reference sections are present with their required subsections (prerequisites, architecture, configuration, MCP tools)
- [x] 6.4 Verify all MCP tool references use correct canonical tool names

## Post-Implementation Updates

After initial implementation, the platform reference sections were extracted into separate steering files per Kiro best practices (manual files should be ≤120 lines):

- `deployment-onpremises.md` (58 lines) — extracted from main file
- `deployment-azure.md` (60 lines) — extracted from main file
- `deployment-gcp.md` (60 lines) — extracted from main file
- `deployment-kubernetes.md` (81 lines) — extracted from main file

Main `module-12-deployment.md` reduced from 549 to 296 lines. All "Platform Reference Section" references updated to "platform steering file" throughout. `agent-instructions.md` and `POWER.md` updated with new file references.
