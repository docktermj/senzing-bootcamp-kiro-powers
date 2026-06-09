# Implementation Plan

## Overview

This plan fixes exactly the two ground-truth-confirmed defects from `design.md`:
(A) the `analyze_record` call-signature contradiction across three files, and
(B) the brittle, unguarded test inventory. Everything else is **preserve-unchanged**.

**Hard constraints carried through every task:**

- The live `get_capabilities(version="current")` response is the single source of truth.
  Confirm names/signatures/semantics against it before editing. **If the MCP server is
  unreachable, BLOCK — surface the MCP connection-troubleshooting steps in `POWER.md`.
  There is no offline fallback.**
- Do **NOT** add `lint_record`. Do **NOT** change any tool count to `14`. The inventory
  stays at the live **13 tools** (12 active + `submit_feedback` disabled-by-default).
- All Python stays **stdlib-only**. All Markdown stays **CommonMark-compliant**.

## Tasks

- [x] 1. Re-confirm the live MCP capabilities before any edit (mandatory gate)
  - Call `get_capabilities(version="current")` against the Senzing MCP server configured
    in `senzing-bootcamp/mcp.json` (`sz-mcp-coworker`, expect `server_version: 1.24.0`).
  - Record from the live response: the `tools[]` array (expect the **13** names listed in
    `design.md` Mandatory First Step), `server_info.tool_count` (expect **13**), the
    absence of `lint_record`, and the `analyze_record` schema (required `workspace_dir`;
    optional `file_paths` array and `version`; **no** `record=`, **no** `data_source=`).
  - Treat this response as authoritative; it supersedes `bugfix.md`, the bundled tool
    reference, and training data wherever they differ.
  - **If the server is unreachable: STOP.** Do not proceed from `bugfix.md` or bundled
    docs. Surface the MCP connection-troubleshooting steps documented in `POWER.md`
    (verify connectivity, test the endpoint, allowlist behind proxy, check DNS, restart),
    and resume only after a live response is obtained.
  - Mark complete only when a live response confirms 13 tools, no `lint_record`, and the
    `analyze_record` schema above.
  - _Source-of-truth constraint (bugfix.md Introduction); design Mandatory First Step_

- [x] 2. Write the `analyze_record` signature exploration tests (BEFORE any fix)
  - **Property 1: Bug Condition** - `analyze_record` signature contradiction
  - **CRITICAL**: These tests MUST FAIL on the unfixed docs — failure confirms the bug exists.
  - **DO NOT attempt to fix the code or the tests when they fail at this step.**
  - **NOTE**: These tests encode the live-confirmed expected signature; they will validate
    the fix when they pass after normalization (task 8.1).
  - **GOAL**: Surface the concrete counterexamples — the three divergent signatures.
  - **Scoped PBT Approach**: The defect is deterministic across a fixed set of three files,
    so scope the property to those concrete files rather than generating file paths.
    Iterate over the three signature-bearing files and assert each `analyze_record`
    example matches the live schema.
  - Add the tests to a new `senzing-bootcamp/tests/test_mcp_tool_inventory.py` (signature
    section) — scanning these files for `analyze_record` call examples:
    - `senzing-bootcamp/steering/mcp-tool-decision-tree.md` (uses `record="{...}"`, no `workspace_dir`)
    - `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` (uses `record=` + `data_source=`)
    - `senzing-bootcamp/steering/troubleshooting-commands.md` (uses `file_paths` but omits `workspace_dir`)
  - Assertion (the Expected Behavior the fix must satisfy): every `analyze_record` example
    contains `file_paths` and `workspace_dir`, and contains **no** `record=` and **no**
    `data_source=`.
  - Run on UNFIXED docs.
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct — it proves the bug exists).
  - Document the three counterexamples found (the exact divergent signature in each file).
  - Mark complete when the tests are written, run, and the failures are documented.
  - _Requirements: 1.1; Property 1 (Fix-Checking) — validates 2.1_

- [x] 3. Capture the preservation baseline on UNFIXED content (BEFORE any fix)
  - **Property 2: Preservation** - Already-correct inventory, counts, routing, hook unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe the unfixed content,
    then assert it is preserved.
  - Observe and record on UNFIXED content (cases where `isBugCondition` is false):
    - `senzing-bootcamp/POWER.md` "Available MCP Tools" lists exactly the **13** live tools
      (names, order, descriptions), including `submit_feedback` disabled-by-default.
    - `senzing-bootcamp/docs/guides/ARCHITECTURE.md` "MCP Tool Categories" states **13**
      tools and routes "validate a mapped record" to `analyze_record`.
    - `senzing-bootcamp/steering/mcp-tool-decision-tree.md` Data Preparation node routes
      validation to `analyze_record`.
    - `senzing-bootcamp/hooks/analyze-after-mapping.kiro.hook` prompt text (uses
      `analyze_record` for validation + quality).
    - `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` is clean.
  - Reuse/extend the existing snapshot-and-preserve approach in
    `senzing-bootcamp/tests/test_no_direct_sql_preservation.py` where appropriate; add the
    13-tool / count / routing / no-`lint_record` preservation assertions to the new
    `senzing-bootcamp/tests/test_mcp_tool_inventory.py` (preservation section).
  - Run on UNFIXED content.
  - **EXPECTED OUTCOME**: These preservation assertions PASS (they capture the baseline to
    preserve). The signature assertions from task 2 still fail — that is expected.
  - Mark complete when the preservation assertions are written, run, and passing on unfixed content.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7; Property 2 (Preservation)_

- [x] 4. Fix for the `analyze_record` signature contradiction and the unguarded inventory

  - [x] 4.1 Create the canonical inventory module (single source of truth)
    - Create `senzing-bootcamp/scripts/mcp_tool_inventory.py` — stdlib-only, no third-party
      imports, following `scripts/` conventions (shebang, `from __future__ import annotations`,
      module docstring, no CLI required).
    - Expose exactly these constants, sourced from the live confirmation in task 1:
      - `ACTIVE_TOOLS: tuple[str, ...]` — the **12** routable tools (`get_capabilities`,
        `mapping_workflow`, `analyze_record`, `download_resource`, `explain_error_code`,
        `search_docs`, `find_examples`, `generate_scaffold`, `get_sample_data`,
        `get_sdk_reference`, `sdk_guide`, `reporting_guide`).
      - `DISABLED_TOOLS: tuple[str, ...] = ("submit_feedback",)`.
      - `ALL_TOOLS: tuple[str, ...]` — the **13** live tools (`ACTIVE_TOOLS + DISABLED_TOOLS`).
      - `TOTAL_COUNT: int = 13`.
      - `VALIDATION_TOOL: str = "analyze_record"`.
    - Module docstring MUST state these values were confirmed against
      `get_capabilities(version="current")` (server v1.24.0) and MUST be re-confirmed live
      before any change. Do **NOT** include `lint_record`; do **NOT** set `TOTAL_COUNT = 14`.
    - _Requirements: 2.2; design §D item 1; Property 1 (Fix-Checking)_

  - [x] 4.2 Normalize the `analyze_record` signature in the three signature-bearing files
    - Use the single live-confirmed form everywhere:
      `analyze_record(file_paths=[...], workspace_dir="<writable-dir>", version="current")`
      — no `record=`, no `data_source=`, `workspace_dir` always present; use a
      project-relative `workspace_dir` (never `/tmp`), `version="current"`.
    - `senzing-bootcamp/steering/mcp-tool-decision-tree.md` — replace the JSON call block
      `{ "tool": "analyze_record", "record": "{...}" }` with the agreed signature in the
      same JSON call-pattern style as its neighbors. Preserve surrounding prose intent.
    - `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` — Step 5
      "Validate Quality": replace `analyze_record(record=transformed_record, data_source="CUSTOMERS")`
      with the agreed signature. Preserve the following prose (Entity-Spec validation +
      feature distribution / attribute coverage / data quality).
    - `senzing-bootcamp/steering/troubleshooting-commands.md` — "Mapping issues" bullet:
      add required `workspace_dir` (and `version="current"`) to the existing
      `analyze_record(file_paths=[...])` example.
    - Do NOT touch other `analyze_record` prose references (they name the tool without a
      signature and already route to `analyze_record` correctly).
    - _Bug_Condition: isBugCondition(X) where X documents the analyze_record signature and X.signature <> LIVE.signature_
    - _Expected_Behavior: signature identical across all files = analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")_
    - _Preservation: surrounding routing/prose unchanged; no re-routing, no lint_record_
    - _Requirements: 1.1, 2.1; design §A; Property 1 (Fix-Checking)_

  - [x] 4.3 Complete the drift guard test
    - Finalize `senzing-bootcamp/tests/test_mcp_tool_inventory.py` (started in tasks 2–3),
      importing the canonical module via the existing `scripts/` + `sys.path` test pattern.
    - Assert:
      - `POWER.md` "Available MCP Tools" lists exactly `ALL_TOOLS` (fails if `lint_record`
        or any phantom is added, or a real tool dropped).
      - `mcp-tool-decision-tree.md` references every tool in `ACTIVE_TOOLS`.
      - `ARCHITECTURE.md` "MCP Tool Categories" lists exactly `ALL_TOOLS` and states `TOTAL_COUNT`.
      - Total-count statements across `POWER.md`, `ARCHITECTURE.md`, and the decision tree
        are mutually consistent and equal `TOTAL_COUNT` (no "14"; no bare "12 tools" as a total).
      - `VALIDATION_TOOL == "analyze_record"` and the decision-tree Data Preparation node
        routes "validate" to `analyze_record`.
      - The `analyze_record` signature in the three normalized files contains `file_paths`
        and `workspace_dir` and contains no `record=` / `data_source=`.
    - _Bug_Condition: isBugCondition(X) where X is a test assertion encoding inventory <> LIVE.tools or providing no drift guard_
    - _Expected_Behavior: tests assert canonical 13-tool inventory + validation tool; fail on drop/phantom/stale-count_
    - _Requirements: 1.2, 2.2; design §D item 2; Property 1 (Fix-Checking)_

  - [x] 4.4 Refactor `test_mcp_tool_decision_tree.py` to use the canonical inventory
    - In `senzing-bootcamp/tests/test_mcp_tool_decision_tree.py`, replace the local
      `_ALL_TOOLS` list with an import of `ACTIVE_TOOLS` from `mcp_tool_inventory`.
    - Rename `test_all_12_tools_present` → `test_all_active_tools_present`; update its
      docstring and the "All 12 MCP tools" comments to reference the canonical count
      rather than a frozen literal `12`.
    - Preserve all other behavior in this file.
    - _Requirements: 1.2, 2.2; design §D item 3; Property 1 (Fix-Checking)_

  - [x] 4.5 Refactor `test_no_direct_sql_preservation.py` to use the canonical inventory
    - In `senzing-bootcamp/tests/test_no_direct_sql_preservation.py`, replace the
      hard-coded `_MCP_TOOL_PATTERNS` list and the "These are the 12 MCP tools..." comment
      with an import of `ACTIVE_TOOLS` from `mcp_tool_inventory`; update
      `test_decision_tree_references_all_tools`'s docstring accordingly.
    - Preserve all SQL-preservation behavior unchanged (it validates a different bugfix —
      only the tool-list source changes).
    - _Requirements: 1.2, 2.2; design §D item 4; Property 2 (Preservation of unrelated behavior)_

  - [x] 4.6 Verify the signature exploration tests now PASS
    - **Property 1: Expected Behavior** - `analyze_record` signature normalized
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests.
    - Run the signature assertions over the three normalized files.
    - **EXPECTED OUTCOME**: Tests PASS (confirms the signature contradiction is fixed).
    - _Requirements: 2.1; Property 1 (Fix-Checking)_

  - [x] 4.7 Verify the preservation baseline still PASSES
    - **Property 2: Preservation** - Inventory, counts, routing, hook unchanged
    - **IMPORTANT**: Re-run the SAME assertions from task 3 — do NOT write new tests.
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — 13 tools, counts at 13,
      validation routes to `analyze_record`, no `lint_record`, hook text unchanged).
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5; Property 2 (Preservation)_

- [x] 5. Recompute the steering token budget
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to recompute and update the
    `token_count` for `mcp-tool-decision-tree.md` in
    `senzing-bootcamp/steering/steering-index.yaml` (currently `2305`, `size_category: large`).
  - Confirm `python3 senzing-bootcamp/scripts/measure_steering.py --check` passes within tolerance.
  - This is the only steering file edited, so no other budget entries should move.
  - _Requirements: 3.6; design Token-budget impact; Property 2 (Preservation)_

- [x] 6. (OPTIONAL) Belt-and-suspenders inventory check in `validate_power.py`
  - **OPTIONAL — not required for the fix.** The pytest guard (task 4.3) is the required minimum.
  - Add a `check_mcp_tool_inventory()` function to `senzing-bootcamp/scripts/validate_power.py`
    (alongside `check_power_md_references` / `check_steering_index_metadata`) that imports
    `mcp_tool_inventory` and performs the same `POWER.md` / `ARCHITECTURE.md` cross-check,
    so the guard also runs in the `validate_power.py` CI gate (not only pytest).
  - Keep it stdlib-only. Do NOT introduce `lint_record` or a 14-count anywhere.
  - _Requirements: 2.2, 3.6; design §D item 5 (optional); Property 1 (Fix-Checking)_

- [x] 7. Preservation verification sweep (assert the already-correct world is untouched)
  - **Property 2: Preservation** - Live-correct content and gates unchanged
  - Explicitly confirm, via the tests and a manual diff review:
    - The **13-tool** inventory and all 13 descriptions in `POWER.md` are unchanged; no
      tool added (no `lint_record`) and none removed.
    - Every tool-count statement remains **13** across `POWER.md`, `ARCHITECTURE.md`, and
      the decision tree; **never 14**.
    - Validation routing still targets `analyze_record` (decision tree + `ARCHITECTURE.md`).
    - `submit_feedback` remains disabled-by-default via `disabledTools` in `mcp.json`.
    - `senzing-bootcamp/hooks/analyze-after-mapping.kiro.hook` prompt text is unchanged.
    - `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` is clean
      (`hook-registry.md` / `hook-registry-modules.md` in sync).
    - MCP URL stays confined to `mcp.json`; no static SDK code introduced; scripts stdlib-only.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7; Property 2 (Preservation)_

- [x] 8. Checkpoint — run the full CI gate sequence and confirm green
  - Run, in order, from the repo root:
    - `python3 senzing-bootcamp/scripts/validate_power.py`
    - `python3 senzing-bootcamp/scripts/measure_steering.py --check`
    - `python3 senzing-bootcamp/scripts/validate_commonmark.py`
    - `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - `python3 -m pytest senzing-bootcamp/tests/ --run` (include the new
      `test_mcp_tool_inventory.py` and the refactored `test_mcp_tool_decision_tree.py` /
      `test_no_direct_sql_preservation.py`)
  - **EXPECTED OUTCOME**: all gates pass; the signature tests pass; the drift guard passes;
    all preservation tests pass.
  - Ensure all tests pass. If questions arise, ask the user.
  - _Requirements: 3.6; design Integration Tests; Properties 1 and 2_

## Task Dependency Graph

Execution waves (tasks within a wave may run in parallel once the prior wave completes):

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1"], "description": "Blocking gate: live get_capabilities re-confirmation (13 tools, no lint_record, analyze_record schema). Block if unreachable." },
    { "wave": 2, "tasks": ["2", "3"], "description": "Exploratory + preservation baseline on UNFIXED content. Task 2 (Property 1: Bug Condition) FAILS; task 3 (Property 2: Preservation) PASSES." },
    { "wave": 3, "tasks": ["4.1"], "description": "Create canonical inventory module (single source of truth) used by guard and refactors." },
    { "wave": 4, "tasks": ["4.2", "4.3", "4.4", "4.5"], "description": "Normalize 3 signatures; add drift guard test; refactor the 2 existing tests to import ACTIVE_TOOLS." },
    { "wave": 5, "tasks": ["4.6", "4.7"], "description": "Verify Property 1 (signature tests now PASS) and Property 2 (preservation still PASSES)." },
    { "wave": 6, "tasks": ["5"], "description": "Recompute mcp-tool-decision-tree.md token_count in steering-index.yaml via measure_steering.py." },
    { "wave": 7, "tasks": ["6"], "description": "OPTIONAL belt-and-suspenders inventory check in validate_power.py (off critical path)." },
    { "wave": 8, "tasks": ["7"], "description": "Preservation verification sweep (inventory, counts, routing, hook text, hook-sync --verify)." },
    { "wave": 9, "tasks": ["8"], "description": "Checkpoint: full CI gate sequence + pytest, confirm green." }
  ]
}
```

Visual overview:

```text
1. Live capabilities re-confirmation (BLOCKING GATE)
        |
        v
+-------------------+        +----------------------------+
| 2. Property 1:    |        | 3. Property 2:             |
|    Bug Condition  |        |    Preservation baseline   |
|    (FAIL on       |        |    (PASS on unfixed)       |
|     unfixed)      |        |                            |
+-------------------+        +----------------------------+
        \                          /
         \                        /
          v                      v
        4. Fix (parent)
        4.1 canonical inventory module  ---------> (enables 4.3, 4.4, 4.5, 6)
        4.2 normalize 3 signatures      ---------> (enables 4.6)
        4.3 drift guard test            (needs 4.1)
        4.4 refactor decision-tree test (needs 4.1)
        4.5 refactor sql-preservation   (needs 4.1)
        4.6 verify Property 1 PASS      (needs 4.2; re-runs task 2)
        4.7 verify Property 2 PASS      (needs 4.3-4.5; re-runs task 3)
                |
                v
        5. measure_steering.py (update token_count)  (needs 4.2)
                |
                v
        6. (OPTIONAL) validate_power.py inventory check  (needs 4.1)
                |
                v
        7. Preservation verification sweep  (needs 4.x, 5)
                |
                v
        8. Checkpoint: full CI gate sequence + pytest  (needs all above)
```

**Critical path:** 1 → (2, 3) → 4.1 → 4.2 → 4.6 → 5 → 7 → 8.
Task 6 is optional and off the critical path.

## Notes

- **Bug-condition methodology.** Task 2 is the Exploratory step: it writes the failing
  property test that encodes the live-confirmed `analyze_record` signature and surfaces
  the three counterexamples on UNFIXED docs. Task 3 captures the preservation baseline.
  The fix (task 4) flips task 2 to PASS (Property 1: Fix-Checking) while keeping task 3
  PASS (Property 2: Preservation).
- **Refuted premise.** The original 14-tool / `lint_record` premise was refuted by the
  live call and is out of scope. No task adds `lint_record` or changes the count to 14.
- **Requirements mapping.** Tasks reference `bugfix.md` clauses 1.1, 1.2, 2.1, 2.2, and
  3.1–3.7, plus design Properties (Property 1 Fix-Checking / Property 2 Preservation).
- **Stdlib + CommonMark.** The new `mcp_tool_inventory.py` and guard test are stdlib-only;
  all edited Markdown stays CommonMark-compliant; the MCP URL stays confined to `mcp.json`.
