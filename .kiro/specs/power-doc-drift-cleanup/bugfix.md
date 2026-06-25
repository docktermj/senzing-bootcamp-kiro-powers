# Bugfix Requirements Document

## Introduction

A consistency / coherence / completeness audit of the `senzing-bootcamp` Kiro Power found
**documentation drift**: shipped, tested code is not reflected in the power's
release-facing documentation, and a hard-coded test-suite count in `POWER.md` no longer
matches reality.

The power is internally **GREEN** on every automated gate — `validate_power.py`,
`measure_steering.py --check`, `sync_hook_registry.py --verify`, and
`validate_commonmark.py` all pass, and the full pytest suite passes with 0 failures. The
drift is therefore invisible to CI: the gates pass while the human-readable record is
stale.

The most recent commit (HEAD), `mcp-tool-inventory-drift`, shipped code and tests but no
documentation entry. Specifically, that work added the canonical 13-tool single-source-of-truth
script (`senzing-bootcamp/scripts/mcp_tool_inventory.py`), its test
(`senzing-bootcamp/tests/test_mcp_tool_inventory.py`), normalized the `analyze_record`
call signature across three documents, and added a `check_mcp_tool_inventory()` gate to
`scripts/validate_power.py` — yet `CHANGELOG.md` has an **empty** `[Unreleased]` section.

This is a **documentation-only** bugfix. No script logic, behavior, test assertions, or
tool inventory is changed. The defects are:

1. `CHANGELOG.md` `[Unreleased]` is empty; the shipped `mcp-tool-inventory-drift` work is
   unrecorded.
2. `POWER.md` claims "pytest at 4,830 passed" as the **current** state in the
   "What's New in 0.12.1" section, but the suite now reports a higher count. (The
   identical phrasing in the "What's New in 0.12.0" section is a *historical* claim that
   was accurate at 0.12.0 and must be left unchanged.)
3. `VERSION` is `0.12.1` while shipped-but-unreleased changes are present, so a
   version-bump decision is required, keeping `VERSION` ↔ `POWER.md` frontmatter ↔
   `CHANGELOG.md` in sync (`validate_power.py` enforces VERSION ↔ frontmatter sync).

**Live inventory re-confirmation:** A live `get_capabilities(version="current")` call
against the connected Senzing MCP server (`sz-mcp-coworker`, `server_version` 1.24.0)
**succeeded** and **positively confirms** the preservation constraints rather than merely
inheriting them from the prior `mcp-tool-inventory-drift` bugfix. The live result reports
`tool_count` 13, with exactly these tools: `get_capabilities`, `mapping_workflow`,
`analyze_record`, `download_resource`, `explain_error_code`, `search_docs`,
`find_examples`, `generate_scaffold`, `get_sample_data`, `get_sdk_reference`, `sdk_guide`,
`reporting_guide`, and `submit_feedback`. **No `lint_record` tool is present.**
`analyze_record` requires the `workspace_dir` parameter (with an optional `file_paths`
array and optional `version`), exposes **no** `record=` and **no** `data_source=`
parameter, and validates records against the Senzing Entity Specification. This live call
therefore confirms the 13-tool inventory in 3.1, the absence of any phantom `lint_record`
(3.1), and the `analyze_record` signature/routing in 2.1/3.2 — and the inventory remains
**unchanged**, so this stays a **documentation-only** bugfix that does not re-derive or
alter the tool inventory.

**Out of scope:** The separate `senzing` reference power (which advertises 14 tools and a
`lint_record` tool) is a **different** repo/power and is not touched by this bugfix — and
it is now additionally contradicted by the live 13-tool, no-`lint_record` result above.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a reader or release process consults `CHANGELOG.md` `[Unreleased]` THEN the system presents an empty section that omits the shipped `mcp-tool-inventory-drift` work (the new `mcp_tool_inventory.py` script, the new `test_mcp_tool_inventory.py` test, the normalized `analyze_record` signature across three documents, and the new `check_mcp_tool_inventory()` gate in `validate_power.py`).
1.2 WHEN a reader consults the current-state pytest claim in the `POWER.md` "What's New in 0.12.1" section THEN the system states "pytest at 4,830 passed / 0 failed", a count that no longer matches the actual passing-test total reported by the live suite.
1.3 WHEN the repository carries shipped-but-unreleased changes THEN the system leaves `VERSION` (`0.12.1`), the `POWER.md` frontmatter version, and `CHANGELOG.md` with no coherent record reconciling the shipped work to a release or an explicit unreleased entry.

### Expected Behavior (Correct)

2.1 WHEN a reader or release process consults `CHANGELOG.md` THEN the system SHALL record the `mcp-tool-inventory-drift` work — under `[Unreleased]` or under a newly chosen version heading — covering the new `mcp_tool_inventory.py` canonical 13-tool single-source-of-truth, the new `test_mcp_tool_inventory.py`, the `analyze_record` signature normalization to `analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")` across `steering/mcp-tool-decision-tree.md`, `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`, and `steering/troubleshooting-commands.md`, and the new `check_mcp_tool_inventory()` gate in `scripts/validate_power.py`.
2.2 WHEN a reader consults the current-state pytest claim in the `POWER.md` "What's New in 0.12.1" section THEN the system SHALL state a passing-test count that equals the actual total reported by running the pytest suite (the exact number determined by running pytest at fix time, not hard-coded from this document).
2.3 WHEN the repository carries the shipped changes THEN the system SHALL apply a coherent version decision — either recording the changes under `[Unreleased]` only, or bumping to a new patch/minor version — such that `VERSION`, the `POWER.md` frontmatter `version`, and `CHANGELOG.md` are mutually consistent and pass the `validate_power.py` VERSION ↔ frontmatter sync check.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the MCP tool inventory is inspected THEN the system SHALL CONTINUE TO list exactly the 13 live tools, report "13 tools" in all counts, and expose no phantom `lint_record` tool (guarded by `test_mcp_tool_inventory.py`).
3.2 WHEN record-validation routing is inspected THEN the system SHALL CONTINUE TO route validation to `analyze_record` exactly as currently documented and tested.
3.3 WHEN the "What's New in 0.12.0" section of `POWER.md` is read THEN the system SHALL CONTINUE TO show its existing historical "4,830 passed / 0 failed / 0 errors" claim unchanged (it was accurate at 0.12.0).
3.4 WHEN any CI gate runs (`validate_power.py`, `measure_steering.py --check`, `sync_hook_registry.py --verify`, `validate_commonmark.py`, and the full pytest suite) THEN the system SHALL CONTINUE TO pass with 0 failures after the documentation edits.
3.5 WHEN scripts, tests, hooks, or steering logic are inspected THEN the system SHALL CONTINUE TO behave identically — no behavioral or script-logic changes, stdlib-only, CommonMark-compliant, and the only MCP server URL confined to `mcp.json`.
3.6 WHEN the separate `senzing` reference power (14 tools / `lint_record`) is inspected THEN the system SHALL CONTINUE TO be untouched by this bugfix, as it is a different repo/power and out of scope.

## Bug Condition and Properties

The "input" `X` is a documentation-fact query — a (document, fact) pair that a reader, a
release process, or a CI gate resolves against the repository's release-facing
documentation. `F` is the documentation state before the fix; `F'` is the documentation
state after the fix.

### Bug Condition — C(X)

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type DocFactQuery   // (document, fact) being resolved
  OUTPUT: boolean

  // Returns true for the three drifted facts only
  RETURN
    (X = CHANGELOG.Unreleased AND mcpToolInventoryDriftWork NOT recorded anywhere in CHANGELOG)
    OR
    (X = POWER.md."What's New in 0.12.1".currentPytestCount AND X.value <> actualPytestPassedCount())
    OR
    (X = VersionRecordCoherence
       AND shippedUnreleasedChangesPresent()
       AND NOT (VERSION, POWER.frontmatter.version, CHANGELOG) are mutually reconciled)
END FUNCTION
```

### Property — Fix Checking (for all buggy inputs)

```pascal
// Property: every drifted fact is corrected by the fix
FOR ALL X WHERE isBugCondition(X) DO
  result <- resolveDoc'(X)        // resolve against post-fix documentation F'

  ASSERT CASE X OF
    CHANGELOG.Unreleased:
      result records the mcp-tool-inventory-drift work
        (mcp_tool_inventory.py, test_mcp_tool_inventory.py,
         analyze_record signature normalization across the 3 named docs,
         check_mcp_tool_inventory() gate in validate_power.py)

    POWER.md."What's New in 0.12.1".currentPytestCount:
      result = actualPytestPassedCount()   // measured by running pytest, not hard-coded

    VersionRecordCoherence:
      reconciled(VERSION, POWER.frontmatter.version, CHANGELOG)
        AND validate_power.py VERSION<->frontmatter sync check passes
  END CASE
END FOR
```

### Property — Preservation Checking (for all non-buggy inputs)

```pascal
// Property: every fact NOT in the bug condition is byte-for-byte unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT resolveDoc(X) = resolveDoc'(X)    // F(X) = F'(X)
END FOR

// Concretely, preservation MUST hold for at least:
//   - the 13-tool inventory, "13 tools" counts, and absence of lint_record
//   - analyze_record validation routing
//   - POWER.md "What's New in 0.12.0" historical "4,830 passed" claim
//   - all CI gates remaining green (0 failures)
//   - all script/test/hook/steering logic (no behavioral change)
//   - the separate `senzing` reference power
```

### Counterexamples (concrete evidence of the bug)

- `CHANGELOG.md` `[Unreleased]` is an empty heading immediately followed by
  `## [0.12.1]`, while `git` HEAD (`mcp-tool-inventory-drift`) shows shipped script + test
  + gate additions — recorded nowhere.
- `POWER.md` line under "What's New in 0.12.1": "...pytest at 4,830 passed / 0 failed",
  contradicted by the live suite's higher passing-test total.
