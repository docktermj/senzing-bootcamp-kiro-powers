# Requirements Document

## Introduction

Optimize the senzing-bootcamp Kiro Power's steering file organization to align with best practices from the "Steering Kiro" article. The always-on core (`agent-instructions.md`, 235 lines / 5,013 tokens) exceeds the recommended ≤80 lines guideline, `module-transitions.md` (107 lines / 1,534 tokens) adds to the always-on footprint, and several manual-inclusion files far exceed the 150-line guideline (hook-registry-critical.md: 526 lines / 8,169 tokens; hook-registry-modules.md: 543 lines / 7,887 tokens; module-03-system-verification.md: 513 lines / 6,419 tokens; onboarding-flow.md: 366 lines / 5,266 tokens). The optimization applies Kiro's Refine-style compression to make steering more terse and LLM-optimized while preserving all behavioral rules and the guided learning experience.

## Glossary

- **Steering_File**: A Markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that provides behavioral instructions to the Kiro agent
- **Always_On_File**: A steering file with `inclusion: always` frontmatter, loaded into agent context on every turn regardless of user activity
- **Auto_File**: A steering file with `inclusion: auto` frontmatter, loaded automatically when contextually relevant (keyword match or module activation)
- **Manual_File**: A steering file with `inclusion: manual` frontmatter, loaded only when explicitly referenced by another steering file or the agent
- **Token_Count**: Approximate token size of a file calculated as `round(len(content) / 4)` by `measure_steering.py`
- **Steering_Index**: The `steering-index.yaml` file that tracks token counts, size categories, module mappings, and budget thresholds for all steering files
- **CI_Validation**: The GitHub Actions pipeline that runs `measure_steering.py --check` to verify stored token counts are within 10% of actual values
- **Refine_Optimization**: A compression technique that makes steering content more terse and LLM-optimized — using tables, shorthand, and structured formats instead of verbose procedural prose
- **Context_Budget**: The total token allocation available for steering files, tracked in `steering-index.yaml` with warn (60%) and critical (80%) thresholds against a 200,000-token reference window

## Requirements

### Requirement 1: Split agent-instructions.md into core and context-specific files

**User Story:** As a power maintainer, I want the always-on core file to contain only essential behavioral rules under 80 lines, so that the agent's base context consumption is minimized and context budget is preserved for module-specific content.

#### Acceptance Criteria

1. WHEN the optimization is complete, THE Always_On_File `agent-instructions.md` SHALL contain no more than 80 non-blank lines (excluding YAML frontmatter delimiters and blank lines used solely for readability)
2. WHEN the optimization is complete, THE Always_On_File `agent-instructions.md` SHALL retain all rules that apply unconditionally across every agent turn: Answer Processing Priority, File Placement (including Root Prohibitions), MCP Rules core (MCP-First Invariant, MCP Failure, SQL-redirect table), Module Steering dispatch, State & Progress core, Communication core (single-question rule, 👉 prefix, Question Stop Protocol), Mandatory Gate Precedence, Context Budget, and Hooks (silence rule, preToolUse retry rule)
3. WHEN the SDK Method Discovery section is extracted, THE Optimizer SHALL place it in a separate Auto_File that activates when the keyword routing in `steering-index.yaml` matches SDK-related keywords (e.g., "sdk method discovery", "which tool", "mcp tool") or when the agent's current module step involves SDK method selection
4. WHEN the Track Switching triggers section is extracted, THE Optimizer SHALL append it to the existing `track-switching.md` Auto_File (which already activates on "switch track", "change track" keywords) rather than creating a new file, to avoid fragmenting related content
5. WHEN the Question_Pending file format section is extracted, THE Optimizer SHALL place it in the `conversation-protocol.md` Auto_File where question handling rules already reside
6. WHEN any section is extracted from `agent-instructions.md`, THE extracted content SHALL be verifiable as semantically complete by confirming that every rule statement (identified by SHALL, NEVER, MUST, or ALWAYS keywords) present in the original section appears in the destination file with equivalent conditions and actions
7. IF a rule extracted to an Auto_File is not loaded during a turn where the agent's response requires that rule (as determined by keyword routing in `steering-index.yaml` or module context), THEN THE Always_On_File SHALL contain a single-line dispatch pointer in the format "For [topic]: load `[filename.md]`" directing the agent to load the relevant file

### Requirement 2: Reduce module-transitions.md always-on footprint

**User Story:** As a power maintainer, I want to minimize the always-on token cost of module transition rules, so that the base context budget is freed for active module content.

#### Acceptance Criteria

1. WHEN the optimization is complete, THE Always_On_File `module-transitions.md` SHALL contain only the sections that apply on every turn: Module Start Banner, Journey Map (at module start), Before/After Framing, Step-Level Progress, Module Completion, Transition Integrity, and Confirmation Response Requirements
2. WHEN detail-heavy sections are identified (Quality Feedback Loop, Sub-Step Convention), THE Optimizer SHALL move them to a new Auto_File named `module-transitions-detail.md` in the same `steering/` directory, with YAML frontmatter specifying a keyword-based activation trigger (e.g., `inclusion: auto` with keywords matching "transition", "sub-step", "quality loop")
3. WHEN `module-transitions.md` is split, THE resulting Always_On_File portion SHALL not exceed 60 lines (excluding YAML frontmatter)
4. WHEN the split is complete, THE Steering_Index `steering-index.yaml` SHALL contain a `file_metadata` entry for both the reduced `module-transitions.md` and the new `module-transitions-detail.md`, each with an updated `token_count` value measured by the same method used for existing entries and a corresponding `size_category`
5. WHEN the split is complete, THE combined content of the Always_On_File and the new Auto_File SHALL preserve all sections and rules present in the original `module-transitions.md` with no content removed or semantically altered

### Requirement 3: Compress large manual-inclusion files

**User Story:** As a power maintainer, I want large manual files compressed using Refine-style optimization, so that they consume fewer tokens when loaded into agent context without losing instructional fidelity.

#### Acceptance Criteria

1. WHEN `hook-registry-critical.md` (8,169 tokens) is optimized, THE resulting file SHALL have a Token_Count at most 70% of the original (no more than 5,718 tokens), where Token_Count is calculated as `round(len(file_content) / 4)`
2. WHEN `hook-registry-modules.md` (7,887 tokens) is optimized, THE resulting file SHALL have a Token_Count at most 70% of the original (no more than 5,521 tokens), where Token_Count is calculated as `round(len(file_content) / 4)`
3. WHEN `module-03-system-verification.md` (6,419 tokens) is optimized, THE resulting file SHALL have a Token_Count at most 75% of the original (no more than 4,814 tokens), where Token_Count is calculated as `round(len(file_content) / 4)`
4. WHEN `onboarding-flow.md` (5,266 tokens) is optimized, THE resulting file SHALL have a Token_Count at most 75% of the original (no more than 3,950 tokens), where Token_Count is calculated as `round(len(file_content) / 4)`
5. WHEN any file is compressed, THE Optimizer SHALL preserve all behavioral rules, step sequences, gate markers (⛔), question markers (👉), and hook definitions such that: (a) every gate marker and question marker present in the original appears in the compressed output with the same step association, (b) every hook name and its trigger-action pair from the original appears in the compressed output, and (c) every numbered step retains its ordinal position and imperative instruction
6. WHEN any file is compressed, THE Optimizer SHALL apply Refine-style techniques: tables instead of prose lists, shorthand notation, removal of redundant explanations, structured key-value formats, and elimination of filler words, transitional phrases, and repeated context that do not alter the instruction set conveyed to an LLM
7. IF a compressed file contains step-by-step instructions with gate markers (⛔) or question prompts (👉), THEN THE Optimizer SHALL retain step numbering, gate markers, and question prompts verbatim while compressing surrounding explanatory prose by at least 30% measured by character count of non-marker prose sections
8. WHEN any file is compressed, THE Optimizer SHALL replace the original file in-place within the `senzing-bootcamp/steering/` directory and update the corresponding `token_count` entry in `steering-index.yaml` to reflect the new measured value
9. IF the Optimizer cannot achieve the target Token_Count ratio for a file after applying all Refine-style techniques, THEN THE Optimizer SHALL report the file name, the achieved token count, and the target token count, and SHALL NOT discard semantic content to force compliance

### Requirement 4: Apply Refine-style optimization to always-on files

**User Story:** As a power maintainer, I want the always-on files written in terse, LLM-optimized format, so that the same behavioral rules are conveyed in fewer tokens.

#### Acceptance Criteria

1. WHEN `agent-instructions.md` is rewritten, THE Optimizer SHALL replace prose paragraphs of three or more consecutive sentences with equivalent tables, bullet lists, or key-value notation such that no behavioral rule present in the original is omitted from the rewritten output
2. WHEN `module-transitions.md` is rewritten, THE Optimizer SHALL replace banner templates and protocol rules with tables or compact bullet notation such that no behavioral rule present in the original is omitted from the rewritten output
3. WHEN Refine optimization is applied to an always-on file, THE Optimizer SHALL reduce the file's token count (as measured by `measure_steering.py`: characters / 4, rounded) by at least 15% compared to the pre-optimization token count
4. WHEN Refine optimization is applied, THE Optimizer SHALL run `measure_steering.py` (update mode) to regenerate the `file_metadata` and `budget` sections of `steering-index.yaml` before CI validation occurs
5. WHEN Refine optimization is applied, THE resulting files SHALL pass CI validation (`measure_steering.py --check`) with all token counts within the 10% tolerance threshold
6. WHEN Refine optimization is applied, THE resulting files SHALL pass `validate_commonmark.py` with zero markdownlint violations under the project's `.markdownlint.json` configuration
7. IF Refine optimization of an always-on file produces output that omits a behavioral rule present in the original file, THEN THE Optimizer SHALL reject the optimization and retain the original content for that section

### Requirement 5: Update steering-index.yaml after all changes

**User Story:** As a power maintainer, I want the steering index to accurately reflect all file changes, so that CI validation passes and the agent's context budget calculations remain correct.

#### Acceptance Criteria

1. WHEN any steering file is created, renamed, split, or deleted, THE Steering_Index SHALL be updated so that the `file_metadata` section contains an entry for every `.md` file in the steering directory, each with a `token_count` computed as `round(character_count / 4)` and a `size_category` of "small" (under 500 tokens), "medium" (500–2000 tokens), or "large" (over 2000 tokens)
2. WHEN a steering file's content is modified, THE Steering_Index SHALL update that file's `token_count` and `size_category` in the `file_metadata` section to reflect the new content
3. WHEN new phase files are created from extracted module sections, THE Steering_Index SHALL include their entries in both the `file_metadata` section and the corresponding module's `phases` mapping with the correct `file`, `token_count`, `size_category`, and `step_range` fields
4. WHEN the optimization is complete, THE CI_Validation command `measure_steering.py --check` SHALL exit with code 0, confirming all stored token counts are within 10% of the calculated values and no files are missing from or orphaned in the index
5. WHEN the total token budget changes, THE Steering_Index `budget.total_tokens` field SHALL equal the sum of all `token_count` values in the `file_metadata` section
6. WHEN new files are created, THE Steering_Index `keywords` section SHALL include at least one keyword-to-file mapping per new file, where each keyword is a term that appears in the file's title or YAML frontmatter `keywords` field

### Requirement 6: Preserve behavioral correctness

**User Story:** As a power maintainer, I want all agent behaviors to remain functionally identical after optimization, so that bootcampers experience no regression in the guided learning flow.

#### Acceptance Criteria

1. THE Optimizer SHALL preserve all ⛔ mandatory gate rules such that each gate retains its original trigger condition, blocking behavior, and precedence relative to other rules in the same steering file
2. THE Optimizer SHALL preserve all 👉 question protocol rules such that the single-question-per-turn constraint, the `.question_pending` file write requirement, and the wait-for-response behavior remain enforceable by the existing hook logic
3. THE Optimizer SHALL preserve all MCP-first invariant rules such that the pre-response checklist sequence (call MCP tool before presenting Senzing facts) and the prohibition on using training data for Senzing content remain explicitly stated
4. THE Optimizer SHALL preserve all hook creation rules such that hook file names match the `hook-id.kiro.hook` naming convention and all required JSON fields (`name`, `version`, `when`, `then`) remain present and semantically unchanged
5. THE Optimizer SHALL preserve all file placement rules and root prohibitions such that the directory-to-content-type mapping defined in the project structure remains explicitly stated in the optimized output
6. WHEN the optimization is complete, THE agent SHALL produce the same state transitions (progress file writes, module advancement, gate enforcement) and the same user-observable outputs (banners, journey maps, closing questions, error messages) for all documented interaction patterns: module starts, module transitions, question handling, and error recovery
7. IF a behavioral rule can be rephrased in more than one semantically distinct way after compression (i.e., two independent readers could derive different agent behaviors from the compressed text), THEN THE Optimizer SHALL retain the verbose form for that specific rule
8. WHEN the optimization is complete, THE Optimizer SHALL verify that the count of distinct behavioral rules (⛔ gates, 👉 protocol rules, MCP-first rules, hook creation rules, file placement rules) in the optimized output equals the count in the original input, and flag any discrepancy as a failed optimization

### Requirement 7: Maintain CI pipeline compatibility

**User Story:** As a power maintainer, I want all CI checks to pass after the optimization, so that the changes can be merged without pipeline failures.

#### Acceptance Criteria

1. WHEN the optimization is complete, THE command `measure_steering.py --check` SHALL exit with code 0, confirming all steering file token counts in `steering-index.yaml` are within 10% of calculated values
2. WHEN the optimization is complete, THE command `validate_commonmark.py` SHALL exit with code 0, confirming no markdownlint violations exist in any markdown file within the repository
3. WHEN the optimization is complete, THE command `validate_power.py` SHALL exit with code 0, confirming all cross-references resolve, all hooks are valid JSON with required fields, all steering files have valid YAML frontmatter, and version files are in sync
4. WHEN new steering files are created, THE files SHALL include YAML frontmatter containing an `inclusion` field with a value of `always`, `auto`, `fileMatch`, or `manual`, and a `description` field
5. WHEN existing steering files are renamed or removed, THE `steering-index.yaml` file SHALL not reference any non-existent files in its `modules`, `file_metadata`, or `keywords` sections
6. WHEN the optimization is complete, THE full CI pipeline defined in `.github/workflows/validate-power.yml` SHALL pass, including `validate_dependencies.py`, `sync_hook_registry.py --verify`, `validate_prerequisites.py`, `validate_yaml_schemas.py`, `ruff check`, and `pytest`
