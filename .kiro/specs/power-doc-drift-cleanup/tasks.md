# Implementation Plan

## Overview

This plan fixes exactly the three drifted documentation facts from `design.md`:
(1) the empty `CHANGELOG.md` `[Unreleased]` section that omits the shipped
`mcp-tool-inventory-drift` work, (2) the stale current-state pytest count in the
`POWER.md` "What's New in 0.12.1" section, and (3) the unreconciled version record
across `VERSION`, `POWER.md` frontmatter, and `CHANGELOG.md`. Everything else is
**preserve-unchanged**.

**This is a documentation-only bugfix.** No script logic, behavior, test assertions,
test logic, hook, steering logic, or tool inventory is changed. **No new test code is
added** — "tests" here are concrete document/gate checks, and preservation is verified
by re-running existing gates and tests (`tests/test_mcp_tool_inventory.py` and the
`check_mcp_tool_inventory()` gate in `validate_power.py`). The bug-condition methodology
is applied: an exploratory step surfaces the drift counterexamples on the UNFIXED docs, a
preservation baseline is captured on UNFIXED content, the fix is applied, then
fix-checking and preservation-checking verify the result, and a final CI checkpoint
confirms green.

**Hard constraints carried through every task:**

- The corrected pytest count MUST be **measured at fix time** by running the full
  suite — it is **never** hard-coded from `bugfix.md` or `design.md`. (It was observed at
  ~4868 during the audit; that figure is a hint only and MUST be re-measured.)
- The measured count is written into **only** the `POWER.md` "What's New in 0.12.1"
  current-state bullet — **never** the "What's New in 0.12.0" historical
  "4,830 passed / 0 failed / 0 errors" bullet (it was accurate at 0.12.0;
  `isBugCondition` is false for it).
- The `CHANGELOG.md` entry records **exactly the four shipped items** — no invented scope.
- Do **NOT** alter the 13-tool inventory, any "13 tools" count, the absence of
  `lint_record`, or the `analyze_record` routing/signature.
- Do **NOT** touch the separate `senzing` reference power (14 tools / `lint_record`) —
  different repo/power, out of scope.
- All edits stay **CommonMark-compliant**; the only MCP server URL stays confined to
  `mcp.json`; scripts stay **stdlib-only**; no behavioral or script-logic change.
- `validate_power.py` enforces `VERSION` == `POWER.md` frontmatter `version` — keep the
  two strings equal under the chosen version decision.

## Tasks

- [x] 1. Measure the actual passing pytest count on the UNFIXED suite (mandatory input gate)
  - Run the **full** suite across both test roots in a single invocation from the repo
    root: `python3 -m pytest senzing-bootcamp/tests/ tests/` (single run, **no watch
    mode**).
  - Read the authoritative passing total from the pytest summary line (e.g., "N passed,
    M skipped in ...") — this `N` is `actualPytestPassedCount()` and is the **only** source
    for the `POWER.md` correction in task 4.2.
  - Record `N` with its thousands separator (e.g., `4,868`). The audit observed ~4868, but
    the value **MUST** be taken from this live run, never copied from `bugfix.md` /
    `design.md`.
  - Confirm the run reports **0 failures** and that `N` does **not** equal `4,830` (this is
    the counterexample surfaced in task 2 for the stale current-state claim). If it
    unexpectedly equals `4,830` or any failure appears, STOP and surface the discrepancy to
    the user before editing (a green suite is a precondition).
  - Mark complete only when a clean, single-run passing total `N` is captured with 0
    failures.
  - _Requirements: 2.2, 3.4; design "Test-Count Reconciliation Approach"; Property 1 (Fix-Checking)_

- [x] 2. Surface the drift counterexamples on the UNFIXED docs (BEFORE any edit)
  - **Property 1: Bug Condition** - Drifted documentation facts (empty changelog, stale 4,830 count, version incoherence)
  - **CRITICAL**: These checks MUST demonstrate the drift on the unfixed docs — that is
    what confirms the bug exists. **DO NOT fix anything at this step.**
  - **NOTE**: This is the exploratory step. Because the fix is documentation-only, the
    "tests" are concrete document/gate inspections; **no new automated test code is added**.
  - **Scoped approach**: The drift is deterministic across exactly three facts, so inspect
    those concrete facts rather than generating inputs.
  - Counterexample A — **Empty changelog `[Unreleased]`**: Confirm
    `senzing-bootcamp/CHANGELOG.md` `## [Unreleased]` is an empty heading immediately
    followed by `## [0.12.1] - 2026-06-08`, while HEAD (`mcp-tool-inventory-drift`) shipped
    `scripts/mcp_tool_inventory.py`, `tests/test_mcp_tool_inventory.py`, the `analyze_record`
    signature normalization across the three named docs, and the `check_mcp_tool_inventory()`
    gate in `scripts/validate_power.py` — recorded nowhere.
  - Counterexample B — **Stale current-state pytest count (4,830)**: Using `N` from task 1,
    confirm the `POWER.md` "What's New in 0.12.1" current-state line ("...pytest at
    4,830 passed / 0 failed") differs from the measured `N`.
  - Counterexample C — **Incoherent version record**: Confirm shipped-but-unreleased
    changes are present while `VERSION` (`0.12.1`), the `POWER.md` frontmatter `version`
    (`0.12.1`), and `CHANGELOG.md` carry no reconciling record.
  - **EXPECTED OUTCOME**: All three counterexamples reproduce (the bug is confirmed on
    unfixed docs).
  - Document the three counterexamples (exact lines / file locations) to ground the fix.
  - Mark complete when the three counterexamples are reproduced and documented.
  - _Requirements: 1.1, 1.2, 1.3; Property 1 (Fix-Checking) — validates 2.1, 2.2, 2.3_

- [x] 3. Capture the preservation baseline on UNFIXED content (BEFORE any edit)
  - **Property 2: Preservation** - 13-tool inventory, no lint_record, analyze_record routing, 0.12.0 claim, gates green, reference power unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe the unfixed content and
    record it, then assert it is preserved after the fix (task 4.5).
  - Observe and record on UNFIXED content (cases where `isBugCondition` is false):
    - The **13-tool** inventory, every "13 tools" count, and the **absence** of
      `lint_record` across the docs — re-run `python3 -m pytest
      senzing-bootcamp/tests/test_mcp_tool_inventory.py` and confirm it PASSES (no new test
      code is written; this existing test is the preservation guard).
    - The `analyze_record` validation routing and signature
      (`analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")`).
    - The `POWER.md` "What's New in 0.12.0" historical "4,830 passed / 0 failed / 0 errors"
      line (must remain byte-for-byte unchanged — it is the edge case, NOT a bug).
    - The separate `senzing` reference power (14 tools / `lint_record`) is out of scope and
      untouched.
    - Baseline green gate outputs (all 0 failures): `validate_power.py` (including
      `check_mcp_tool_inventory()`), `measure_steering.py --check`, `validate_commonmark.py`,
      `sync_hook_registry.py --verify`, and the full pytest suite (from task 1).
  - **EXPECTED OUTCOME**: All preservation observations hold on the UNFIXED content and all
    gates are green (this is the baseline to preserve). The drift counterexamples from task
    2 still reproduce — that is expected.
  - Mark complete when the preservation baseline is observed and recorded on unfixed content.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6; Property 2 (Preservation)_

- [x] 4. Fix the three drifted documentation facts

  - [x] 4.0 Confirm the version decision (JUDGMENT-CALL TASK — surface to the user; default Option B)
    - **This is the one judgment-call task in the plan.** Surface the version decision to
      the user/maintainer before editing. **Default to Option B** (the design
      recommendation), while noting **Option A remains valid**.
    - **Option B — bump to `0.12.2` (RECOMMENDED, default):** Set `senzing-bootcamp/VERSION`
      to `0.12.2`, set the `POWER.md` frontmatter `version` to `0.12.2`, and add a new
      `## [0.12.2] - <date>` heading in `CHANGELOG.md` capturing the
      `mcp-tool-inventory-drift` work, leaving a fresh empty `## [Unreleased]` above it. All
      three records (`VERSION` ↔ frontmatter ↔ `CHANGELOG` heading) then describe the same
      released state. Touches one extra file (`VERSION`) and the frontmatter, so the
      version-sync gate and CommonMark must be re-verified after the edit.
    - **Option A — record under `[Unreleased]` only (still valid, lowest-risk):** Add the
      `mcp-tool-inventory-drift` entry under the existing `## [Unreleased]` heading and leave
      `VERSION` / frontmatter at `0.12.1`. Appropriate only if no release is being cut now;
      tradeoff is the shipped, tested work stays formally "unreleased."
    - **Synchronization invariant (both options):** `VERSION` == `POWER.md` frontmatter
      `version` MUST hold so the `validate_power.py` sync check passes, and `CHANGELOG.md`
      MUST contain a heading (the bumped version, or `[Unreleased]`) under which the shipped
      work is recorded.
    - Proceed with **Option B** unless the user explicitly chooses Option A.
    - _Requirements: 1.3, 2.3; design "Version Decision (Defect 3)"; Property 1 (Fix-Checking)_

  - [x] 4.1 Record the four shipped `mcp-tool-inventory-drift` items in `CHANGELOG.md`
    - Edit `senzing-bootcamp/CHANGELOG.md` in Keep a Changelog format. Under **Option B**
      (default) place the entry under a new `## [0.12.2] - <date>` heading directly above
      `## [0.12.1]`, leaving a fresh empty `## [Unreleased]` above the new heading. Under
      **Option A** place the entry under the existing `## [Unreleased]` heading. The entry
      content is identical either way and records **exactly these four shipped items**:
    - **Added** — `scripts/mcp_tool_inventory.py`: the canonical single source of truth for
      the 13-tool MCP inventory (`ALL_TOOLS` + `TOTAL_COUNT`), confirmed live against
      `get_capabilities(version="current")` on `sz-mcp-coworker` v1.24.0.
    - **Added** — `tests/test_mcp_tool_inventory.py`: pins the 13-tool inventory and asserts
      the absence of any `lint_record` tool.
    - **Added** — `check_mcp_tool_inventory()` gate in `scripts/validate_power.py`: fails CI
      if `POWER.md` / `ARCHITECTURE.md` tool listings drift from `mcp_tool_inventory.py`.
    - **Changed** — normalized the `analyze_record` call signature to
      `analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")` across
      `steering/mcp-tool-decision-tree.md`,
      `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`, and
      `steering/troubleshooting-commands.md`.
    - The entry describes **shipped work only** — introduce no new code, no new behavior,
      and no scope beyond these four items. Keep it CommonMark-compliant and consistent with
      the surrounding changelog style.
    - _Bug_Condition: isBugCondition(X) where X = CHANGELOG.Unreleased AND mcpToolInventoryDriftWork NOT recorded_
    - _Expected_Behavior: CHANGELOG records mcp_tool_inventory.py, test_mcp_tool_inventory.py, the analyze_record normalization across the 3 named docs, and the check_mcp_tool_inventory() gate_
    - _Preservation: every existing CHANGELOG section from [0.12.1] downward is unchanged_
    - _Requirements: 1.1, 2.1; design "Fix Implementation File 1"; Property 1 (Fix-Checking)_

  - [x] 4.2 Write the MEASURED count into ONLY the "What's New in 0.12.1" bullet of `POWER.md`
    - Edit `senzing-bootcamp/POWER.md` "What's New in 0.12.1" section: on the single bullet
      reading "...pytest at 4,830 passed / 0 failed", replace `4,830` with the measured `N`
      from task 1 (formatted with its thousands separator, e.g. `4,868`).
    - Match on the surrounding "0.12.1" / "ruff" / "now green" context to edit the correct
      line. Preserve the existing `passed / 0 failed` phrasing — do **not** import the
      `/ 0 errors` clause from the 0.12.0 line.
    - The replacement number MUST equal `actualPytestPassedCount()` (`N`) measured at fix
      time — **never** hard-coded from this plan or the design.
    - **Do NOT** touch the "What's New in 0.12.0" historical
      "4,830 passed / 0 failed / 0 errors" claim — it is the preserved edge case and must
      remain byte-for-byte unchanged.
    - Change only the count; preserve all surrounding phrasing and CommonMark structure.
    - _Bug_Condition: isBugCondition(X) where X = POWER.md."What's New in 0.12.1".currentPytestCount AND X.value <> actualPytestPassedCount()_
    - _Expected_Behavior: the 0.12.1 current-state count equals N (measured by running pytest at fix time)_
    - _Preservation: the 0.12.0 historical "4,830 passed / 0 failed / 0 errors" claim and all other POWER.md content unchanged_
    - _Requirements: 1.2, 2.2, 3.3; design "Fix Implementation File 2"; Property 1 (Fix-Checking)_

  - [x] 4.3 Apply the version decision and reconcile the three artifacts
    - For **Option B** (default): set `senzing-bootcamp/VERSION` to `0.12.2`, set the
      `POWER.md` frontmatter `version: "0.12.1"` to `version: "0.12.2"`, and confirm the
      `## [0.12.2]` heading from task 4.1 is present.
    - For **Option A** (if chosen): make **no** version change — confirm `VERSION` and the
      `POWER.md` frontmatter both remain `0.12.1`; the changelog entry from task 4.1 (under
      `[Unreleased]`) supplies the reconciling record.
    - Verify `VERSION` == `POWER.md` frontmatter `version` so the `validate_power.py`
      `check_version_sync()` check passes, and that `CHANGELOG.md` carries the heading
      recording the shipped work.
    - Make no unrelated `VERSION` / frontmatter edits.
    - _Bug_Condition: isBugCondition(X) where X = VersionRecordCoherence AND shippedUnreleasedChangesPresent() AND NOT reconciled(VERSION, frontmatter, CHANGELOG)_
    - _Expected_Behavior: reconciled(VERSION, POWER.frontmatter.version, CHANGELOG) AND check_version_sync() passes_
    - _Preservation: no unrelated VERSION/frontmatter edits; sync invariant maintained_
    - _Requirements: 1.3, 2.3; design "Fix Implementation File 3" + "Version Decision"; Property 1 (Fix-Checking)_

  - [x] 4.4 Verify the drift counterexamples are now resolved (Fix-Checking)
    - **Property 1: Expected Behavior** - Drifted facts corrected
    - **IMPORTANT**: Re-resolve the SAME three facts from task 2 — do NOT introduce new tests.
    - Confirm: `CHANGELOG.md` now records the four shipped `mcp-tool-inventory-drift` items;
      the `POWER.md` "What's New in 0.12.1" current-state count now equals `N`; and `VERSION`
      / frontmatter / `CHANGELOG.md` are mutually reconciled (`0.12.2` under Option B).
    - **EXPECTED OUTCOME**: All three counterexamples no longer reproduce (the bug is fixed).
    - _Requirements: 2.1, 2.2, 2.3; Property 1 (Fix-Checking)_

  - [x] 4.5 Verify the preservation baseline still holds (Preservation-Checking)
    - **Property 2: Preservation** - Non-drifted facts and all behavior unchanged
    - **IMPORTANT**: Re-check the SAME baseline observations from task 3 by re-running the
      EXISTING tests/gates — do NOT introduce new tests.
    - Re-run `python3 -m pytest senzing-bootcamp/tests/test_mcp_tool_inventory.py` and the
      `check_mcp_tool_inventory()` gate (via `validate_power.py`): both still PASS — 13
      tools, no `lint_record`, unchanged routing.
    - **EXPECTED OUTCOME**: The 13-tool inventory, "13 tools" counts, and absence of
      `lint_record` are unchanged; `analyze_record` routing/signature is unchanged; the
      0.12.0 historical "4,830 passed" claim is byte-for-byte unchanged; the separate
      `senzing` reference power is untouched; and all gates remain green.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6; Property 2 (Preservation)_

- [x] 5. Preservation verification sweep (assert only the intended edit targets changed)
  - **Property 2: Preservation** - Scoped diff review confirms nothing else moved
  - Via a focused diff review of the working tree, confirm the ONLY changed files are the
    intended edit targets: `senzing-bootcamp/CHANGELOG.md`, `senzing-bootcamp/POWER.md`,
    and (Option B, the default) `senzing-bootcamp/VERSION`.
  - Explicitly confirm each preserved fact is untouched:
    - The **13-tool** inventory, every "13 tools" count, and the absence of `lint_record`
      (re-run `tests/test_mcp_tool_inventory.py`).
    - `analyze_record` validation routing/signature across docs and tests.
    - The `POWER.md` "What's New in 0.12.0" "4,830 passed / 0 failed / 0 errors" line is
      byte-for-byte unchanged.
    - The separate `senzing` reference power (14 tools / `lint_record`) is not modified.
    - No script/test/hook/steering **logic** changed; scripts remain stdlib-only; the only
      MCP server URL stays confined to `mcp.json`.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6; Property 2 (Preservation)_

- [x] 6. Checkpoint — run the full CI gate sequence in order and confirm green
  - Run, in this exact order, from the repo root:
    - `python3 senzing-bootcamp/scripts/validate_power.py` (includes `check_version_sync()`
      VERSION ↔ frontmatter sync and `check_mcp_tool_inventory()`)
    - `python3 senzing-bootcamp/scripts/measure_steering.py --check`
    - `python3 senzing-bootcamp/scripts/validate_commonmark.py`
    - `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - `python3 -m pytest senzing-bootcamp/tests/ tests/` (full suite, single run, no watch
      mode)
  - **EXPECTED OUTCOME**: every gate passes with **0 failures**; the pytest passing total
    matches the `N` now recorded in `POWER.md`; `validate_commonmark.py` passes on the edited
    `CHANGELOG.md` and `POWER.md`; the VERSION ↔ frontmatter sync passes for the chosen
    version decision (`0.12.2` under Option B).
  - Ensure all gates pass. If any question or discrepancy arises, ask the user.
  - _Requirements: 3.4, 3.5; design "CI Gate Re-Verification" + Integration Tests; Properties 1 and 2_

## Task Dependency Graph

Execution waves (tasks within a wave may run in parallel once the prior wave completes):

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1"], "description": "Blocking input gate: measure actualPytestPassedCount() (N) on the UNFIXED full suite (single run, 0 failures). N feeds the POWER.md 0.12.1 bullet. Re-measure at fix time; never hard-code." },
    { "wave": 2, "tasks": ["2", "3"], "description": "Exploratory + preservation baseline on UNFIXED content. Task 2 (Property 1: Bug Condition) reproduces the 3 counterexamples (empty [Unreleased], stale 4,830, version incoherence); task 3 (Property 2: Preservation) records the baseline (13 tools, no lint_record, analyze_record routing, 0.12.0 claim, gates green, reference power)." },
    { "wave": 3, "tasks": ["4.0"], "description": "JUDGMENT-CALL version decision: default Option B (bump to 0.12.2 + new [0.12.2] heading); Option A (record under [Unreleased]) remains valid. Surface to the user. Governs how 4.1/4.3 record the work." },
    { "wave": 4, "tasks": ["4.1", "4.2", "4.3"], "description": "Apply the three edits: CHANGELOG entry recording the four shipped items; POWER.md 0.12.1 current-state count = measured N; reconcile VERSION/frontmatter/CHANGELOG per the decision (0.12.2 for Option B)." },
    { "wave": 5, "tasks": ["4.4", "4.5"], "description": "Verify Property 1 (3 counterexamples resolved) and Property 2 (baseline preserved by re-running test_mcp_tool_inventory.py + check_mcp_tool_inventory())." },
    { "wave": 6, "tasks": ["5"], "description": "Preservation verification sweep: scoped diff review confirms only CHANGELOG.md, POWER.md, and VERSION (Option B) changed." },
    { "wave": 7, "tasks": ["6"], "description": "Checkpoint: full CI gate sequence in order (validate_power.py, measure_steering.py --check, validate_commonmark.py, sync_hook_registry.py --verify, full pytest), confirm green with 0 failures." }
  ]
}
```

Visual overview:

```text
1. Measure actualPytestPassedCount() N on UNFIXED suite (BLOCKING INPUT GATE)
        |
        v
+-------------------+        +----------------------------+
| 2. Property 1:    |        | 3. Property 2:             |
|    Bug Condition  |        |    Preservation baseline   |
|    (3 counter-    |        |    (holds on unfixed,      |
|     examples      |        |     gates green)           |
|     reproduce)    |        |                            |
+-------------------+        +----------------------------+
        \                          /
         \                        /
          v                      v
        4.0 Version decision (JUDGMENT CALL — default Option B)
                |
                v
        4. Fix (parent)
        4.1 CHANGELOG entry: four shipped items (needs 4.0)  ---------> (enables 4.4)
        4.2 POWER.md 0.12.1 count = measured N (needs 1)     ---------> (enables 4.4)
        4.3 reconcile VERSION/frontmatter/CHANGELOG (needs 4.0, 4.1)
        4.4 verify Property 1 PASS (needs 4.1-4.3; re-resolves task 2)
        4.5 verify Property 2 PASS (needs 4.1-4.3; re-runs existing tests/gates from task 3)
                |
                v
        5. Preservation verification sweep (scoped diff)  (needs 4.x)
                |
                v
        6. Checkpoint: full CI gate sequence + pytest  (needs all above)
```

**Critical path:** 1 → 2 → 4.0 → 4.1 → 4.3 → 4.4 → 5 → 6.
Task 4.2 depends on task 1 (the measured `N`) and joins at 4.4.

## Notes

- **Bug-condition methodology.** Task 1 measures the live pytest count `N` that the fix
  depends on. Task 2 is the Exploratory step: it reproduces the three drift counterexamples
  on UNFIXED docs (Property 1: Bug Condition). Task 3 captures the preservation baseline
  (Property 2). The fix (task 4) resolves the counterexamples (Fix-Checking, 4.4) while
  keeping the baseline preserved (Preservation-Checking, 4.5).
- **Documentation-only; no new test code.** No script logic, behavior, test assertions,
  test logic, hook, or steering logic is changed. Preservation is verified by **re-running
  the existing** `test_mcp_tool_inventory.py` and `check_mcp_tool_inventory()` gate, not by
  writing new tests. The exact edit targets are `CHANGELOG.md`, `POWER.md`, and (Option B)
  `VERSION`.
- **Measured, never hard-coded.** The corrected `POWER.md` count comes solely from the
  task-1 pytest summary at fix time and is written into **only** the 0.12.1 bullet. The
  ~4868 audit observation is a hint that MUST be re-measured.
- **Edge case preserved.** The `POWER.md` "What's New in 0.12.0" historical "4,830 passed"
  claim was accurate at 0.12.0 and is left byte-for-byte unchanged.
- **Version decision is the one judgment call.** Task 4.0 defaults to Option B (bump to
  `0.12.2`) per the design recommendation, while keeping Option A valid; it is surfaced to
  the maintainer because the release-cadence call is theirs.
- **Requirements mapping.** Tasks reference `bugfix.md` / `design.md` clauses 1.1–1.3,
  2.1–2.3, and 3.1–3.6, plus Property 1 (Fix-Checking) and Property 2 (Preservation).
- **Constraints.** Stdlib-only scripts; CommonMark-compliant Markdown; the only MCP server
  URL stays confined to `mcp.json`; the separate `senzing` reference power stays untouched.
