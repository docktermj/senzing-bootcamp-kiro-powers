# Implementation Plan: Steering Corpus Split

## Overview

This plan reorganizes the four oversized always-loaded / early-loaded steering files in the
`senzing-bootcamp` power so that every individually-loadable steering unit is at or under
`budget.split_threshold_tokens` (5,000) and the per-session baseline shrinks — without losing any
Guidance_Content and without breaking the phase-loading or keyword-routing machinery. The work is
mechanical content relocation/trimming plus `steering-index.yaml` registration in the
`split_steering.py` format, followed by a `measure_steering.py` update-mode run and new
property/structure tests.

The four per-file split plans (A: `agent-instructions.md`, B: `onboarding-flow.md`,
C: `module-03-system-verification.md`, D: `module-03-phase2-visualization.md`) are largely
independent and proceed in parallel after a fresh re-measure. The index update depends on all four
file plans; the measure/`--check` run depends on the index update; tests follow the components they
validate; a final CI checkpoint runs last.

Content is Markdown (steering files) and YAML (`steering-index.yaml`); the only new code is the
Python test suite (pytest + Hypothesis, stdlib-only, in `senzing-bootcamp/tests/`).

**Prerequisite (Requirement 6):** Implement after the `steering-index-token-count-sync` spec. If that
spec is not yet merged when work begins, re-measure every in-scope file first (Task 1) and base all
split decisions on the freshly measured `file_metadata.token_count`, never on stored
`phases.*.token_count`.

## Tasks

- [x] 1. Establish an accurate token baseline (prerequisite)
  - [x] 1.1 Re-measure the four in-scope files and record fresh counts
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` (read/update mode) and capture the
      authoritative `file_metadata.token_count` for `agent-instructions.md`, `onboarding-flow.md`,
      `module-03-system-verification.md`, and `module-03-phase2-visualization.md`
    - Confirm each is measured with `calculate_token_count` (`round(len(content)/4)`); base every
      split boundary in Tasks 2–5 on these counts, not on stored `phases.*.token_count`
    - Document that this feature follows the `steering-index-token-count-sync` spec, or that the
      re-measure above replaces stale counts if that spec is not yet complete
    - Files: `senzing-bootcamp/steering/steering-index.yaml` (read; counts captured for planning)
    - _Requirements: 6.1, 6.2, 6.3, 2.3_

- [x] 2. Plan A — reduce the always-loaded `agent-instructions.md` below threshold
  - [x] 2.1 Relocate `### SDK Method Discovery` to `mcp-usage-reference.md` and leave a pointer stub
    - Section-inventory the SDK Method Discovery block first; if `mcp-usage-reference.md` already
      carries the discovery flow, perform a redundancy-trim (Req 3.2), otherwise append the block
      verbatim (Req 3.1)
    - Replace the block in `agent-instructions.md` with a one-line pointer stub naming the trigger
      and route: "SDK method discovery & disambiguation flow: load `mcp-usage-reference.md`
      (trigger: *sdk method discovery*)."
    - Keep `agent-instructions.md` as `inclusion: always`; do NOT move any Requirement-5.3 always-on
      rule (Answer Processing Priority, MCP-First Invariant, Mandatory Gate Precedence, Question Stop
      Protocol). This move alone reduces the file to ~4,634 tokens (< 5,000), so no exemption is
      needed
    - Files: `senzing-bootcamp/steering/agent-instructions.md`,
      `senzing-bootcamp/steering/mcp-usage-reference.md`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 4.6, 3.1, 3.2, 2.5_

  - [x] 2.2 Relocate the `## Track Switching` trigger list to `track-switching.md` and leave a pointer stub
    - Inventory the trigger list; if `track-switching.md` already lists the triggers, redundancy-trim
      (Req 3.2), otherwise append verbatim (Req 3.1)
    - Leave a one-line stub in `agent-instructions.md`: "Track switch triggers (*switch track*,
      *change track*, …): load `track-switching.md`."
    - Files: `senzing-bootcamp/steering/agent-instructions.md`,
      `senzing-bootcamp/steering/track-switching.md`
    - _Requirements: 5.2, 5.4, 4.6, 3.1, 3.2_

  - [x] 2.3 Relocate the `## Context Budget` detail to `agent-context-management.md` and leave a pointer stub
    - Inventory the Context Budget detail; redundancy-trim if `agent-context-management.md` already
      carries warn/critical/unload detail (Req 3.2), otherwise append verbatim (Req 3.1)
    - Leave a one-line stub in `agent-instructions.md`: "Context-budget warn/critical/unload detail:
      load `agent-context-management.md` (trigger: *context budget*)." Keep a one-line phase-cost
      pointer so the `test_split_steering.py::TestUnitAgentInstructionsUpdated` assertions still
      resolve (see Task 9.2)
    - Files: `senzing-bootcamp/steering/agent-instructions.md`,
      `senzing-bootcamp/steering/agent-context-management.md`
    - _Requirements: 5.2, 5.4, 4.6, 3.1, 3.2, 5.5_

- [x] 3. Plan B — split `onboarding-flow.md` phase 1
  - [x] 3.1 Create `onboarding-phase1b-intro-language.md` (steps 3–5b)
    - Extract `## 3. Entity Resolution Introduction`, 4 Programming-Language Selection, 5 Bootcamp
      Intro, 5a Verbosity, and 5b Comprehension from `onboarding-flow.md` into the new file with
      `---\ninclusion: manual\n---` frontmatter; place at
      `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`
    - Move the existing "After Step 5b, load `onboarding-phase2-track-setup.md`" load instruction so
      it travels with Step 5b (preserves the documented Routing_Reference, Req 4.4)
    - Keep every `👉`/`🛑 STOP` pair (Steps 4, 5a, 5b) intact within this unit; the boundary at `## 3`
      bisects no pair (Req 3.5). Target ~2.1k (≤ 5,000)
    - Files: `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md` (new)
    - _Requirements: 1.1, 3.1, 3.3, 3.5, 4.1, 4.4_

  - [x] 3.2 Trim `onboarding-flow.md` root to steps 0–2 and add the phase manifest + continue pointer
    - Remove the steps 3–5b content (now in phase 1b) from the root; retain Preamble, 0 Setup,
      0b MCP Health, 0c Version, 1 Directory, 1b Team, and 2/2a–2d Prerequisites
    - Add a `## Phase Sub-Files` manifest line for `onboarding-phase1b-intro-language.md` and a
      one-line "continue to phase 1b" instruction at the end of Step 2d; leave `onboard`/`start`
      keyword routes pointing at the root unchanged. Target ~3.4k (≤ 5,000)
    - Files: `senzing-bootcamp/steering/onboarding-flow.md`
    - _Requirements: 2.1, 3.1, 4.1, 4.2, 4.4, 4.6_

- [x] 4. Plan C — split `module-03-system-verification.md` by step range
  - [x] 4.1 Create `module-03-phase1-verification.md` (steps 1–8)
    - Extract `## Phase 1` + Steps 1–8 into the new file with `inclusion: manual` frontmatter; end
      with a one-line prose pointer "Step 9 is mandatory — load `module-03-phase2-visualization.md`"
      (do NOT duplicate the Step 9 `⛔` gate as a numbered step here)
    - Preserve every numbered-step↔`**Checkpoint:**` correspondence and `👉`/`STOP` pair within the
      unit (Req 3.5). Place at `senzing-bootcamp/steering/module-03-phase1-verification.md`. Target
      ~2.6k, `step_range [1, 8]`
    - Files: `senzing-bootcamp/steering/module-03-phase1-verification.md` (new)
    - _Requirements: 1.1, 2.1, 3.1, 3.3, 3.4, 3.5, 4.1, 4.2_

  - [x] 4.2 Create `module-03-phase3-report-close.md` (steps 10–12)
    - Extract the PRE-ADVANCEMENT VERIFICATION self-check (top of file) plus `## Phase 2` Steps 10
      (Report), 11 (Cleanup), 12 (Close) into the new file with `inclusion: manual` frontmatter;
      place at `senzing-bootcamp/steering/module-03-phase3-report-close.md`
    - Preserve step↔checkpoint correspondence and behavioral markers across the move (Req 3.3, 3.5).
      Target ~1.9k, `step_range [10, 12]`
    - Files: `senzing-bootcamp/steering/module-03-phase3-report-close.md` (new)
    - _Requirements: 1.1, 2.1, 3.1, 3.3, 3.5, 4.1, 4.2_

  - [x] 4.3 Trim `module-03-system-verification.md` to the root unit and fix the step-range overlap
    - Reduce the root to: Title, banner instruction, Prerequisites, Before/After, TruthSet note,
      Opt-Out Gate, a `## Phase Sub-Files` manifest, and the shared Error Handling / Success Criteria
      / Agent Rules tails; remove Steps 1–12 and the Step 9 stub (its unique `⛔` gate language is
      relocated into the visualization file in Task 5.2 — not duplicated here)
    - Correct the Phase_Map so coverage is disjoint and total: `[1,8] ∪ [9,9] ∪ [10,12]` = steps
      1–12 with no overlap (removes the old `[9,12]` overlap); keep the
      `module-03-phase2-visualization.md` filename unchanged so generated `hook-registry-modules.md`
      references stay valid (no Generated_File edit). Retain Before/After + Prerequisites so the
      module-root structural properties still pass. Target ~1.5k
    - Files: `senzing-bootcamp/steering/module-03-system-verification.md`
    - _Requirements: 2.1, 3.1, 3.2, 3.4, 4.2, 8.4, 1.3, 9.3_

- [x] 5. Plan D — trim `module-03-phase2-visualization.md` below threshold
  - [x] 5.1 Create the manual companion `module-03-visualization-api-reference.md`
    - Relocate the full `/api/stats`, `/api/graph`, `/api/merges`, `/api/search` JSON response
      schemas and the `search_builder.py` enrichment specification (extraction functions,
      graceful-degradation, single-record/error response examples) into the new file with
      `inclusion: manual` frontmatter; place at
      `senzing-bootcamp/steering/module-03-visualization-api-reference.md`. Target ~1.7k (≤ 5,000)
    - Files: `senzing-bootcamp/steering/module-03-visualization-api-reference.md` (new)
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 4.3, 4.6_

  - [x] 5.2 Trim `module-03-phase2-visualization.md` and wire the companion + relocated gate
    - Keep Purpose, prerequisites, generation lessons, the mandatory gate, 9.1 generation approach +
      required-files table, compact endpoint summaries, the 9.3 page-component spec, and 9.4
      start/verify + guided tour including the `👉 Take your time exploring…` question with its
      `🛑 STOP` and the `**Checkpoint:**` block (Req 3.3, 3.5)
    - Add a `#[[file:]]` reference to `module-03-visualization-api-reference.md` for the relocated
      schemas; incorporate the unique Step 9 `⛔` gate language relocated from the verification root
      (Task 4.3) as the existing "Phase 2 Execution Is Mandatory" gate (relocate, do not duplicate).
      Keep the filename unchanged (generated hook-registry references stay valid; `sync_hook_registry.py`
      untouched). Target ~4.0k (≤ 5,000)
    - Files: `senzing-bootcamp/steering/module-03-phase2-visualization.md`
    - _Requirements: 2.1, 3.1, 3.2, 3.3, 3.5, 4.3, 4.4, 4.6, 1.3, 9.3_

- [x] 6. Checkpoint - content relocation complete
  - Confirm every relocated Guidance_Content block has exactly one destination and the union balances
    against the pre-split inventory (no drop, no orphan); confirm all `👉`/`⛔`/`STOP`/`**Checkpoint:**`
    markers are preserved. Ensure all tests pass, ask the user if questions arise.

- [x] 7. Register the new units in `steering-index.yaml` and re-measure
  - [x] 7.1 Apply the `steering-index.yaml` entries in the `split_steering.py` format
    - Repoint `modules.3.phases` to `phase1-verification` (`module-03-phase1-verification.md`,
      `[1,8]`), `phase2-visualization` (`module-03-phase2-visualization.md`, `[9,9]`), and
      `phase3-report-close` (`module-03-phase3-report-close.md`, `[10,12]`); add the `onboarding`
      `phase1b-intro-language` entry (`onboarding-phase1b-intro-language.md`, `[3,"5b"]`)
    - Add `keywords` routes `visualization api` and `api reference` →
      `module-03-visualization-api-reference.md`; add `file_metadata` keys for every new file
      (`module-03-phase1-verification.md`, `module-03-phase3-report-close.md`,
      `module-03-visualization-api-reference.md`, `onboarding-phase1b-intro-language.md`). Leave the
      four threshold keys (`warn_threshold_pct`, `critical_threshold_pct`, `split_threshold_tokens`,
      `reference_window`) untouched and do not change step numbering/`step_range` semantics
    - Files: `senzing-bootcamp/steering/steering-index.yaml`
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 9.1, 9.4_

  - [x] 7.2 Run `measure_steering.py` update mode, then `--check`
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` (update mode) to refresh
      `file_metadata` and `budget.total_tokens` for the new file set, then
      `python3 senzing-bootcamp/scripts/measure_steering.py --check` and confirm it exits 0
    - Verify the four threshold keys are preserved verbatim and that the recomputed
      `budget.total_tokens` reflects the smaller always/early-loaded footprint
    - Files: `senzing-bootcamp/steering/steering-index.yaml`
    - _Requirements: 4.7, 2.3, 7.1, 9.1_

- [x] 8. Add the property-based test suite `test_steering_corpus_split.py`
  - [x] 8.1 Write Property 1 — threshold compliance
    - **Property 1: Threshold compliance**
    - **Validates: Requirements 2.1, 2.2, 2.3, 8.1, 8.2, 5.5**
    - Create `senzing-bootcamp/tests/test_steering_corpus_split.py`; import `calculate_token_count`
      from `measure_steering` via the `sys.path` pattern and reuse `parse_steering_index`. Define a
      module-level `EXEMPTIONS` `frozenset` (empty in v1). `TestPropertyThresholdCompliance` with
      `st_loadable_unit()` plus a concrete pass over the real index: assert every Loadable_Unit
      (`phases.*.file`, flat `file_metadata`, keyword/language/deployment targets) is
      ≤ `split_threshold_tokens` OR is in `EXEMPTIONS`; for each exemption assert the named file
      exists in the index
    - Conventions: `from __future__ import annotations`, class-based, `st_`-prefixed strategies,
      `@settings(max_examples=20)`, type hints on all signatures, stdlib + pytest + Hypothesis only
    - Files: `senzing-bootcamp/tests/test_steering_corpus_split.py` (new)
    - _Requirements: 2.1, 2.2, 2.3, 8.1, 8.2, 5.5, 8.5_

  - [x] 8.2 Write Property 2 — routability / no orphan
    - **Property 2: Routability / no orphan**
    - **Validates: Requirements 4.3, 4.5, 4.6, 8.3, 8.6**
    - Add `TestPropertyRoutability` with `st_index_reference()` drawing from phase-map/keyword/
      language/deployment targets plus a concrete pass over the real index; assert each referenced
      filename resolves to a file that exists on disk
    - Files: `senzing-bootcamp/tests/test_steering_corpus_split.py`
    - _Requirements: 4.3, 4.5, 4.6, 8.3, 8.6, 8.5_

  - [x] 8.3 Write Property 3 — step coverage is total and unambiguous
    - **Property 3: Step coverage is total and unambiguous**
    - **Validates: Requirements 4.2, 8.4**
    - Add `TestPropertyStepCoverage`: for each module with a Phase_Map, build the union of integer
      steps from all `step_range` values (reduce string sub-steps like `"5b"` to their parent via the
      `parse_parent_step` rule) and assert each maps to exactly one phase sub-file via `step_to_phase`
    - Files: `senzing-bootcamp/tests/test_steering_corpus_split.py`
    - _Requirements: 4.2, 8.4, 8.5_

  - [x] 8.4 Write Property 4 — content preservation and always-on-core retention
    - **Property 4: Content preservation and always-on-core retention**
    - **Validates: Requirements 3.1, 3.2, 3.3, 5.1, 5.3**
    - Add `TestPropertyContentPreservation`: `st_split_assignment()` generates a synthetic file with
      marked guidance blocks + markers, partitions it at a random heading boundary, and asserts the
      union preserves all blocks and the count of each marker (`👉`, `⛔`, `STOP`/`WAIT`,
      `**Checkpoint:**`); add a concrete before/after inventory check for each real in-scope file and
      assert `agent-instructions.md` still has `inclusion: always` and contains the Requirement-5.3
      rule anchors (Answer Processing Priority, MCP-First Invariant, Mandatory Gate Precedence,
      Question Stop Protocol)
    - Files: `senzing-bootcamp/tests/test_steering_corpus_split.py`
    - _Requirements: 3.1, 3.2, 3.3, 5.1, 5.3, 8.5_

  - [x] 8.5 Write the no-external-URL / no-MCP-URL scan
    - Add a lightweight assertion that scans every touched steering file (the four in-scope files and
      the four new units) and fails if any contains an `http`/`https` link or the MCP server host,
      enforcing the security rules (this is a guard assertion, not one of the four design properties)
    - Files: `senzing-bootcamp/tests/test_steering_corpus_split.py`
    - _Requirements: 7.6, 8.5_

- [x] 9. Update existing test suites for the new structure
  - [x] 9.1 Update `test_steering_structure_properties.py` for the Module 3 phases
    - Update the Module-3 expectations and `test_phased_entry_resolves_to_root_plus_phases` to the
      new phase filenames (`module-03-phase1-verification.md`, `module-03-phase2-visualization.md`,
      `module-03-phase3-report-close.md`); verify the Module 3 root still satisfies Before/After +
      Prerequisites and the new sub-files satisfy step-checkpoint, single-question, and frontmatter
      rules, preserving each test's original intent
    - Files: `senzing-bootcamp/tests/test_steering_structure_properties.py`
    - _Requirements: 7.3, 7.4, 3.4_

  - [x] 9.2 Update `test_split_steering.py::TestUnitAgentInstructionsUpdated`
    - Update the assertions that `agent-instructions.md` documents phase loading and "Context
      Budget … phases" so they resolve against the retained one-line phase-cost pointer (or repoint
      them at `agent-context-management.md`) after the Context Budget trim in Task 2.3, preserving
      original intent; modules 5/6 integration tests are unaffected
    - Files: `senzing-bootcamp/tests/test_split_steering.py`
    - _Requirements: 7.3, 7.4, 5.4_

  - [x] 9.3 Update `test_token_budget_optimization.py` for the re-measured totals
    - Confirm `test_actual_steering_index_total_tokens_equals_sum` and
      `test_actual_steering_files_token_counts_within_tolerance` pass after the Task 7.2 update-mode
      run; adjust any hard-coded expected totals to the freshly measured values
    - Files: `senzing-bootcamp/tests/test_token_budget_optimization.py`
    - _Requirements: 7.3, 4.7_

  - [x] 9.4 Update `test_steering_optimization_unit.py` / `test_steering_optimization_properties.py` baselines
    - If either suite hard-codes the old `agent-instructions.md` size, update the expected baseline to
      the new (smaller) measured count; otherwise confirm they still pass unchanged
    - Files: `senzing-bootcamp/tests/test_steering_optimization_unit.py`,
      `senzing-bootcamp/tests/test_steering_optimization_properties.py`
    - _Requirements: 7.3, 7.4_

- [x] 10. Final checkpoint - run the full CI suite and confirm invariants
  - Run, in CI order: `python3 senzing-bootcamp/scripts/measure_steering.py --check`,
    `python3 senzing-bootcamp/scripts/validate_power.py`,
    `python3 senzing-bootcamp/scripts/validate_commonmark.py`,
    `python3 senzing-bootcamp/scripts/validate_dependencies.py`,
    `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`, then
    `pytest senzing-bootcamp/tests/` (full steering suite incl. the new file)
  - Confirm no Guidance_Content was lost (inventory balances), `agent-instructions.md` is still
    `inclusion: always` and < 5,000 tokens, and the Module 3 step map `[1,8]/[9,9]/[10,12]` is
    disjoint and total. Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6, 2.4, 2.5, 8.4, 3.1, 5.1_

## Notes

- Tasks marked with `*` are test sub-tasks (per repo convention); Task 8 implements the new tests
  mandated by Requirement 8 and is strongly recommended rather than skipped.
- Each leaf task references specific (granular) requirement clauses for traceability; each new test
  sub-task names the design Property number it implements.
- The four per-file plans (Tasks 2–5) are independent and can proceed in parallel after the
  re-measure (Task 1); the index update (Task 7) depends on all four; measure/`--check` depends on
  the index update; tests follow the components they validate.
- Sub-tasks that write the same file are sequenced into different waves to avoid conflicts:
  `agent-instructions.md` (2.1→2.2→2.3), `steering-index.yaml` (7.1→7.2), and the new test file
  (8.1→8.5).
- No exemption is required in v1 — every in-scope unit reduces ≤ 5,000 by relocation alone — so the
  threshold test ships with an empty enumerated `EXEMPTIONS` frozenset.
- Generated files (`hook-registry*.md`) and `sync_hook_registry.py` are out of scope and untouched;
  the `module-03-phase2-visualization.md` filename is intentionally preserved so generated references
  stay valid and `--verify` stays green.
- All scripts/tests remain stdlib-only (pytest + Hypothesis for tests); no steering file introduces an
  external clickable link or an MCP server host outside `mcp.json`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "4.1", "4.2", "5.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "4.3", "5.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["7.1"] },
    { "id": 5, "tasks": ["7.2"] },
    { "id": 6, "tasks": ["8.1", "9.1", "9.2", "9.3", "9.4"] },
    { "id": 7, "tasks": ["8.2"] },
    { "id": 8, "tasks": ["8.3"] },
    { "id": 9, "tasks": ["8.4"] },
    { "id": 10, "tasks": ["8.5"] }
  ]
}
```
