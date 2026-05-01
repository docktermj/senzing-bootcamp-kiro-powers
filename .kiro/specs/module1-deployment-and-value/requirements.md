# Requirements Document

## Introduction

Module 1 (Business Problem) currently captures the bootcamper's problem, data sources, and success criteria across 16 steps in two phases. This feature adds two capabilities: (1) a deployment target discovery step in Phase 1 that captures where the final solution will run, and (2) a contextual Senzing value restatement step in Phase 2 that reinforces why entity resolution matters for the bootcamper's specific problem. The deployment target feeds forward into Modules 8 and 11, and the value restatement strengthens the bootcamper's mental model before they move into data collection.

## Glossary

- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that provides step-by-step agent instructions for a bootcamp module or workflow.
- **Phase_1_File**: The steering file `module-01-business-problem.md` containing Module 1 Steps 1–8 (discovery and gap-filling).
- **Phase_2_File**: The steering file `module-01-phase2-document-confirm.md` containing Module 1 Steps 9–16 (document and confirm).
- **Preferences_File**: The YAML file `config/bootcamp_preferences.yaml` that persists bootcamper choices (language, track, cloud provider, deployment target, etc.) across modules.
- **Business_Problem_Document**: The markdown file `docs/business_problem.md` created in Phase 2 Step 11 that captures the bootcamper's problem statement, data sources, and success criteria.
- **Deployment_Target**: The platform or infrastructure where the bootcamper intends to deploy the final entity resolution solution (e.g., AWS, Azure, GCP, Kubernetes, Docker Swarm, current machine, other internal infrastructure).
- **Deployment_Category**: A grouping of deployment targets into categories: cloud hyperscalers, container platforms, local/on-premises, or undecided.
- **Value_Restatement**: A contextual explanation of why Senzing entity resolution is valuable for the bootcamper's specific problem, tied to their use case rather than generic marketing.
- **Module_8**: The Performance Testing module that reads `cloud_provider` from the Preferences_File to tailor performance targets.
- **Module_11**: The Deployment and Packaging module whose Step 1 asks about deployment target; if already captured in Module 1, Module_11 should confirm rather than re-ask.
- **Cloud_Provider_Setup**: The steering file `cloud-provider-setup.md` loaded at the Module 7→8 gate that asks about production infrastructure and persists `cloud_provider` to the Preferences_File.
- **Senzing_MCP_Server**: The MCP server at `mcp.senzing.com` that provides `search_docs` and other tools for retrieving current Senzing documentation and value proposition content.

## Requirements

### Requirement 1: Deployment Target Step in Phase 1

**User Story:** As a bootcamper, I want to specify my intended deployment platform during the business problem discovery phase, so that later modules can tailor their guidance to my infrastructure without re-asking.

#### Acceptance Criteria

1. WHEN the bootcamper completes Step 8 (software integration question), THE Phase_1_File SHALL contain a new Step 9 that asks the bootcamper about their intended deployment platform.
2. THE Phase_1_File SHALL present deployment options organized into categories: cloud hyperscalers (AWS, Azure, GCP), container platforms (Kubernetes, Docker Swarm), local/on-premises (current machine, other internal infrastructure), and "not sure yet".
3. THE Phase_1_File SHALL include a reassurance statement within the deployment target step explaining that the initial solution will be developed locally and deployment code will be created later, isolating development from deployment.
4. THE Phase_1_File SHALL instruct the agent to persist the bootcamper's deployment target choice to the Preferences_File as `deployment_target`.
5. IF the bootcamper selects a cloud hyperscaler, THEN THE Phase_1_File SHALL instruct the agent to also persist the choice as `cloud_provider` in the Preferences_File, using the same value format as Cloud_Provider_Setup (e.g., `aws`, `azure`, `gcp`).
6. IF the bootcamper selects "not sure yet", THEN THE Phase_1_File SHALL instruct the agent to persist `deployment_target: undecided` in the Preferences_File and reassure the bootcamper that the choice can be revisited later.
7. THE Phase_1_File SHALL instruct the agent to write a checkpoint for the new step to `config/bootcamp_progress.json`.
8. THE Phase_1_File SHALL follow the one-question-at-a-time pattern established by the existing steps, presenting the deployment target as a separate question not combined with Step 8.

### Requirement 2: Phase 2 Step Renumbering

**User Story:** As a bootcamp maintainer, I want the Phase 2 steps to be renumbered to accommodate the new Phase 1 step, so that step numbers remain sequential across both phases.

#### Acceptance Criteria

1. WHEN a new Step 9 is added to Phase_1_File, THE Phase_2_File SHALL renumber its steps from 10–17 (previously 9–16) to maintain sequential numbering across both phases.
2. THE Phase_2_File SHALL update all checkpoint instructions to reference the new step numbers.
3. THE Phase_2_File SHALL update the header text "Steps 9–16" to reflect the new range "Steps 10–17".
4. THE Phase_1_File SHALL update its Phase 2 reference text to say "Steps 10–17" instead of "Steps 9–16".

### Requirement 3: Business Problem Document Template Update

**User Story:** As a bootcamper, I want my deployment target included in the business problem document, so that the documented problem statement is complete and includes infrastructure context.

#### Acceptance Criteria

1. THE Phase_2_File SHALL include a "Deployment Target" section in the Business_Problem_Document template (Step 11, renumbered to Step 12).
2. THE Business_Problem_Document template Deployment Target section SHALL contain fields for: platform (the selected deployment target), category (cloud/container platform/local/undecided), and a note that development will proceed locally first.
3. WHEN the bootcamper selected "not sure yet" for deployment target, THE Business_Problem_Document template SHALL display "To be determined" for the Deployment Target section.

### Requirement 4: Senzing Value Restatement Step in Phase 2

**User Story:** As a bootcamper, I want Kiro to explain why Senzing entity resolution is valuable for my specific problem near the end of Module 1, so that I understand the value proposition in the context of my use case before proceeding to data collection.

#### Acceptance Criteria

1. THE Phase_2_File SHALL contain a new step after the solution approach step (renumbered Step 14) and before the confirmation step that provides a contextual Senzing value restatement.
2. THE Phase_2_File SHALL instruct the agent to use the Senzing_MCP_Server `search_docs` tool to retrieve current value proposition content relevant to the bootcamper's use case category.
3. THE Value_Restatement step SHALL instruct the agent to tie the value explanation to the bootcamper's specific problem, data sources, and desired outcomes rather than presenting generic marketing content.
4. THE Value_Restatement step SHALL instruct the agent to explain what entity resolution does (matching, relating, and deduplicating records across sources without manual rules or model training) in terms of the bootcamper's data and goals.
5. THE Value_Restatement step SHALL instruct the agent to write a checkpoint for the step to `config/bootcamp_progress.json`.
6. IF the bootcamper identified integration targets in Step 8, THEN THE Value_Restatement step SHALL instruct the agent to explain how Senzing fits into the bootcamper's broader architecture alongside those systems.

### Requirement 5: Module 11 Deployment Target Pre-Population

**User Story:** As a bootcamper, I want Module 11 to use the deployment target I already provided in Module 1, so that I am not asked the same question twice.

#### Acceptance Criteria

1. WHEN `deployment_target` exists in the Preferences_File, THE Module_11 steering file Step 1 SHALL instruct the agent to confirm the previously captured deployment target rather than asking the question from scratch.
2. WHEN `deployment_target` is set to `undecided` in the Preferences_File, THE Module_11 steering file Step 1 SHALL instruct the agent to ask the full deployment target question as if it had not been previously captured.
3. THE Module_11 steering file Step 1 SHALL continue to check for `cloud_provider` in the Preferences_File as it does today, in addition to checking `deployment_target`.

### Requirement 6: Module 8 Deployment Context Awareness

**User Story:** As a bootcamper, I want Module 8 to be aware of my deployment target when setting performance targets, so that benchmarks are relevant to my intended infrastructure.

#### Acceptance Criteria

1. THE Module_8 steering file SHALL instruct the agent to read `deployment_target` from the Preferences_File in addition to `cloud_provider`.
2. WHEN `deployment_target` is set and `cloud_provider` is not set, THE Module_8 steering file SHALL instruct the agent to use the deployment target to inform performance target guidance (e.g., container platform targets differ from bare-metal targets).

### Requirement 7: Steering Index Update

**User Story:** As a bootcamp maintainer, I want the steering index to reflect updated token counts for modified files, so that context budget tracking remains accurate.

#### Acceptance Criteria

1. WHEN the Phase_1_File is modified, THE steering index (`steering-index.yaml`) SHALL be updated with the new token count and the step range changed from `[1, 8]` to `[1, 9]`.
2. WHEN the Phase_2_File is modified, THE steering index SHALL be updated with the new token count and the step range changed from `[9, 16]` to `[10, 18]`.

### Requirement 8: Existing Step Preservation

**User Story:** As a bootcamp maintainer, I want all existing Module 1 step content to remain intact after the changes, so that no current functionality is lost.

#### Acceptance Criteria

1. THE Phase_1_File SHALL preserve the full content of existing Steps 1–8 without modification to their instructional text, checkpoint instructions, or question patterns.
2. THE Phase_2_File SHALL preserve the full content of existing steps (renumbered) without modification to their instructional text other than step number references and checkpoint number updates.
3. THE Phase_1_File SHALL retain its YAML frontmatter (`inclusion: manual`) unchanged.
4. THE Phase_2_File SHALL retain its YAML frontmatter (`inclusion: manual`) unchanged.
