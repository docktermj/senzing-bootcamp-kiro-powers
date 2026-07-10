# Implementation Plan: Module 4 SQLite Load-Time Warning

## Overview

Convert the design into incremental Python coding steps (stdlib only, matching the existing
`senzing-bootcamp/scripts/` pattern). The plan builds bottom-up so every pure helper and its
property test land before the code that wires them together, and no code is left orphaned:

1. Pure helpers in `scripts/volume_utils.py` (trigger predicate + warning-text builder) — testable
   in isolation, alongside the existing `should_prompt` / `build_hard_prompt` / `build_license_framing`.
2. The new orchestration module `scripts/load_time_warning.py` — load identity, sampling helpers,
   and decision-marker read/write + Module 6 scoping — reusing `record_count_backfill`,
   `data_sources`, `preferences_utils`, and `volume_utils` with no parallel logic.
3. The additive `sqlite_volume_prompt` schema extension in `scripts/preferences_utils.py`.
4. Steering wiring in `steering/module-04-data-collection.md` and
   `steering/module-06-phaseA-build-loading.md`.
5. The CLI entry point that ties the module together, plus integration/structural tests.

Tests live in `senzing-bootcamp/tests/`, follow the project pattern (pytest + Hypothesis,
class-based, `sys.path` import of `scripts/`, profile-driven example counts with no inline
`@settings(max_examples=...)` override), and use synthetic-only fixtures (no PII, credentials, or
real data). Everything under `senzing-bootcamp/` ships to users — no dev-only files.

## Tasks

- [x] 1. Add the pure trigger predicate to `scripts/volume_utils.py`
  - [x] 1.1 Implement `LOAD_WARNING_THRESHOLD = 75_000` and `should_warn_load_time(collected_total, db_type)`
    - Pure, stdlib-only, no I/O, never raises; takes no tier and no license argument
    - Normalize `db_type` case-insensitively and whitespace-trimmed; reject `bool` totals
    - Return `True` iff `collected_total` is a real `int` strictly greater than the threshold AND normalized `db_type == "sqlite"`; `False` at/below threshold, non-SQLite, or indeterminate (`None`/empty/unrecognized)
    - Place alongside the existing `should_prompt` / `build_hard_prompt` helpers
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.4, 2.5, 7.1, 7.2_

  - [x] 1.2 Write property test for the trigger predicate
    - **Property 1: Trigger fires exactly on (total > threshold) AND SQLite**
    - Use `st_total()` (ints incl. 75,000 boundary/negatives, bools, `None`) × `st_db_type()` (mixed-case/whitespace `sqlite`, `postgresql`, `""`, `None`, junk); assert independence from tier/license
    - File: `tests/test_load_time_warning.py`, class `TestLoadTimeWarningTrigger`
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.5, 7.1, 7.2**

  - [x] 1.3 Write property test for the collected-total lower bound feeding the trigger
    - **Property 2: Collected total sums only resolved counts and is a sound lower bound**
    - Use `st_registry()` mixing metadata counts, missing counts in countable formats (csv/jsonl), and uncountable formats; assert `compute_collected_count(registry, row_count=True).known_total` sums only resolved counts, lists unresolved sources in `unknown_sources` (never zero), and that a `known_total` above threshold drives `should_warn_load_time(known_total, "sqlite") == True` even with unknowns remaining
    - Reuse `record_count_backfill.compute_collected_count`; File: `tests/test_load_time_warning.py`
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [x] 1.4 Write boundary/indeterminate example tests for the trigger truth table
    - Assert `should_warn_load_time`: `(75_001, "sqlite")→True`, `(75_000, "sqlite")→False`, `(100_000, "postgresql")→False`, `(None, "sqlite")→False`, `(100_000, None)→False`
    - File: `tests/test_load_time_warning.py`, class `TestLoadTimeWarningTrigger`
    - _Requirements: 1.2, 1.3, 1.4, 8.1_

- [x] 2. Add the pure warning-text builder to `scripts/volume_utils.py`
  - [x] 2.1 Implement the `TimingGuidance` dataclass and `build_load_time_warning(collected_total, timing, *, migration_guide_path)`
    - Frozen dataclass with four `str | None` fields (`expected_throughput`, `throughput_degradation`, `expected_load_duration`, `redo_phase_duration`)
    - Always name `collected_total` and the "expected to be slow" framing; always state throughput degrades, redo phase needs additional time, and slow-but-progressing (not stalled)
    - Include each figure only when present; for each `None` figure state it is "currently unavailable from the MCP server" with no substituted number
    - Always offer load-all / sample / switch-database, naming the migration guide by repo-relative path; never emit the Mandatory_Gate marker (⛔); refer to the MCP server by name only (no URLs)
    - Mirror the existing `build_license_framing` omission style
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.5_

  - [x] 2.2 Write property test for the warning-text builder
    - **Property 3: Warning names the total, states all fixed concerns, omits only unavailable figures, and offers all options without gating**
    - Use non-negative totals × `st_timing()` (each of the four figures independently a string or `None`); assert presence/omission per figure, the three fixed qualitative statements, all three options naming the migration guide, and no ⛔
    - File: `tests/test_load_time_warning.py`, class `TestLoadTimeWarningContent`
    - **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.5**

  - [x] 2.3 Write MCP-unavailable example test
    - A `TimingGuidance` with all four figures `None` yields a warning that states each value is currently unavailable and contains no fabricated numbers
    - File: `tests/test_load_time_warning.py`, class `TestLoadTimeWarningContent`
    - _Requirements: 3.4, 8.2_

- [x] 3. Checkpoint - Ensure all `volume_utils` helper tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Scaffold `scripts/load_time_warning.py` and the load-identity helper
  - [x] 4.1 Create the module scaffold and implement `compute_load_identity(registry)`
    - Project script pattern: shebang, `from __future__ import annotations`, stdlib only, `argparse` + `main(argv=None)` stub returning exit 0/1, and `sys.path` insertion importing `volume_utils`, `preferences_utils`, `record_count_backfill`, `data_sources`
    - `compute_load_identity`: build an order-independent signature from each source's `(data_source, record_count-or-"unknown")` pair sorted by `data_source`, hash with `hashlib.sha256`, return `"sha256:<hexdigest>"`; names/counts only (no row content/PII); pure, never raises
    - _Requirements: 6.4, 7.4_

- [x] 5. Implement the sampling helpers in `scripts/load_time_warning.py`
  - [x] 5.1 Implement `validate_sample_target(target, collected_total)` and `SampleTargetValidation`
    - Valid iff `target` is a real `int` (not `bool`) with `target > 0`, `collected_total` a real `int`, and `target < collected_total`; otherwise `valid=False` with a non-empty, PII-free reason; never raises
    - _Requirements: 5.5, 5.6_

  - [x] 5.2 Write property test for sampling-target validation
    - **Property 4: Sampling target is valid exactly when it is a positive integer below the total**
    - Use `st_target()` (ints, bools, `None`) × totals (ints, `None`)
    - File: `tests/test_load_time_sampling.py`, class `TestSampling`
    - **Validates: Requirements 5.5, 5.6**

  - [x] 5.3 Implement `select_first_n(total, target)` and `select_random_n(total, target, seed)`
    - `select_first_n` returns `range(min(target, total))` as a list; `select_random_n` uses `random.Random(seed).sample` for deterministic, distinct in-range indices; both pure, no global RNG state
    - _Requirements: 5.2, 5.4_

  - [x] 5.4 Write property test for count-based selection
    - **Property 5: Count-based selection returns exactly target distinct in-range indices**
    - For `total > 0`, `0 < target < total`, any `seed`: both selectors return exactly `target` distinct indices in `[0, total)`; `select_random_n` deterministic for fixed seed
    - File: `tests/test_load_time_sampling.py`, class `TestSampling`
    - **Validates: Requirements 5.2, 5.4**

  - [x] 5.5 Implement `select_er_demonstrating(clusters, singletons, target, seed)`
    - Add whole match clusters until the next whole cluster would exceed `target`, then fill from singletons; a cluster is always included in full or excluded in full; deterministic given `seed`; pure, never raises
    - _Requirements: 5.7_

  - [x] 5.6 Write property test for ER-demonstrating selection
    - **Property 6: ER-demonstrating selection never splits a match cluster**
    - For any `clusters`, `singletons`, `target`, `seed`: for every cluster the result contains all members or none — never a strict subset
    - File: `tests/test_load_time_sampling.py`, class `TestSampling`
    - **Validates: Requirements 5.7**

  - [x] 5.7 Implement `write_sample`, `write_sample_manifest`, `SampleWriteResult`, and `VALID_SAMPLING_STRATEGIES`
    - Strategy constants (`first_n`, `random_n`, `er_demonstrating`, `described`) and their tuple
    - `write_sample`: stream the source file (csv keeps header + selected rows; jsonl keeps selected lines) writing only kept records under `data/samples/`; return `SampleWriteResult(success, reason)` (no raise) — unreadable/unwritable/non-countable → `success=False`
    - `write_sample_manifest`: write a small sidecar under `data/samples/` recording strategy + target + kept count (counts/strategy only, no row content)
    - _Requirements: 5.4, 7.5_

  - [x] 5.8 Write sample-I/O and sampling-vocabulary example tests
    - `write_sample` keeps a CSV header + selected rows / selected JSONL lines in `tmp_path`, and `write_sample_manifest` records strategy + target; unreadable source / uncountable format returns `success=False` without raising; assert `VALID_SAMPLING_STRATEGIES` includes first-N, random-N, ER-demonstrating, and described
    - File: `tests/test_load_time_sampling.py`, class `TestSampling`
    - _Requirements: 5.2, 5.3, 5.4, 7.5_

- [x] 6. Checkpoint - Ensure all sampling helper tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Extend the shared `sqlite_volume_prompt` schema in `scripts/preferences_utils.py`
  - [x] 7.1 Additively extend the marker schema for the Module 4 shape
    - Add `"source"` and `"load_identity"` to `SQLITE_VOLUME_PROMPT_KEYS`; extend `VALID_SQLITE_VOLUME_CHOICE` to `("proceed", "migrate", "sample", "switch_db")`; add `"source": str` and `"load_identity": str` to `_SQLITE_VOLUME_PROMPT_TYPES`; add a `source` enum `("module4_load_time", "module6_volume")`; keep `tier`/`raw_value` optional so both the Module 4 and Module 6 marker shapes validate
    - _Requirements: 6.2_

  - [x] 7.2 Write schema unit tests for both marker shapes
    - `validate_preferences_schema` accepts the Module 4 shape (`source: module4_load_time`, `choice ∈ {proceed, sample, switch_db}`, `load_identity`) and the unchanged Module 6 shape (`source: module6_volume`, `tier`, `raw_value`, `choice ∈ {proceed, migrate}`); rejects unknown sub-keys and out-of-enum values
    - File: `tests/test_load_time_decision.py`, class `TestDecisionMarker`
    - _Requirements: 6.2_

- [x] 8. Implement decision-marker read/write and Module 6 scoping in `scripts/load_time_warning.py`
  - [x] 8.1 Implement `LOAD_MARKER_SOURCE`, `write_load_decision(choice, load_identity, preferences_path)`, and `read_load_decision(preferences_path)`
    - `write_load_decision` records `{decided: true, choice, source: LOAD_MARKER_SOURCE, load_identity}` under the shared `sqlite_volume_prompt` key via `preferences_utils.write_preference`; returns the writer's `WriteResult` (never raises)
    - `read_load_decision` reuses `preferences_utils.load_preferences` / `parse_yaml`, returns the marker dict or `None` when absent/unreadable; never raises
    - _Requirements: 6.1, 6.2_

  - [x] 8.2 Write property test for the decision-marker round-trip
    - **Property 7: Decision-marker round-trips choice and load identity through the shared marker**
    - For `choice ∈ {proceed, sample, switch_db}` × any `load_identity`: write then read yields a `sqlite_volume_prompt` marker with `decided=True`, matching `choice`, `source == "module4_load_time"`, and matching `load_identity` (use a `tmp_path` preferences file)
    - File: `tests/test_load_time_decision.py`, class `TestDecisionMarker`
    - **Validates: Requirements 6.1, 6.2**

  - [x] 8.3 Implement `module4_decision_applies(marker, current_identity, db_type)`
    - Pure; returns `True` iff `marker` is a decided Module 4 marker (`source == LOAD_MARKER_SOURCE`, `decided is True`) whose `load_identity == current_identity` AND normalized `db_type == "sqlite"`; a different identity or non-Module-4/undecided marker yields `False`; never raises, no I/O
    - _Requirements: 6.3, 6.4_

  - [x] 8.4 Write property test for identity determinism and Module 6 scoping
    - **Property 8: Module 6 honors a Module 4 decision only for the same load on SQLite**
    - For two `st_registry()` values: `compute_load_identity` is deterministic and order-independent, differing source/count sets differ; for a decided Module 4 marker with `load_identity = id_a`, `module4_decision_applies` returns `True` iff `current_identity == id_a` and normalized `db_type == "sqlite"`, `False` otherwise
    - File: `tests/test_load_time_decision.py`, class `TestDecisionMarker`
    - **Validates: Requirements 6.3, 6.4**

- [x] 9. Checkpoint - Ensure all decision-marker tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Wire the Module 4 steering block
  - [x] 10.1 Add the "SQLite Load-Time Warning (collection-time heads-up)" block to `steering/module-04-data-collection.md`
    - Place after Step 8a (record-count back-fill) and before the Step 9 transition to Module 5
    - Read `config/data_sources.yaml` (via the `data_sources` reader chain) and `database_type` from `config/bootcamp_preferences.yaml`; compute the total via `record_count_backfill.compute_collected_count(registry, row_count=True).known_total` (uncomputable → `None`); call `volume_utils.should_warn_load_time`
    - On `True`: consult the Senzing MCP server at request time for the four `TimingGuidance` figures (unreturned/errored figures stay `None`), present `build_load_time_warning(...)`, then 🛑 STOP for the choice
    - Load-all → obtain explicit time-cost confirmation before continuing; Sample → ask the `Sampling_Strategy` sub-choice (offer first-N/random-N/ER-demonstrating; accept a described strategy), `validate_sample_target` + re-ask on invalid, create the sample with the chosen selector, `write_sample` under `data/samples/`, `write_sample_manifest`; Switch DB → route to the `database-migration-guide` without inlining steps
    - Record the decision via `write_load_decision(choice, compute_load_identity(registry))`; label the block NOT a Mandatory_Gate (no ⛔), present the concern as distinct from the license-capacity sampling framing, refer to the MCP server by name only and the migration guide by repo-relative path; every step non-blocking
    - Update `steering/steering-index.yaml` token budget if the file's count changed
    - _Requirements: 1.1, 3.2, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 6.1, 7.3, 7.5_

- [x] 11. Wire the Module 6 honor-decision change
  - [x] 11.1 Extend the `already_decided` computation in `steering/module-06-phaseA-build-loading.md`
    - Additively OR in `module4_decision_applies(marker, compute_load_identity(registry), db_type)` alongside the existing Module 6 tier/raw_value match, so a Module 4 decision for the current load on SQLite suppresses the re-prompt while a differing identity falls back to the existing Module 6 condition
    - Update `steering/steering-index.yaml` token budget if the file's count changed
    - _Requirements: 6.3, 6.4_

- [x] 12. Integrate the CLI entry point and add structural/integration tests
  - [x] 12.1 Complete `load_time_warning.main(argv=None)` to tie the helpers into a runnable diagnostic
    - Read the registry + preferences, compute the collected total via `record_count_backfill`, evaluate `should_warn_load_time`, and print either the built warning text (via `build_load_time_warning`) or a "no warning — continue" report plus the current decision-marker status; exit 0 normally, non-zero only on argparse misuse; every path non-blocking (indeterminate input → continue)
    - _Requirements: 7.4, 7.5_

  - [x] 12.2 Write Module 4 steering-structure tests
    - Assert the block appears after Step 8a and before the Step 9 transition; asks the sampling sub-choice before creating a sample; obtains an explicit confirmation on the load-all path; presents the time/performance concern distinctly from the license-capacity framing while still listing sampling as one option; and that `load_time_warning.py` imports `volume_utils`, `preferences_utils`, `record_count_backfill`, `data_sources` (reuse, no parallel record-count/tier logic)
    - File: `tests/test_load_time_steering.py`, class `TestSteeringStructure`
    - _Requirements: 4.4, 5.1, 5.3, 7.3, 7.4_

  - [x] 12.3 Write Module 6 steering-structure test
    - Assert the Module 6 Phase A block ORs `module4_decision_applies` into its `already_decided` computation
    - File: `tests/test_load_time_steering.py`, class `TestSteeringStructure`
    - _Requirements: 6.3_

  - [x] 12.4 Write non-blocking fallback example test
    - An uncomputable/unreadable registry drives the collected total to `None`, so the trigger is `False` and the diagnostic reports "continue" without raising
    - File: `tests/test_load_time_steering.py`, class `TestNonBlockingFallback`
    - _Requirements: 7.5, 8.3_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core
  implementation sub-tasks are never marked optional.
- Each task references specific requirements (and, for property tests, the exact design property)
  for traceability.
- Property tests validate the eight universal correctness properties; unit/example and
  structural tests cover boundary cells, MCP omission, sample I/O, marker mechanism, steering
  structure, and the non-blocking fallback.
- All new pure helpers are stdlib-only and reuse `record_count_backfill`, `data_sources`,
  `preferences_utils`, and `volume_utils` — no parallel logic.
- Tests use synthetic-only fixtures and the project's profile-driven Hypothesis example counts
  (no inline `@settings(max_examples=...)`), and live in `senzing-bootcamp/tests/`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "4.1", "7.1"] },
    { "id": 1, "tasks": ["2.1", "5.1", "1.2", "7.2"] },
    { "id": 2, "tasks": ["5.3", "1.3", "5.2"] },
    { "id": 3, "tasks": ["5.5", "1.4", "5.4"] },
    { "id": 4, "tasks": ["5.7", "2.2", "5.6"] },
    { "id": 5, "tasks": ["8.1", "2.3", "5.8"] },
    { "id": 6, "tasks": ["8.3", "8.2"] },
    { "id": 7, "tasks": ["12.1", "8.4"] },
    { "id": 8, "tasks": ["10.1", "11.1", "12.4"] },
    { "id": 9, "tasks": ["12.2"] },
    { "id": 10, "tasks": ["12.3"] }
  ]
}
```
