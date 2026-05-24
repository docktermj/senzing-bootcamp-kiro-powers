# Requirements Document

## Introduction

Split the oversized steering file `module-07-phase2-discover.md` (6,428 tokens) into two files at the boundary between steps 4a–4c and steps 4d–4e, producing two files of approximately equal size (~3,200 tokens each). Update all referencing artifacts (steering-index.yaml, root module file) and verify consistency via `measure_steering.py`.

## Glossary

- **Steering_File**: A Markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that provides agent instructions for bootcamp module execution.
- **Steering_Index**: The `steering-index.yaml` file that maps steering files to their token counts, size categories, phase ranges, and keyword associations.
- **Root_File**: The parent steering file `module-07-query-visualize-discover.md` that references phase sub-files via load instructions.
- **Measure_Script**: The `measure_steering.py` Python script that counts tokens in steering files and validates consistency with `steering-index.yaml`.
- **Token_Budget**: The per-file token limit (5,000 tokens as defined by `split_threshold_tokens` in `steering-index.yaml`) above which a steering file should be split.
- **Part_A_File**: The resulting `module-07-phase2-discover.md` containing steps 4a–4c (data pattern analysis, why analysis, how analysis).
- **Part_B_File**: The resulting `module-07-phase2b-discover.md` containing steps 4d–4e (relationship networks, visualization suggestions, Discover Phase Completion).

## Requirements

### Requirement 1: File Split

**User Story:** As a power maintainer, I want the oversized discover phase file split into two files at the step 4c/4d boundary, so that each file stays within the token budget threshold.

#### Acceptance Criteria

1. WHEN the split is performed, THE Part_A_File SHALL contain the frontmatter, introduction, opt-in section, step 4a (Data Pattern Analysis), step 4b (Why Analysis Introduction), and step 4c (How Analysis Introduction) with their checkpoints.
2. WHEN the split is performed, THE Part_B_File SHALL contain its own frontmatter, step 4d (Relationship Network Exploration), step 4e (Data-Specific Visualization Suggestions), and the Discover Phase Completion section with their checkpoints.
3. THE Part_A_File SHALL include a navigation instruction at the end directing the agent to load `module-07-phase2b-discover.md` for steps 4d–4e.
4. THE Part_B_File SHALL include a header note indicating it continues from `module-07-phase2-discover.md` and returns to the root file on completion.
5. THE Part_A_File SHALL have a measured token count below 5,000 tokens.
6. THE Part_B_File SHALL have a measured token count below 5,000 tokens.

### Requirement 2: Steering Index Update

**User Story:** As a CI pipeline, I want the steering-index.yaml to accurately reflect the split files, so that token budget validation passes.

#### Acceptance Criteria

1. WHEN the split is performed, THE Steering_Index SHALL replace the single `phase2-discover` entry under module 7 with two entries: `phase2a-discover` (file: `module-07-phase2-discover.md`, step_range: ["4a", "4c"]) and `phase2b-discover` (file: `module-07-phase2b-discover.md`, step_range: ["4d", "4e"]).
2. WHEN the split is performed, THE Steering_Index SHALL update the `file_metadata` section to replace the single `module-07-phase2-discover.md` entry with two entries containing the measured token counts for Part_A_File and Part_B_File.
3. WHEN the split is performed, THE Steering_Index SHALL update the `budget.total_tokens` value to reflect the new aggregate token count across all steering files.
4. THE Steering_Index SHALL pass `measure_steering.py --check` validation (all token counts within 10% tolerance).

### Requirement 3: Root File Reference Update

**User Story:** As an agent following the module-07 workflow, I want the root file to reference both phase sub-files, so that the agent loads the correct file at each stage of the Discover phase.

#### Acceptance Criteria

1. WHEN the split is performed, THE Root_File SHALL update the step 4 phase file reference to mention both `module-07-phase2-discover.md` (steps 4a–4c) and `module-07-phase2b-discover.md` (steps 4d–4e).
2. THE Root_File SHALL preserve all other content unchanged.

### Requirement 4: No Hook Modification

**User Story:** As a power maintainer, I want hooks to remain untouched during this optimization, so that no behavioral changes are introduced.

#### Acceptance Criteria

1. THE token-budget-optimization task SHALL NOT modify any `.kiro.hook` files.
2. THE token-budget-optimization task SHALL NOT modify `hook-categories.yaml`.

### Requirement 5: Content Preservation

**User Story:** As a power maintainer, I want all instructional content preserved across the split, so that no agent guidance is lost.

#### Acceptance Criteria

1. THE Part_A_File and Part_B_File combined SHALL contain all agent instructions, checkpoints, and success criteria from the original `module-07-phase2-discover.md`.
2. WHEN the split is performed, THE Part_A_File and Part_B_File SHALL each retain the `inclusion: manual` frontmatter directive.
3. THE Part_A_File and Part_B_File SHALL each include the session resumption instruction directing the agent to read `config/bootcamp_progress.json` and resume from the first incomplete step.
