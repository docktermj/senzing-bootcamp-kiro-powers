# Requirements Document

## Introduction

This feature addresses five UX and workflow improvements identified during real bootcamp usage of the Senzing Bootcamp Kiro Power. The improvements fall into three categories: (1) enforcing the one-question-at-a-time communication rule in Module 1, (2) silencing internal hook evaluation output that leaks to the bootcamper, and (3) ensuring per-source mapping specification documents are created automatically in the correct directory (`docs/`) during Module 5. All changes target steering files (Markdown agent instructions) and hook definitions (JSON), with no Python code changes expected.

## Glossary

- **Agent**: The Kiro AI assistant that guides the bootcamper through the Senzing Bootcamp modules
- **Bootcamper**: The human user working through the Senzing Bootcamp
- **Steering_File**: A Markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that provides behavioral instructions to the Agent
- **Hook**: A JSON file in `senzing-bootcamp/hooks/` that intercepts Agent actions (preToolUse, agentStop, etc.) and triggers evaluation prompts
- **preToolUse_Hook**: A Hook that fires before the Agent executes a tool action (e.g., file write), used to validate or redirect the action
- **Hook_Evaluation_Output**: Text the Agent produces when evaluating a Hook prompt — should be invisible to the Bootcamper when no corrective action is needed
- **Mapping_Specification**: A per-source Markdown document recording field mappings, mapping decisions, and quality notes for a data source processed in Module 5
- **Module_1_Steering**: The steering file `senzing-bootcamp/steering/module-01-business-problem.md` that guides the business problem discovery workflow
- **Module_5_Phase2_Steering**: The steering file `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` that guides the data mapping workflow
- **Agent_Instructions**: The always-loaded steering file `senzing-bootcamp/steering/agent-instructions.md` containing core Agent behavioral rules
- **Project_Structure_Steering**: The auto-loaded steering file `senzing-bootcamp/steering/project-structure.md` defining directory layout conventions
- **Hook_Registry**: The steering file `senzing-bootcamp/steering/hook-registry.md` containing definitions for all bootcamp hooks

## Requirements

### Requirement 1: One Question Per Turn in Module 1 Gap-Filling

**User Story:** As a Bootcamper, I want the Agent to ask only one question per turn when filling information gaps in Module 1, so that I can give focused answers without being overwhelmed by multiple questions at once.

#### Acceptance Criteria

1. WHEN the Agent identifies multiple undetermined items during Module 1 Step 7 gap-filling, THE Module_1_Steering SHALL instruct the Agent to ask about only one undetermined item per turn.
2. WHEN the Bootcamper answers a gap-filling question and additional undetermined items remain, THE Agent SHALL ask about the next undetermined item in a subsequent turn.
3. THE Module_1_Steering Step 7 instructions SHALL NOT contain language directing the Agent to ask multiple gap-filling questions in a single grouped question.
4. THE Module_1_Steering Step 7 instructions SHALL contain explicit language directing the Agent to queue remaining questions for subsequent turns after the Bootcamper responds.

### Requirement 2: Silent Hook Evaluation When No Action Needed

**User Story:** As a Bootcamper, I want hook evaluations to be completely invisible when no corrective action is required, so that my conversational flow is not interrupted by internal implementation details.

#### Acceptance Criteria

1. WHEN a preToolUse_Hook check passes with no corrective action needed, THE Agent SHALL produce zero visible output — no acknowledgment, no reasoning, no status message.
2. THE Agent_Instructions SHALL contain an explicit rule stating that when a Hook check passes with no action needed, the Agent must produce no output and must not narrate the evaluation process.
3. WHEN a preToolUse_Hook check identifies a problem requiring corrective action, THE Agent SHALL produce output describing only the corrective action taken.
4. THE enforce-working-directory Hook prompt SHALL contain explicit instruction to produce zero output when all paths are within the working directory.
5. THE verify-senzing-facts Hook prompt SHALL contain explicit instruction to produce zero output when no Senzing-specific content is present or all content was already verified.
6. THE enforce-feedback-path Hook prompt SHALL contain explicit instruction to produce zero output when the Agent is not in the feedback workflow.

### Requirement 3: Automatic Per-Source Mapping Specification Creation

**User Story:** As a Bootcamper, I want per-source mapping specification documents to be created automatically as part of the Module 5 mapping workflow, so that I do not have to notice the omission and ask for them manually.

#### Acceptance Criteria

1. WHEN the Agent completes the mapping workflow for a data source in Module 5 Phase 2, THE Module_5_Phase2_Steering SHALL instruct the Agent to create a Mapping_Specification document for that source before proceeding to the next source or declaring the module complete.
2. THE Module_5_Phase2_Steering SHALL instruct the Agent to save Mapping_Specification documents in the `docs/` directory with the naming pattern `docs/{source_name}_mapper.md`.
3. THE Module_5_Phase2_Steering SHALL NOT reference `scripts/` as the target directory for Mapping_Specification documents.
4. WHEN all data sources have been mapped, THE Module_5_Phase2_Steering SHALL instruct the Agent to verify that every completed source has a corresponding Mapping_Specification document in `docs/` before marking Module 5 as complete.

### Requirement 4: Markdown Documentation Directory Enforcement

**User Story:** As a Bootcamper, I want all Markdown documentation files to be placed in the `docs/` directory, so that documentation is not mixed with executable code in `scripts/`.

#### Acceptance Criteria

1. THE Project_Structure_Steering SHALL contain an explicit rule that all Markdown files (`*.md`) created during the bootcamp belong in the `docs/` directory or an appropriate subdirectory of `docs/`.
2. THE Project_Structure_Steering SHALL contain an explicit rule that the `scripts/` directory is reserved for executable code only.
3. THE Agent_Instructions file placement table SHALL list Markdown documentation under the `docs/` location.
4. IF the Agent is about to write a Markdown file to `scripts/`, THEN THE Agent SHALL redirect the write to `docs/` instead.

### Requirement 5: Hook Registry Consistency with Directory Fixes

**User Story:** As a Bootcamper, I want the hook registry definitions to be consistent with the corrected directory conventions, so that hooks created from the registry reflect the correct file placement rules.

#### Acceptance Criteria

1. THE Hook_Registry definitions for enforce-working-directory, verify-senzing-facts, and enforce-feedback-path hooks SHALL contain prompt text consistent with the zero-output-on-pass rule described in Requirement 2.
2. THE Hook_Registry SHALL be consistent with the actual Hook JSON files in `senzing-bootcamp/hooks/` for all hooks affected by these changes.
