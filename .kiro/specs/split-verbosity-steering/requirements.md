# Requirements Document

## Introduction

The steering file `senzing-bootcamp/steering/verbosity-control.md` is 248 lines and 4,152 tokens with `inclusion: always`, meaning it loads into the agent's context on every conversation turn. The "Steering Kiro: Best Practices" guideline recommends that always-included files stay within 40–80 lines each. At 248 lines, this file is a "context bomb" — it consumes 4,152 tokens on every interaction regardless of whether the bootcamper is discussing verbosity.

Most of the file's bulk comes from detailed per-level content rules and framing pattern examples that the agent only needs when it is actively applying a specific verbosity level's output rules. The actionable decision-making content — preset definitions, category names, NL term mapping, and adjustment instructions — is compact enough to fit within the 80-line guideline.

This feature splits `verbosity-control.md` into two files: a lean core file (always-loaded, ~80 lines) containing the decision-making content the agent needs on every turn, and a detailed reference file (manually-loaded, ~170 lines) containing the full category definitions, content rules by level, and framing pattern examples that the agent loads on demand when it needs to apply level-specific output rules.

## Glossary

- **Core_File**: The steering file at `senzing-bootcamp/steering/verbosity-control.md` after the split, containing the lean always-loaded verbosity decision-making content. Retains `inclusion: always` in its YAML frontmatter.
- **Reference_File**: The new steering file at `senzing-bootcamp/steering/verbosity-control-reference.md` containing the detailed verbosity reference content loaded on demand. Uses `inclusion: manual` in its YAML frontmatter.
- **Steering_Index**: The file at `senzing-bootcamp/steering/steering-index.yaml` that registers all steering files with their token counts, size categories, and keyword mappings.
- **Agent**: The Kiro-powered assistant that delivers the bootcamp content, reads steering files, and generates output for the Bootcamper.
- **Decision_Content**: The subset of verbosity control content the agent needs on every turn to identify presets, map natural language terms, and process adjustment requests. Includes: preset definitions table, category names with one-line descriptions, NL term mapping table, adjustment instructions (preset changes, NL adjustments, custom preset logic), and session-start preferences reading instructions.
- **Reference_Content**: The subset of verbosity control content the agent consults only when applying level-specific output rules. Includes: full output category definitions with examples, content rules by level for each category, and framing pattern examples (what/why, code execution, step recap) at each level.
- **File_Reference_Directive**: A `#[[file:]]` directive in the Core_File that tells the agent where to find the Reference_File so it can load it on demand.
- **Bootcamper**: The user participating in the Senzing bootcamp learning exercise.

## Requirements

### Requirement 1: Split Verbosity Steering into Core and Reference Files

**User Story:** As the bootcamp power author, I want the verbosity steering content split into a lean always-loaded core and a detailed on-demand reference, so that the agent's per-turn context cost drops from 4,152 tokens to approximately 80 lines while preserving all existing content.

#### Acceptance Criteria

1. THE Core_File SHALL exist at the path `senzing-bootcamp/steering/verbosity-control.md`.
2. THE Reference_File SHALL exist at the path `senzing-bootcamp/steering/verbosity-control-reference.md`.
3. THE Core_File and Reference_File combined SHALL contain all content present in the original `verbosity-control.md` — no content SHALL be removed, only reorganized between the two files.
4. THE Core_File SHALL be no longer than 80 lines.
5. THE total token count of the Core_File and Reference_File combined SHALL be approximately equal to the original file's token count of 4,152 tokens, with no more than 5% inflation.

### Requirement 2: Core File Content

**User Story:** As the bootcamp power author, I want the core file to contain only the actionable decision-making content the agent needs on every turn, so that the always-loaded context cost is minimized.

#### Acceptance Criteria

1. THE Core_File SHALL contain the preset definitions table mapping each preset name (`concise`, `standard`, `detailed`) to its per-category levels.
2. THE Core_File SHALL contain a list of all five output category names (`explanations`, `code_walkthroughs`, `step_recaps`, `technical_details`, `code_execution_framing`) with a one-line description for each.
3. THE Core_File SHALL contain the natural language term mapping table that maps common terms to output categories.
4. THE Core_File SHALL contain the adjustment instructions for preset changes, including the steps to identify the requested preset, update all five category levels, write to the preferences file, and confirm the change.
5. THE Core_File SHALL contain the adjustment instructions for natural language adjustments, including the steps to match the term, adjust the level by +1 or -1 clamped to 1–3, set the preset to `custom` or detect a matching named preset, write to the preferences file, and confirm the change.
6. THE Core_File SHALL contain the instructions for reading verbosity preferences on session start, including handling missing, present, and malformed `verbosity` keys.
7. THE Core_File SHALL contain the definition of the `custom` preset behavior.

### Requirement 3: Core File Frontmatter and Reference Directive

**User Story:** As the bootcamp power author, I want the core file to retain always-loaded status and include a directive pointing to the reference file, so that the agent can find and load the detailed content when needed.

#### Acceptance Criteria

1. THE Core_File SHALL use `inclusion: always` in its YAML frontmatter.
2. THE Core_File SHALL include a `#[[file:]]` reference directive pointing to `verbosity-control-reference.md` so the agent can load the Reference_File on demand.
3. THE Core_File SHALL instruct the Agent to load the Reference_File when the Agent needs to apply level-specific content rules for the first time in a session.

### Requirement 4: Reference File Content

**User Story:** As the bootcamp power author, I want the reference file to contain the detailed verbosity definitions, content rules, and framing examples, so that the agent can consult them when applying specific verbosity levels.

#### Acceptance Criteria

1. THE Reference_File SHALL contain the full output category definitions, including the definition paragraph and examples of content that falls under each category.
2. THE Reference_File SHALL contain the content rules by level (1, 2, 3) for each of the five output categories, specifying what content to include and what to omit at each level.
3. THE Reference_File SHALL contain the framing pattern examples for the "what and why" framing (explanations category) at all three levels.
4. THE Reference_File SHALL contain the framing pattern examples for the code execution framing (code_execution_framing category) at all three levels.
5. THE Reference_File SHALL contain the framing pattern examples for the step recap framing (step_recaps category) at all three levels.

### Requirement 5: Reference File Frontmatter

**User Story:** As the bootcamp power author, I want the reference file to use manual inclusion, so that it only loads into the agent's context when explicitly requested.

#### Acceptance Criteria

1. THE Reference_File SHALL use `inclusion: manual` in its YAML frontmatter.

### Requirement 6: Steering Index Updates

**User Story:** As the bootcamp power author, I want the steering index updated to reflect the new two-file structure, so that the agent's context budget tracking remains accurate and the reference file is discoverable.

#### Acceptance Criteria

1. THE Steering_Index `file_metadata` section SHALL contain an entry for `verbosity-control-reference.md` with its `token_count` and `size_category`.
2. THE Steering_Index `file_metadata` entry for `verbosity-control.md` SHALL be updated with the new token count and size category reflecting the reduced core file.
3. THE Steering_Index `keywords` section SHALL include keyword entries that map to `verbosity-control-reference.md` so the agent can discover the reference file by keyword search.
4. THE Steering_Index `budget.total_tokens` value SHALL be updated to reflect the combined token counts of both files (which should be approximately equal to the original total since no content is added or removed).

### Requirement 7: Existing Test Compatibility

**User Story:** As a developer, I want all existing tests that reference `verbosity-control.md` to continue passing after the split, so that the refactoring does not break the test suite.

#### Acceptance Criteria

1. WHEN the test suite runs, THE tests in `senzing-bootcamp/tests/test_verbosity_properties.py` SHALL pass without modification to the test file.
2. WHEN the test suite runs, THE tests in `senzing-bootcamp/tests/test_verbosity_unit.py` SHALL pass.
3. IF any test in `test_verbosity_unit.py` checks for content that has moved from the Core_File to the Reference_File, THEN THE test SHALL be updated to check the correct file while preserving the original test intent.
4. THE steering file smoke tests in `TestSteeringFileSmokeTests` that verify content presence in `verbosity-control.md` SHALL be updated to check the appropriate file (Core_File or Reference_File) for each piece of content.
5. THE smoke tests that verify `inclusion: always` in the Core_File frontmatter SHALL continue to pass without modification.
6. THE smoke tests that verify keyword entries in `steering-index.yaml` SHALL continue to pass without modification.
