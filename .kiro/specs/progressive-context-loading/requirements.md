# Requirements Document

## Introduction

Module 5 (5,355 tokens) and Module 6 (9,176 tokens) are the two largest steering files in the bootcamp. The agent currently loads the entire file when a user enters the module, consuming significant context budget in a single operation. This feature splits these large steering files into phase-level sub-files and updates the loading mechanism so the agent loads only the phase relevant to the current workflow step. The steering index already tracks token counts and size categories per file — this feature extends that metadata to drive phase-level loading decisions.

The scope is limited to: splitting the two large module files, updating `steering-index.yaml` metadata, and updating the loading instructions in `agent-instructions.md`. Module content itself does not change.

## Glossary

- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides workflow instructions to the agent for a specific module or concern.
- **Steering_Index**: The `steering-index.yaml` file that maps module numbers to steering file paths and tracks file metadata (token counts, size categories).
- **Phase**: A top-level workflow section within a module steering file (e.g., "Phase 1 — Quality Assessment", "Phase A: Build Loading Program"). Each phase represents a distinct stage of the module workflow.
- **Sub_File**: A steering file containing the content for a single phase of a module, named with the pattern `module-{NN}-{slug}-phase{N}.md`.
- **Root_File**: A reduced version of the original module steering file that contains shared preamble content (title, purpose, prerequisites, before/after framing) and a manifest listing its sub-files, but not the phase content itself.
- **Agent**: The AI agent that loads steering files and guides the user through the bootcamp.
- **Context_Budget**: The token-based budget system defined in `agent-instructions.md` that tracks cumulative token usage and applies warn/critical thresholds.
- **Token_Threshold**: A configurable token count (defined in `steering-index.yaml`) above which a steering file is considered eligible for phase-level splitting.

## Requirements

### Requirement 1: Split Module 5 into Phase-Level Sub-Files

**User Story:** As a bootcamp maintainer, I want Module 5's steering file split into phase-level sub-files, so that the agent only loads the phase it needs instead of the entire 5,355-token file.

#### Acceptance Criteria

1. WHEN Module 5 is split, THE Root_File (`module-05-data-quality-mapping.md`) SHALL contain only the shared preamble (title, purpose, prerequisites, before/after framing) and a manifest listing all Sub_Files with their phase names and file paths.
2. WHEN Module 5 is split, THE Sub_Files SHALL be named `module-05-phase1-quality-assessment.md`, `module-05-phase2-data-mapping.md`, and `module-05-phase3-test-load.md`, corresponding to the three existing phases.
3. THE Root_File SHALL retain the YAML front matter (`inclusion: manual`) from the original file.
4. WHEN a Sub_File is created, THE Sub_File SHALL contain the complete, unmodified content of its corresponding phase from the original steering file, including all agent instructions, checkpoints, and workflow steps.
5. WHEN a Sub_File is created, THE Sub_File SHALL include YAML front matter with `inclusion: manual`.
6. THE combined content of the Root_File and all Sub_Files SHALL preserve all content from the original `module-05-data-quality-mapping.md` with no omissions or additions to the instructional text.

### Requirement 2: Split Module 6 into Phase-Level Sub-Files

**User Story:** As a bootcamp maintainer, I want Module 6's steering file split into phase-level sub-files, so that the agent only loads the phase it needs instead of the entire 9,176-token file.

#### Acceptance Criteria

1. WHEN Module 6 is split, THE Root_File (`module-06-load-data.md`) SHALL contain only the shared preamble (title, purpose, prerequisites, before/after framing, conditional workflow check) and a manifest listing all Sub_Files with their phase names and file paths.
2. WHEN Module 6 is split, THE Sub_Files SHALL be named `module-06-phaseA-build-loading.md`, `module-06-phaseB-load-first-source.md`, `module-06-phaseC-multi-source.md`, and `module-06-phaseD-validation.md`, corresponding to the four existing phases plus shared reference/recovery content appended to the appropriate sub-file.
3. THE Root_File SHALL retain the YAML front matter (`inclusion: manual`) from the original file.
4. WHEN a Sub_File is created, THE Sub_File SHALL contain the complete, unmodified content of its corresponding phase from the original steering file, including all agent instructions, checkpoints, workflow steps, and reference material.
5. WHEN a Sub_File is created, THE Sub_File SHALL include YAML front matter with `inclusion: manual`.
6. THE combined content of the Root_File and all Sub_Files SHALL preserve all content from the original `module-06-load-data.md` with no omissions or additions to the instructional text.

### Requirement 3: Update Steering Index with Sub-File Metadata

**User Story:** As a bootcamp maintainer, I want the steering index to track sub-file metadata, so that the agent can make informed loading decisions based on token counts.

#### Acceptance Criteria

1. WHEN a module is split into sub-files, THE Steering_Index SHALL include a `phases` map under that module's entry, listing each Sub_File path with its `token_count` and `size_category`.
2. WHEN a module is split into sub-files, THE Steering_Index `file_metadata` section SHALL include entries for the Root_File and each Sub_File with accurate `token_count` and `size_category` values.
3. WHEN a module is split into sub-files, THE Steering_Index SHALL remove the original monolithic file's `file_metadata` entry and replace it with the Root_File and Sub_File entries.
4. THE Steering_Index `budget.total_tokens` field SHALL be recalculated to reflect the sum of all current file token counts after splitting.

### Requirement 4: Update Agent Loading Instructions for Phase-Level Loading

**User Story:** As a bootcamp maintainer, I want the agent loading instructions updated so the agent loads only the relevant phase sub-file when entering a module phase, instead of loading the entire module file at once.

#### Acceptance Criteria

1. WHEN the Agent enters a module that has been split into phases, THE Agent SHALL first load the Root_File to obtain the preamble and phase manifest.
2. WHEN the Agent begins work on a specific phase within a split module, THE Agent SHALL load only the Sub_File for that phase.
3. WHEN the Agent transitions from one phase to another within the same module, THE Agent SHALL unload the previous phase's Sub_File before loading the next phase's Sub_File.
4. THE `agent-instructions.md` "Module Steering" section SHALL document the phase-level loading behavior for split modules.
5. THE `agent-instructions.md` "Context Budget" section SHALL reference the Steering_Index `phases` metadata as the source for phase-level token costs.

### Requirement 5: Define Token Threshold for Splitting Eligibility

**User Story:** As a bootcamp maintainer, I want a configurable token threshold in the steering index, so that future large steering files can be identified as candidates for splitting using the same mechanism.

#### Acceptance Criteria

1. THE Steering_Index SHALL include a `split_threshold_tokens` field under the `budget` section, set to a value that captures Module 5 and Module 6 as eligible (e.g., 5000 tokens).
2. WHEN a steering file's `token_count` in `file_metadata` exceeds the `split_threshold_tokens` value, THE Steering_Index SHALL flag that file as a candidate for phase-level splitting.
3. THE `split_threshold_tokens` value SHALL be configurable by editing the Steering_Index file directly.

### Requirement 6: Preserve Cross-References and Session Resume Compatibility

**User Story:** As a bootcamp maintainer, I want all existing cross-references and session resume behavior to continue working after the split, so that no existing functionality breaks.

#### Acceptance Criteria

1. WHEN another steering file references `module-05-data-quality-mapping.md` or `module-06-load-data.md` by filename, THE Root_File SHALL remain at the original path so that existing references resolve correctly.
2. WHEN the Agent resumes a session mid-module using `session-resume.md` and `bootcamp_progress.json`, THE Agent SHALL determine the current phase from the progress checkpoint and load only the corresponding Sub_File instead of the full module.
3. IF a Sub_File cannot be found at the expected path, THEN THE Agent SHALL fall back to loading the Root_File and log a warning that the sub-file is missing.
