# Requirements Document

## Introduction

The Module 12 (Deployment and Packaging) steering file at `senzing-bootcamp/steering/module-12-deployment.md` currently provides detailed deployment guidance only for AWS CDK. Other deployment platforms — on-premises, Azure, GCP, and Kubernetes/container — are mentioned in Step 1's platform selection but lack corresponding detailed guidance in the packaging and deployment phases. When a bootcamper selects a non-AWS platform, the agent has no platform-specific instructions for containerization patterns, database migration, CI/CD pipelines, or deployment scripts.

This spec expands the steering file to include structured deployment guidance for all supported platforms while keeping the existing AWS CDK content intact. The steering file references MCP tools (`search_docs`, `sdk_guide`, `generate_scaffold`, `find_examples`) for platform-specific details rather than hardcoding instructions that may become stale.

This is a Kiro Power — the "code" is a markdown steering file that guides AI agent behavior. Changes go in `senzing-bootcamp/steering/module-12-deployment.md` (the distributed power file).

## Glossary

- **Steering_File**: A markdown file loaded by the AI agent at runtime that provides step-by-step workflow instructions, decision gates, and behavioral rules for guiding a bootcamper through a module
- **Agent**: The AI assistant that reads steering files and guides bootcampers through the Senzing Bootcamp
- **Bootcamper**: The human user working through the bootcamp modules
- **Platform_Section**: A clearly delineated section within the steering file that provides deployment guidance specific to a single deployment target (e.g., Azure, GCP, on-premises, Kubernetes)
- **MCP_Tool**: A tool provided by the Senzing MCP server that the agent calls to generate code, validate records, or retrieve documentation
- **CDK**: AWS Cloud Development Kit — an infrastructure-as-code framework for defining AWS resources in a programming language
- **Helm_Chart**: A package format for Kubernetes that bundles resource definitions, configuration templates, and dependency information
- **ARM_Template**: Azure Resource Manager template — Azure's native infrastructure-as-code format
- **Deployment_Target**: The platform or environment where the bootcamper intends to deploy their Senzing entity resolution system (AWS, Azure, GCP, on-premises, or Kubernetes)

## Requirements

### Requirement 1: Platform Selection Step Enhancement

**User Story:** As an AI agent, I want an enhanced platform selection step that clearly branches into platform-specific guidance, so that I can direct the bootcamper to the correct deployment workflow for their chosen target.

#### Acceptance Criteria

1. THE Steering_File SHALL include a platform selection step that instructs the Agent to ask the bootcamper which deployment target they are using before proceeding with packaging
2. WHEN the bootcamper selects a deployment target, THE Steering_File SHALL direct the Agent to the corresponding Platform_Section for all subsequent platform-specific steps
3. THE Steering_File SHALL support at least five deployment targets: AWS, Azure, GCP, on-premises, and Kubernetes/container
4. WHEN the bootcamper selects a platform, THE Steering_File SHALL instruct the Agent to call `search_docs(query='deployment <platform>', version='current')` to retrieve current Senzing guidance for that platform
5. THE Steering_File SHALL persist the selected deployment target in `config/bootcamp_preferences.yaml` as `deployment_target`

### Requirement 2: On-Premises Deployment Section

**User Story:** As an AI agent, I want a dedicated on-premises deployment section in the steering file, so that I can guide bootcampers through deploying Senzing on their own infrastructure with appropriate prerequisites, architecture, configuration, and MCP tool references.

#### Acceptance Criteria

1. THE Steering_File SHALL include an on-premises Platform_Section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
2. THE Steering_File SHALL instruct the Agent to use `search_docs(query='on-premises deployment', version='current')` to retrieve current Senzing on-premises guidance
3. THE Steering_File SHALL instruct the Agent to use `sdk_guide(topic='install', platform='linux', language='<chosen_language>', version='current')` for platform-specific SDK installation steps
4. THE Steering_File SHALL include on-premises prerequisites covering: PostgreSQL database provisioning, network configuration, hardware sizing, and Senzing SDK installation
5. THE Steering_File SHALL include on-premises architecture guidance covering: Docker Compose for multi-service orchestration, direct host installation as an alternative, and database connectivity
6. THE Steering_File SHALL include on-premises configuration steps for: environment-specific config files, database connection strings, log aggregation, and backup procedures
7. THE Steering_File SHALL instruct the Agent to use `find_examples(query='Docker Compose deployment')` for container orchestration patterns

### Requirement 3: Azure Deployment Section

**User Story:** As an AI agent, I want a dedicated Azure deployment section in the steering file, so that I can guide bootcampers through deploying Senzing on Azure with appropriate prerequisites, architecture, configuration, and MCP tool references.

#### Acceptance Criteria

1. THE Steering_File SHALL include an Azure Platform_Section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
2. THE Steering_File SHALL instruct the Agent to use `search_docs(query='Azure deployment', version='current')` to retrieve current Senzing Azure guidance
3. THE Steering_File SHALL include Azure prerequisites covering: Azure subscription, Azure CLI installation, resource group creation, and container registry setup
4. THE Steering_File SHALL include Azure architecture guidance covering: Azure Container Instances or Azure Kubernetes Service for compute, Azure Database for PostgreSQL for the database, and Azure Key Vault for secrets
5. THE Steering_File SHALL include Azure configuration steps for: ARM template or Bicep definitions, environment-specific settings, managed identity configuration, and monitoring with Azure Monitor
6. THE Steering_File SHALL instruct the Agent to use `generate_scaffold` and `find_examples` for Azure-compatible code patterns

### Requirement 4: GCP Deployment Section

**User Story:** As an AI agent, I want a dedicated GCP deployment section in the steering file, so that I can guide bootcampers through deploying Senzing on Google Cloud Platform with appropriate prerequisites, architecture, configuration, and MCP tool references.

#### Acceptance Criteria

1. THE Steering_File SHALL include a GCP Platform_Section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
2. THE Steering_File SHALL instruct the Agent to use `search_docs(query='GCP deployment', version='current')` to retrieve current Senzing GCP guidance
3. THE Steering_File SHALL include GCP prerequisites covering: GCP project, gcloud CLI installation, Artifact Registry setup, and IAM service account configuration
4. THE Steering_File SHALL include GCP architecture guidance covering: Cloud Run or GKE for compute, Cloud SQL for PostgreSQL for the database, and Secret Manager for secrets
5. THE Steering_File SHALL include GCP configuration steps for: Terraform or Deployment Manager definitions, environment-specific settings, workload identity configuration, and monitoring with Cloud Monitoring
6. THE Steering_File SHALL instruct the Agent to use `generate_scaffold` and `find_examples` for GCP-compatible code patterns

### Requirement 5: Kubernetes/Container Deployment Section

**User Story:** As an AI agent, I want a dedicated Kubernetes/container deployment section in the steering file, so that I can guide bootcampers through deploying Senzing on any Kubernetes cluster with appropriate prerequisites, architecture, configuration, and MCP tool references.

#### Acceptance Criteria

1. THE Steering_File SHALL include a Kubernetes Platform_Section with subsections for prerequisites, architecture overview, key configuration steps, and MCP tool references
2. THE Steering_File SHALL instruct the Agent to use `search_docs(query='Kubernetes deployment', version='current')` to retrieve current Senzing Kubernetes guidance
3. THE Steering_File SHALL include Kubernetes prerequisites covering: cluster access (any provider or local), kubectl and Helm installation, container registry access, and namespace creation
4. THE Steering_File SHALL include Kubernetes architecture guidance covering: Helm chart structure for Senzing components, StatefulSet or Deployment patterns, persistent volume claims for database storage, and service mesh considerations
5. THE Steering_File SHALL include Kubernetes configuration steps for: Helm values files per environment, ConfigMap and Secret resources, horizontal pod autoscaling, and liveness/readiness probes
6. THE Steering_File SHALL instruct the Agent to use `find_examples(query='Kubernetes Helm')` for Helm chart patterns and `search_docs(query='container deployment', version='current')` for container guidance

### Requirement 6: Preserve Existing AWS CDK Content

**User Story:** As a power developer, I want the existing AWS CDK deployment content preserved intact, so that bootcampers who choose AWS continue to receive the same detailed guidance.

#### Acceptance Criteria

1. THE Steering_File SHALL retain all existing AWS CDK-specific content in Steps 3, 5, 6, 7, and 10 without modification
2. THE Steering_File SHALL retain the existing Step 1 platform selection logic including the CDK Power recommendation for AWS users
3. THE Steering_File SHALL retain the existing Phase 1 and Phase 2 structure with all current steps numbered and ordered as they are

### Requirement 7: MCP-First Content Strategy

**User Story:** As a power developer, I want all platform-specific deployment details to be retrieved via MCP tools at runtime rather than hardcoded in the steering file, so that the guidance stays current as Senzing's deployment recommendations evolve.

#### Acceptance Criteria

1. THE Steering_File SHALL reference MCP tools (`search_docs`, `sdk_guide`, `generate_scaffold`, `find_examples`) for all platform-specific technical details rather than embedding specific version numbers, CLI commands, or configuration values
2. WHEN the Agent needs platform-specific deployment instructions, THE Steering_File SHALL instruct the Agent to call `search_docs` with a platform-specific query before providing guidance
3. THE Steering_File SHALL provide workflow structure and decision points for each platform while delegating technical specifics to MCP tool responses
4. THE Steering_File SHALL instruct the Agent to consult `search_docs` when mentioning third-party deployment tools in the context of Senzing integration, consistent with the agent-instructions.md MCP rules

### Requirement 8: Steering File Structure and Conventions

**User Story:** As a power developer, I want the expanded steering file to maintain the established steering file conventions, so that it integrates seamlessly with the rest of the power.

#### Acceptance Criteria

1. THE Steering_File SHALL retain the existing YAML front matter with `inclusion: manual`
2. THE Steering_File SHALL retain the existing reference to `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md`
3. THE Steering_File SHALL use the same formatting conventions as other steering files: WAIT directives for user input, MCP tool call syntax, and 👉 markers for bootcamper questions
4. THE Steering_File SHALL organize platform-specific sections as a clearly labeled appendix or reference block after the main workflow so that the primary step flow remains uncluttered
5. THE Steering_File SHALL include all MCP tool references using the exact tool names and parameter formats used in other steering files
