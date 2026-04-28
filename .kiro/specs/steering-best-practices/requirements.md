# Requirements Document

## Introduction

Align the senzing-bootcamp power's steering files with the best practices from the "Steering Kiro" article. An audit identified six gaps: the security file uses the wrong inclusion mode, the always-on file exceeds the recommended line limit, several manual files far exceed the 150-line guideline, file references are underused, and the always-on context budget has not been validated. This spec addresses each gap while respecting that this power IS a steering-file-driven curriculum — some files will necessarily be longer than typical project steering, but should still be minimized where possible.

## Glossary

- **Steering_File**: A Markdown file with YAML frontmatter (`inclusion` field) that provides instructions to the Kiro agent at runtime.
- **Always_File**: A steering file with `inclusion: always` — loaded into every conversation, never skipped.
- **Auto_File**: A steering file with `inclusion: auto` — Kiro decides whether to include it based on conversation relevance.
- **Manual_File**: A steering file with `inclusion: manual` — loaded only when explicitly requested by the agent or user.
- **File_Reference**: A `#[[file:path]]` directive in a steering file that tells the agent to load content from another file on demand, keeping the steering file lean.
- **Hook_Registry**: The section in `onboarding-flow.md` that defines all 18 bootcamp hooks with their parameters for the `createHook` tool.
- **Token_Count**: The number of tokens a steering file consumes in the agent's context window, as measured by `measure_steering.py`.
- **Context_Budget**: The total token cost of all currently loaded steering files, tracked against the 200k reference window.
- **Steering_Index**: The `steering-index.yaml` file that maps steering files to modules, keywords, and token counts.
- **Validate_Power_Script**: The `validate_power.py` script that checks cross-references, hooks, and steering file integrity.

## Requirements

### Requirement 1: Change security-privacy.md Inclusion Mode

**User Story:** As a power maintainer, I want the security and privacy steering file to use `always` inclusion, so that security rules are never skipped in any conversation.

#### Acceptance Criteria

1. WHEN the `security-privacy.md` frontmatter is read, THE Steering_File SHALL have `inclusion: always` instead of `inclusion: auto`.
2. THE Steering_File SHALL retain all existing content from `security-privacy.md` without removing any security rules.
3. WHEN `validate_power.py` is run after the change, THE Validate_Power_Script SHALL pass without errors related to `security-privacy.md`.

### Requirement 2: Trim agent-instructions.md to Under 80 Lines

**User Story:** As a power maintainer, I want the always-on agent instructions file to be under 80 lines, so that it stays within the article's recommended 40–80 line range for always-on files.

#### Acceptance Criteria

1. THE Steering_File `agent-instructions.md` SHALL contain fewer than 80 lines (currently 92 lines).
2. THE Steering_File SHALL preserve all critical agent rules: session start behavior, file placement table, MCP rules, MCP failure handling, module steering loading, state and progress tracking, communication rules, hook management, and context budget management.
3. IF content is removed from `agent-instructions.md` to reduce line count, THEN THE Steering_File SHALL relocate that content to an appropriate existing or new manual steering file rather than deleting it.
4. WHEN `validate_power.py` is run after the change, THE Validate_Power_Script SHALL pass without errors related to `agent-instructions.md`.

### Requirement 3: Split graduation.md to Approach 150 Lines

**User Story:** As a power maintainer, I want the graduation workflow file split into a main workflow and reference sections, so that the main file approaches the 150-line guideline for manual files.

#### Acceptance Criteria

1. THE Steering_File `graduation.md` SHALL contain the core workflow steps (pre-checks, Steps 1–5, graduation report generation) in under 200 lines (currently 449 lines).
2. WHEN content is extracted from `graduation.md`, THE Steering_File SHALL move detailed reference material (file tables, conditional checklist logic, configuration file templates) into a new `graduation-reference.md` manual steering file.
3. THE Steering_File `graduation.md` SHALL use File_Reference directives (`#[[file:]]`) to point to the extracted reference material.
4. WHEN the agent loads `graduation.md` and follows the workflow, THE Steering_File SHALL produce the same graduation artifacts (production directory, config files, README, migration checklist, graduation report) as the current version.
5. WHEN `validate_power.py` is run after the split, THE Validate_Power_Script SHALL pass without errors.

### Requirement 4: Extract Hook Registry from onboarding-flow.md

**User Story:** As a power maintainer, I want the Hook Registry extracted from the onboarding flow into a separate reference file, so that `onboarding-flow.md` is shorter and the Hook Registry is reusable.

#### Acceptance Criteria

1. THE Steering_File `onboarding-flow.md` SHALL not contain the full Hook Registry definitions inline (the Hook Registry currently occupies approximately 150 lines).
2. WHEN the Hook Registry is extracted, THE Steering_File SHALL place it in a new `hook-registry.md` manual steering file.
3. THE Steering_File `onboarding-flow.md` SHALL use a File_Reference directive (`#[[file:]]`) to reference `hook-registry.md` where the Hook Registry was previously inline.
4. THE Steering_File `agent-instructions.md` SHALL reference `hook-registry.md` instead of `onboarding-flow.md` for hook definitions, since the Hook Registry is no longer inline in the onboarding flow.
5. WHEN the agent executes the onboarding flow and creates hooks, THE Steering_File SHALL produce the same hooks with the same parameters as the current version.
6. WHEN `validate_power.py` is run after the extraction, THE Validate_Power_Script SHALL pass without errors.

### Requirement 5: Trim module-12-deployment.md

**User Story:** As a power maintainer, I want the Module 12 deployment file trimmed, so that it approaches the 150-line guideline by leveraging the existing platform-specific deployment files.

#### Acceptance Criteria

1. THE Steering_File `module-12-deployment.md` SHALL contain fewer than 250 lines (currently 359 lines).
2. THE Steering_File SHALL preserve all step definitions (Steps 1–15) and the phase gate between packaging and deployment.
3. WHEN platform-specific content (AWS CDK blocks, Azure/GCP/on-premises guidance) is condensed, THE Steering_File SHALL use File_Reference directives or explicit "load the platform file" instructions to reference the existing `deployment-azure.md`, `deployment-gcp.md`, `deployment-onpremises.md`, and `deployment-kubernetes.md` files.
4. WHEN the agent runs Module 12 for any deployment target, THE Steering_File SHALL produce the same artifacts and follow the same workflow as the current version.
5. WHEN `validate_power.py` is run after the changes, THE Validate_Power_Script SHALL pass without errors.

### Requirement 6: Trim module-07-multi-source.md

**User Story:** As a power maintainer, I want the Module 7 multi-source file trimmed, so that it approaches the 150-line guideline by leveraging the existing `module-07-reference.md`.

#### Acceptance Criteria

1. THE Steering_File `module-07-multi-source.md` SHALL contain fewer than 250 lines (currently 341 lines).
2. THE Steering_File SHALL preserve all 16 step definitions and the decision gate.
3. WHEN detailed reference material (source ordering examples, conflict resolution, common issues) is condensed, THE Steering_File SHALL use a File_Reference directive to reference the existing `module-07-reference.md`.
4. WHEN the agent runs Module 7, THE Steering_File SHALL produce the same artifacts and follow the same workflow as the current version.
5. WHEN `validate_power.py` is run after the changes, THE Validate_Power_Script SHALL pass without errors.

### Requirement 7: Evaluate Trimming common-pitfalls.md

**User Story:** As a power maintainer, I want to evaluate whether `common-pitfalls.md` can be further trimmed or split, so that it approaches the 150-line guideline.

#### Acceptance Criteria

1. THE Steering_File `common-pitfalls.md` SHALL contain fewer than 180 lines (currently 204 lines).
2. IF content is extracted, THEN THE Steering_File SHALL move it to a new reference file or use File_Reference directives to existing files.
3. THE Steering_File SHALL preserve the guided troubleshooting flow (ask-before-scanning diagnostic questions) and all module-specific pitfall tables.
4. WHEN `validate_power.py` is run after the changes, THE Validate_Power_Script SHALL pass without errors.

### Requirement 8: Evaluate Trimming troubleshooting-decision-tree.md

**User Story:** As a power maintainer, I want to evaluate whether `troubleshooting-decision-tree.md` can be further trimmed, so that it approaches the 150-line guideline.

#### Acceptance Criteria

1. THE Steering_File `troubleshooting-decision-tree.md` SHALL contain fewer than 200 lines (currently 224 lines).
2. THE Steering_File SHALL preserve the visual flowchart format and all six diagnostic sections (A–F).
3. IF sections are condensed, THEN THE Steering_File SHALL retain enough detail for the agent to guide the bootcamper through diagnosis without loading additional files.
4. WHEN `validate_power.py` is run after the changes, THE Validate_Power_Script SHALL pass without errors.

### Requirement 9: Add File References to Steering Files

**User Story:** As a power maintainer, I want more steering files to use `#[[file:]]` references instead of inline content, so that steering files stay lean and reference existing templates, policies, and examples.

#### Acceptance Criteria

1. WHEN a steering file contains inline content that duplicates or paraphrases content from an existing template, policy, or example file, THE Steering_File SHALL replace the inline content with a File_Reference directive pointing to the source file.
2. THE Steering_File modifications SHALL increase the total number of File_Reference directives across all steering files from the current count of 3 to at least 8.
3. THE Steering_File modifications SHALL not change the functional behavior of any steering file — the agent SHALL produce the same outputs when following the referenced content.
4. WHEN `validate_power.py` is run after the changes, THE Validate_Power_Script SHALL pass without errors.

### Requirement 10: Update Steering Index and Token Counts

**User Story:** As a power maintainer, I want the steering index updated after all changes, so that token counts and file metadata remain accurate.

#### Acceptance Criteria

1. WHEN all steering file changes are complete, THE Steering_Index SHALL be updated by running `measure_steering.py` to recalculate token counts for all modified and new files.
2. THE Steering_Index SHALL include entries for any new steering files created during this work (such as `graduation-reference.md` and `hook-registry.md`).
3. THE Steering_Index `file_metadata` section SHALL reflect accurate `token_count` and `size_category` values for every steering file.
4. WHEN `measure_steering.py --check` is run after the update, THE Validate_Power_Script SHALL report all token counts are within 10% of actual.

### Requirement 11: Validate Always-On Context Budget

**User Story:** As a power maintainer, I want the always-on context budget validated, so that I can confirm the total always-on token cost is lean and within the article's recommendations.

#### Acceptance Criteria

1. WHEN all changes are complete, THE Context_Budget for always-on files (`inclusion: always`) SHALL be documented with the total token count.
2. THE Context_Budget for always-on files SHALL be under 3,000 tokens total (the article recommends total always-on under ~400 lines across 3–6 files; with 2 always files — `agent-instructions.md` and `security-privacy.md` — the combined token count should remain lean).
3. IF the always-on budget exceeds 3,000 tokens, THEN THE Steering_File changes SHALL include further trimming of always-on files to bring the total under the threshold.
4. THE Context_Budget total across all 44+ steering files SHALL be documented in the `budget` section of `steering-index.yaml`.

### Requirement 12: Full Power Validation

**User Story:** As a power maintainer, I want the entire power validated after all changes, so that I can confirm nothing is broken.

#### Acceptance Criteria

1. WHEN all changes are complete, THE Validate_Power_Script (`validate_power.py`) SHALL pass with zero errors.
2. WHEN `measure_steering.py --check` is run, THE Validate_Power_Script SHALL confirm all stored token counts are within 10% of actual.
3. THE Steering_Index SHALL list every steering file in the `senzing-bootcamp/steering/` directory — no files missing, no phantom entries for deleted files.
