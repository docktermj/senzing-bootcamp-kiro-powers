# Implementation Plan: Bootcamp Verbosity Control

## Overview

Build a verbosity control system for the senzing-bootcamp power. The implementation starts with the testable Python logic module, validates it with property-based and unit tests, then creates the steering file content, modifies the onboarding flow, and registers the new file in the steering index. All Python code uses stdlib only (no PyYAML). Tests use pytest + Hypothesis.

## Tasks

- [x] 1. Implement the verbosity logic module (`senzing-bootcamp/scripts/verbosity.py`)
  - [x] 1.1 Create the `VerbosityPreferences` dataclass and constants
    - Define the `VerbosityPreferences` dataclass with `preset: str` and `categories: dict[str, int]` fields
    - Define `CATEGORIES` list: `["explanations", "code_walkthroughs", "step_recaps", "technical_details", "code_execution_framing"]`
    - Define `PRESETS` dict with the three named presets and their per-category level mappings: `concise` (1,1,2,1,1), `standard` (2,2,2,2,2), `detailed` (3,3,3,3,3)
    - Define `NL_TERM_MAP` dict mapping all natural language terms from the design to their category names (e.g., `"explanations"` → `explanations`, `"context"` → `explanations`, `"code detail"` → `code_walkthroughs`, etc.)
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 5.3_

  - [x] 1.2 Implement `resolve_preset` and `detect_preset` functions
    - `resolve_preset(preset_name)` returns a `VerbosityPreferences` for a named preset; raises `ValueError` for unknown names
    - `detect_preset(categories)` returns the matching preset name or `"custom"` by comparing against all preset definitions
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.5_

  - [x] 1.3 Implement `adjust_category` and `match_nl_term` functions
    - `adjust_category(prefs, category, delta)` returns new preferences with one category adjusted by delta, clamped to [1, 3]; sets preset to `"custom"` if result doesn't match a named preset; raises `ValueError` for unknown category
    - `match_nl_term(term)` returns the matching category name from `NL_TERM_MAP` or `None` if no match
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.6_

  - [x] 1.4 Implement `serialize_preferences` and `deserialize_preferences` functions
    - `serialize_preferences(prefs)` converts `VerbosityPreferences` to a YAML string fragment (stdlib only, no PyYAML — use string formatting)
    - `deserialize_preferences(yaml_text)` parses a YAML verbosity block into `VerbosityPreferences` using minimal custom parsing (stdlib only)
    - Ensure round-trip consistency: `deserialize(serialize(prefs))` produces identical values
    - _Requirements: 6.1, 6.2, 6.5_

  - [x] 1.5 Implement `validate_preferences` function
    - `validate_preferences(data)` checks a dict for: presence of `preset` field, presence of `categories` map, all five categories present, levels are integers in range 1–3, preset is a valid string
    - Returns a list of error strings (empty means valid)
    - _Requirements: 6.2, 6.4_

- [x] 2. Write property-based tests (`senzing-bootcamp/tests/test_verbosity_properties.py`)
  - [x] 2.1 Write property test for serialization round-trip
    - **Property 1: Preferences Serialization Round-Trip**
    - For any valid `VerbosityPreferences` (preset in `{"concise", "standard", "detailed", "custom"}`, all category levels in 1–3), `deserialize_preferences(serialize_preferences(prefs))` produces identical `preset` and `categories` values
    - Use Hypothesis strategies: `st.sampled_from` for preset names, `st.integers(1, 3)` for levels, `st.fixed_dictionaries` for categories
    - `@settings(max_examples=100)`
    - **Validates: Requirements 2.5, 3.3, 4.2, 5.4, 6.2**

  - [x] 2.2 Write property test for category level clamping
    - **Property 2: Category Level Adjustment Clamping**
    - For any valid preferences, any category, and any delta in `{+1, -1}`, `adjust_category` produces a level equal to `clamp(original + delta, 1, 3)` with all other levels unchanged
    - `@settings(max_examples=100)`
    - **Validates: Requirements 5.1, 5.2**

  - [x] 2.3 Write property test for preset detection after adjustment
    - **Property 3: Preset Detection After Adjustment**
    - For any named preset and any single-category adjustment, if the resulting levels don't match any preset definition then `detect_preset` returns `"custom"`; if they do match, it returns that preset's name
    - `@settings(max_examples=100)`
    - **Validates: Requirements 5.5**

  - [x] 2.4 Write property test for unrecognized NL term rejection
    - **Property 4: Unrecognized Natural Language Term Rejection**
    - For any string not in `NL_TERM_MAP`, `match_nl_term` returns `None`; for any key in `NL_TERM_MAP`, it returns the correct category
    - Use `st.text(min_size=1, max_size=50).filter(lambda t: t.lower().strip() not in NL_TERM_MAP)` for non-matching terms
    - `@settings(max_examples=100)`
    - **Validates: Requirements 5.6**

- [x] 3. Write unit tests (`senzing-bootcamp/tests/test_verbosity_unit.py`)
  - [x] 3.1 Write unit tests for preset definitions and resolution
    - Verify `resolve_preset("concise")` returns exact levels: explanations=1, code_walkthroughs=1, step_recaps=2, technical_details=1, code_execution_framing=1
    - Verify `resolve_preset("standard")` returns all levels at 2
    - Verify `resolve_preset("detailed")` returns all levels at 3
    - Verify `resolve_preset("unknown")` raises `ValueError`
    - _Requirements: 2.2, 2.3, 2.4_

  - [x] 3.2 Write unit tests for default behavior and NL term mapping
    - Verify missing verbosity key defaults to standard preset behavior (via `resolve_preset("standard")`)
    - Verify all NL terms from Requirement 5.3 are present in `NL_TERM_MAP`: "explanations", "context", "code detail", "code walkthrough", "code walkthroughs", "line by line", "recaps", "summaries", "recap", "summary", "technical", "internals", "technical detail", "technical details", "before and after", "execution framing", "code framing", "framing"
    - Verify `match_nl_term` returns `None` for unrecognized terms
    - _Requirements: 3.5, 5.3, 5.6, 6.4_

  - [x] 3.3 Write unit tests for boundary clamping and validation errors
    - Verify level 3 + delta +1 stays at 3
    - Verify level 1 + delta -1 stays at 1
    - Verify `adjust_category` raises `ValueError` for unknown category name
    - Verify `validate_preferences` catches: missing `preset` field, missing categories, out-of-range levels (0, 4), wrong types (string instead of int)
    - _Requirements: 5.1, 5.2, 6.2_

- [x] 4. Checkpoint — Run all tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Create the verbosity steering file (`senzing-bootcamp/steering/verbosity-control.md`)
  - [x] 5.1 Write YAML frontmatter and output category taxonomy
    - Add YAML frontmatter with `inclusion: always`
    - Define the five Output_Categories with definitions and examples of what content falls under each
    - Define content rules for each category at each level (1, 2, 3) — what to include and what to omit
    - _Requirements: 1.1, 1.2, 1.4, 10.1, 10.2, 10.3, 10.4_

  - [x] 5.2 Write preset definitions and NL term mapping sections
    - Define the three presets (`concise`, `standard`, `detailed`) with their per-category level mappings in a table
    - Define the natural language term-to-category mapping table for agent use during NL adjustments
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.3, 10.5, 10.6_

  - [x] 5.3 Write framing patterns and adjustment instructions
    - Define the "what and why" framing pattern with examples at each level for the `explanations` category
    - Define the code execution framing pattern (before / what this code does / after) with examples at each level
    - Define the step recap pattern with examples at each level
    - Define adjustment instructions: how the agent handles preset changes, NL adjustments, and the `custom` preset transition
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 10.7, 10.8, 10.9_

- [x] 6. Modify the onboarding flow (`senzing-bootcamp/steering/onboarding-flow.md`)
  - [x] 6.1 Add verbosity question as a sub-step in Step 4
    - Insert a new sub-step after the overview presentation and before track selection (Step 5)
    - Present the three presets with one-line descriptions; mark `standard` as recommended
    - Instruct the agent to persist the selection to the `verbosity` key in the preferences file
    - Include the follow-up message: "You can change your verbosity level at any time by saying 'change verbosity' or by fine-tuning specific categories like 'I want more code walkthroughs'."
    - If the bootcamper skips, apply `standard` as default and inform them
    - This is NOT a mandatory gate (⛔) — the bootcamper can skip it
    - Do NOT renumber existing steps — this is a sub-step of Step 4
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Update the steering index (`senzing-bootcamp/steering/steering-index.yaml`)
  - [x] 7.1 Register verbosity-control.md in the steering index
    - Add keyword entries: `verbosity: verbosity-control.md`, `verbose: verbosity-control.md`, `output level: verbosity-control.md`
    - Add `file_metadata` entry for `verbosity-control.md` with `token_count` (measure after creation) and `size_category` (small/medium/large based on token count)
    - _Requirements: 10.10_

- [x] 8. Add steering file smoke tests to the unit test file
  - [x] 8.1 Write steering file smoke tests
    - Verify `senzing-bootcamp/steering/verbosity-control.md` exists
    - Verify frontmatter contains `inclusion: always`
    - Verify all five category names appear in the file
    - Verify all three preset names appear in the file
    - Verify NL term mapping table is present
    - Verify what/why framing examples exist for all three levels
    - Verify code execution framing examples exist for all three levels
    - Verify step recap examples exist for all three levels
    - Verify `senzing-bootcamp/steering/steering-index.yaml` contains the three keyword entries (`verbosity`, `verbose`, `output level`)
    - _Requirements: 1.1, 1.2, 1.4, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10_

- [x] 9. Final checkpoint — Run all tests
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Python 3.11+ stdlib only for `scripts/verbosity.py` (no PyYAML)
- Tests use pytest + Hypothesis; test files live in `senzing-bootcamp/tests/`
- The onboarding flow modification is a sub-step of Step 4, not a new top-level step
- Property tests validate the four correctness properties from the design document
- Checkpoints ensure incremental validation after the logic module and after all artifacts
