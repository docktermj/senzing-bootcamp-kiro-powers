# Implementation Plan: Module 6 SQLite Volume Hard_Prompt

## Overview

Add a stop-and-confirm **Hard_Prompt** to Module 6 that fires before the Phase B load only for the
risky combination `Volume_Tier ∈ {Medium, Large}` **and** `SQLite_Active`. The decision is a single
pure predicate, `should_prompt(tier, db_type, already_decided)`, and the wording is a companion pure
builder, `build_hard_prompt(tier, record_count)`; both are added to the existing
`senzing-bootcamp/scripts/volume_utils.py` (stdlib only, reusing the `TIER_*` constants and
`VALID_TIERS` — no new script, no new dependency). The Module 6 Phase A steering
(`module-06-phaseA-build-loading.md`) reads already-persisted preferences via `preferences_utils`,
computes `already_decided` from a load-scoped decision marker, calls the predicate, presents the
builder's output when it fires, routes the migrate choice to the existing `database-migration-guide`
(no duplicated migration steps), records the proceed choice, and never becomes a Mandatory_Gate (⛔).

Work proceeds bottom-up: the two pure functions first (each with its property test placed right after
implementation), then the focused example/guardrail tests, then the steering wiring, and finally the
steering-structure test. All code targets Python 3.11+ stdlib only and follows the project
script/test conventions (pytest + Hypothesis, class-based, `sys.path` import, registered profiles —
no hand-set `max_examples`).

## Tasks

- [x] 1. Implement the pure trigger predicate
  - [x] 1.1 Implement `should_prompt` in `volume_utils.py`
    - Add `should_prompt(tier: str | None, db_type: str | None, already_decided: bool = False) -> bool`
      to `senzing-bootcamp/scripts/volume_utils.py`, reusing the existing `TIER_MEDIUM`,
      `TIER_LARGE`, and `VALID_TIERS` — do not re-derive tiers from record counts
    - Normalize `db_type` case-insensitively with surrounding whitespace stripped
      (`"SQLite"`, `" sqlite "` → `"sqlite"`); return `True` **iff**
      `tier in (TIER_MEDIUM, TIER_LARGE)` AND normalized `db_type == "sqlite"` AND
      `already_decided is False`
    - Return `False` for Demo/Small tiers, any non-SQLite engine, any indeterminate `tier`/`db_type`
      (`None`/empty/unrecognized), and whenever `already_decided is True`; never raise, never do I/O
    - _Requirements: 1.1, 1.2, 1.3, 2.4, 3.2, 3.3_

  - [x] 1.2 Write property test for the trigger truth table
    - **Property 1: Trigger fires exactly on Medium/Large-on-SQLite (comprehensive truth table)**
    - Add `st_tier()` (VALID_TIERS + `None` + junk) and `st_db_type()` (`sqlite` in mixed case/with
      whitespace, `postgresql`, `""`, `None`, junk) strategies; assert the exact boolean formula
      across `st_tier() × st_db_type() × st.booleans()` and that the predicate never raises
    - **Validates: Requirements 1.1, 1.2, 1.3, 2.4, 3.3**

- [x] 2. Implement the prompt wording builder
  - [x] 2.1 Implement `build_hard_prompt` in `volume_utils.py`
    - Add `build_hard_prompt(tier: str, record_count: int | None = None) -> str` to
      `senzing-bootcamp/scripts/volume_utils.py`
    - Always include the human tier label and a statement that a Medium/Large load on SQLite is
      expected to be slow; include the record count when `record_count is not None` and omit the
      figure gracefully when it is `None`
    - Always offer both the Migration_Alternative (naming `database-migration-guide` /
      `DATABASE_MIGRATION.md`) and a proceed-on-SQLite option; never emit the Mandatory_Gate marker
      (⛔) and never inline the migration procedure text; never raise
    - _Requirements: 2.1, 2.2, 3.1, 3.2_

  - [x] 2.2 Write property test for prompt content
    - **Property 2: Prompt names the tier, record count, and expected slowdown**
    - Add `st_record_count()` (non-negative integers plus `None`); over
      `st.sampled_from([TIER_MEDIUM, TIER_LARGE]) × st_record_count()` assert the text names the
      tier, states the slowdown, includes the count when present, omits it gracefully when `None`,
      and never raises
    - **Validates: Requirements 2.1**

  - [x] 2.3 Write property test for options and non-blocking wording
    - **Property 3: Prompt always offers migration and proceed, and is never a mandatory gate**
    - Over the same generators as Property 2, assert the output always contains a
      Migration_Alternative option naming `database-migration-guide` / `DATABASE_MIGRATION.md` and a
      proceed-on-SQLite option, and never contains the ⛔ marker
    - **Validates: Requirements 2.2, 3.1**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add focused example and guardrail tests
  - [x] 4.1 Write explicit truth-table cell tests
    - In `senzing-bootcamp/tests/test_sqlite_volume_hard_prompt.py` (class-based
      `TestSqliteVolumeHardPrompt`, `sys.path` import of `scripts/`), assert the four corner cases:
      `(medium, sqlite) → True`, `(large, sqlite) → True`, `(small, sqlite) → False`,
      `(medium, postgresql) → False`
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2_

  - [x] 4.2 Write indeterminate-fallback and no-reprompt tests
    - Assert `should_prompt(None, "sqlite")` and `should_prompt("medium", None)` both return `False`
      (indeterminate fallback), and `should_prompt("medium", "sqlite", already_decided=True)` returns
      `False` (no re-prompt for the same load)
    - _Requirements: 2.4, 3.3, 4.1_

  - [x] 4.3 Write migration-routing / reuse guardrail tests
    - Assert `build_hard_prompt` names the `database-migration-guide` / `DATABASE_MIGRATION.md` and
      inlines no migration steps, and assert `should_prompt`/`build_hard_prompt` are defined in
      `volume_utils.py` and rely on the existing tier constants rather than re-deriving tiers from
      record counts
    - _Requirements: 2.3, 3.2, 4.1_

- [x] 5. Wire the Hard_Prompt into Module 6 Phase A steering
  - [x] 5.1 Add the "SQLite Volume Hard_Prompt (pre-load check)" block
    - Edit `senzing-bootcamp/steering/module-06-phaseA-build-loading.md` to add an agent-instruction
      block at the end of Phase A (after tier persistence), positioned before the Phase B load, that
      reads `production_volume.tier`, `production_volume.raw_value`, and `database_type` via
      `preferences_utils.load_preferences` / `parse_yaml`
    - Compute `already_decided` from the `sqlite_volume_prompt` decision marker (marker exists with
      `decided: true` AND its `tier`/`raw_value` match the current `production_volume`), call
      `volume_utils.should_prompt(tier, db_type, already_decided)`, and on `True` present
      `volume_utils.build_hard_prompt(tier, raw_value)` verbatim and 🛑 STOP for the choice; on
      `False` say nothing new and continue with existing advisory behavior
    - On **Migrate**: record the choice in the decision marker via `preferences_utils.write_preference`,
      then route to the existing `database-migration-guide` (`docs/guides/DATABASE_MIGRATION.md`)
      without inlining migration steps. On **Proceed on SQLite**: record the choice and continue the
      load with no re-prompt for this load. Label the block explicitly as **not** a Mandatory_Gate
      (no ⛔); refer to the migration guide by repo-relative path only (no external URLs)
    - _Requirements: 1.2, 1.3, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_

  - [x] 5.2 Write steering-structure test
    - Assert the Module 6 Phase A block calls `should_prompt` before the Phase B load, presents
      `build_hard_prompt` on the trigger, routes the migrate choice to the existing
      `database-migration-guide`, records the proceed/migrate choice via the decision marker, inlines
      no migration steps, contains no ⛔ marker, and references no external URLs
    - _Requirements: 2.3, 3.1, 3.2, 4.2_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/test_sqlite_volume_hard_prompt.py`, are class-based
  (`TestSqliteVolumeHardPrompt`), and import `scripts/` via the `sys.path` convention.
- Each property task references its property number and the requirement clause it validates for
  traceability; each `st_`-prefixed strategy is defined in the test module.
- Both pure functions are added to the existing `volume_utils.py` (Python 3.11+, stdlib only) and
  reuse the existing tier constants; the migration procedure is never duplicated — the prompt and
  steering only point to `database-migration-guide` (Requirements 2.3, 3.2).
- Fixtures use only synthetic values (no PII, credentials, or connection strings), and steering
  references the migration guide by repo-relative path — no external URLs (security steering).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "4.1", "4.2", "4.3"] },
    { "id": 3, "tasks": ["5.1"] },
    { "id": 4, "tasks": ["5.2"] }
  ]
}
```
