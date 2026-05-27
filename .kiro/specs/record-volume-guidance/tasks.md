# Implementation Plan: Record Volume Guidance

## Overview

Implement a record volume guidance step in Module 6 Phase A that asks bootcampers about their expected production record volume, classifies the response into a tier, persists the selection, and generates tier-specific guidance on licensing, architecture, database, and performance. The implementation consists of a Python utility module (`scripts/volume_utils.py`), steering file modifications, and config updates.

## Tasks

- [x] 1. Create volume utility module with parsing and classification
  - [x] 1.1 Create `senzing-bootcamp/scripts/volume_utils.py` with constants and `parse_volume_input`
    - Define module-level constants: `TIER_DEMO`, `TIER_SMALL`, `TIER_MEDIUM`, `TIER_LARGE`, `VALID_TIERS`, `TIER_BOUNDARIES`
    - Implement `parse_volume_input(text: str) -> int | None` using stdlib `re` to handle plain digits, comma-separated numbers, K/M/B suffixes, decimal suffixes (e.g., "1.5M"), and word multipliers ("10 million", "5 thousand")
    - Return `None` for unparseable input (no digits, no numeric abbreviations, no numeric word forms)
    - _Requirements: 1.4, 1.5_

  - [x] 1.2 Implement `classify_tier` and `should_ask_volume` in `volume_utils.py`
    - Implement `classify_tier(record_count: int) -> str` using `TIER_BOUNDARIES` to map count to tier; raise `ValueError` for negative input
    - Implement `should_ask_volume(preferences: dict) -> bool` returning `False` only when `production_volume` has valid integer `raw_value` and recognized `tier`
    - _Requirements: 1.4, 2.3, 2.4_

  - [x] 1.3 Write property tests for parsing and classification (Properties 1, 2)
    - **Property 1: Numeric input classification correctness** — for any string with recognizable numeric value, `parse_volume_input` returns an integer and `classify_tier` returns the correct tier
    - **Validates: Requirements 1.4**
    - **Property 2: Non-numeric input rejection** — for any string with no recognizable numeric content, `parse_volume_input` returns None
    - **Validates: Requirements 1.5**

  - [x] 1.4 Write property tests for session resume logic (Properties 4, 5)
    - **Property 4: Session resume skip detection** — for any preferences dict with valid `production_volume` (integer `raw_value` + tier in `VALID_TIERS`), `should_ask_volume` returns False
    - **Validates: Requirements 2.3**
    - **Property 5: Session resume re-ask detection** — for any preferences dict where `production_volume` is missing, None, has non-integer `raw_value`, or unrecognized tier, `should_ask_volume` returns True
    - **Validates: Requirements 2.4**

- [x] 2. Implement persistence and guidance generators
  - [x] 2.1 Implement `persist_volume_selection` in `volume_utils.py`
    - Write `persist_volume_selection(raw_value, tier, preferences_path, progress_path, step_number)` that writes `production_volume` key (with `raw_value` and `tier` fields) to the YAML preferences file and writes step checkpoint to the JSON progress file
    - Use stdlib `json` for progress; use simple YAML write (or read-modify-write with existing YAML handling) for preferences
    - _Requirements: 1.6, 2.1, 2.2_

  - [x] 2.2 Write property test for persistence round-trip (Property 3)
    - **Property 3: Volume persistence round-trip** — for any valid record count and classified tier, persisting and reading back produces matching `raw_value` and `tier`
    - **Validates: Requirements 1.6, 2.1**

  - [x] 2.3 Implement `get_license_guidance` in `volume_utils.py`
    - Return `None` if tier is `None` (skip guidance per Req 3.5)
    - For `demo` tier: state 500-record evaluation license is sufficient
    - For `small`/`medium`/`large`: state production license required, mention MCP server and Senzing sales options
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

  - [x] 2.4 Implement `get_architecture_guidance` in `volume_utils.py`
    - `demo`: recommend single-threaded, no additional planning needed
    - `small`: recommend single-threaded, mention multi-threading beyond 100K records
    - `medium`: recommend multi-threaded with thread pool, reference MCP `generate_scaffold` with `record_count`
    - `large`: recommend distributed/queue-based, reference MCP `sdk_guide` with `topic='load'`
    - All tiers: include "production recommendation" label and bootcamp single-threaded disclaimer
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 2.5 Implement `get_database_guidance` in `volume_utils.py`
    - `demo`/`small`: confirm SQLite sufficient
    - `medium`/`large` with `current_database="sqlite"`: recommend PostgreSQL, explain single-writer limitation
    - `medium`/`large` with `current_database="postgresql"`: acknowledge existing config, skip limitation explanation
    - All tiers: include bootcamp-continues-with-current-database disclaimer
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 2.6 Implement `get_performance_guidance` in `volume_utils.py`
    - `demo`/`small`: loading completes in seconds to minutes, no additional config needed
    - `medium`: minutes to hours depending on CPU/threads, reference Module 8
    - `large`: hours to days, distributed architecture required, reference Modules 8 and 11
    - All tiers: reference MCP `search_docs` with `category="configuration"`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 2.7 Write property tests for guidance generators (Properties 6–13)
    - **Property 6: License guidance for non-demo tiers** — for any tier in {small, medium, large}, output mentions production license AND MCP/sales options
    - **Validates: Requirements 3.2, 3.3**
    - **Property 7: Architecture guidance universal disclaimers** — for any tier, output contains "production recommendation" label and single-threaded bootcamp statement
    - **Validates: Requirements 4.5**
    - **Property 8: Database guidance — SQLite sufficient for low tiers** — for any tier in {demo, small}, output confirms SQLite sufficient
    - **Validates: Requirements 5.1**
    - **Property 9: Database guidance — PostgreSQL for high tiers** — for any tier in {medium, large} with sqlite, output recommends PostgreSQL and explains single-writer limitation
    - **Validates: Requirements 5.2**
    - **Property 10: Database guidance — bootcamp disclaimer for all tiers** — for any tier, output states bootcamp continues with current database
    - **Validates: Requirements 5.3**
    - **Property 11: Database guidance — PostgreSQL acknowledgment** — for any tier in {medium, large} with postgresql, output acknowledges config and does NOT contain single-writer limitation
    - **Validates: Requirements 5.4**
    - **Property 12: Performance guidance — fast completion for low tiers** — for any tier in {demo, small}, output indicates seconds to minutes
    - **Validates: Requirements 6.1**
    - **Property 13: Performance guidance — MCP reference for all tiers** — for any tier, output references `search_docs` with `category="configuration"`
    - **Validates: Requirements 6.4**

- [x] 3. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update steering files and config
  - [x] 4.1 Modify `senzing-bootcamp/steering/module-06-phaseA-build-loading.md` to insert volume step as step 1
    - Insert new step 1 with bold title "Assess production record volume:", pointing question (👉), 🛑 STOP directive, example ranges for all four tiers, agent instruction blockquote with parsing/classification/persistence logic, fallback for unparseable input, and checkpoint line
    - Renumber existing step 1 → step 2, step 2 → step 3, step 3 → step 4 (update headings, checkpoint lines)
    - Add conditional agent instruction to step 3 (formerly step 2) to read `production_volume` from preferences and pass `record_count` to `generate_scaffold` for medium/large tiers
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.7, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

  - [x] 4.2 Update `senzing-bootcamp/steering/module-06-data-processing.md` phase sub-files section
    - Change Phase A step range from "steps 1–3" to "steps 1–4"
    - Change Phase B step range from "steps 4–10" to "steps 5–11"
    - Change Phase C step range from "steps 11–19" to "steps 12–20"
    - Change Phase D step range from "steps 20–27" to "steps 21–28"
    - _Requirements: 7.2_

  - [x] 4.3 Update `senzing-bootcamp/steering/steering-index.yaml` Module 6 phase entries
    - `phase1-build-loading-program`: `step_range: [1, 4]`
    - `phase2-load-first-source`: `step_range: [5, 11]`
    - `phase3-multi-source-orchestration`: `step_range: [12, 20]`
    - `phase4-validation`: `step_range: [21, 28]`
    - _Requirements: 7.5_

- [x] 5. Write unit and integration tests
  - [x] 5.1 Write unit tests in `senzing-bootcamp/tests/test_record_volume_guidance_unit.py`
    - Test specific parsing examples: "500", "1M", "10 million", "1,000,000", "1.5M"
    - Test tier boundary values: 0, 499, 500, 499_999, 500_000, 9_999_999, 10_000_000
    - Test license guidance content for demo tier (500-record evaluation license)
    - Test architecture guidance content per tier
    - Test performance guidance for medium and large tiers
    - Test default fallback to demo tier for unparseable input
    - _Requirements: 1.4, 1.5, 1.7, 3.1, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3_

  - [x] 5.2 Write integration tests in `senzing-bootcamp/tests/test_record_volume_guidance_integration.py`
    - Test end-to-end flow: parse → classify → persist → read back → generate guidance
    - Test steering file structure validation: step numbering consistency, phase ranges in steering-index.yaml match steering files
    - _Requirements: 2.1, 2.2, 7.1, 7.2, 7.5_

- [x] 6. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python 3.11+ stdlib only (no third-party deps in production code)
- Tests use pytest + Hypothesis per project convention (`@settings(max_examples=20)`)
- All test files go in `senzing-bootcamp/tests/`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["1.3", "1.4", "2.2", "2.3", "2.4", "2.5", "2.6"] },
    { "id": 3, "tasks": ["2.7", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3"] },
    { "id": 5, "tasks": ["5.1", "5.2"] }
  ]
}
```
