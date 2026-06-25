# Power Documentation Drift Cleanup Bugfix Design

## Overview

A consistency audit of the `senzing-bootcamp` Kiro Power found three **documentation
drift** defects: shipped, tested code from the `mcp-tool-inventory-drift` work is not
recorded in `CHANGELOG.md`; the `POWER.md` "What's New in 0.12.1" section claims a
current pytest passing count (`4,830 passed`) that no longer matches the live suite; and
the repository carries shipped-but-unreleased changes without a coherent version record
reconciling `VERSION`, the `POWER.md` frontmatter, and `CHANGELOG.md`.

The fix is **documentation-only**. It edits exactly three release-facing artifacts
(`CHANGELOG.md`, `POWER.md`, and — under one version option — `VERSION`). It changes no
script logic, no test assertion, no hook, no steering routing, and does not re-derive or
alter the MCP tool inventory. The strategy is framed with the bug-condition methodology:
each of the three drifted facts is a buggy input `X` where `isBugCondition(X)` is true and
must be corrected (Fix-Checking), while every other documentation fact — the 13-tool
inventory, the `analyze_record` routing, the 0.12.0 historical claim, and all CI-gate
behavior — must remain byte-for-byte identical (Preservation, `F(X) = F'(X)`).

The power is currently GREEN on every automated gate. The drift is invisible to CI
because the gates check internal consistency, not the freshness of the human-readable
release record. The fix must leave every gate green while making the record accurate.

## Glossary

- **Bug_Condition (C)**: The condition identifying a drifted documentation fact — one of
  the three `(document, fact)` pairs where the release-facing record disagrees with the
  shipped reality (empty `[Unreleased]`, stale current pytest count, unreconciled version
  record).
- **Property (P)**: The desired post-fix behavior — the `CHANGELOG` records the shipped
  work, the "What's New in 0.12.1" current pytest count equals the measured passing total,
  and `VERSION` ↔ frontmatter ↔ `CHANGELOG` are mutually coherent.
- **Preservation**: Every documentation fact NOT in the bug condition must be unchanged —
  notably the 13-tool inventory and "13 tools" counts, the absence of `lint_record`, the
  `analyze_record` validation routing, the 0.12.0 historical `4,830 passed` claim, all CI
  gate behavior, and the separate `senzing` reference power.
- **DocFactQuery (X)**: A `(document, fact)` pair that a reader, release process, or CI
  gate resolves against the power's documentation. `F` is the documentation state before
  the fix; `F'` is the state after the fix.
- **`actualPytestPassedCount()`**: The authoritative passing-test total obtained by
  running the full pytest suite at implementation time. It is NOT hard-coded from this
  document.
- **`check_version_sync()`**: The `scripts/validate_power.py` gate that asserts the
  `VERSION` file value equals the `POWER.md` frontmatter `version` value.
- **`mcp-tool-inventory-drift`**: The HEAD commit whose shipped code (canonical 13-tool
  inventory script, its test, an `analyze_record` signature normalization, and a new
  `validate_power.py` gate) is the unrecorded work this fix documents.

## Bug Details

### Bug Condition

The bug manifests when a reader, release process, or CI gate resolves one of three
specific `(document, fact)` queries against the power's release-facing documentation and
the documentation disagrees with the shipped, tested reality of the repository. The
documentation is either silent (empty `[Unreleased]`), numerically stale (current pytest
count), or internally unreconciled (version record). No other documentation fact is
affected.

**Formal Specification:**

```text
FUNCTION isBugCondition(X)
  INPUT: X of type DocFactQuery   // (document, fact) being resolved
  OUTPUT: boolean

  // True for exactly the three drifted facts
  RETURN
    (X = CHANGELOG.Unreleased
       AND mcpToolInventoryDriftWork NOT recorded anywhere in CHANGELOG)
    OR
    (X = POWER.md."What's New in 0.12.1".currentPytestCount
       AND X.value <> actualPytestPassedCount())
    OR
    (X = VersionRecordCoherence
       AND shippedUnreleasedChangesPresent()
       AND NOT reconciled(VERSION, POWER.frontmatter.version, CHANGELOG))
END FUNCTION
```

### Examples

- **CHANGELOG.Unreleased (buggy):** `CHANGELOG.md` shows `## [Unreleased]` as an empty
  heading immediately followed by `## [0.12.1] - 2026-06-08`. Expected: the section (or a
  new version heading) records the `mcp-tool-inventory-drift` work. Actual: nothing is
  recorded, though `git` HEAD shows the shipped script, test, and gate.
- **POWER.md current pytest count (buggy):** The "What's New in 0.12.1" bullet reads
  `...the full CI suite is now green, with pytest at 4,830 passed / 0 failed`. Expected:
  the count equals `actualPytestPassedCount()` (a full-suite run during analysis reported
  `4868 passed / 86 skipped`, but the implementer must re-run pytest for the authoritative
  number). Actual: it states `4,830`, which the live suite contradicts.
- **VersionRecordCoherence (buggy):** `VERSION` is `0.12.1`, the `POWER.md` frontmatter is
  `version: "0.12.1"`, and `CHANGELOG.md` carries shipped-but-unreleased changes with no
  reconciling record. Expected: a coherent version decision (see Fix Implementation).
- **13-tool inventory (NOT buggy — preserved):** A query for the MCP tool count resolves
  to "13 tools" with no `lint_record`. Live `get_capabilities(version="current")` against
  `sz-mcp-coworker` v1.24.0 confirms this. `isBugCondition` is false; it must not change.
- **0.12.0 historical claim (NOT buggy — preserved):** The "What's New in 0.12.0" bullet
  states `pytest at 4,830 passed / 0 failed / 0 errors`. This was accurate at 0.12.0;
  `isBugCondition` is false; it must remain unchanged.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- The MCP tool inventory continues to list exactly the 13 live tools, all "13 tools"
  counts are unchanged, and no phantom `lint_record` tool appears (guarded by
  `test_mcp_tool_inventory.py` and `check_mcp_tool_inventory()`).
- Record-validation routing continues to route to `analyze_record` exactly as currently
  documented and tested, with the `analyze_record(file_paths=[...], workspace_dir="<dir>",
  version="current")` signature unchanged.
- The `POWER.md` "What's New in 0.12.0" historical `4,830 passed / 0 failed / 0 errors`
  claim remains byte-for-byte unchanged.
- Every CI gate (`validate_power.py`, `measure_steering.py --check`,
  `sync_hook_registry.py --verify`, `validate_commonmark.py`, and the full pytest suite)
  continues to pass with 0 failures.
- All script, test, hook, and steering logic behaves identically — stdlib-only,
  CommonMark-compliant, with the only MCP server URL confined to `mcp.json`.
- The separate `senzing` reference power (14 tools / `lint_record`) is untouched.

**Scope:**

All documentation facts that do NOT satisfy `isBugCondition` must be completely unaffected
by this fix. This includes:

- Every existing `CHANGELOG.md` version section from `[0.12.1]` downward.
- Every `POWER.md` section other than the single "What's New in 0.12.1" current pytest
  count (and, under the version-bump option, the frontmatter `version` line).
- Every non-documentation file in the repository — scripts, tests, hooks, steering, and
  config.

The actual expected correct behavior for the buggy facts is defined in the Correctness
Properties section (Property 1).

## Hypothesized Root Cause

This is a process/record drift, not a code defect. Based on the audit, the causes are:

1. **Missing release-note step on the prior bugfix.** The `mcp-tool-inventory-drift` work
   shipped code, a test, and a CI gate but its workflow did not append a `CHANGELOG.md`
   `[Unreleased]` entry, so the section remained empty.

2. **Hard-coded test count in narrative prose.** The "What's New in 0.12.1" pytest count
   was written as a literal (`4,830`) rather than regenerated from a live run, so suite
   growth (new tests including `test_mcp_tool_inventory.py`) silently invalidated it.

3. **No version-decision checkpoint for unreleased work.** Because CI only enforces
   `VERSION` ↔ frontmatter sync (not `CHANGELOG` heading sync), shipped-but-unreleased
   changes accumulated without forcing a "record under `[Unreleased]` vs bump version"
   decision.

4. **CI blind spot.** The gates verify internal consistency, so a stale-but-consistent
   record passes silently — there is no gate that compares the human-readable release
   narrative against shipped git history.

## Correctness Properties

Property 1: Bug Condition - Drifted Documentation Facts Are Corrected

_For any_ documentation-fact query `X` where the bug condition holds (`isBugCondition(X)`
returns true), the fixed documentation `F'` SHALL resolve `X` correctly: the
`CHANGELOG.md` SHALL record the `mcp-tool-inventory-drift` work (the new
`senzing-bootcamp/scripts/mcp_tool_inventory.py` canonical 13-tool single source of truth,
the new `senzing-bootcamp/tests/test_mcp_tool_inventory.py`, the `analyze_record`
signature normalization to `analyze_record(file_paths=[...], workspace_dir="<dir>",
version="current")` across `steering/mcp-tool-decision-tree.md`,
`docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`, and
`steering/troubleshooting-commands.md`, and the new `check_mcp_tool_inventory()` gate in
`scripts/validate_power.py`); the `POWER.md` "What's New in 0.12.1" current pytest count
SHALL equal `actualPytestPassedCount()` measured by running pytest at fix time; and
`VERSION`, the `POWER.md` frontmatter `version`, and `CHANGELOG.md` SHALL be mutually
reconciled such that `check_version_sync()` passes.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Drifted Documentation Facts Are Unchanged

_For any_ documentation-fact query `X` where the bug condition does NOT hold
(`isBugCondition(X)` returns false), the fixed documentation `F'` SHALL produce exactly the
same result as the original documentation `F` (`F(X) = F'(X)`), preserving the 13-tool
inventory and "13 tools" counts with no `lint_record`, the `analyze_record` validation
routing, the `POWER.md` "What's New in 0.12.0" historical `4,830 passed` claim, all CI gate
behavior (0 failures), all script/test/hook/steering logic, and the separate `senzing`
reference power.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

This fix touches at most three files. Defect 1 (CHANGELOG) and Defect 2 (pytest count) are
fixed unconditionally. Defect 3 (version coherence) is resolved by choosing one of two
options below; the chosen option determines whether `VERSION` and the frontmatter change.

**File 1 — `senzing-bootcamp/CHANGELOG.md` (Defect 1, always)**

Record the `mcp-tool-inventory-drift` work. Under **Option A** the entry goes under the
existing `## [Unreleased]` heading; under **Option B** a new `## [0.12.2] - <date>` heading
replaces the empty `[Unreleased]` (and a fresh empty `[Unreleased]` may sit above it). The
entry content is identical either way:

```text
### Added

- `scripts/mcp_tool_inventory.py` — canonical single source of truth for the
  13-tool MCP inventory (ALL_TOOLS + TOTAL_COUNT), confirmed live against
  get_capabilities(version="current") on sz-mcp-coworker v1.24.0
- `tests/test_mcp_tool_inventory.py` — pins the 13-tool inventory and the
  absence of any lint_record tool
- `check_mcp_tool_inventory()` gate in `scripts/validate_power.py` — fails CI if
  POWER.md / ARCHITECTURE.md tool listings drift from mcp_tool_inventory.py

### Changed

- Normalized the `analyze_record` call signature to
  `analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")`
  across `steering/mcp-tool-decision-tree.md`,
  `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`, and
  `steering/troubleshooting-commands.md`
```

Placement: this content replaces the empty body of the `[Unreleased]` section (Option A)
or becomes the body of the new `[0.12.2]` section directly above `## [0.12.1]` (Option B).
The wording is descriptive of shipped reality; do not invent scope beyond the four shipped
items.

**File 2 — `senzing-bootcamp/POWER.md` "What's New in 0.12.1" (Defect 2, always)**

Edit the single bullet whose current text is:

```text
- "Lint Python (ruff)" CI gate brought from 438 violations to 0 — the full CI suite is now green, with pytest at 4,830 passed / 0 failed
```

Replace `4,830` with the value of `actualPytestPassedCount()` measured at fix time (see
Test-Count Reconciliation below). Keep the rest of the bullet intact. Do **not** touch the
"What's New in 0.12.0" bullet that reads `pytest at 4,830 passed / 0 failed / 0 errors` —
that is the preserved historical claim (Requirement 3.3). The two bullets are textually
similar but only the 0.12.1 occurrence is in the bug condition; match on the surrounding
"0.12.1" / "ruff" / "now green" context to edit the correct line.

**File 3 — `senzing-bootcamp/VERSION` + `POWER.md` frontmatter (Defect 3, Option B only)**

Under Option B, set `VERSION` to `0.12.2` and update the `POWER.md` frontmatter
`version: "0.12.1"` to `version: "0.12.2"` so `check_version_sync()` stays green. Under
Option A, both files are left unchanged.

### Version Decision (Defect 3)

The requirements allow either option; this is a judgment call left to the implementer/user.

- **Option A — Record under `[Unreleased]` only.** Keep `VERSION` at `0.12.1` and the
  frontmatter at `0.12.1`. The shipped work lives under `[Unreleased]` until a future
  release cuts it. `check_version_sync()` already passes (both are `0.12.1`) and stays
  untouched. Smallest change; lowest risk. Tradeoff: the shipped, tested work remains
  formally "unreleased," so the installed power's advertised version (`0.12.1`) does not
  signal that the inventory gate is present.

- **Option B — Bump to `0.12.2` (recommended).** Move the entry under a new
  `## [0.12.2] - <date>` heading, set `VERSION` to `0.12.2`, and set the frontmatter
  `version` to `0.12.2`. All three records (`VERSION` ↔ frontmatter ↔ `CHANGELOG` heading)
  then describe the same released state. Tradeoff: touches one more file (`VERSION`) and
  the frontmatter, so the version-sync gate and CommonMark must be re-verified after the
  edit.

**Recommendation:** Option B. The `mcp-tool-inventory-drift` work shipped real code, a
test, and a CI gate; a patch bump makes the release record honestly reflect what users
install and keeps all three version records mutually coherent rather than leaving tested
behavior indefinitely "unreleased." Both options are kept viable because the
release-cadence call belongs to the maintainer.

### Test-Count Reconciliation Approach

The new count is **measured, not transcribed**. At implementation time:

1. Run the full pytest suite from the repository root (the same invocation CI uses) and
   read the summary line, e.g. `==== N passed, M skipped in ... ====`.
2. Use `N` (the passed count) as `actualPytestPassedCount()`. Analysis-time observation was
   `4868 passed / 86 skipped`, but the implementer MUST use the value from their own run;
   the suite count can move as tests are added.
3. Write `N` into the "What's New in 0.12.1" bullet using the existing thousands-separator
   formatting (e.g. `4,868`). Preserve the `/ 0 failed` phrasing if and only if the run
   reports 0 failures; if failures appear, stop and treat that as a separate problem (a
   green suite is a precondition per Requirement 3.4).

Note the existing 0.12.1 bullet says `4,830 passed / 0 failed` (no `/ 0 errors`), while the
0.12.0 bullet says `4,830 passed / 0 failed / 0 errors`. Edit only the 0.12.1 phrasing and
keep its existing structure (`passed / failed`) — do not import the `/ 0 errors` clause
from the 0.12.0 line.

### CI Gate Re-Verification

After the edits, re-run every gate to confirm Preservation (Requirement 3.4):

- **`validate_power.py`** — confirms `check_version_sync()` passes (`VERSION` ==
  frontmatter, trivially under Option A, and at `0.12.2` under Option B) and
  `check_mcp_tool_inventory()` still passes (no inventory change). CHANGELOG is only checked
  for existence, so its new content cannot break this gate.
- **`measure_steering.py --check`** — unaffected; no steering file is edited.
- **`sync_hook_registry.py --verify`** — unaffected; no hook is edited.
- **`validate_commonmark.py`** — re-verify because `CHANGELOG.md` and `POWER.md` are edited.
  Keep list markers, blank-line spacing, and fenced-code conventions consistent with the
  existing files so MD rules stay satisfied. (`validate_links.py` excludes `CHANGELOG.md`,
  so changelog URLs are not re-checked.)
- **Full pytest suite** — re-run to confirm 0 failures and to source the authoritative
  passing count for Defect 2. No test asserts on `CHANGELOG`/`POWER.md` prose counts, so the
  edits do not change pass/fail outcomes.

## Testing Strategy

### Validation Approach

Because this is a documentation-only fix with no executable behavior change, the "tests"
are gate runs and targeted documentation assertions rather than new unit logic. The
approach still follows two phases: first observe the drift on the unfixed docs
(counterexamples), then verify the fix corrects each drifted fact while every preserved
fact and every CI gate is unchanged.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples demonstrating the drift BEFORE editing, and confirm the
root-cause analysis (record drift, not code defect).

**Test Plan**: Inspect the unfixed documents and `git` HEAD to capture each drifted fact.
Confirm the suite count and tool inventory against live reality so the fix targets only
documentation.

**Test Cases**:

1. **Empty Unreleased**: Confirm `CHANGELOG.md` `[Unreleased]` is an empty heading while
   `git` HEAD (`mcp-tool-inventory-drift`) shows the shipped script, test, and gate (drift
   present on unfixed docs).
2. **Stale pytest count**: Run pytest and confirm the passing total differs from the
   `4,830` stated in "What's New in 0.12.1" (drift present on unfixed docs).
3. **Version incoherence**: Confirm `VERSION` is `0.12.1` with shipped-but-unreleased
   changes and no reconciling `CHANGELOG` record (drift present on unfixed docs).
4. **Inventory sanity (edge)**: Confirm via live `get_capabilities(version="current")` that
   the inventory is 13 tools with no `lint_record` — establishing it is NOT in the bug
   condition and must be preserved.

**Expected Counterexamples**:

- `[Unreleased]` empty despite shipped HEAD work.
- Measured pytest passing count > `4,830`.
- Root cause confirmed as missing release-record steps, not a code fault.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed
documentation produces the expected behavior.

**Pseudocode:**

```text
FOR ALL X WHERE isBugCondition(X) DO
  result := resolveDoc_fixed(X)
  ASSERT CASE X OF
    CHANGELOG.Unreleased:
      result records mcp_tool_inventory.py, test_mcp_tool_inventory.py,
        analyze_record signature normalization across the 3 named docs,
        and check_mcp_tool_inventory() gate
    POWER.md."What's New in 0.12.1".currentPytestCount:
      result = actualPytestPassedCount()      // measured, not hard-coded
    VersionRecordCoherence:
      reconciled(VERSION, POWER.frontmatter.version, CHANGELOG)
        AND check_version_sync() passes
  END CASE
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed
documentation produces the same result as the original.

**Pseudocode:**

```text
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT resolveDoc_original(X) = resolveDoc_fixed(X)    // F(X) = F'(X)
END FOR
```

**Testing Approach**: For documentation, preservation is checked by (a) confirming the
existing CI gates remain green after edits and (b) diff-scoping — verifying the patch
touches only the three intended facts. The existing `test_mcp_tool_inventory.py` plus
`check_mcp_tool_inventory()` already act as property-style guards that the 13-tool
inventory and absence of `lint_record` are unchanged; re-running them confirms preservation
across the whole inventory domain rather than a single spot check.

**Test Plan**: Observe the preserved facts on unfixed docs, apply the edits, then re-run all
gates and re-read the preserved facts to confirm they are identical.

**Test Cases**:

1. **0.12.0 historical claim**: Confirm "What's New in 0.12.0" still reads `4,830 passed /
   0 failed / 0 errors` after the fix (unchanged).
2. **13-tool inventory**: Re-run `test_mcp_tool_inventory.py` and `check_mcp_tool_inventory()`
   — still 13 tools, no `lint_record`.
3. **analyze_record routing**: Confirm validation routing and the documented signature are
   unchanged.
4. **Version sync**: Confirm `check_version_sync()` passes (Option A: both `0.12.1`; Option
   B: both `0.12.2`).
5. **Separate `senzing` power**: Confirm it is untouched.

### Unit Tests

- No new unit tests are added (documentation-only fix; no executable behavior to assert).
- Existing inventory unit tests (`test_mcp_tool_inventory.py`) are re-run unchanged to guard
  the preserved inventory.

### Property-Based Tests

- No new property-based tests are added. The preservation property `F(X) = F'(X)` for the
  tool inventory is already enforced over the inventory domain by the existing
  `test_mcp_tool_inventory.py` Hypothesis/assertion coverage and the
  `check_mcp_tool_inventory()` gate, which are re-run to confirm no inventory fact changed.

### Integration Tests

- Run the full CI gate sequence end to end (`validate_power.py`, `measure_steering.py
  --check`, `sync_hook_registry.py --verify`, `validate_commonmark.py`, then full pytest)
  and confirm 0 failures, mirroring the GitHub Actions pipeline.
- Confirm the measured pytest passing count used in POWER.md matches the count reported by
  this same suite run.
