# Design Document: Expand Module 12 Deployment Examples

## Overview

This design describes how to expand the Module 12 (Deployment and Packaging) steering file to include deployment guidance for multiple platforms beyond AWS CDK. The expansion adds four new platform-specific reference sections (on-premises, Azure, GCP, Kubernetes) and enhances the existing Step 1 platform selection to branch into these sections. The file being modified is `senzing-bootcamp/steering/module-12-deployment.md`.

The existing AWS CDK content remains intact. New platform sections are added as a reference appendix after the main workflow, keeping the primary step flow uncluttered. Each platform section provides workflow structure (prerequisites, architecture, configuration, MCP tool references) while delegating technical specifics to MCP tool calls at runtime.

## Architecture

### File Structure

The expanded steering file extends the current structure with platform-specific reference sections:

```text
module-12-deployment.md
├── YAML front matter (inclusion: manual)
├── Title, user reference, language/preferences note
├── Prerequisites, Before/After, Two-phase explanation
├── Step 1: Deployment Target (ENHANCED — adds platform branching)
├── Phase 1: Packaging (Steps 2-11, existing — AWS "If AWS" blocks preserved)
├── Phase 2: Deployment (Steps 12-16, existing — unchanged)
├── --- (section break)
├── Platform Reference Sections (NEW)
│   ├── On-Premises Deployment Reference
│   │   ├── Prerequisites
│   │   ├── Architecture Overview
│   │   ├── Key Configuration Steps
│   │   └── MCP Tool References
│   ├── Azure Deployment Reference
│   │   ├── Prerequisites
│   │   ├── Architecture Overview
│   │   ├── Key Configuration Steps
│   │   └── MCP Tool References
│   ├── GCP Deployment Reference
│   │   ├── Prerequisites
│   │   ├── Architecture Overview
│   │   ├── Key Configuration Steps
│   │   └── MCP Tool References
│   └── Kubernetes/Container Deployment Reference
│       ├── Prerequisites
│       ├── Architecture Overview
│       ├── Key Configuration Steps
│       └── MCP Tool References
```

### Design Decisions

**Appendix approach over inline branching:** Platform sections are placed after the main workflow as reference blocks rather than inlining platform-specific content into every step. This keeps the primary workflow readable and avoids deeply nested conditional blocks. The agent reads the relevant platform section once at Step 1 and applies its guidance throughout the packaging/deployment phases.

**MCP-first content strategy:** Each platform section provides the workflow skeleton (what to do and in what order) but delegates specific CLI commands, version numbers, and configuration values to MCP tool calls. This prevents the steering file from becoming stale as Senzing's deployment recommendations evolve.

**Preserve existing AWS content:** The current file has detailed AWS CDK guidance embedded as "If AWS:" blocks within Steps 3, 5, 6, 7, and 10. These remain untouched. The new platform sections follow the same pattern but are consolidated into reference blocks rather than scattered across steps.

### Content Conventions

All new content follows the established steering file conventions:

1. **WAIT directives**: Explicit `WAIT for response.` after every bootcamper question
2. **👉 markers**: All bootcamper-facing questions prefixed with 👉
3. **MCP tool calls**: Exact tool names with parameter syntax (e.g., `search_docs(query='Azure deployment', version='current')`)
4. **File path references**: Always project-relative (e.g., `config/bootcamp_preferences.yaml`, `infra/`)
5. **"If <platform>:" pattern**: Matches the existing "If AWS:" convention for conditional guidance

## Detailed Design

### Enhancement 1: Step 1 Platform Branching

The existing Step 1 already asks about deployment target and method. The enhancement adds:

- An explicit instruction for the agent to load the corresponding platform reference section after the bootcamper selects their target
- A `search_docs` call with the selected platform to get current Senzing guidance
- Persistence of the choice in `config/bootcamp_preferences.yaml`

The existing AWS-specific content in Step 1 (CDK Power recommendation) is preserved.

### Enhancement 2: Platform-Conditional Guidance in Packaging Steps

Steps 3, 5, 6, 7, and 10 already have "If AWS:" blocks. The enhancement adds brief "If <platform>:" pointers in these steps that reference the corresponding platform appendix section. This keeps the steps concise while ensuring the agent knows to consult platform-specific guidance.

### Section 3: On-Premises Deployment Reference

**Prerequisites:**
- PostgreSQL database (or SQLite for evaluation)
- Docker and Docker Compose (recommended) or direct host installation
- Network access between components
- Hardware sizing guidance via `search_docs`

**Architecture Overview:**
- Docker Compose multi-service setup: Senzing loader, query service, PostgreSQL, optional API gateway
- Alternative: direct host installation with systemd services
- Agent calls `find_examples(query='Docker Compose deployment')` and `search_docs(query='on-premises deployment', version='current')`

**Key Configuration Steps:**
- Database provisioning and connection configuration
- Environment-specific config files in `config/dev/`, `config/staging/`, `config/prod/`
- Log aggregation setup (agent consults `search_docs` for Senzing logging guidance)
- Backup and restore procedures using deployment scripts

**MCP Tool References:**
- `sdk_guide(topic='install', platform='linux', language='<lang>', version='current')` for SDK installation
- `search_docs(query='PostgreSQL configuration', version='current')` for database setup
- `find_examples(query='Docker Compose deployment')` for container patterns
- `generate_scaffold` for deployment-ready code structure

### Section 4: Azure Deployment Reference

**Prerequisites:**
- Azure subscription and resource group
- Azure CLI installed and authenticated
- Azure Container Registry (ACR) for container images
- Agent calls `search_docs(query='Azure deployment', version='current')`

**Architecture Overview:**
- Compute: Azure Container Instances (simple) or Azure Kubernetes Service (scalable)
- Database: Azure Database for PostgreSQL — Flexible Server
- Secrets: Azure Key Vault with managed identity access
- Monitoring: Azure Monitor and Log Analytics

**Key Configuration Steps:**
- Infrastructure definition via ARM templates, Bicep, or Terraform
- Managed identity for service-to-service authentication
- Container image build and push to ACR
- Environment-specific Helm values or ARM parameter files

**MCP Tool References:**
- `search_docs(query='Azure deployment', version='current')` for Senzing Azure guidance
- `generate_scaffold` for Azure-compatible application code
- `find_examples(query='container deployment')` for containerization patterns
- `search_docs(query='PostgreSQL configuration', version='current')` for database setup

### Section 5: GCP Deployment Reference

**Prerequisites:**
- GCP project with billing enabled
- gcloud CLI installed and authenticated
- Artifact Registry for container images
- IAM service account with appropriate roles

**Architecture Overview:**
- Compute: Cloud Run (serverless) or GKE (Kubernetes)
- Database: Cloud SQL for PostgreSQL
- Secrets: Secret Manager with workload identity access
- Monitoring: Cloud Monitoring and Cloud Logging

**Key Configuration Steps:**
- Infrastructure definition via Terraform or Deployment Manager
- Workload identity for pod-to-service authentication (GKE)
- Container image build and push to Artifact Registry
- Environment-specific Terraform variable files

**MCP Tool References:**
- `search_docs(query='GCP deployment', version='current')` for Senzing GCP guidance
- `generate_scaffold` for GCP-compatible application code
- `find_examples(query='container deployment')` for containerization patterns
- `search_docs(query='PostgreSQL configuration', version='current')` for database setup

### Section 6: Kubernetes/Container Deployment Reference

**Prerequisites:**
- Kubernetes cluster access (any provider: EKS, AKS, GKE, on-prem, local)
- kubectl and Helm v3 installed
- Container registry access
- Namespace created for Senzing workloads

**Architecture Overview:**
- Helm chart structure: loader Deployment/Job, query service Deployment, PostgreSQL StatefulSet (or external managed database)
- Persistent volume claims for database storage (if self-managed)
- Service and Ingress for API access
- ConfigMap for Senzing configuration, Secret for credentials

**Key Configuration Steps:**
- Helm values files per environment (`values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`)
- Horizontal Pod Autoscaler for query service
- Liveness and readiness probes for health checking
- Pod disruption budgets for availability during upgrades

**MCP Tool References:**
- `search_docs(query='Kubernetes deployment', version='current')` for Senzing K8s guidance
- `find_examples(query='Kubernetes Helm')` for Helm chart patterns
- `search_docs(query='container deployment', version='current')` for container best practices
- `generate_scaffold` for Kubernetes-compatible application code

## Correctness Properties

Since this is a markdown content file (not executable code), correctness properties focus on structural validation.

### Property 1: Existing AWS Content Preserved (Requirement 6)

**Type:** Content validation
**Property:** All existing "If AWS:" blocks in Steps 3, 5, 6, 7, and 10 remain present and unmodified after the expansion.
**Verification:** Diff the expanded file against the original; all "If AWS:" blocks and their content must be identical.

### Property 2: All Platform Sections Present (Requirements 2-5)

**Type:** Structural validation
**Property:** The file contains four new platform reference sections: On-Premises, Azure, GCP, and Kubernetes.
**Verification:** Grep for section headers matching each platform name. All four must be present.

### Property 3: MCP Tool References Use Correct Names (Requirement 7)

**Type:** Content validation
**Property:** All MCP tool references in the file use tool names from the canonical set: `search_docs`, `sdk_guide`, `generate_scaffold`, `find_examples`, `explain_error_code`, `reporting_guide`, `get_sdk_reference`, `mapping_workflow`, `analyze_record`, `get_capabilities`.
**Verification:** Extract all backtick-quoted function-call patterns and verify each tool name is in the canonical set.

### Property 4: Each Platform Section Has Required Subsections (Requirements 2-5)

**Type:** Structural validation
**Property:** Each platform reference section contains subsections for: prerequisites, architecture overview, key configuration steps, and MCP tool references.
**Verification:** For each platform section, verify the presence of all four subsection headers.

### Property 5: Front Matter and Structure Preserved (Requirement 8)

**Type:** Structural validation
**Property:** The file retains YAML front matter with `inclusion: manual`, the user reference link, Before/After framing, Prerequisites, Phase 1/Phase 2 structure, and all existing step numbers.
**Verification:** Check that the file starts with `---` containing `inclusion: manual`, and that all existing structural elements are present.

## Alternatives Considered

### Alternative 1: Separate Steering Files Per Platform

Create `module-12-deployment-azure.md`, `module-12-deployment-gcp.md`, etc. and load the relevant one alongside the main file.

**Rejected because:** This would require the agent to load two steering files for Module 12, increasing context overhead. The agent-instructions.md maps each module to a single steering file. Adding conditional multi-file loading would require changes to the agent instructions and module steering conventions.

### Alternative 2: Inline Platform Branching in Every Step

Add "If Azure:", "If GCP:", "If On-Prem:", "If Kubernetes:" blocks inside every packaging step alongside the existing "If AWS:" blocks.

**Rejected because:** This would make the file extremely long and hard to read. Steps 3, 5, 6, 7, and 10 would each have five conditional blocks, creating a deeply nested structure. The appendix approach keeps the main workflow clean and puts platform details in one consolidated place per platform.

### Alternative 3: Hardcode Platform-Specific CLI Commands

Embed specific Azure CLI commands, gcloud commands, Terraform snippets, and Helm commands directly in the steering file.

**Rejected because:** These commands change frequently and would become stale. The MCP-first approach delegates specific commands to `search_docs` and `find_examples` calls, ensuring the agent always gets current guidance from the Senzing documentation server.
