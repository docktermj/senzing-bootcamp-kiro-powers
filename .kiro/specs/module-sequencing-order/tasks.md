# Implementation Plan

## Overview

This bugfix establishes **numeric-order-by-default sequencing** for any selected track and guarantees
**Module 3 (System Verification) runs after Module 2 and before any data loading (Module 6)** unless
the bootcamper explicitly requests to skip verification. The running order is produced by the agent
following the sequencing steering plus the machine-readable dependency graph in
`config/module-dependencies.yaml` (there is no standalone sequencer program).

The fix uses two reinforcing mechanisms plus documentation reconciliation across five surfaces:

1. **Dependency graph** — promote Module 3 from a *soft* to a *hard* prerequisite of Module 4
   (`4.requires = [1, 3]`, drop `4.soft_requires`) so no dependency-respecting order can place 4/5/6
   before 3 or silently omit 3. Module 3 stays explicitly skippable via its module-level `skip_if`.
2. **Steering** — add a Numeric-Order-by-Default Sequencing rule to the always-included
   `module-transitions.md`.
3. **Documentation/consistency** — reconcile the `module-prerequisites.md` table cell + "Soft
   Prerequisite Behavior" section, the `module-artifacts.yaml` Module 4 comment, and the one pinning
   unit test in `test_module3_default_on_unit.py`.

`validate_dependencies.py` cross-references `sorted(requires + soft_requires)` against the
prerequisites table; moving Module 3 from `soft_requires` to `requires` keeps that union at `[1, 3]`,
so the cross-reference stays green with no script change.

Two new property-based test files (pytest + Hypothesis; stdlib + Hypothesis only, loading the graph
with PyYAML exactly as `validate_dependencies.py` does, per `python-conventions.md`) validate the
fix: an exploration suite (Property 1 — Fix Checking) authored to FAIL on the unfixed config, and a
preservation suite (Property 2 — Preservation Checking) authored to PASS on the unfixed config. A
shared domain model mirrors `isBugCondition` from `bugfix.md`:

```python
@dataclass
class SeqInput:
    track: list[int]            # selected track modules, e.g. [1,2,3,4,5,6,7]
    order: list[int]            # produced running order
    requested_skip: set[int]    # modules the bootcamper explicitly skipped

def is_bug_condition(x: SeqInput) -> bool:
    not_numeric = any(a > b for a, b in zip(x.order, x.order[1:]))
    m3_skipped = (3 in x.track) and (3 not in x.order) and (3 not in x.requested_skip)
    pos = {m: i for i, m in enumerate(x.order)}
    m3_after_load = (3 in pos) and (6 in pos) and pos[3] > pos[6]
    return not_numeric or m3_skipped or m3_after_load
```

A reference sequencer `numeric_order_with_deps(track, graph, requested_skip)` returns the ascending
order subject to hard `requires` edges (topological tiebreak preferring the smallest eligible module
number) — the executable model of F'.

## Tasks

- [x] 1. Write bug condition exploration test (Fix Checking)
  - **Property 1: Fix Checking** - Numeric-Order-by-Default Sequencing
  - **CRITICAL**: This test MUST FAIL on unfixed config (Module 4 soft-requires Module 3; no numeric-order rule) — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples demonstrating that a dependency-only order can interleave/skip Module 3 (e.g., `1 → 4 → 5 → 2 → 6 → 7`) under the current config
  - **Scoped PBT Approach**: For the deterministic config/steering assertions, scope to the concrete files; use Hypothesis to enumerate the bug-condition input space (orders satisfying `is_bug_condition`)
  - Create `senzing-bootcamp/tests/test_module_sequencing_order_exploration.py`
  - Per `python-conventions.md`: `from __future__ import annotations`, class-based organization, type hints (`X | None`, `list[str]`), `st_`-prefixed strategies, `@settings(max_examples=20)`, stdlib + Hypothesis (load the graph with PyYAML as `validate_dependencies.py` does)
  - Define the `SeqInput` dataclass `{ track: list[int], order: list[int], requested_skip: set[int] }` and `is_bug_condition(x) -> bool` mirroring the `isBugCondition` pseudocode in `bugfix.md`
  - Define the reference sequencer `numeric_order_with_deps(track, graph, requested_skip) -> list[int]` (ascending order honoring hard `requires` edges; explicitly skipped modules omitted)
  - Add `st_seq_input()` composite strategy drawing a track (Core/Advanced), a candidate `order`, and a `requested_skip` subset
  - Load `config/module-dependencies.yaml` via a path relative to the test file (`Path(__file__).resolve().parent.parent / "config"`)
  - **Test 1 — Module 4 hard-requires Module 3**: assert `3 in graph["modules"][4]["requires"]` and `1 in graph["modules"][4]["requires"]`
  - **Test 2 — Numeric-order rule present**: parse `senzing-bootcamp/steering/module-transitions.md` and assert it contains an explicit ascending / numeric-order-by-default sequencing instruction AND the "Module 3 after Module 2, before data loading (Module 6)" guarantee
  - **Test 3 — Prerequisites doc reconciled**: parse `senzing-bootcamp/steering/module-prerequisites.md` and assert it no longer contains the "Warn but do not block" Soft Prerequisite Behavior wording for Module 3
  - **Property test**: for every `SeqInput` where `is_bug_condition(x)` holds, assert that the reference sequencer's output `numeric_order_with_deps(x.track, graph, x.requested_skip)` is ascending numeric AND places Module 3 after Module 2 and before Module 6 (or Module 3 is in `requested_skip`)
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it)
  - Run on UNFIXED config: `pytest senzing-bootcamp/tests/test_module_sequencing_order_exploration.py`
  - **EXPECTED OUTCOME**: Test FAILS (correct — Module 4 still soft-requires Module 3, the numeric-order rule is absent, and the prerequisites doc still carries the Soft Prerequisite Behavior section)
  - Document counterexamples found (e.g., "module 4 has soft_requires: [3] and requires: [1] only"; "module-transitions.md has no numeric-order-by-default rule"; "a dependency-respecting Core order such as `1 → 4 → 5 → 2 → 6 → 7` triggers `is_bug_condition`")
  - Mark task complete when the test is written, run, and the failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Buggy Sequences Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe behavior on UNFIXED config, snapshot it, then assert it is preserved
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Create `senzing-bootcamp/tests/test_module_sequencing_order_preservation.py`
  - Per `python-conventions.md`: `from __future__ import annotations`, class-based organization, type hints, `st_`-prefixed strategies, `@settings(max_examples=20)`, stdlib + Hypothesis (PyYAML for the graph)
  - Reuse `SeqInput`, `is_bug_condition`, `numeric_order_with_deps`, and `st_seq_input()` (import or redefine); load the graph via the path-relative pattern
  - **Observation phase**: snapshot via SHA-256 the UNFIXED unrelated regions — graph entries for modules other than 4, the `tracks` block, the `gates` block, and steering/config files not edited by this fix
  - **Test — Track membership preserved (3.1)**: assert `graph["tracks"]["core_bootcamp"]["modules"] == [1,2,3,4,5,6,7]` and `graph["tracks"]["advanced_topics"]["modules"] == [1,2,3,4,5,6,7,8,9,10,11]` — true on unfixed and fixed config
  - **Test — Hard dependencies preserved (3.2)**: assert every pre-existing `requires` edge is unchanged (e.g., `graph["modules"][6]["requires"] == [2,5]`, `graph["modules"][5]["requires"] == [4]`, `graph["modules"][3]["requires"] == [2]`); the only edge change is Module 4 gaining `3`
  - **Test — Explicit-skip preserved (3.3)**: for a `SeqInput` with `requested_skip == {3}`, assert `is_bug_condition` is False when `order` omits Module 3, and `numeric_order_with_deps(core, graph, {3})` omits Module 3 while keeping the rest ascending
  - **Test — Quality feedback loop preserved (3.4)**: assert `module-transitions.md` still documents the Module 7 → Module 5 backward transition, and that such a backward transition is NOT produced/forbidden by the forward numeric-order default (it is a separate, explicit path)
  - **Test — Path-completion detection preserved (3.5)**: assert `module-completion-track.md` still maps Core → complete after Module 7 and Advanced → complete after Module 11
  - **Test — Snapshot of unrelated regions (Preservation)**: assert the SHA-256 of the unrelated graph regions / unedited files is unchanged from the baseline
  - **PBT — Non-bug-condition equivalence (`F(X) = F'(X)`)**: for every `SeqInput` where `NOT is_bug_condition(x)` and `order` is already ascending numeric with Module 3 placed correctly (or explicitly skipped), assert the reference sequencer reproduces `order` identically
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it)
  - Run on UNFIXED config: `pytest senzing-bootcamp/tests/test_module_sequencing_order_preservation.py`
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed config
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix — establish numeric-order-by-default sequencing with Module 3 before data loading

  - [x] 3.1 Promote Module 3 to a hard prerequisite of Module 4 in `module-dependencies.yaml`
    - Edit `senzing-bootcamp/config/module-dependencies.yaml` module `4` entry
    - Change `requires: [1]` to `requires: [1, 3]` and remove the `soft_requires: [3]` key entirely
    - Leave module 3's `skip_if` ("Bootcamper explicitly requests skip ...") unchanged so an explicit skip still satisfies the new hard edge
    - Do NOT change any other module entry, the `tracks` lists, or the `gates` block
    - _Bug_Condition: isBugCondition(X) — Module 3 soft-required by Module 4 allows a dependency-respecting order to interleave/skip Module 3 (notNumericOrder OR module3Skipped OR module3AfterLoading)_
    - _Expected_Behavior: with Module 3 hard-required by Module 4, no dependency-respecting order places 4/5/6 before 3 nor omits 3 without an explicit skip — order is ascending with Module 3 before Module 6 (Property 1)_
    - _Preservation: tracks lists, gates, and all other `requires` edges unchanged; explicit-skip via skip_if preserved (Property 2 reqs 3.1, 3.2, 3.3)_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Add a Numeric-Order-by-Default Sequencing rule to `module-transitions.md`
    - Edit `senzing-bootcamp/steering/module-transitions.md`: add a section (e.g., after "Journey Map") stating: present/run the selected track's modules in ascending numeric order; deviate only for a clear, stated dependency reason; Module 3 runs immediately after Module 2 and before any data loading (Module 6) unless explicitly skipped; this default governs forward sequencing only and does not override the Module 7 → Module 5 quality feedback loop
    - Keep the existing journey-map, transition-integrity, confirmation-response, and quality-feedback-loop content intact
    - Keep CommonMark valid and within the steering token budget; do NOT introduce any external URL (security hook blocks it)
    - _Bug_Condition: no numeric-order-by-default rule lets the agent follow a raw dependency/completion order (notNumericOrder)_
    - _Expected_Behavior: the agent presents/runs modules in ascending numeric order with Module 3 after Module 2 and before data loading (Property 1 reqs 2.1, 2.4)_
    - _Preservation: existing journey-map and Module 7 → Module 5 quality-loop content unchanged (Property 2 req 3.4)_
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 3.3 Reconcile `module-prerequisites.md` (table cell + Soft Prerequisite Behavior section)
    - Edit `senzing-bootcamp/steering/module-prerequisites.md`
    - **Table**: change the Module 4 Requires cell from "Module 1 + Module 3 (soft prerequisite)" to "Module 1 + Module 3" (the validator parses `[1, 3]` from both forms — cross-reference stays green)
    - **Section**: replace the `### Soft Prerequisite Behavior` block (which says "Warn but do not block") with a `### Module 3 Sequencing` section stating: Module 3 runs after Module 2 and before Module 4 (and before data loading in Module 6); modules run in ascending numeric order by default; Module 3 is omitted only on an explicit bootcamper skip request and is never silently skipped or reordered after data loading; on insisted skip, warn about downstream risk (Modules 5–7) but allow it
    - Keep CommonMark valid; do NOT introduce any external URL
    - _Bug_Condition: documentation declared Module 3 a soft prerequisite ("Warn but do not block"), reinforcing the interleave/skip behavior_
    - _Expected_Behavior: docs state numeric-order-by-default and Module 3 after Module 2 / before data loading (Property 1 reqs 2.2, 2.3, 2.4)_
    - _Preservation: explicit-skip (warn-but-allow) behavior retained; table still parses to [1, 3] so validate_dependencies stays green (Property 2 reqs 3.2, 3.3)_
    - _Requirements: 2.2, 2.3, 2.4, 3.3_

  - [x] 3.4 Update the Module 4 comment in `module-artifacts.yaml`
    - Edit `senzing-bootcamp/config/module-artifacts.yaml`: change the Module 4 `requires_from` comment "# Module 3 is a soft prerequisite — warn if missing but do not block" to one reflecting the hard prerequisite, e.g. "# Module 3 is a prerequisite — runs before Module 4 by default; only an explicit bootcamper skip omits it"
    - Leave the `requires_from` mapping `3: ["docs/progress/MODULE_3_COMPLETE.md"]` and all other entries unchanged
    - _Bug_Condition: artifacts comment described Module 3 as "soft / do not block"_
    - _Expected_Behavior: comment reflects the hard prerequisite (Property 1 req 2.2)_
    - _Preservation: requires_from mapping and all other module entries unchanged (Property 2 req 3.2)_
    - _Requirements: 2.2_

  - [x] 3.5 Update the pinning unit test in `test_module3_default_on_unit.py`
    - Edit `senzing-bootcamp/tests/test_module3_default_on_unit.py`: update `test_module_dependencies_soft_requires` (rename to e.g. `test_module_dependencies_module4_hard_requires_module3`) to assert Module 4 hard-requires Module 3 — `3 in module_4["requires"]` and `1 in module_4["requires"]` — and that `soft_requires` is absent or does not list Module 3
    - **Updated, not deleted**
    - Confirm `senzing-bootcamp/tests/test_module3_default_on_properties.py` still passes unchanged (its backward-reachability follows both `requires` and `soft_requires`, and Module 3 is now reachable via `requires`)
    - _Bug_Condition: the existing test pinned `4.soft_requires` containing 3 as "correct"_
    - _Expected_Behavior: the test asserts Module 4 hard-requires Module 3 (Property 1 reqs 2.2)_
    - _Preservation: Module 4 → 3 → 2 reachability property unchanged; hard-dependency edges asserted (Property 2 req 3.2)_
    - _Requirements: 2.2, 3.2_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Fix Checking** - Numeric-Order-by-Default Sequencing
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes, Module 4 hard-requires Module 3, the numeric-order rule is present, the prerequisites doc is reconciled, and the reference sequencer produces ascending orders with Module 3 before Module 6
    - Run `pytest senzing-bootcamp/tests/test_module_sequencing_order_exploration.py`
    - **EXPECTED OUTCOME**: Test PASSES (confirms the bug is fixed across the graph, steering, and docs)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Buggy Sequences Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run `pytest senzing-bootcamp/tests/test_module_sequencing_order_preservation.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — track membership, existing hard edges, explicit-skip handling, the Module 7 → Module 5 quality loop, and path-completion detection unchanged; already-numeric orders reproduced identically)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests and validators pass
  - Run the two new suites: `pytest senzing-bootcamp/tests/test_module_sequencing_order_exploration.py senzing-bootcamp/tests/test_module_sequencing_order_preservation.py`
  - Run the updated/affected existing suites: `pytest senzing-bootcamp/tests/test_module3_default_on_unit.py senzing-bootcamp/tests/test_module3_default_on_properties.py`
  - Run CI validators: `python senzing-bootcamp/scripts/validate_dependencies.py` (graph internally consistent and prerequisites table matches: `sorted(requires + soft_requires) == [1, 3]` for Module 4), `python senzing-bootcamp/scripts/validate_commonmark.py`, `python senzing-bootcamp/scripts/measure_steering.py --check`
  - Confirm no MCP server URL was introduced into any edited surface
  - Ensure all tests pass; ask the user if questions arise.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5"] },
    { "id": 2, "tasks": ["3.6", "3.7"] },
    { "id": 3, "tasks": ["4"] }
  ]
}
```

- **Wave 0** — `[1, 2]`: the exploration suite (must FAIL on unfixed config) and the preservation suite (must PASS on unfixed config) are authored against the unfixed baseline and can run in parallel.
- **Wave 1** — `[3.1, 3.2, 3.3, 3.4, 3.5]`: all touch distinct files and are independent — 3.1 edits the dependency graph, 3.2 the transitions steering, 3.3 the prerequisites steering, 3.4 the artifacts config, and 3.5 the existing unit test.
- **Wave 2** — `[3.6, 3.7]`: verification re-runs the unchanged task 1 / task 2 suites after the fix lands.
- **Wave 3** — `[4]`: the final checkpoint runs all suites and CI validators after verification.

## Notes

- Tests use pytest + Hypothesis (property-based testing); stdlib + Hypothesis only, except the dependency graph is loaded with PyYAML exactly as `validate_dependencies.py` does (the documented `tech.md` exception). Tests live in `senzing-bootcamp/tests/`.
- The exploration test (task 1) is authored to FAIL on unfixed config (Module 4 soft-requires Module 3; no numeric-order rule) — this confirms the bug across the graph, steering, and docs.
- The preservation test (task 2) is authored to PASS on unfixed config — this captures baseline behavior to preserve. After the fix (tasks 3.1–3.5), both suites PASS.
- The dependency graph (`module-dependencies.yaml`) is the single source of truth; the prerequisites table cell still parses to `[1, 3]`, so `validate_dependencies.py` stays green after 3.1 + 3.3.
- Module 3 remains explicitly skippable via its module-level `skip_if`; the new hard `requires` edge is satisfied by an explicit skip, preserving req 3.3.
- The `assess_entry_point.py` recommender (already ascending-order) and the Module 7 → Module 5 quality feedback loop are NOT modified.
- No MCP server URL is introduced into any config, steering, or test (security hook blocks it; the power's `mcp.json` remains the single source of truth).
- Existing tests in task 3.5 are updated/inverted, never deleted.
